"""Extra report figures and table summaries, built only from saved results (no new runs).

Run: python -m experiments.report_extras
Outputs (experiments/results/):
  talus_ladder.png         edge-estimator success vs N for ring sizes n = 8..256, ML-DSA-44, TALUS BCC channel
                           (talus_edge_ML-DSA-44_bcc_s2.json for n <= 128, the 20-trial dense file for n = 256;
                           seed = talus_edge_scaling default 2026, not stored in the files)
  trilithium_gap.png       squared Hellinger distance between rejected w_H and the simulator vs n, q = 17
                           (exact: trilithium_dim.json n = 2..6; Monte Carlo: trilithium_mc.json n = 8, bias-corrected)
  report_extra_tables.txt  per-set summaries for the Mithril, TALUS insider and controls tables
"""
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = Path("experiments/results")
INK, MUTED, GRID = "#1f1f1d", "#5f5e58", "#e6e5e0"
BLUES = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]
CAT = {4: "#2a78d6", 8: "#eb6834", 16: "#1baf7a"}
MARK = {4: "o", 8: "s", 16: "^"}


def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=7)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def ladder():
    pts = json.loads((RES / "talus_edge_ML-DSA-44_bcc_s2.json").read_text())["points"]
    dense = json.loads((RES / "talus_edge_ML-DSA-44_bcc_s2_n256_dense.json").read_text())["points"]
    by_n = defaultdict(list)
    for p in pts:
        if p["n"] < 256:
            by_n[p["n"]].append(p)
    by_n[256] = dense
    fig, ax = plt.subplots(figsize=(3.5, 2.5), dpi=300)
    style(ax)
    ax.axvline(13, color=MUTED, linestyle="--", linewidth=0.8)
    ax.text(13.08, 0.25, "cap 2^13", rotation=90, fontsize=6.5, color=MUTED, va="center")
    lines = []
    for color, n in zip(BLUES, sorted(by_n)):
        rows = sorted(by_n[n], key=lambda p: p["N"])
        x = [math.log2(p["N"]) for p in rows]
        y = [p["succ_edge"] for p in rows]
        ax.plot(x, y, color=color, marker="o", markersize=3, linewidth=1.4,
                label=f"n = {n} ({rows[0]['trials']} trials)")
        lines.append((n, rows[0]["trials"], [(round(a, 2), b) for a, b in zip(x, y)]))
    ax.set_xlim(12.5, 20)
    ax.set_ylim(-0.03, 1.05)
    ax.set_xlabel("log2 N (signatures)", fontsize=7.5, color=INK)
    ax.set_ylabel("success rate, one element", fontsize=7.5, color=INK)
    leg = ax.legend(fontsize=5.8, frameon=True, loc="upper left", bbox_to_anchor=(0.1, 1.0), framealpha=1.0)
    leg.get_frame().set_edgecolor("none")
    fig.tight_layout()
    fig.savefig(RES / "talus_ladder.png")
    plt.close(fig)
    return lines


