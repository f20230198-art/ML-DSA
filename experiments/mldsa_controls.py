"""Positive / negative controls for the edge-aware estimator on transcripts from real ML-DSA signing.

Run: python -m experiments.mldsa_controls --N 100000 200000 400000 --trials 3
Positive control: signer without the r0 check (b = LowBits(w) - c (s2 - t0)); the estimator must
recover s2 - t0 (= key). Negative control: genuine ML-DSA (b = c t0 + r0); the estimator must NOT
return s2 - t0 (it may return -t0, which is public-equivalent). Both runs use the same estimator
settings (box for s2 - t0), as an attacker would not know which case it is in.
"""
import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from harness.estimators import edge
from harness.mldsa.params import ALL, D
from harness.schemes.mldsa_controls import Signer

_SIGNER = None


def _init(name, xi):
    global _SIGNER
    _SIGNER = Signer(ALL[name], xi)


def _work(args):
    seed, count, r0_check = args
    return _SIGNER.transcript(np.random.default_rng(seed), count, 0, r0_check)


def transcript(pool, seed, count, r0_check, workers):
    share = -(-count // workers)
    parts = list(pool.map(_work, [([*seed, i], share, r0_check) for i in range(workers)]))
    return np.concatenate([p[0] for p in parts])[:count], np.concatenate([p[1] for p in parts])[:count]


def estimate(c, b, box, rng, device):
    if device == "gpu":
        from harness.estimators import edge_gpu
        obs = edge_gpu.GpuObs(c, b)
        x, _, info = edge_gpu.chebyshev_cutting_plane_gpu(c, b, box, rng, obs=obs)
        return x, obs.least_squares(), info
    x, _, info = edge.chebyshev_cutting_plane(c, b, box, rng)
    return x, edge.least_squares_fft(c, b), info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default="ML-DSA-44", choices=list(ALL))
    ap.add_argument("--N", type=int, nargs="+", default=[100000, 200000, 400000])
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--device", default="gpu", choices=["cpu", "gpu"])
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    p = ALL[args.params]
    out = args.out or f"experiments/results/mldsa_controls_{args.params}.json"
    data = json.load(open(out)) if os.path.exists(out) else dict(args=vars(args), rows=[])
    done = {(r["trial"], r["control"], r["N"]) for r in data["rows"]}
    target_max = (1 << (D - 1)) + p.eta
    for trial in range(args.trials):
        xi = np.random.default_rng([args.seed, trial]).bytes(32)
        with ProcessPoolExecutor(args.workers, initializer=_init, initargs=(args.params, xi)) as pool:
            signer = Signer(p, xi)
            key = signer.target(0, positive=True)
            t0neg = signer.target(0, positive=False)
            for control, r0_check in (("positive", False), ("negative", True)):
                todo = [n for n in args.N if (trial, control, n) not in done]
                if not todo:
                    continue
                t = time.time()
                c, b = transcript(pool, [args.seed, trial, int(r0_check)], max(todo), r0_check, args.workers)
                t_sign = time.time() - t
                for n in sorted(todo):
                    rng = np.random.default_rng([args.seed, trial, n, int(r0_check)])
                    t = time.time()
                    x, xl, info = estimate(c[:n], b[:n], target_max + 1, rng, args.device)
                    rx = edge.round_to_range(x, target_max)
                    rl = edge.round_to_range(xl, target_max)
                    row = dict(trial=trial, control=control, N=n,
                               edge_is_key=bool((rx == key).all()), edge_is_t0=bool((rx == t0neg).all()),
                               ls_is_key=bool((rl == key).all()),
                               err_key=float(np.abs(x - key).max()), err_t0=float(np.abs(x - t0neg).max()),
                               converged=None if info is None else info.get("converged"),
                               sign_seconds=t_sign, est_seconds=time.time() - t)
                    data["rows"].append(row)
                    json.dump(data, open(out, "w"), indent=1)
                    print(f"trial {trial} {control:8s} N={n:7d} key={row['edge_is_key']!s:5} "
                          f"t0={row['edge_is_t0']!s:5} err_key={row['err_key']:.3g} err_t0={row['err_t0']:.3g} "
                          f"({row['est_seconds']:.0f}s est, {t_sign:.0f}s sign)", flush=True)


if __name__ == "__main__":
    main()
