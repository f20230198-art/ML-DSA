"""Paper plan item 9: corrected Devevey-Fawzi-Passelegue-Stehle App. A.6 bound, checked numerically.

With x = 1 - 1/phi^2 and h = 1/phi, the statements compared (log2) are
  printed (A.6 / Mithril Lemma 2.5):   x^(n-1) * n * (1 - h)                         [not an upper bound]
  cylinder done exactly:               2 V_{n-1}/V_n * x^((n-1)/2) * (1 - h)
  closed form (proposition, part a):   sqrt(2(n+2)/pi) * x^((n-1)/2) * (1 - h)
  sharp form (proposition, part b):    sqrt(2(n+2)/pi) * x^((n+1)/2) / ((n-1) h)
against the exact I_x((n+1)/2, 1/2) (mpmath, 50 digits). Claims checked: exact <= cylinder <= closed, and exact <= sharp (n >= 2).

  python -m experiments.a6_corrected_bound > experiments/results/a6_corrected_bound.txt
"""
import math

import mpmath as mp

from harness.schemes.mithril_params import cylinder_bound_log2, lemma25_bound_log2

mp.mp.dps = 50


def exact_log2(n, phi):
    x = 1 - mp.mpf(1) / phi ** 2
    return float(mp.log(mp.betainc((n + 1) / mp.mpf(2), mp.mpf(1) / 2, 0, x, regularized=True), 2))


def closed_log2(n, phi):
    return 0.5 * math.log2(2 * (n + 2) / math.pi) + (n - 1) / 2 * math.log2(1 - 1 / phi ** 2) + math.log2(1 - 1 / phi)


def sharp_log2(n, phi):
    return 0.5 * math.log2(2 * (n + 2) / math.pi) + (n + 1) / 2 * math.log2(1 - 1 / phi ** 2) - math.log2((n - 1) / phi)


dims = [2, 3, 4, 8, 16, 32, 64, 100, 128, 256, 512, 1024, 1536, 2048, 2304, 2560, 3072, 3584, 4096, 8192]
phis = [1.05, 1.2, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 25, 50]
bad_cyl = bad_closed = bad_sharp = printed_invalid = 0
worst_sharp = 0.0
worst_gap = 0.0
for n in dims:
    for phi in phis:
        e, cy, cl, pr = exact_log2(n, phi), cylinder_bound_log2(n, phi), closed_log2(n, phi), lemma25_bound_log2(n, phi)
        bad_cyl += cy < e - 1e-9
        bad_closed += cl < cy - 1e-9
        printed_invalid += pr < e
        worst_gap = max(worst_gap, cl - e)
        sh = sharp_log2(n, phi)
        bad_sharp += sh < e - 1e-9
        worst_sharp = max(worst_sharp, sh - e)
print(f"grid: {len(dims)} dims x {len(phis)} phis = {len(dims) * len(phis)} points")
print(f"cylinder bound below exact (violations): {bad_cyl}")
print(f"closed form below cylinder (violations): {bad_closed}")
print(f"printed A.6 bound below exact (invalid points): {printed_invalid}")
print(f"largest slack closed - exact: {worst_gap:.2f} bits")
print(f"sharp form below exact (violations): {bad_sharp}; largest slack sharp - exact: {worst_sharp:.2f} bits\n")
print("Mithril dimensions dim = 256(k + l) with the script's phi (ML-DSA-44/65/87), plus n = 100")
print("    n  phi   exact   printed  cylinder  closed   sharp")
for n, phi in [(2048, 7), (2816, 8), (3840, 9), (100, 7)]:
    print(f" {n:5d} {phi:4} {exact_log2(n, phi):8.2f} {lemma25_bound_log2(n, phi):8.2f} "
          f"{cylinder_bound_log2(n, phi):8.2f} {closed_log2(n, phi):8.2f} {sharp_log2(n, phi):8.2f}")
