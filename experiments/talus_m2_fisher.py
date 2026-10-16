"""Paper plan item 3, open point: check the hand-cut m = 2 Fisher number in talus_insider_wall.py.

Insider with m = 2 honest nonce shares sees z' = y_h + c s1, y_h = u1 + u2, each u_i uniform on w
consecutive integers (w = 2 gamma1 / nu). The pmf of y_h is a discrete triangle on 2w - 1 points.
Shifting by an integer k = (c s1)_j is a location parameter; the discrete Fisher information for a
unit shift is I = sum_x (p(x) - p(x-1))^2 / p(x-1)-type; we use the symmetric form
I = sum over x of (p(x+1) - p(x))^2 / (p(x+1) + p(x)) * 2, which is the chi-square-like divergence rate
between neighbouring shifts. Outside the support the shift is detected with certainty (edge), handled
separately: an observation outside the shifted support rules out that shift. We report both:
  - bulk information (interior, exact sum)
  - the first-pass formula 2 ln(a) / a^2 used earlier
and the resulting wall q = 4 / (I tau) in bits, for the MPC profile nu = 2T - 1.
"""
import math

LEVELS = [("ML-DSA-44", 2 ** 17, 39, 13), ("ML-DSA-65", 2 ** 19, 49, 14), ("ML-DSA-87", 2 ** 19, 60, 14)]


def tri_pmf(w):
    # sum of two uniforms on {0..w-1}: p(k) = (min(k, 2w-2-k) + 1) / w^2, k = 0..2w-2
    return [(min(k, 2 * w - 2 - k) + 1) / (w * w) for k in range(2 * w - 1)]


def bulk_info(w):
    p = tri_pmf(w)
    # interior slopes only (skip the two edge points where the support ends)
    s = 0.0
    for k in range(len(p) - 1):
        a, b = p[k], p[k + 1]
        s += (b - a) ** 2 / ((a + b) / 2)
    return s


def main():
    print("m = 2: exact discrete bulk Fisher information vs first-pass formula 2 ln(a)/a^2")
    for w in [64, 256, 1024, 4096, 16384]:
        i_ex = bulk_info(w)
        i_fp = 2 * math.log(w) / w ** 2
        print(f"  w={w:6d}  exact {i_ex:.3e}  first-pass {i_fp:.3e}  ratio exact/first-pass {i_ex / i_fp:.3f}")
    print("\nWall for MPC profile, m = T = 2 only (nu = 3), using the exact bulk information (no edge help):")
    for name, g1, tau, cap in LEVELS:
        w = 2 * g1 // 3
        # exact sum is too long for w ~ 1e5 in pure python? it is O(w): fine.
        i_ex = bulk_info(w)
        q = 4 / (i_ex * tau)
        print(f"  {name}: w={w}, I={i_ex:.3e}, wall 2^{math.log2(q):.1f}, margin {math.log2(q) - cap:+.1f} bits")


if __name__ == "__main__":
    main()
