"""Group the element trials of experiments/run_item8_full.sh into full secrets (4 consecutive trials = one ML-DSA-44 s2)
and report full-secret success with Clopper-Pearson 95% intervals next to the per-element rate and the prediction p_elem^4.

  python -m experiments.item8_full_analysis > experiments/results/item8_full/summary.txt
"""
import glob
import json
import math
import re

from scipy.stats import beta

K = 4
CAP = 13


def cp(k, n):
    lo = beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return lo, hi


print(f"ML-DSA-44 full s2 (k = {K} ring elements, ILP finish, 120 s limit, seed 2081); cap 2^{CAP}")
print("       N  log2N  elem ok     full ok   95% CI full   p_elem^4")
for f in sorted(glob.glob("experiments/results/item8_full/ilp_ML-DSA-44_*.json"),
                key=lambda s: int(re.findall(r"_(\d+)\.json", s)[0])):
    rows = sorted(json.load(open(f))["rows"], key=lambda r: r["trial"])
    N = rows[0]["N"]
    oks = [bool(r["ilp_ok"]) for r in rows]
    ne = len(oks)
    pe = sum(oks) / ne
    groups = [all(oks[i:i + K]) for i in range(0, ne - ne % K, K)]
    k, n = sum(groups), len(groups)
    lo, hi = cp(k, n)
    print(f"{N:8d}  {math.log2(N):5.2f}  {sum(oks):3d}/{ne:3d}  {k:3d}/{n:3d}  [{lo:.2f}, {hi:.2f}]  {pe ** K:.2f}")
