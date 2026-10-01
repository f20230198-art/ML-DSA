"""Measure ILWE least-squares error vs. sample count and compare with the
Gaussian prediction std = gamma2/sqrt(3*tau*N), then extrapolate how many
signatures are needed to round every coefficient correctly.

Run from the repo root:  python -m experiments.ilwe_scaling
"""
import math

import numpy as np
from scipy.special import erfcinv

from harness.estimators.ilwe import least_squares
from harness.mldsa.params import ML_DSA_44
from harness.mldsa.sampling import sample_secret
from harness.schemes.ilwe_transcript import make_transcript

p = ML_DSA_44
rng = np.random.default_rng(12345)
print(f"{p.name}: gamma2={p.gamma2} tau={p.tau}; Niot-style N = 4*g2^2/(3*tau) = {4*p.gamma2**2/(3*p.tau):.3g}")
print(f"{'N':>8} {'std measured':>13} {'std theory':>11} {'round-ok frac':>14} {'theory frac':>12}")
for n in (5_000, 20_000, 80_000, 160_000):
    errs, ok = [], []
    for _ in range(3):
        s = sample_secret(rng, p.eta)
        c, b = make_transcript(rng, p, s, n)
        est = least_squares(c, b)
        errs.append(est - s)
        ok.append(np.rint(est) == s)
    errs = np.concatenate(errs)
    theory = p.gamma2 / math.sqrt(3 * p.tau * n)
    th_ok = math.erf(0.5 / (theory * math.sqrt(2)))
    print(f"{n:>8} {errs.std():>13.3f} {theory:>11.3f} {np.concatenate(ok).mean():>14.3f} {th_ok:>12.3f}")

# Extrapolation with the validated Gaussian model.
coeffs = 256 * p.k
print(f"\nExtrapolation for all {coeffs} coefficients (k={p.k} ring elements of s2):")
for target in (0.5, 0.99):
    # need per-coefficient failure f with (1-f)^coeffs >= target
    f = 1 - target ** (1 / coeffs)
    z = math.sqrt(2) * erfcinv(f)  # P(|err|>0.5) = f  ->  0.5/std = z
    std = 0.5 / z
    n = p.gamma2 ** 2 / (3 * p.tau * std ** 2)
    print(f"  full-recovery prob {target}: std needed {std:.3f}, N = {n:.3g} signatures "
          f"(= {n / (4*p.gamma2**2/(3*p.tau)):.2f} x Niot-style 4g2^2/(3tau))")
