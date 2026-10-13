"""Stage C2 extras: (1) theory curves (harness/estimators/fisher.py) against the measured ladders,
(2) edge-only rounding vs edge + integer finishing (harness/estimators/ilp.py) on small n.

  python -m experiments.edge_theory_ilp --trials 20 --seed 2031 > experiments/results/edge_theory_ilp.txt

Writes experiments/results/edge_theory_ilp.json too. Channel: ML-DSA-44, BCC noise, target s2
(harness/schemes/talus_bcc.py). Trials per point and seed are printed in the output.
"""
import argparse
import json
import math
import time

import numpy as np

from harness.estimators import edge, fisher, ilp
from harness.mldsa.params import ALL
from harness.schemes.talus_bcc import make_channel, make_transcript, sample_target

LADDERS = [
    "experiments/results/talus_edge_ML-DSA-44_bcc_s2.json",
    "experiments/results/talus_edge_ML-DSA-44_bcc_s2_n256_dense.json",
    "experiments/results/talus_edge_ML-DSA-65_bcc_s2.json",
    "experiments/results/talus_edge_ML-DSA-87_bcc_s2.json",
]
# ROADMAP section 2 measured N*99 at n = 256 (per ring element)
MEASURED = {"ML-DSA-44": 1.45e5, "ML-DSA-65": 3.58e5, "ML-DSA-87": 3.69e5}


def part_theory():
    print("== Part 1: theory vs measured ==")
    pts = []
    for f in LADDERS:
        d = json.load(open(f))
        for p in d["points"]:
            pts.append(dict(params=d["params"], n=p["n"], tau=p["tau"], bound=p["bound"],
                            N=p["N"], trials=p["trials"], succ=p["succ_edge"]))
    out = {"fit_by_tau": {}, "nstar": {}}
    print("fitted LP constant c per (params, n, tau) from the existing ladder files (binomial MLE, 95% LR interval):")
    for key in sorted({(p["params"], p["n"], p["tau"]) for p in pts}, key=lambda k: (k[0], k[1])):
        sel = [p for p in pts if (p["params"], p["n"], p["tau"]) == key]
        c, (lo, hi) = fisher.fit_c(sel)
        tr = sum(p["trials"] for p in sel)
        out["fit_by_tau"][f"{key[0]} n={key[1]} tau={key[2]}"] = dict(c=c, lo=lo, hi=hi, trials=tr)
        print(f"  {key[0]} n={key[1]:3d} tau={key[2]:2d}: c = {c:5.2f}  [{lo:5.2f}, {hi:5.2f}]  ({tr} trials total)")
    xs = np.array([math.log(v["c"]) for v in out["fit_by_tau"].values()])
    ts = np.array([math.log(int(k.split("tau=")[1])) for k in out["fit_by_tau"]])
    slope, icpt = np.polyfit(ts, xs, 1)
    out["c_vs_tau"] = dict(a=math.exp(icpt), b=slope)
    print(f"  power fit over all keys: c ~ {math.exp(icpt):.2f} * tau^{slope:.2f}")

    print("\nN*99 at n = 256 (per ring element):")
    print("  params  tau  2B+1    LS/CRB (Gauss)     edge oracle c=1   measured   c_eff=measured/oracle")
    for name, meas in MEASURED.items():
        p = ALL[name] if isinstance(ALL, dict) else next(q for q in ALL if q.name == name)
        ch = make_channel(p, 256, "bcc", "s2")
        ls = fisher.ls_nstar(256, ch.bound, ch.tau)
        orc = fisher.edge_nstar(256, ch.bound, ch.tau)
        out["nstar"][name] = dict(tau=ch.tau, bound=ch.bound, ls=ls, oracle=orc, measured=meas,
                                  c_eff=meas / orc)
        print(f"  {name}  {ch.tau:3d}  {2*ch.bound+1:6d}  {ls:9.3g} (2^{math.log2(ls):.1f})"
              f"  {orc:9.3g} (2^{math.log2(orc):.1f})  {meas:8.3g}   {meas/orc:.2f}")
    return out


def part_mc_check(seed):
    print("\n== Part 1b: brute-force midrange check of P_fail = rho (one coefficient) ==")
    rng = np.random.default_rng(seed)
    rows = []
    for B, M in [(50, 101), (50, 202), (200, 805), (1000, 3000)]:
        trials = 4000
        mc = fisher.midrange_monte_carlo(B, M, trials, rng)
        th = fisher.rho(B, 1, M)
        se = math.sqrt(th * (1 - th) / trials)
        rows.append(dict(B=B, M=M, trials=trials, mc=mc, theory=th))
        print(f"  B={B:5d} M={M:5d}: MC {mc:.4f}  theory {th:.4f}  (+-{se:.4f} 1 s.e., {trials} trials)")
    return rows


