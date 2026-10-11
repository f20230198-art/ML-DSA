"""Sanity check: Niot's attack 2 (ePrint 2026/1386) on transcripts from real ML-DSA signing.

Channel: signer without the r0 check (as in early TALUS), b = LowBits(w) - c (s2 - t0).
Niot's estimator is least squares; its per-coefficient error std in the uniform-noise model is
    sigma(N) = gamma2 / sqrt(3 tau N),
and his sample formula N = 4 gamma2^2 / (3 tau) is where sigma = 0.5.
We measure the least-squares error on real transcripts against sigma(N), then extrapolate.
Run: python -m experiments.niot_sanity --N 5000 20000 80000 200000 --trials 3
"""
import argparse
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from harness.estimators import edge
from harness.mldsa.params import ALL
from experiments.mldsa_controls import _init, transcript


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default="ML-DSA-44", choices=list(ALL))
    ap.add_argument("--N", type=int, nargs="+", default=[5000, 20000, 80000, 200000])
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=1386)
    args = ap.parse_args()
    p = ALL[args.params]
    from harness.schemes.mldsa_controls import Signer
    rows = []
    print(f"{args.params}: gamma2={p.gamma2} tau={p.tau}; Niot N = 4 g2^2/(3 tau) = "
          f"{4 * p.gamma2 ** 2 / (3 * p.tau):.3g}")
    print(f"{'trial':>5} {'N':>7} {'std meas':>9} {'std theory':>10} {'ratio':>6} {'round-ok':>8}")
    for trial in range(args.trials):
        xi = np.random.default_rng([args.seed, trial]).bytes(32)
        key = Signer(p, xi).target(0, positive=True)
        with ProcessPoolExecutor(args.workers, initializer=_init, initargs=(args.params, xi)) as pool:
            t = time.time()
            c, b = transcript(pool, [args.seed, trial], max(args.N), False, args.workers)
            t_sign = time.time() - t
        for n in sorted(args.N):
            x = edge.least_squares_fft(c[:n], b[:n])
            err = x - key
            meas = float(err.std())
            theory = p.gamma2 / math.sqrt(3 * p.tau * n)
            ok = float((np.rint(x) == key).mean())
            rows.append(dict(trial=trial, N=n, std=meas, theory=theory, round_ok=ok, sign_seconds=t_sign))
            print(f"{trial:5d} {n:7d} {meas:9.3f} {theory:10.3f} {meas / theory:6.3f} {ok:8.3f}", flush=True)
    ratios = np.array([r["std"] / r["theory"] for r in rows])
    print(f"mean ratio measured/theory = {ratios.mean():.3f} (sd {ratios.std():.3f}, {len(ratios)} runs)")
    json.dump(dict(args=vars(args), rows=rows),
              open(f"experiments/results/niot_sanity_{args.params}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
