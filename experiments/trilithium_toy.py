"""Exact toy-size test of Trilithium's rejected w_H (H-F2). Run: python -m experiments.trilithium_toy"""
import argparse
import json
import os

import numpy as np

from harness.schemes.trilithium_toy import run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gamma1", type=int, nargs="+", default=[4, 8, 12, 16, 24, 32])
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--q", type=int, default=257)
    ap.add_argument("--gamma2", type=int, default=16)
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default="experiments/results/trilithium_toy.json")
    args = ap.parse_args()
    rows = run(args.gamma1, args.n, args.q, args.gamma2, args.trials, args.seed)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(dict(args=vars(args), rows=rows), open(args.out, "w"), indent=1)
    keys = ["p_rej3", "p_rej2", "sd3_sim", "h2_3_sim", "sd2_sim", "h2_2_sim", "sd_sim_unif", "sd3_key", "h2_3_key"]
    print(f"n={args.n} q={args.q} gamma2={args.gamma2} trials={args.trials} seed={args.seed} (means over trials)")
    print("gamma1 " + " ".join(f"{k:>10s}" for k in keys) + "  ~1/H2(3,sim)")
    for g1 in args.gamma1:
        sel = [r for r in rows if r["gamma1"] == g1]
        mean = {k: np.nanmean([r[k] for r in sel]) for k in keys}
        print(f"{g1:6d} " + " ".join(f"{mean[k]:10.3g}" for k in keys) + f"  {1 / mean['h2_3_sim']:10.3g}")


if __name__ == "__main__":
    main()