def run_trial(p, n, N, seed, trial, window):
    ch = make_channel(p, n, "bcc", "s2")
    rng = np.random.default_rng([seed, n, N, trial])
    s = sample_target(rng, ch)
    c, b = make_transcript(rng, ch, s, N)
    x, _, info = edge.chebyshev_cutting_plane(c, b, ch.target_max + 1, rng)
    r = edge.round_to_range(x, ch.target_max).astype(np.int64)
    z, finfo = ilp.finish(c, b, x, ch.target_max, ch.bound, window=window)
    return dict(round_ok=bool((r == s).all()), ilp_ok=bool((z == s).all()),
                wrong_round=int((r != s).sum()), free=finfo["free"], status=finfo["status"],
                round_feasible=bool(edge.is_feasible(c, b, r.astype(float), ch.bound)),
                t_over=finfo["t"] - ch.bound)


def part_ilp(trials, seed, window, ns):
    print(f"\n== Part 2: edge rounding vs edge + ILP finish (ML-DSA-44, BCC, s2; window={window}; "
          f"{trials} trials/point; seed {seed}, rng = default_rng([seed, n, N, trial])) ==")
    p = ALL["ML-DSA-44"] if isinstance(ALL, dict) else next(q for q in ALL if q.name == "ML-DSA-44")
    res = {}
    for n in ns:
        ch = make_channel(p, n, "bcc", "s2")
        orc = fisher.edge_nstar(n, ch.bound, ch.tau, p=0.5)
        grid = [int(orc * f) for f in (0.5, 0.7, 1.0, 1.4, 2.0, 2.8)]
        res[n] = []
        for N in grid:
            t0 = time.time()
            rows = [run_trial(p, n, N, seed, t, window) for t in range(trials)]
            ro = np.mean([r["round_ok"] for r in rows])
            io = np.mean([r["ilp_ok"] for r in rows])
            fr = np.median([r["free"] for r in rows])
            wr = np.median([r["wrong_round"] for r in rows])
            st = sorted({r["status"] for r in rows})
            wrong = [r for r in rows if not r["round_ok"]]
            wf = sum(r["round_feasible"] for r in wrong)
            res[n].append(dict(N=N, tau=ch.tau, trials=trials, round=ro, ilp=io, free_med=fr,
                               wrong_round_med=wr, status=st, round_wrong=len(wrong), round_wrong_but_feasible=wf, seconds=time.time() - t0))
            print(f"  n={n:3d} tau={ch.tau:2d} N={N:8d}: round {ro:.2f}  ilp {io:.2f}  "
                  f"median wrong-after-round {wr:.0f}  median free {fr:.0f}  wrong-but-feasible {wf}/{len(wrong)}  {st}  ({time.time()-t0:.0f}s)", flush=True)
    print("\nN at 50% / 90% success by log-linear interpolation (None = not reached on grid):")
    summary = {}
    for n, pts in res.items():
        line = {}
        for key in ("round", "ilp"):
            line[key] = {q: interp(pts, key, q) for q in (0.5, 0.9)}
        summary[n] = line
        r50, i50 = line["round"][0.5], line["ilp"][0.5]
        r90, i90 = line["round"][0.9], line["ilp"][0.9]
        ratio = lambda a, b: f"{a/b:.2f}" if a and b else "n/a"
        print(f"  n={n:3d}: N50 round {fmt(r50)} ilp {fmt(i50)} (ratio {ratio(r50, i50)}); "
              f"N90 round {fmt(r90)} ilp {fmt(i90)} (ratio {ratio(r90, i90)})")
    return res, summary


def fmt(v):
    return "None" if v is None else f"{v:.3g}"


def interp(pts, key, q):
    for a, b in zip(pts, pts[1:]):
        if a[key] < q <= b[key]:
            fa, fb = a[key], b[key]
            w = (q - fa) / (fb - fa)
            return math.exp(math.log(a["N"]) + w * (math.log(b["N"]) - math.log(a["N"])))
    if pts[0][key] >= q:
        return pts[0]["N"]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--seed", type=int, default=2031)
    ap.add_argument("--window", type=float, default=1.0)
    ap.add_argument("--n", type=int, nargs="+", default=[8, 16, 32, 64])
    ap.add_argument("--out", default="experiments/results/edge_theory_ilp.json")
    a = ap.parse_args()
    theory = part_theory()
    mc = part_mc_check(a.seed)
    res, summary = part_ilp(a.trials, a.seed, a.window, a.n)
    json.dump(dict(seed=a.seed, trials=a.trials, window=a.window, theory=theory, midrange_mc=mc,
                   ilp=res, ilp_summary={str(k): {kk: {str(q): v for q, v in vv.items()}
                                                   for kk, vv in s.items()} for k, s in summary.items()}),
              open(a.out, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
