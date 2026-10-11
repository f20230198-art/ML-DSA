"""Dimension trend of Trilithium's rejected w_H gap, exact by convolution.
Run: python -m experiments.trilithium_dim"""
import argparse
import json
import os

import numpy as np

from harness.schemes.trilithium_conv import run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, nargs="+", default=[2, 3, 4, 5, 6])
    ap.add_argument("--gamma1", type=int, nargs="+", default=[4, 8, 16])
    ap.add_argument("--q", type=int, default=17)
    ap.add_argument("--gamma2", type=int, default=4)
    ap.add_argument("--tau", type=int, default=1)
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default="experiments/results/trilithium_dim.json")
    args = ap.parse_args()
    rows = []
    keys = ["p_rej3", "p_rej2", "h2_3_sim", "h2_2_sim", "h2_3_key"]
    print(f"q={args.q} gamma2={args.gamma2} tau={args.tau} eta=1 trials={args.trials} seed={args.seed}+n (means)")
    print("   n gamma1 " + " ".join(f"{k:>10s}" for k in keys), flush=True)
    for n in args.n:
        for g1 in args.gamma1:
            sel = run([n], [g1], args.q, args.gamma2, args.tau, 1, args.trials, args.seed)
            rows += sel
            json.dump(dict(args=vars(args), rows=rows), open(args.out, "w"), indent=1)
            mean = {k: np.nanmean([r[k] for r in sel]) for k in keys}
            print(f"{n:4d} {g1:6d} " + " ".join(f"{mean[k]:10.3g}" for k in keys), flush=True)


if __name__ == "__main__":
    main()
