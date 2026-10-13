"""Least-squares error vs number of signatures N, with the theory curve (instructor feedback item 3).

Run: python -m experiments.ls_error_plot
Synthetic channel (harness.schemes.ilwe_transcript, ML-DSA-44, plain LowBits noise, n = 256, one ring element):
N in {1e3, 3e3, 1e4, 3e4, 1e5, 3e5}, 10 trials per N, seed 2033, rng = default_rng([2033, N, trial]);
secret s2 from sample_secret (|s| <= eta). Measured = RMS of (estimate - s) over all coefficients of all trials.
Theory = gamma2 / sqrt(3 tau N) (Gaussian approximation of uniform LowBits noise; Cramér-Rao bound).
Also overlays real-signature points from TALUS v0.1 (experiments/results/talus_v01_niot_*.log, rms over 4x256 coeffs).
Outputs experiments/results/ls_error_vs_N.{json,png}.
"""
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from harness.estimators.ilwe import least_squares
from harness.mldsa.params import ML_DSA_44 as P
from harness.mldsa.sampling import sample_secret
from harness.schemes.ilwe_transcript import make_transcript

SEED, TRIALS = 2033, 10
GRID = [1_000, 3_000, 10_000, 30_000, 100_000, 300_000]
OUT = Path("experiments/results")


def theory(n):
    return P.gamma2 / math.sqrt(3 * P.tau * n)


def run():
    rows = []
    for n in GRID:
        per = []
        for t in range(TRIALS):
            rng = np.random.default_rng([SEED, n, t])
            s = sample_secret(rng, P.eta)
            c, b = make_transcript(rng, P, s, n)
            per.append(float(np.sqrt(np.mean((least_squares(c, b) - s) ** 2))))
        rows.append(dict(N=n, rms_mean=float(np.mean(per)), rms_min=min(per), rms_max=max(per),
                         per_trial=per, theory=theory(n)))
        print(f"N={n:>7}  measured {np.mean(per):8.3f}  [{min(per):.3f}, {max(per):.3f}]  theory {theory(n):8.3f}", flush=True)
    return rows


def real_points():
    pts = []
    for f in sorted(OUT.glob("talus_v01_niot_*.log")):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.search(r"N\s*=\s*([\d.e+]+).*?rms\s*(?:err(?:or)?)?\s*[=:]?\s*([\d.]+)", line, re.I)
            if m:
                pts.append((float(m.group(1)), float(m.group(2))))
    return pts


def plot(rows, real):
    blue, orange, grey, ink = "#2a78d6", "#eb6834", "#8a8984", "#52514e"
    fig, ax = plt.subplots(figsize=(3.5, 2.5), dpi=300)
    xs = np.logspace(math.log10(GRID[0] / 1.5), math.log10(GRID[-1] * 1.5), 100)
    ax.plot(xs, [theory(x) for x in xs], color=grey, lw=1.2, ls="--", label=r"theory $\gamma_2/\sqrt{3\tau N}$", zorder=1)
    n = [r["N"] for r in rows]
    m = np.array([r["rms_mean"] for r in rows])
    lo = m - np.array([r["rms_min"] for r in rows])
    hi = np.array([r["rms_max"] for r in rows]) - m
    ax.errorbar(n, m, yerr=[lo, hi], fmt="o", ms=4, color=blue, ecolor=blue, elinewidth=1, capsize=2,
                markeredgecolor="white", markeredgewidth=0.6, label=f"synthetic ({TRIALS} trials/N)", zorder=3)
    if real:
        ax.plot(*zip(*real), "s", ms=6, mfc="none", markeredgecolor=orange, markeredgewidth=1.0,
                label="real TALUS v0.1 signatures (3 keys)", zorder=4)
    ax.set_xscale("log"), ax.set_yscale("log")
    ax.set_xlabel("signatures N", color=ink, fontsize=8)
    ax.set_ylabel("RMS error per coefficient", color=ink, fontsize=8)
    ax.tick_params(labelsize=7, colors=ink)
    ax.grid(True, which="major", color="#e4e3df", lw=0.5)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(fontsize=6.5, frameon=False)
    ax.set_title("ML-DSA-44 least squares, n = 256", fontsize=8, color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(OUT / "ls_error_vs_N.png")


def main():
    import sys
    if "--plot-only" in sys.argv:
        d = json.load(open(OUT / "ls_error_vs_N.json"))
        plot(d["rows"], [tuple(x) for x in d["real_points"]])
        return
    rows = run()
    real = real_points()
    json.dump(dict(params=P.name, seed=SEED, trials=TRIALS, grid=GRID, rows=rows, real_points=real),
              open(OUT / "ls_error_vs_N.json", "w"), indent=1)
    plot(rows, real)
    print("real points:", real)


if __name__ == "__main__":
    main()
