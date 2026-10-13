"""Gate B end-to-end check: real ML-DSA-44 attempts -> TalusBCCView -> observations_to_cb -> the
unchanged edge estimator, which must recover the key target s2 - t0 for ring element 0.

Run: python -m experiments.gate_b_views --N 200000 --trials 2
Rejection (BCC and z-norm) is applied by the view itself, so attempts are drawn until N accepted
observations exist. Same estimator settings as experiments/mldsa_controls.py.
"""
import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from harness.estimators import edge
from harness.mldsa.params import ALL, D
from harness.schemes.mldsa_controls import Signer
from harness.schemes.views import PublicKey, TalusBCCView, observations_to_cb, raw_attempts

_S = None


def _init(name, xi):
    global _S
    signer = Signer(ALL[name], xi)
    pk = PublicKey.from_signer(signer)
    _S = (signer, pk, TalusBCCView(pk))


def _work(args):
    seed, want, chunk = args
    signer, pk, view = _S
    rng = np.random.default_rng(seed)
    cs, bs, drawn, got = [], [], 0, 0
    while got < want:
        obs = view.observe_all(raw_attempts(signer, rng, chunk))
        drawn += chunk
        c, b = observations_to_cb(obs, pk, 0)
        cs.append(c)
        bs.append(b)
        got += len(c)
    return np.concatenate(cs), np.concatenate(bs), drawn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default="ML-DSA-44", choices=list(ALL))
    ap.add_argument("--N", type=int, nargs="+", default=[200000])
    ap.add_argument("--trials", type=int, default=2)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--device", default="gpu", choices=["cpu", "gpu"])
    ap.add_argument("--seed", type=int, default=2029)
    ap.add_argument("--out", default="experiments/results/gate_b_views.json")
    args = ap.parse_args()
    p = ALL[args.params]
    target_max = (1 << (D - 1)) + p.eta
    rows = []
    for trial in range(args.trials):
        xi = np.random.default_rng([args.seed, trial]).bytes(32)
        signer = Signer(p, xi)
        key = signer.target(0, positive=True)
        t = time.time()
        share = -(-max(args.N) // args.workers)
        with ProcessPoolExecutor(args.workers, initializer=_init, initargs=(args.params, xi)) as pool:
            parts = list(pool.map(_work, [([args.seed, trial, i], share, 2000) for i in range(args.workers)]))
        c = np.concatenate([q[0] for q in parts])
        b = np.concatenate([q[1] for q in parts])
        drawn = sum(q[2] for q in parts)
        t_sign = time.time() - t
        for n in sorted(args.N):
            rng = np.random.default_rng([args.seed, trial, n])
            t = time.time()
            if args.device == "gpu":
                from harness.estimators import edge_gpu
                x, _, info = edge_gpu.chebyshev_cutting_plane_gpu(c[:n], b[:n], target_max + 1, rng)
            else:
                x, _, info = edge.chebyshev_cutting_plane(c[:n], b[:n], target_max + 1, rng)
            rx = edge.round_to_range(x, target_max)
            row = dict(trial=trial, N=n, attempts_drawn=drawn, accept_rate=len(c) / drawn,
                       edge_is_key=bool((rx == key).all()), err_key=float(np.abs(x - key).max()),
                       sign_seconds=t_sign, est_seconds=time.time() - t)
            rows.append(row)
            print(row, flush=True)
            json.dump(dict(args=vars(args), rows=rows), open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
