"""Edge-aware (Chebyshev) estimator vs least squares on the TALUS s2 channel, scaling ladder.

For each ring size n and each signature count N: draw fresh secrets and transcripts, run both
estimators, and record the maximum coefficient error, the exact-recovery rate after rounding,
and whether the rounded edge estimate is a feasible explanation of ALL observations.
Results are appended to a JSON file after every point, so an interrupted run can be resumed.

Run from the repo root (nothing here has been executed yet; see docs/RUNBOOK.md):

  python -m experiments.talus_edge_scaling --n 8 16 32 --trials 20            # small, minutes
  python -m experiments.talus_edge_scaling --n 64 --trials 10 --steps 6        # longer
  python -m experiments.talus_edge_scaling --n 256 --trials 3 --steps 5 --noise bcc --solver cp
  python -m experiments.talus_edge_scaling --summary experiments/results/talus_edge_ML-DSA-44_bcc_s2.json

Model and caveats: harness/schemes/talus_bcc.py.
"""
import argparse
import json
import math
import os
import time

import numpy as np

from harness.estimators import edge
from harness.mldsa.params import ALL
from harness.schemes.talus_bcc import make_channel, make_transcript, sample_target


def solve_edge(c, b, ch, solver, rng):
    if solver == "lp":
        A = edge.negacyclic_rows(c.astype(np.int64))
        x, _ = edge.chebyshev(A, b.astype(float).ravel())
        return x, None
    x, _, info = edge.chebyshev_cutting_plane(c, b, ch.target_max + 1, rng)
    return x, info


def run_point(p, n, count, trials, noise, target, solver, seed):
    ch = make_channel(p, n, noise, target)
    rows = []
    for trial in range(trials):
        rng = np.random.default_rng([seed, n, count, trial])
        s = sample_target(rng, ch)
        c, b = make_transcript(rng, ch, s, count)
        t0 = time.time()
        xe, info = solve_edge(c, b, ch, solver, rng)
        t_edge = time.time() - t0
        xl = edge.least_squares_cg(c, b)
        re = edge.round_to_range(xe, ch.target_max)
        rl = edge.round_to_range(xl, ch.target_max)
        rows.append(dict(
            err_edge=float(np.abs(xe - s).max()),
            err_ls=float(np.abs(xl - s).max()),
            ok_edge=bool((re == s).all()),
            ok_ls=bool((rl == s).all()),
            feasible_rounded=bool(edge.is_feasible(c, b, re, ch.bound)),
            true_feasible=bool(edge.is_feasible(c, b, s.astype(float), ch.bound)),
            seconds=t_edge,
            converged=None if info is None else info["converged"],
        ))
    return ch, rows


def point_summary(ch, count, rows):
    a = lambda k: np.array([r[k] for r in rows], dtype=float)
    return dict(
        n=ch.n, tau=ch.tau, bound=ch.bound, N=count, trials=len(rows),
        succ_edge=a("ok_edge").mean(), succ_ls=a("ok_ls").mean(),
        err_edge_med=float(np.median(a("err_edge"))), err_ls_med=float(np.median(a("err_ls"))),
        K_hat=float(np.median(a("err_edge")) * count / ch.bound),
        feasible_rounded=a("feasible_rounded").mean(),
        true_feasible=a("true_feasible").mean(),
        seconds=float(a("seconds").mean()),
    )


def nstar(points, target):
    """Smallest N with success >= target, by log-linear interpolation; None if not bracketed."""
    pts = sorted((q["N"], q["succ_edge"]) for q in points)
    for (n0, s0), (n1, s1) in zip(pts, pts[1:]):
        if s0 < target <= s1:
            f = (target - s0) / (s1 - s0) if s1 > s0 else 1.0
            return math.exp(math.log(n0) + f * (math.log(n1) - math.log(n0)))
    if pts and pts[0][1] >= target:
        return float(pts[0][0])  # already above target at the smallest N: upper bound only
    return None