def trilithium():
    exact = json.loads((RES / "trilithium_dim.json").read_text())
    mc = json.loads((RES / "trilithium_mc.json").read_text())
    ex_rows = exact["rows"] if isinstance(exact, dict) else exact
    mc_rows = mc["rows"] if isinstance(mc, dict) else mc

    def mean(rows, n, g, key):
        v = [r[key] for r in rows if r["n"] == n and r["gamma1"] == g]
        return sum(v) / len(v) if v else None

    fig, axes = plt.subplots(2, 1, figsize=(3.5, 3.9), dpi=300, sharex=True)
    out = []
    for ax, branch, title in ((axes[0], "3", "branch 3 (z check failed)"), (axes[1], "2", "branch 2 (r0 check failed)")):
        style(ax)
        ax.set_yscale("log")
        for g in (4, 8, 16):
            xs, ys = [], []
            for n in (2, 3, 4, 5, 6):
                v = mean(ex_rows, n, g, f"h2_{branch}_sim")
                if v is not None:
                    xs.append(n)
                    ys.append(v)
            ax.plot(xs, ys, color=CAT[g], marker=MARK[g], markersize=3.5, linewidth=1.4, label=f"γ1 = {g}")
            v, b = mean(mc_rows, 8, g, f"h2_{branch}_sim"), mean(mc_rows, 8, g, f"bias{branch}")
            floor = mean(mc_rows, 8, g, "bias_null")
            if v is None:
                continue
            corr = v - b
            if corr > floor:
                ax.plot([8], [corr], color=CAT[g], marker=MARK[g], markersize=4, linestyle="none")
                out.append((branch, g, 8, f"{corr:.2e}", "Monte Carlo, bias-corrected"))
            else:
                ax.plot([8], [floor], color=CAT[g], marker="v", markersize=4, linestyle="none",
                        markerfacecolor="white")
                out.append((branch, g, 8, f"<= {floor:.2e}", "below Monte Carlo floor"))
            for x, y in zip(xs, ys):
                out.append((branch, g, x, f"{y:.2e}", "exact"))
        ax.set_title(title, fontsize=7, color=INK, loc="left")
        ax.set_ylabel("squared Hellinger H²", fontsize=7, color=INK)
    axes[1].set_xlabel("ring dimension n", fontsize=7.5, color=INK)
    axes[0].legend(fontsize=6, frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(RES / "trilithium_gap.png")
    plt.close(fig)
    return out


def mithril():
    pub = (RES / "mithril_params.txt").read_text()
    cor = (RES / "mithril_corrected.txt").read_text()
    c64 = (RES / "mithril_corrected_2e64.txt").read_text()
    row = re.compile(r"^\s+\((\d),(\d)\)\s+(.*)$")

    def blocks(text):
        out, cur = {}, None
        for line in text.splitlines():
            m = re.match(r"^(ML-DSA-\d\d)", line.strip())
            if m:
                cur = m.group(1)
                out.setdefault(cur, [])
                continue
            r = row.match(line)
            if r and cur:
                out[cur].append(((int(r.group(1)), int(r.group(2))), r.group(3).replace("|", " ").split()))
        return out

    p, c, c6 = blocks(pub), blocks(cor), blocks(c64)
    lines = []
    for s in ("ML-DSA-44", "ML-DSA-65", "ML-DSA-87"):
        qs = [float(v[3]) for _, v in p[s]]
        typ = [float(v[-1]) for _, v in p[s]]
        short = sum(t < 50 for t in typ)
        # corrected rows: K_pub log2M_pub phi_new r'_pub r'_new log2M_new K_new K_new/K_pub success_pub success_new
        kf = [float(v[7]) for _, v in c[s]]
        kmax = max(c[s], key=lambda r: float(r[1][7]))
        kf64 = [float(v[7]) for _, v in c6.get(s, [])]
        phi = [float(v[2]) for _, v in c[s]]
        lines.append(f"{s}: sets {len(qs)}; Thm 3.2 with paper B: 2^{min(qs):.1f}..2^{max(qs):.1f}; "
                     f"typical (emp): 2^{min(typ):.1f}..2^{max(typ):.1f}, below 2^50: {short}; "
                     f"phi_new {min(phi):.2f}..{max(phi):.2f}; "
                     f"K_new/K_pub at 2^50: {min(kf):.2f}..{max(kf):.2f} (max at {kmax[0]}: K {kmax[1][0]} -> {kmax[1][6]}); "
                     + (f"at 2^64: {min(kf64):.2f}..{max(kf64):.2f}" if kf64 else "2^64: n/a"))
    return lines


def insider():
    text = (RES / "talus_insider_wall.txt").read_text()
    out = []
    for s in ("ML-DSA-44", "ML-DSA-65", "ML-DSA-87"):
        blk = text[text.index(s):]
        nxt = [blk.find(t, 5) for t in ("ML-DSA-44", "ML-DSA-65", "ML-DSA-87") if blk.find(t, 5) > 0]
        blk = blk[:min(nxt)] if nxt else blk
        mpc = blk[blk.index("MPC"):blk.index("TEE")]
        tee = blk[blk.index("TEE"):]
        mw = [float(x) for x in re.findall(r"wall 2\^\s*([\d.]+)", mpc)]
        mm = [float(x) for x in re.findall(r"margin\s+\+?([-\d.]+)", mpc)]
        below = re.findall(r"T=\s*(\d+): wall 2\^\s*([\d.]+).*BELOW", tee)
        tw2 = re.search(r"T=\s*2: wall 2\^\s*([\d.]+)", tee).group(1)
        out.append(f"{s}: MPC (T=2..6) wall 2^{min(mw)}..2^{max(mw)}, margin +{min(mm)}..+{max(mm)}; "
                   f"TEE T=2 wall 2^{tw2}; first T below cap: {below[0][0] if below else 'none <= 12'}")
    return out


def controls():
    out = []
    for f in ("mldsa_controls_ML-DSA-44.json", "mldsa_controls_fp_ML-DSA-44.json"):
        d = json.loads((RES / f).read_text())
        agg = defaultdict(lambda: [0, 0, 0, 0, []])
        for r in d["rows"]:
            a = agg[r["control"]]
            a[0] += 1
            a[1] += r["edge_is_key"]
            a[2] += r["edge_is_t0"]
            a[3] += r["ls_is_key"]
            a[4].append(r["est_seconds"])
        for k, a in agg.items():
            out.append(f"{f} seed {d['args']['seed']} N {d['args']['N']} {k}: runs {a[0]}, edge=key {a[1]}, "
                       f"edge=-t0 {a[2]}, LS=key {a[3]}, estimator {min(a[4]):.0f}-{max(a[4]):.0f} s")
    g = [json.loads(l.replace("'", '"').replace("True", "true").replace("False", "false"))
         for l in (RES / "gate_b_views_output.txt").read_text().splitlines() if l.startswith("{")]
    by = defaultdict(list)
    for r in g:
        by[r["N"]].append(r["edge_is_key"])
    out.append("gate B (seed 2029, real ML-DSA-44 -> TalusBCCView): "
               + ", ".join(f"N {n}: {sum(v)}/{len(v)}" for n, v in sorted(by.items())))
    return out


def main():
    lad, tri = ladder(), trilithium()
    lines = ["# Report extra tables (generated by experiments/report_extras.py from saved results)", "",
             "## TALUS ring-size ladder (edge, rounding; one element)"]
    lines += [f"n={n} trials={t}: {pts}" for n, t, pts in lad]
    lines += ["", "## Trilithium H^2 (branch, gamma1, n, value, source)"]
    lines += [str(r) for r in tri]
    lines += ["", "## Mithril"] + mithril()
    lines += ["", "## TALUS insider walls"] + insider()
    lines += ["", "## Controls"] + controls()
    (RES / "report_extra_tables.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
