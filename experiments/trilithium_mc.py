"""Trilithium rejected w_H gap at n = 8 by Monte Carlo (validated at n = 6 against the exact values).
Run: python -m experiments.trilithium_mc"""
import argparse
import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from harness.schemes.trilithium_mc import compare
from harness.schemes.trilithium_toy import Toy


def _one(job):
    n, g1, t, a, cfg = job
    toy = Toy(n=n, q=cfg["q"], gamma2=cfg["gamma2"], gamma1=g1, tau=cfg["tau"], eta=1)
    rng = np.random.default_rng([cfg["seed"], n, g1, t])
    a, s1, s2, c = toy.sample(rng)
    row = compare(toy, a, s1, s2, c, cfg["samples"], rng)
    row.update(n=n, gamma1=g1, trial=t)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, nargs="+", default=[6, 8])
    ap.add_argument("--gamma1", type=int, nargs="+", default=[4, 8, 16])
    ap.add_argument("--q", type=int, default=17)
    ap.add_argument("--gamma2", type=int, default=4)
    ap.add_argument("--tau", type=int, default=1)
    ap.add_argument("--samples", type=int, default=200_000_000)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default="experiments/results/trilithium_mc.json")
    args = ap.parse_args()
    cfg = vars(args)
    jobs = [(n, g1, t, None, cfg) for n in args.n for g1 in args.gamma1 for t in range(args.trials)]
    keys = ["p_rej3", "p_rej2", "h2_3_sim", "bias3", "h2_2_sim", "bias2", "h2_null", "bias_null"]
    print(f"q={args.q} gamma2={args.gamma2} tau={args.tau} eta=1 samples={args.samples:.2g} per stream, "
          f"trials={args.trials}, seed={args.seed} (means over trials)")
    print("   n gamma1 " + " ".join(f"{k:>10s}" for k in keys), flush=True)
    with ProcessPoolExecutor(args.workers) as pool:
        rows = list(pool.map(_one, jobs))
    json.dump(dict(args=cfg, rows=rows), open(args.out, "w"), indent=1)
    for n in args.n:
        for g1 in args.gamma1:
            sel = [r for r in rows if r["n"] == n and r["gamma1"] == g1]
            mean = {k: np.nanmean([r[k] for r in sel]) for k in keys}
            print(f"{n:4d} {g1:6d} " + " ".join(f"{mean[k]:10.3g}" for k in keys), flush=True)


if __name__ == "__main__":
    main()
