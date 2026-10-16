"""Paper plan item 3 (first pass): TALUS insider views, back-of-envelope walls.

Source: TALUS arXiv 2603.22109v5, App. D "Insiders" (lines ~1732-1767 of our text extraction) and
Sec. 8 (Theorem 4). An insider holding t of the nu nonce shares subtracts them from z, leaving
z' = y_h + c s1 with y_h ~ IH(m), m = nu - t, each summand uniform of width 2 gamma1 / nu.
MPC profile: nu = 2T - 1, corrupt minority t = T - 1, so m = T >= 2. TEE coalition: m = 1.

Estimates (ours, rough, not from the paper unless marked):
  m = 1 (uniform, sharp edge): integer-uniqueness wall (2 gamma1 / nu) ln(2 n l) / tau
        [this formula is quoted from the paper for the TEE insider, with nu = T].
  m = 2 (triangular): location Fisher information of a discretised triangle of half-width a is
        about 2 ln(a) / a^2 (the continuous integral diverges logarithmically at the edges; we cut
        it at distance 1). Fisher-rate wall q ~ 4 / (I tau), the paper's own form for the external view.
  m >= 3: smooth density, Fisher ~ 1 / variance-ish; we use the IH(m) variance m w^2 / 12 as a
        lower bound on the wall (Cramer-Rao with Gaussian-like noise: I >= 1 / var).
Compared against the per-key cap Q_cap = 2^13 / 2^14 / 2^14 (PW v0.22).
"""
import math

LEVELS = [("ML-DSA-44", 2 ** 17, 39, 4, 13), ("ML-DSA-65", 2 ** 19, 49, 5, 14),
          ("ML-DSA-87", 2 ** 19, 60, 7, 14)]
N = 256


def wall_bits(gamma1, tau, l, nu, m):
    w = 2 * gamma1 / nu            # width of one nonce summand
    if m == 1:
        q = w * math.log(2 * N * l) / tau
    elif m == 2:
        a = w                      # triangle half-width = one summand width
        info = 2 * math.log(a) / a ** 2
        q = 4 / (info * tau)
    else:
        var = m * w ** 2 / 12
        q = 4 * var / tau
    return math.log2(q)


def main():
    print("TALUS insider walls (log2 signatures) vs cap; rough, see docstring")
    for name, g1, tau, l, cap in LEVELS:
        print(f"\n{name} (cap 2^{cap})")
        print("  MPC insider, nu = 2T-1, t = T-1, m = T:")
        for T in range(2, 7):
            b = wall_bits(g1, tau, l, 2 * T - 1, T)
            print(f"    T={T}: wall 2^{b:5.1f}  margin {b - cap:+5.1f} bits")
        print("  TEE coalition, nu = T, m = 1:")
        for T in range(2, 13):
            b = wall_bits(g1, tau, l, T, 1)
            flag = "  BELOW CAP" if b < cap else ""
            print(f"    T={T:2d}: wall 2^{b:5.1f}  margin {b - cap:+5.1f} bits{flag}")


if __name__ == "__main__":
    main()
