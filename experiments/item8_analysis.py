"""Paper plan item 8: success rates with 95% Clopper-Pearson intervals and a logistic fit in log2 N.

  python -m experiments.item8_analysis > experiments/results/item8/summary.txt
"""
import collections
import json
import math

import numpy as np
from scipy.optimize import minimize
from scipy.stats import beta

CAP = {"ML-DSA-44": 13, "ML-DSA-65": 14, "ML-DSA-87": 14}
WALL = {"ML-DSA-44": 15.2, "ML-DSA-65": 16.4, "ML-DSA-87": 16.2}


def cp(k, n):
    lo = beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return lo, hi


def fit(x, y):
    """Logistic P(ok) = 1 / (1 + exp(-(x - m) / s)), maximum likelihood over trials."""
    def nll(v):
        m, s = v[0], math.exp(v[1])
        p = np.clip(1 / (1 + np.exp(-(x - m) / s)), 1e-12, 1 - 1e-12)
        return -(y * np.log(p) + (1 - y) * np.log(1 - p)).sum()
    r = minimize(nll, [x.mean(), math.log(0.1)], method="Nelder-Mead")
    return r.x[0], math.exp(r.x[1])


for name in ["ML-DSA-44", "ML-DSA-65", "ML-DSA-87"]:
    rows = json.load(open(f"experiments/results/item8/ilp_{name}.json"))["rows"]
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r["N"], []).append(r["ilp_ok"])
    print(f"{name}  (cap 2^{CAP[name]}, uniqueness wall ~2^{WALL[name]}; 120 s ILP limit, seed 2041)")
    print("       N   log2N   ok/n    95% CI")
    for N, oks in by.items():
        k, n = sum(oks), len(oks)
        lo, hi = cp(k, n)
        print(f"  {N:7d}  {math.log2(N):5.2f}  {k:2d}/{n:2d}  [{lo:.2f}, {hi:.2f}]")
    x = np.array([math.log2(r["N"]) for r in rows])
    y = np.array([float(r["ilp_ok"]) for r in rows])
    m, s = fit(x, y)
    n95 = m + s * math.log(19)
    print(f"  logistic fit: 50% at 2^{m:.2f}, 95% at 2^{n95:.2f} (scale {s:.3f}); "
          f"95% point is +{n95 - CAP[name]:.2f} bits vs cap, {n95 - WALL[name]:+.2f} vs wall\n")
