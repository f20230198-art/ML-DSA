"""WP-T: measured full-secret TALUS recovery on real keys with a SHARED challenge set.

Replaces the independence shortcut (item8_full_secret.py: P_full = P_elem^k) and the
grouped-independent-trials run (item8_full_analysis.py, where 4 consecutive trials were 4
INDEPENDENT random targets, not 4 elements of one key). Here:

  * the k targets are the real coefficients of one key's s2 (from keygen_internal), so the
    per-element difficulty is unchanged (s2 entries are uniform on [-eta, eta], the same law
    sample_target used);
  * ALL k elements share ONE challenge set c (drawn once per key), because in the real
    protocol every element sees the same challenge per signature. This is the correlation the
    product approximation dropped: a well-conditioned c helps all k elements at once, so the
    full-secret events are positively correlated and P_full >= P_elem^k;
  * noise is independent per element (LowBits of distinct w coordinates), bound = gamma2-beta.

For each key we AND the k per-element successes to get one full-secret success, then report the
full-secret rate over R keys with a bootstrap CI, next to the per-element rate and the product
prediction p_elem^k, so the independence assumption is validated or refuted, not assumed.

This is the same channel model as talus_bcc.py / the paper (Level 2: a reconstructed channel,
not deployed TALUS v0.22). It does not add any new modelling claim.

Run (ML-DSA-44 first, cheapest):
  python -m experiments.full_secret_real --params ML-DSA-44 \
      --N 55000 60000 65000 70000 --keys 30 --seed 3001 --device gpu
One GPU job at a time; a full set is a multi-day run. Use --keys 2 --N 3000 --device cpu to
smoke-test the plumbing (it will not recover at such small N; it checks the pipeline runs).
"""
import argparse
import json
import os
import time

import numpy as np

from harness.estimators import edge, ilp
from harness.mldsa.dsa import keygen_internal
from harness.mldsa.params import ALL
from harness.mldsa.ringn import get_ring, sample_challenges_n, scaled_tau
from harness.schemes.talus_bcc import make_channel


def real_s2(p, xi):
    """The genuine s2 of a keygen_internal key, centered, shape (k, N)."""
    _, _, sec = keygen_internal(xi, p)
    return np.asarray(sec["s2"], dtype=np.int64)


def shared_transcript(rng, ch, s2, count):
    """Draw ONE challenge set c (count, n) and, for each of the k elements, b_e = -c*s2[e] + e_e
    with independent uniform noise. Yields (c, [b_0..b_{k-1}]). float32 is exact here (|b|<2^24)."""
    ring = get_ring(ch.n)
    c = sample_challenges_n(rng, count, ch.n, ch.tau)
    bs = []
    for e in range(s2.shape[0]):
        cs = np.rint(ring.mul(c, s2[e]))
        noise = rng.integers(-ch.bound, ch.bound + 1, size=cs.shape)
        bs.append((-cs + noise).astype(np.float32))
    return c, bs


def recover_element(c, b, ch, rng, device, time_limit):
    """Edge estimate (GPU or CPU) + ILP finish for one element. Returns (round_ok_vec, ilp_vec)."""
    if device == "gpu":
        from harness.estimators import edge_gpu
        x, _, _ = edge_gpu.chebyshev_cutting_plane_gpu(c, b, ch.target_max + 1, rng)
    else:
        x, _, _ = edge.chebyshev_cutting_plane(c, b, ch.target_max + 1, rng)
    z, _ = ilp.finish(c, b, x, ch.target_max, ch.bound, window=1, time_limit=time_limit)
    return x, z


