"""Paper plan item 4, step 2: what is the partial s2 knowledge below the wall worth to a lattice attacker?

Input: measured RMS error of the edge estimate of s2 (ML-DSA-44, n = 256, experiments/results/partial_recovery_rms.json).
Model (optimistic for the attacker, stated): treat the estimate as x = s2 + e with e Gaussian of the measured RMS
sigma_e; Bayes update of the uniform-on-[-eta, eta] prior (variance eta(eta+1)/3) by Gaussian likelihood gives the posterior
variance 1/(1/var0 + 1/sigma_e^2) per coefficient, applied to ALL k*256 coefficients of s2. Then the primal-uSVP core-SVP
estimate (harness.schemes.mithril_hint, Python substitute for the lattice estimator) with the s2 standard deviation reduced.
s1 is not hinted. Gaussian posterior and an unbiased estimator are both generous to the attacker (the estimate is a
polytope vertex, biased); a proper per-coordinate posterior would be needed to do better, and could only be lower in cost.

Run: python -m experiments.soft_hint_lwe
"""
import json
import math
from collections import defaultdict

from harness.mldsa.params import ML_DSA_44
from harness.schemes.mithril_hint import core_svp_bits, primal_usvp_beta

p = ML_DSA_44
rows = json.load(open("experiments/results/partial_recovery_rms.json"))
by = defaultdict(list)
for r in rows:
    by[r["N"]].append(r["rms_err"])
var0 = p.eta * (p.eta + 1) / 3
sd0 = math.sqrt(var0)
n_s, m = p.l * 256, p.k * 256
b0 = primal_usvp_beta(n_s, m, sd0, sd0)
print(f"{p.name} cap 2^13. Baseline: beta {b0}, core-SVP {core_svp_bits(b0):.1f} bits")
print("N        log2N  rms_err  post_sd  beta  core-SVP  loss(bits)")
for N in sorted(by):
    se = sum(by[N]) / len(by[N])
    post = math.sqrt(1 / (1 / var0 + 1 / se ** 2))
    b = primal_usvp_beta(n_s, m, sd0, post)
    print(f"{N:6d}  {math.log2(N):5.1f}  {se:7.3f}  {post:7.3f}  {b:4d}  {core_svp_bits(b):8.1f}  {core_svp_bits(b0) - core_svp_bits(b):8.1f}")
