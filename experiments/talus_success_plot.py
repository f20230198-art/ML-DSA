"""Success rate vs signatures N for the TALUS s2 channel, ML-DSA-44, n = 256 (Phase 2 plan stage 2 output).

Run: python -m experiments.talus_success_plot
Reads existing results only (no new runs):
  - least squares and edge (plain rounding), one ring element, 20 trials per N, seed 2026:
    experiments/results/talus_edge_ML-DSA-44_bcc_s2_n256_dense.json
  - edge + ILP finishing, one ring element, 20 trials per N, seed 2041: experiments/results/item8/summary.txt
  - edge + ILP, whole secret (all k = 4 elements), 20 secrets per N, seed 2081: experiments/results/item8_full/summary.txt
Cap 2^13 and uniqueness wall 2^15.2 are the TALUS authors' figures.
Least squares needs about 3.6e9 signatures (2^31.7) in our model, far off the right edge.
Outputs experiments/results/talus_success_vs_N.png.
"""
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = Path("experiments/results")
CAP, WALL, LS_NEED = 13.0, 15.2, math.log2(3.6e9)
BLUE, ORANGE, AQUA, GRAY, INK, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a85", "#1f1f1d", "#5f5e58"


def dense():
    pts = json.loads((RES / "talus_edge_ML-DSA-44_bcc_s2_n256_dense.json").read_text())["points"]
    return [(math.log2(p["N"]), p["succ_edge"], p["succ_ls"]) for p in pts]


def summary_rows(path, header, pattern):
    """Rows of the first table after `header` in a summary file, parsed with `pattern`."""
    text = path.read_text()
    block = text[text.index(header):]
    rows = []
    for line in block.splitlines()[2:]:
        m = re.match(pattern, line)
        if not m:
            if rows:
                break
            continue
        rows.append(m.groups())
    return rows


def ilp_element():
    rows = summary_rows(RES / "item8" / "summary.txt", "ML-DSA-44",
                        r"\s+\d+\s+([\d.]+)\s+(\d+)/(\d+)")
    return [(float(l), int(k) / int(n)) for l, k, n in rows]


def ilp_whole():
    rows = summary_rows(RES / "item8_full" / "summary.txt", "ML-DSA-44",
                        r"\s+\d+\s+([\d.]+)\s+\d+/\s*\d+\s+(\d+)/\s*(\d+)")
    return [(float(l), int(k) / int(n)) for l, k, n in rows]


def main():
    d, e, w = dense(), ilp_element(), ilp_whole()
    fig, ax = plt.subplots(figsize=(3.5, 2.6), dpi=300)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=7)
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.6)
    ax.set_axisbelow(True)

    for x, label in ((CAP, "cap 2^13"), (WALL, "wall 2^15.2")):
        ax.axvline(x, color=MUTED, linestyle="--", linewidth=0.8)
        ax.text(x + 0.08, 0.25, label, rotation=90, fontsize=6.5, color=MUTED, va="center")

    ax.plot([p[0] for p in d], [p[2] for p in d], color=GRAY, marker="x", markersize=4, linewidth=1.2,
            label="Least squares (element)")
    ax.plot([p[0] for p in d], [p[1] for p in d], color=BLUE, marker="o", markersize=3.5, linewidth=1.5,
            label="Edge, rounding (element)")
    ax.plot([p[0] for p in e], [p[1] for p in e], color=ORANGE, marker="s", markersize=3.5, linewidth=1.5,
            label="Edge + ILP (element)")
    ax.plot([p[0] for p in w], [p[1] for p in w], color=AQUA, marker="^", markersize=4, linewidth=1.5,
            label="Edge + ILP (whole secret)")

    ax.annotate(f"least squares\nneeds ~2^{LS_NEED:.1f}", xy=(17.8, 0.03), xytext=(16.75, 0.33),
                fontsize=6.5, color=MUTED, ha="left",
                arrowprops=dict(arrowstyle="->", color=MUTED, linewidth=0.6))
    ax.set_xlim(12.5, 18.1)
    ax.set_ylim(-0.03, 1.05)
    ax.set_xlabel("log2 N (signatures)", fontsize=7.5, color=INK)
    ax.set_ylabel("success rate (20 trials)", fontsize=7.5, color=INK)
    leg = ax.legend(fontsize=6, frameon=True, loc="upper left", handlelength=1.8, framealpha=1.0)
    leg.get_frame().set_edgecolor("none")
    fig.tight_layout()
    out = RES / "talus_success_vs_N.png"
    fig.savefig(out)
    print("wrote", out)
    for name, pts in (("dense (log2N, edge, ls)", d), ("ILP element", e), ("ILP whole", w)):
        print(name, [tuple(round(v, 2) for v in p) for p in pts])


if __name__ == "__main__":
    main()
