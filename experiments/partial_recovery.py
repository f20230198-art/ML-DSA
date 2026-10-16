"""Paper plan item 4 (lattice-finish idea), step 1: how much of s2 does the edge estimator get right
BELOW the full-recovery wall, i.e. at and near the per-key cap?

If a fraction f of the s2 coefficients is known exactly, then t = A s1 + s2 gives f*k*n exact linear
equations on s1, and the rest is a smaller LWE instance (see experiments/partial_recovery_lwe.py).

For each N: n = 256 edge estimate (cutting-plane Chebyshev, GPU if present), then
  - fraction of coefficients with round(x) == s2,
  - the same fraction among the coefficients whose |x - round(x)| < tau_conf (a confidence filter),
  - precision of that filter (how many of the kept ones are right).

Run: python -m experiments.partial_recovery --params ML-DSA-44 --N 8192 16384 32768 --trials 3
"""
import argparse
import json
import time

import numpy as np

from harness.estimators import edge, edge_gpu
from harness.mldsa.params import ALL
from harness.schemes.talus_bcc import make_channel, make_transcript, sample_target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default="ML-DSA-44", choices=sorted(ALL))
    ap.add_argument("--N", type=int, nargs="+", default=[8192, 16384, 32768])
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--seed", type=int, default=2041)
    ap.add_argument("--out", default="experiments/results/partial_recovery.json")
    args = ap.parse_args()
    p = ALL[args.params]
    ch = make_channel(p, 256, "bcc", "s2")
    rows = []
    for N in args.N:
        for t in range(args.trials):
            rng = np.random.default_rng([args.seed, N, t])
            s = sample_target(rng, ch)
            c, b = make_transcript(rng, ch, s, N)
            t0 = time.time()
            x, _, info = edge_gpu.chebyshev_cutting_plane_gpu(c, b, ch.target_max + 1, rng)
            r = edge.round_to_range(x, ch.target_max).astype(np.int64)
            ok = r == s
            dist = np.abs(x - np.rint(x))
            row = dict(N=N, trial=t, frac_ok=float(ok.mean()), max_err=float(np.abs(x - s).max()),
                       med_err=float(np.median(np.abs(x - s))), rms_err=float(np.sqrt(np.mean((x - s) ** 2))), converged=bool(info["converged"]),
                       seconds=time.time() - t0)
            for thr in (0.05, 0.1, 0.2, 0.3):
                keep = dist < thr
                row[f"keep_{thr}"] = float(keep.mean())
                row[f"prec_{thr}"] = float(ok[keep].mean()) if keep.any() else None
            rows.append(row)
            print(json.dumps(row), flush=True)
            json.dump(rows, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
