"""Paper plan item 8, open part: from one ring element to the whole s2.

The ILP trials (experiments/results/item8) recover ONE ring element of s2 (n = 256). The full s2 has k
elements; a full-key attack needs all of them from the SAME N signatures. If the per-element success events are
independent given N, P_full(N) = P_elem(N)^k. We take P_elem from the logistic fit (same fit as
item8_analysis.py) and report N for P_full = 50% and 95%.

Caveat (stated in the output): extrapolation under an independence assumption, not a run. The elements share
the challenges c, so the events are positively correlated; independence therefore gives a slightly pessimistic
(too high) N for the attacker. No full-secret ILP run was done.

Run: python -m experiments.item8_full_secret
"""
import json
import math

import numpy as np
from scipy.optimize import minimize

CAP = {"ML-DSA-44": 13, "ML-DSA-65": 14, "ML-DSA-87": 14}
K = {"ML-DSA-44": 4, "ML-DSA-65": 6, "ML-DSA-87": 8}


def fit(x, y):
    def nll(v):
        m, s = v[0], math.exp(v[1])
        p = np.clip(1 / (1 + np.exp(-(x - m) / s)), 1e-12, 1 - 1e-12)
        return -(y * np.log(p) + (1 - y) * np.log(1 - p)).sum()
    r = minimize(nll, [x.mean(), math.log(0.1)], method="Nelder-Mead")
    return r.x[0], math.exp(r.x[1])


def n_for(m, s, target):
    return m + s * math.log(target / (1 - target))


def main():
    print("Full-secret extrapolation, P_full = P_elem^k (independence assumed; extrapolated, not run)")
    for name in CAP:
        rows = json.load(open(f"experiments/results/item8/ilp_{name}.json"))["rows"]
        x = np.array([math.log2(r["N"]) for r in rows])
        y = np.array([float(r["ilp_ok"]) for r in rows])
        m, s = fit(x, y)
        k = K[name]
        out = [f"{name}: k = {k}, per-element 50% at 2^{m:.2f}, 95% at 2^{n_for(m, s, 0.95):.2f}"]
        for tgt in (0.5, 0.95):
            pe = tgt ** (1 / k)
            lg = n_for(m, s, pe)
            out.append(f"full {int(tgt * 100)}%: need per-element {pe:.3f} -> 2^{lg:.2f} (+{lg - CAP[name]:.2f} bits vs cap)")
        print("  " + "; ".join(out))


if __name__ == "__main__":
    main()
