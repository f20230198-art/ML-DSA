"""Niot's attacks on real TALUS v0.1 transcripts (harness/schemes/talus_v01.py), ML-DSA-44.

Attack 1: s1 from KeyGen Feldman broadcast, and from one MPC signature (Phi_{h,0} = A y_h).
Attack 2: least squares on b = r0 - c (s2 - t0), all k = 4 rows, error vs N against theory
          sigma_e / sqrt(N tau), sigma_e = (gamma2 - beta)/sqrt(3).
Usage: python -m experiments.talus_v01_niot [N_max] [keys]
"""
import sys
import time

import numpy as np

from harness.estimators.ilwe import least_squares
from harness.mldsa.params import ALL, Q
from harness.mldsa.rounding import mod_pm
from harness.schemes.talus_v01 import (TalusV01, TalusV01MPCView, TalusV01SigView, attack1_keygen,
                                       attack1_nonce, s2_channel)

P = ALL["ML-DSA-44"]
N_MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
KEYS = [int(s) for s in sys.argv[2].split(",")] if len(sys.argv) > 2 else [101, 102, 103]
GRID = [n for n in (1_000, 3_000, 10_000, 30_000, 100_000, 300_000) if n <= N_MAX]


def main():
    sigma_e = (P.gamma2 - P.beta) / np.sqrt(3)
    print(f"ML-DSA-44, |S|=3, keys(seeds)={KEYS}, N grid={GRID}")
    for seed in KEYS:
        t = TalusV01(P, bytes([seed % 256]) * 32, n_signers=3, seed=seed)
        a1k = attack1_keygen(t.a_hat, t.keygen_broadcast(), t.ids)
        t0 = time.time()
        c = np.empty((N_MAX, 256), dtype=np.float32)
        b = np.empty((N_MAX, P.k, 256), dtype=np.float32)
        att_total, a1n_ok, a1n_tried = 0, 0, 0
        for i in range(N_MAX):
            _, att = t.sign(i.to_bytes(4, "little"))
            att_total += len(att)
            o = TalusV01MPCView().observe(att[-1])
            if i < 20:
                a1n_tried += 1
                r = attack1_nonce(t.a_hat, o)
                a1n_ok += int(r is not None and (r == t.sec["s1"]).all())
            c[i] = o.fields["c"]
            b[i] = s2_channel(P, t.a_hat, t.sec["t1"], o)
        print(f"seed {seed}: attack1 keygen exact={a1k is not None and (a1k == t.sec['s1']).all()}, "
              f"attack1 one-signature exact {a1n_ok}/{a1n_tried}; "
              f"{N_MAX} sigs from {att_total} attempts ({N_MAX/att_total:.3f} per attempt) "
              f"in {time.time()-t0:.0f}s")
        target = mod_pm(t.sec["s2"] - t.sec["t0"], Q).astype(float)
        for n in GRID:
            errs, exact = [], 0
            for j in range(P.k):
                x = least_squares(c[:n].astype(float), b[:n, j].astype(float))
                errs.append(x - target[j])
                exact += int((np.rint(x) == target[j]).sum())
            e = np.concatenate(errs)
            theory = sigma_e / np.sqrt(n * P.tau)
            print(f"  N={n:>7}: rms err {np.sqrt(np.mean(e**2)):8.2f}  theory {theory:8.2f}  "
                  f"coeffs exact {exact}/{P.k*256}  max|err| {np.abs(e).max():.1f}")
    n_need = (sigma_e / 0.25) ** 2 / P.tau
    print(f"theory: rms error 0.25 (most coefficients round correctly) needs N ~ {n_need:.2e}")


if __name__ == "__main__":
    main()
