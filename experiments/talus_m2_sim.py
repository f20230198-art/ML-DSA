"""Paper plan item 3: simulate the TALUS MPC insider with m = 2 honest nonce shares (triangular noise).

Channel (arXiv 2603.22109v5 App. D): after subtracting its own shares the insider sees
  z' = y_h + c s1,  y_h = u1 + u2,  u_i uniform on w consecutive integers (w = 2 gamma1 / nu).
We scale the ring and w down (n, tau, w free) so that the success threshold is reachable in seconds, find the
smallest N giving exact recovery with probability 50% / 95% for two estimators:
  LS : least squares then rounding;
  ML : maximum likelihood for the triangular density (concave: sum log(w - |r|)), Newton from the
       Chebyshev-LP start so every residual is inside the support.
and compare with the Fisher-rate prediction q = 4 / (I tau) used in talus_insider_wall.py, where
I is the exact discrete bulk information of the triangle (talus_m2_fisher.py).

Run: python -m experiments.talus_m2_sim --w 32 64 128 --n 8 --tau 4 --trials 20
"""
import argparse
import json
import math

import numpy as np

from harness.estimators import edge
from harness.mldsa.ringn import get_ring, sample_challenges_n
from experiments.talus_m2_fisher import bulk_info


def make(rng, n, tau, w, N, eta):
    s = rng.integers(-eta, eta + 1, size=n)
    c = sample_challenges_n(rng, N, n, tau)
    ring = get_ring(n)
    cs = np.rint(ring.mul(c, s.astype(float))).astype(np.int64)
    u = rng.integers(0, w, size=(2, N, n))
    e = u[0] + u[1] - (w - 1)            # triangle on [-(w-1), w-1]
    return s, c, cs + e


def ml_estimate(c, z, w, x0, iters=60):
    """Maximise sum log(w - |z - c x|) (continuous triangle of half-width w) by damped Newton."""
    ring = get_ring(c.shape[1])
    n = c.shape[1]
    x = x0.copy()
    N = c.shape[0]
    cf = c.astype(float)

    def resid(x):
        return z - ring.mul(cf, x)

    def objective(r):
        d = w - np.abs(r)
        if (d <= 0).any():
            return np.inf
        return -np.log(d).sum()

    r = resid(x)
    f = objective(r)
    for _ in range(iters):
        d = w - np.abs(r)
        sg = np.sign(r)
        # d f/dr = sg / d ; d2 f/dr2 = 1 / d^2 ; r = z - C x so grad_x = -C^T (sg/d)
        g1 = sg / d
        wgt = 1.0 / d ** 2
        grad = -(ring.mul(_adj(cf), g1)).sum(axis=0)
        # Hessian: sum_i C_i^T diag(wgt_i) C_i, built row-block by block with matrices of the ring
        H = np.zeros((n, n))
        for k in range(n):
            ek = np.zeros(n)
            ek[k] = 1.0
            ck = ring.mul(cf, ek)                 # (N, n): column k of every block
            H[:, k] = (ring.mul(_adj(cf), wgt * ck)).sum(axis=0)
        H += 1e-12 * np.eye(n)
        try:
            step = -np.linalg.solve(H, grad)
        except np.linalg.LinAlgError:
            break
        t = 1.0
        while t > 1e-6:
            r2 = resid(x + t * step)
            f2 = objective(r2)
            if f2 < f:
                break
            t /= 2
        else:
            break
        x, r, f = x + t * step, r2, f2
        if np.abs(t * step).max() < 1e-7:
            break
    return x


def _adj(c):
    out = np.empty_like(c)
    out[..., 0] = c[..., 0]
    out[..., 1:] = -c[..., :0:-1]
    return out


def trial(seed, n, tau, w, N, eta):
    rng = np.random.default_rng(seed)
    s, c, z = make(rng, n, tau, w, N, eta)
    ring = get_ring(n)
    # LS via normal equations
    cf = c.astype(float)
    M = np.zeros((n, n))
    for k in range(n):
        ek = np.zeros(n)
        ek[k] = 1
        ck = ring.mul(cf, ek)
        M[:, k] = ring.mul(_adj(cf), ck).sum(axis=0)
    rhs = ring.mul(_adj(cf), z.astype(float)).sum(axis=0)
    x_ls = np.linalg.solve(M, rhs)
    ok_ls = bool((np.clip(np.rint(x_ls), -eta, eta) == s).all())
    # feasible start for ML: shrink LS toward the box until inside support
    x0 = np.clip(np.rint(x_ls), -eta, eta).astype(float)
    r0 = np.abs(z - ring.mul(cf, x0)).max()
    if r0 >= w:                                   # fall back: scale step to the LP start
        A = edge.negacyclic_rows(c.astype(np.int64))
        x0, _ = edge.chebyshev(A, -z.astype(float).ravel())
        x0 = -x0 if np.abs(z - ring.mul(cf, x0)).max() >= w else x0
    xm = ml_estimate(c, z.astype(float), w, x0)
    ok_ml = bool((np.clip(np.rint(xm), -eta, eta) == s).all())
    return ok_ls, ok_ml


def threshold(results, target):
    pts = sorted(results.items())
    for (n0, s0), (n1, s1) in zip(pts, pts[1:]):
        if s0 < target <= s1:
            f = (target - s0) / (s1 - s0)
            return math.exp(math.log(n0) + f * (math.log(n1) - math.log(n0)))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=int, nargs="+", default=[32, 64, 128])
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--tau", type=int, default=4)
    ap.add_argument("--eta", type=int, default=2)
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--seed", type=int, default=2061)
    ap.add_argument("--out", default="experiments/results/talus_m2_sim.json")
    args = ap.parse_args()
    out = []
    for w in args.w:
        pred = 4 / (bulk_info(w) * args.tau)
        # sweep N around the prediction (x 0.1 .. x 6)
        grid = sorted({max(50, int(pred * f)) for f in (0.1, 0.2, 0.4, 0.7, 1.0, 1.5, 2.5, 4.0, 6.0)})
        ls, ml = {}, {}
        for N in grid:
            res = [trial([args.seed, w, N, t], args.n, args.tau, w, N, args.eta) for t in range(args.trials)]
            ls[N] = float(np.mean([r[0] for r in res]))
            ml[N] = float(np.mean([r[1] for r in res]))
            print(f"w={w} N={N} (pred {pred:.0f}) LS {ls[N]:.2f} ML {ml[N]:.2f}", flush=True)
        row = dict(w=w, n=args.n, tau=args.tau, trials=args.trials, pred_wall=pred, ls=ls, ml=ml,
                   N50_ls=threshold(ls, 0.5), N50_ml=threshold(ml, 0.5), N95_ml=threshold(ml, 0.95))
        out.append(row)
        print(f"w={w}: predicted wall {pred:.0f}; N50 LS {row['N50_ls']}, N50 ML {row['N50_ml']}, N95 ML {row['N95_ml']}",
              flush=True)
        json.dump(out, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
