"""Open-artifact driver (paper plan item 12): one command per table or figure.

  python -m experiments.reproduce            # list every item, its command, cost and output
  python -m experiments.reproduce --fast     # run the items marked fast (minutes, CPU only)
  python -m experiments.reproduce --run ID   # run one item by id

Outputs are written under experiments/results/. Items marked heavy need a GPU and hours and are
listed with the command that produced the stored results; they are not run by --fast.
"""
import argparse
import subprocess
import sys

R = "experiments/results"
# id, what it backs, command (argv, run from repo root), cost, output file, stdout captured into output?
ITEMS = [
    ("insider-wall", "Scorecard: TALUS MPC/TEE insider walls", ["-m", "experiments.talus_insider_wall"], "fast", f"{R}/talus_insider_wall.txt", True),
    ("m2-fisher", "Scorecard: exact m = 2 Fisher check", ["-m", "experiments.talus_m2_fisher"], "fast", f"{R}/talus_m2_fisher.txt", True),
    ("a6-bound", "Mithril App. A.6 corrected bound (320-point check)", ["-m", "experiments.a6_corrected_bound"], "fast", f"{R}/a6_corrected_bound.txt", True),
    ("item8-summary", "TALUS success table with CIs and logistic fit", ["-m", "experiments.item8_analysis"], "fast", f"{R}/item8/summary.txt", True),
    ("item8-full", "TALUS whole-secret extrapolation from the fitted per-element curve", ["-m", "experiments.item8_full_secret"], "fast", f"{R}/item8/full_secret.txt", True),
    ("arch-diagram", "Figure: harness architecture", ["-m", "experiments.arch_diagram"], "fast", f"{R}/harness_architecture.png", False),
    ("ls-error-plot", "Figure: least-squares error vs N with theory curve", ["-m", "experiments.ls_error_plot"], "fast-ish", f"{R}/ls_error_vs_N.png", False),
    ("coordinator-tail", "Scorecard: TALUS coordinator out-of-box tail probabilities", ["-m", "experiments.talus_coordinator_tail"], "fast", f"{R}/talus_coordinator_tail.txt", True),
    ("m2-sim", "TALUS m = 2 insider simulation (writes .json; table in .txt made from it)", ["-m", "experiments.talus_m2_sim", "--w", "32", "64", "128", "256", "--trials", "20"], "medium (CPU, ~1 h)", f"{R}/talus_m2_sim.json", False),
    ("kao-p2-real", "Kao P2 broadcast leak at real ML-DSA size (s1 from one signature)", ["-m", "experiments.kao_p2_real_demo", "--params", "ML-DSA-44", "--keys", "5"], "fast", f"{R}/kao_p2_real_demo_44.txt", True),
    ("item8-ilp", "TALUS ILP trials behind the success table", ["sh", "experiments/run_item8.sh"], "heavy (GPU, hours)", f"{R}/item8/ilp_*.json", False),
    ("partial-recovery", "TALUS partial recovery at the cap", ["-m", "experiments.partial_recovery"], "medium (GPU, minutes)", f"{R}/partial_recovery.json", False),
    ("mithril-real", "Mithril views on real Go transcripts (needs Go, harness/mithril_go/dump_test.go)", ["-m", "experiments.mithril_real_transcripts"], "medium", f"{R}/mithril_real_transcripts.txt", True),
    ("mithril-hint", "Mithril ML-DSA-65 hint accounting (Sage script, run separately)", ["sage", "experiments/mithril_hint_estimator_full65.sage"], "heavy (Sage)", f"{R}/mithril_hint_estimator_full65.txt", False),
]


def run(item):
    ident, _, argv, _, out, capture = item
    cmd = argv if argv[0] in ("sh", "sage") else [sys.executable] + argv
    print(f"== {ident}: {' '.join(cmd)}", flush=True)
    if capture:
        res = subprocess.run(cmd, capture_output=True, text=True)
        sys.stdout.write(res.stdout)
        if res.returncode == 0:
            with open(out, "w", encoding="utf-8") as f:
                f.write(res.stdout)
        else:
            sys.stderr.write(res.stderr)
        return res.returncode
    return subprocess.run(cmd).returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--run", default=None)
    args = ap.parse_args()
    if args.run:
        sel = [i for i in ITEMS if i[0] == args.run]
        if not sel:
            sys.exit(f"unknown id {args.run}")
        sys.exit(run(sel[0]))
    if args.fast:
        bad = [i[0] for i in ITEMS if i[3] == "fast" and run(i) != 0]
        print("FAILED:" if bad else "all fast items ok", *bad)
        sys.exit(1 if bad else 0)
    for ident, what, argv, cost, out, _ in ITEMS:
        print(f"{ident:17s} {cost:24s} {out}\n    {what}\n    {' '.join(argv)}")


if __name__ == "__main__":
    main()
