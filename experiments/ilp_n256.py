"""Does the ILP finishing step lower N* at full size? ML-DSA-44, n = 256, BCC, target s2 (one ring element).

Run: python -m experiments.ilp_n256 --N 60000 80000 100000 120000 --trials 8
Edge estimate on the GPU (as for the n = 256 ladder), then harness.estimators.ilp.finish with window 1.
"""
import argparse
import json
import time

import numpy as np

from harness.estimators import edge, edge_gpu, ilp
from harness.mldsa.params import ALL
from harness.schemes.talus_bcc import make_channel, make_transcript, sample_target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, nargs="+", default=[60000, 80000, 100000, 120000])
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--seed", type=int, default=2032)
    ap.add_argument("--time-limit", type=float, default=60.0)
    ap.add_argument("--out", default="experiments/results/ilp_n256.json")
    args = ap.parse_args()
    p = ALL["ML-DSA-44"]
    ch = make_channel(p, 256, "bcc", "s2")
    rows = []
    for N in args.N:
        for t in range(args.trials):
            rng = np.random.default_rng([args.seed, N, t])
            s = sample_target(rng, ch)
            c, b = make_transcript(rng, ch, s, N)
            t0 = time.time()
            x, _, _ = edge_gpu.chebyshev_cutting_plane_gpu(c, b, ch.target_max + 1, rng)
            r = edge.round_to_range(x, ch.target_max).astype(np.int64)
            z, info = ilp.finish(c, b, x, ch.target_max, ch.bound, window=1, time_limit=args.time_limit)
            row = dict(N=N, trial=t, round_ok=bool((r == s).all()), ilp_ok=bool((z == s).all()),
                       wrong_round=int((r != s).sum()), free=info["free"], status=info["status"],
                       seconds=time.time() - t0)
            rows.append(row)
            print(row, flush=True)
            json.dump(dict(args=vars(args), rows=rows), open(args.out, "w"), indent=1)
    for N in args.N:
        rs = [r for r in rows if r["N"] == N]
        print(f"N={N}: round {np.mean([r['round_ok'] for r in rs]):.2f}  ilp {np.mean([r['ilp_ok'] for r in rs]):.2f}")


if __name__ == "__main__":
    main()
