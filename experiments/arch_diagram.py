"""Harness architecture diagram (instructor feedback item 4). Run: python -m experiments.arch_diagram
Writes experiments/results/harness_architecture.png (sized for one IEEE column)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

INK, MUTED, LINE = "#0b0b0b", "#52514e", "#8a8984"
FILL = {"core": "#cde2fb", "view": "#fde1d4", "est": "#d3f0e3", "out": "#efeeea"}

# (title, subtitle, kind)
LAYERS = [
    ("ML-DSA core  (harness/mldsa)", "NTT, SHAKE sampling, hints, sign/verify;\nACVP vectors pass; every attempt kept", "core"),
    ("Attempt records", "c, y, z, w, which check failed (secret internals)", "core"),
    ("Scheme views  (harness/schemes)", "plain ML-DSA (neg. control), y-leak (pos. control),\nTALUS-BCC, TALUS v0.1, Mithril\n(+ Quorus, Trilithium, Kao simulators)", "view"),
    ("Observations -> adapter", "only what the scheme releases; turned into (c, b)\nwith b = -c x + e", "view"),
    ("Estimators  (harness/estimators)", "least squares, edge LP (CPU/GPU), ILP finish;\nfisher.py theory curves", "est"),
    ("Experiments -> results", "N* ladders, controls, margins in bits;\nexperiments/results/*.json", "out"),
]


def main():
    fig, ax = plt.subplots(figsize=(3.5, 4.2), dpi=300)
    ax.set_xlim(0, 1), ax.set_ylim(0, 1), ax.axis("off")
    h, gap, top = 0.125, 0.04, 0.985
    ys = []
    for i, (title, sub, kind) in enumerate(LAYERS):
        y = top - h - i * (h + gap)
        ys.append(y)
        ax.add_patch(FancyBboxPatch((0.04, y), 0.92, h, boxstyle="round,pad=0.004,rounding_size=0.015",
                                    fc=FILL[kind], ec=LINE, lw=0.6))
        ax.text(0.07, y + h - 0.028, title, fontsize=6.6, weight="bold", color=INK, va="center")
        ax.text(0.07, y + 0.042, sub, fontsize=5.4, color=MUTED, va="center", linespacing=1.25)
    for i in range(len(ys) - 1):
        ax.add_patch(FancyArrowPatch((0.5, ys[i]), (0.5, ys[i + 1] + h), arrowstyle="-|>", mutation_scale=6,
                                     color=LINE, lw=0.8))
    ax.text(0.53, (ys[2] + ys[3] + h) / 2, "secrets stop here", fontsize=5, color=MUTED, ha="left", va="center",
            style="italic")
    fig.savefig("experiments/results/harness_architecture.png", bbox_inches="tight", pad_inches=0.02)


if __name__ == "__main__":
    main()
