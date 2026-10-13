"""Aggregate per-trial ilp_n256 results for ML-DSA-65/87 into experiments/results/ilp_n256_summary.txt."""
import glob
import json
import math

TRIALS = 4
FAC = (0.4, 0.5, 0.6, 0.7)
INFO = {"ML-DSA-65": (3.58e5, 14, 16.4), "ML-DSA-87": (3.69e5, 14, 16.2)}
out = ["ILP finishing at n = 256, BCC, target s2, window 1, time limit 300 s, seed 2032.",
       f"{TRIALS} trials per point (trials 0..{TRIALS-1}); small samples, a point at k/{TRIALS} is only indicative.", ""]
for P, (rnd, cap, wall) in INFO.items():
    out.append(f"{P}: plain-rounding N*99 = {rnd:.3g} (2^{math.log2(rnd):.1f}); cap 2^{cap}; uniqueness wall ~2^{wall}")
    out.append("  factor      N   trials  ILP ok  rounding ok  mean s")
    best = None
    for f in FAC:
        N = round(rnd * f / 1000) * 1000
        rows = []
        for fn in sorted(glob.glob(f"experiments/results/ilp_n256_{P}_{N//1000}k_t[0-9].json")):
            t = int(fn.rsplit("_t", 1)[1][:-5])
            if t < TRIALS:
                rows += json.load(open(fn))["rows"]
        n = len(rows)
        i = sum(r["ilp_ok"] for r in rows); r_ = sum(r["round_ok"] for r in rows)
        sec = sum(r["seconds"] for r in rows) / max(n, 1)
        out.append(f"  {f:.1f}   {N:7d}   {n:4d}   {i}/{n}     {r_}/{n}        {sec:6.0f}")
        if n == TRIALS and i == n and best is None:
            best = N
    if best:
        lg = math.log2(best)
        out.append(f"  smallest N with {TRIALS}/{TRIALS} ILP: {best} = 2^{lg:.2f}; {lg-cap:+.2f} bits vs cap 2^{cap}; {lg-wall:+.2f} bits vs wall 2^{wall}")
    else:
        out.append(f"  no tested N reached {TRIALS}/{TRIALS} ILP success")
    out.append("")
open("experiments/results/ilp_n256_summary.txt", "w").write("\n".join(out))
print("\n".join(out))
