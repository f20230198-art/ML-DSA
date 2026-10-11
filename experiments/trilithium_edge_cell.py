"""Is Trilithium's toy branch-2 floor caused by Decompose's irregular HighBits cell r1 = 0?

FIPS 204 Decompose maps the top values near q - 1 to r1 = 0, so cell 0 is wider than the others.
We recompute the branch-2 gap (H^2 vs simulator) after removing every w_H that has r1 = 0 in any
coordinate (both distributions renormalised on the remaining cells). If the floor came from that
cell, the masked H^2 should be much smaller than the full one.
Run: python -m experiments.trilithium_edge_cell
"""
import json

import numpy as np

from harness.schemes.trilithium_toy import Toy, distances

CASES = [(257, 16, 32), (257, 16, 48), (513, 32, 32), (513, 32, 64), (1025, 64, 64)]


def main(trials=5, seed=2026):
    rows = []
    print(f"{'q':>5} {'g2':>3} {'g1':>3} {'H2 full':>9} {'H2 masked':>10} {'mass kept':>9}")
    for q, g2, g1 in CASES:
        toy = Toy(n=4, q=q, gamma2=g2, gamma1=g1)
        rng = np.random.default_rng(seed)
        digits = (np.arange(toy.m ** 4)[:, None] // toy.m ** np.arange(4)) % toy.m
        keep = (digits != 0).all(axis=1)
        full, masked, kept = [], [], []
        for _ in range(trials):
            a, s1, s2, c = toy.sample(rng)
            h_all, h2, _ = toy.histograms(a, s1, s2, c)
            if not h2.sum():
                continue
            full.append(distances(h2, h_all)[1])
            masked.append(distances(h2[keep], h_all[keep])[1])
            kept.append(h2[keep].sum() / h2.sum())
        r = dict(q=q, gamma2=g2, gamma1=g1, h2_full=float(np.mean(full)), h2_masked=float(np.mean(masked)),
                 mass_kept=float(np.mean(kept)))
        rows.append(r)
        print(f"{q:5d} {g2:3d} {g1:3d} {r['h2_full']:9.3g} {r['h2_masked']:10.3g} {r['mass_kept']:9.3f}",
              flush=True)
    json.dump(dict(trials=trials, seed=seed, rows=rows),
              open("experiments/results/trilithium_edge_cell.json", "w"), indent=1)


if __name__ == "__main__":
    main()