def summarize(path):
    data = json.load(open(path))
    pts = data["points"]
    print(f"{data['params']} noise={data['noise']} target={data['target']} solver={data['solver']}")
    for n in sorted({q["n"] for q in pts}):
        sub = [q for q in pts if q["n"] == n]
        print(f"\nn={n} tau={sub[0]['tau']} bound={sub[0]['bound']}")
        print(f"{'N':>9} {'ok edge':>8} {'ok LS':>6} {'err edge':>9} {'err LS':>9} {'K_hat':>6} {'feas':>5}")
        for q in sorted(sub, key=lambda q: q["N"]):
            print(f"{q['N']:>9} {q['succ_edge']:>8.2f} {q['succ_ls']:>6.2f} {q['err_edge_med']:>9.3f} "
                  f"{q['err_ls_med']:>9.1f} {q['K_hat']:>6.2f} {q['feasible_rounded']:>5.2f}")
        big = [q for q in sub if q["err_edge_med"] > 0]
        if len(big) >= 2:
            x = np.log([q["N"] for q in big])
            y = np.log([q["err_edge_med"] for q in big])
            lx = np.log([q["N"] for q in sub])
            ly = np.log([max(q["err_ls_med"], 1e-9) for q in sub])
            print(f"  fitted slope log(err)/log(N): edge {np.polyfit(x, y, 1)[0]:.2f}, "
                  f"LS {np.polyfit(lx, ly, 1)[0]:.2f}  (1/N law = -1, 1/sqrt(N) law = -0.5)")
        for tgt in (0.5, 0.99):
            v = nstar(sub, tgt)
            print(f"  N*(success>={tgt}) per ring element: {'not bracketed' if v is None else f'{v:.3g}'}")
    print("\nFull-secret recovery over k ring elements needs success^k; see docs/RUNBOOK.md step 5.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default="ML-DSA-44", choices=list(ALL))
    ap.add_argument("--n", type=int, nargs="+", default=[8, 16, 32])
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--steps", type=int, default=8, help="grid points in N per ring size")
    ap.add_argument("--lo", type=float, default=0.25, help="grid start, x N0")
    ap.add_argument("--hi", type=float, default=2.5, help="grid end, x N0")
    ap.add_argument("--k0", type=float, default=1.5, help="guess of err*N/bound; N0 = 2*k0*bound")
    ap.add_argument("--noise", default="bcc", choices=["bcc", "plain"])
    ap.add_argument("--target", default="s2", choices=["s2", "s2-t0"])
    ap.add_argument("--solver", default="cp", choices=["cp", "lp"],
                    help="cp = cutting plane (any n); lp = full sparse LP (n <= 32 only)")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default=None)
    ap.add_argument("--summary", default=None, help="print a summary of a results file and exit")
    args = ap.parse_args()

    if args.summary:
        summarize(args.summary)
        return

    p = ALL[args.params]
    out = args.out or f"experiments/results/talus_edge_{p.name}_{args.noise}_{args.target}.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    data = json.load(open(out)) if os.path.exists(out) else dict(
        params=p.name, noise=args.noise, target=args.target, solver=args.solver, points=[])
    done = {(q["n"], q["N"]) for q in data["points"]}

    for n in args.n:
        ch = make_channel(p, n, args.noise, args.target)
        n0 = 2 * args.k0 * ch.bound
        grid = sorted({int(round(v)) for v in n0 * np.geomspace(args.lo, args.hi, args.steps)})
        for count in grid:
            if (n, count) in done:
                continue
            t0 = time.time()
            ch, rows = run_point(p, n, count, args.trials, args.noise, args.target, args.solver, args.seed)
            q = point_summary(ch, count, rows)
            data["points"].append(q)
            json.dump(data, open(out, "w"), indent=1)
            print(f"n={n:4d} N={count:8d} ok_edge={q['succ_edge']:.2f} ok_ls={q['succ_ls']:.2f} "
                  f"err_edge={q['err_edge_med']:.3f} K={q['K_hat']:.2f} feas={q['feasible_rounded']:.2f} "
                  f"({time.time() - t0:.0f}s)", flush=True)
    summarize(out)


if __name__ == "__main__":
    main()