def boot_ci(successes, iters=20000, seed=0):
    """Bootstrap 95% CI for a mean over a 0/1 list."""
    a = np.asarray(successes, dtype=float)
    if len(a) == 0:
        return (0.0, 0.0)
    r = np.random.default_rng(seed)
    means = a[r.integers(0, len(a), size=(iters, len(a)))].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default="ML-DSA-44", choices=sorted(ALL))
    ap.add_argument("--N", type=int, nargs="+", default=[55000, 60000, 65000, 70000])
    ap.add_argument("--keys", type=int, default=30)
    ap.add_argument("--key-start", type=int, default=None,
                    help="first key index (inclusive); for splitting across machines")
    ap.add_argument("--key-end", type=int, default=None,
                    help="last key index (exclusive); default = --keys")
    ap.add_argument("--seed", type=int, default=3001)
    ap.add_argument("--device", default="gpu", choices=["cpu", "gpu"])
    ap.add_argument("--time-limit", type=float, default=120.0)
    ap.add_argument("--out", default=None,
                    help="default: experiments/results/full_secret_real_<params>.json")
    args = ap.parse_args()
    k0 = 0 if args.key_start is None else args.key_start
    k1 = args.keys if args.key_end is None else args.key_end
    span = "" if (k0 == 0 and k1 == args.keys) else f"_k{k0}-{k1}"
    if args.out is None:
        args.out = f"experiments/results/full_secret_real_{args.params}{span}.json"
    p = ALL[args.params]
    ch = make_channel(p, 256, "bcc", "s2")
    Nmax = max(args.N)
    # per (key, N): list over keys of {element oks}; we AND across elements for full-secret
    rows = []
    # resume: keep rows already in the output file if they came from the same seed and set
    if os.path.exists(args.out):
        old = json.load(open(args.out))
        oa = old.get("args", {})
        if oa.get("seed") == args.seed and oa.get("params") == args.params:
            rows = [r for r in old.get("rows", [])
                    if r["N"] in args.N and k0 <= r["key"] < k1]
            print(f"resuming: {len(rows)} (key, N) rows already done", flush=True)
    done = {(r["key"], r["N"]) for r in rows}
    for key in range(k0, k1):
        if all((key, N) in done for N in args.N):
            continue
        xi = np.random.default_rng([args.seed, key]).bytes(32)
        s2 = real_s2(p, xi)                      # (k, N) real key
        krng = np.random.default_rng([args.seed, key, 7])
        c_full, b_full = shared_transcript(krng, ch, s2, Nmax)
        for N in sorted(args.N):
            if (key, N) in done:
                continue
            t0 = time.time()
            elem_ok = []
            for e in range(p.k):
                rng = np.random.default_rng([args.seed, key, N, e])
                x, z = recover_element(c_full[:N], b_full[e][:N], ch, rng, args.device, args.time_limit)
                r = edge.round_to_range(x, ch.target_max).astype(np.int64)
                elem_ok.append(bool((z == s2[e]).all()))
                _ = r  # round-only success could be logged too; ILP is the reported one
            row = dict(params=p.name, key=key, N=N, k=int(p.k),
                       elem_ok=elem_ok, elem_ok_count=int(sum(elem_ok)),
                       full_ok=bool(all(elem_ok)), seconds=round(time.time() - t0, 1))
            rows.append(row)
            print(json.dumps(row), flush=True)
            tmp = args.out + ".tmp"
            with open(tmp, "w") as f:
                json.dump(dict(args=vars(args), rows=rows), f, indent=1)
            os.replace(tmp, args.out)   # atomic: a crash mid-write cannot corrupt the file

    print_summary(rows, p)


def print_summary(rows, p):
    """Full-secret rate per N over however many keys `rows` holds. Shared by the merge script."""
    Ns = sorted({r["N"] for r in rows})
    nkeys = len({r["key"] for r in rows})
    print(f"\n{p.name}: full-secret recovery on {nkeys} real keys, shared challenges "
          f"(cap depends on set; model = reconstructed BCC channel, Level 2)")
    print("      N   full ok   95% CI (bootstrap)   per-elem   p_elem^k (indep. prediction)")
    for N in Ns:
        rs = [r for r in rows if r["N"] == N]
        full = [r["full_ok"] for r in rs]
        pe = np.mean([r["elem_ok_count"] for r in rs]) / p.k
        lo, hi = boot_ci(full, seed=N)
        print(f"{N:8d}   {np.mean(full):5.2f}   [{lo:.2f}, {hi:.2f}]        "
              f"{pe:.3f}      {pe ** p.k:.3f}   (n={len(full)})")
    print("If 'full ok' sits ABOVE p_elem^k, the shared challenge makes the events positively "
          "correlated and the independence extrapolation was pessimistic (threshold is lower).")


if __name__ == "__main__":
    main()
