"""Exhaustive check of Quorus (ePrint 2025/1163, USENIX Security 2026) Lemma 8, eq. (2), on toy parameters.

Lemma 8: q, alpha, beta integers, alpha even, alpha | q-1, beta < alpha/2, delta = (q-1)/alpha. For any s with |s| <= beta,
U' = HighBits(a' + s) with a' uniform in Z_q conditioned on |a'_0| >= alpha/2 - beta equals U~, printed as
  U~(a1) = (2 beta + 1) / (2 (beta + 1) delta + 1)   for a1 != 0
  U~(0)  = (2 beta + 2) / (2 (beta + 1) delta + 1).
We enumerate every a' and every s, compute U', and compare with the printed U~ and with the corrected normaliser
(2 beta + 1) delta + 1 (support size). Run: python -m experiments.quorus_lemma8_check
"""
from fractions import Fraction


def decompose(r, q, alpha):
    r %= q
    r0 = r % alpha
    if r0 > alpha // 2:
        r0 -= alpha
    if r - r0 == q - 1:
        return 0, r0 - 1
    return (r - r0) // alpha, r0


def dist(q, alpha, beta, s):
    cnt = {}
    n = 0
    for a in range(q):
        _, a0 = decompose(a, q, alpha)
        if abs(a0) < alpha // 2 - beta:
            continue
        a1, _ = decompose(a + s, q, alpha)
        cnt[a1] = cnt.get(a1, 0) + 1
        n += 1
    return cnt, n


def main():
    for q, alpha, beta in [(97, 8, 2), (97, 8, 3), (193, 16, 5), (193, 12, 3), (257, 16, 7), (769, 32, 9)]:
        if (q - 1) % alpha or alpha % 2 or beta >= alpha // 2:
            continue
        delta = (q - 1) // alpha
        printed_den = 2 * (beta + 1) * delta + 1
        right_den = (2 * beta + 1) * delta + 1
        same = None
        ok_right = True
        for s in range(-beta, beta + 1):
            cnt, n = dist(q, alpha, beta, s)
            d = {k: Fraction(v, n) for k, v in cnt.items()}
            same = d if same is None else same
            if d != same:
                print(f"  q={q} alpha={alpha} beta={beta}: depends on s (!)")
            exp = {a: Fraction((2 * beta + 2) if a == 0 else (2 * beta + 1), right_den) for a in range(delta)}
            ok_right &= (d == exp)
        total_printed = sum(Fraction((2 * beta + 2) if a == 0 else (2 * beta + 1), printed_den) for a in range(delta))
        print(f"q={q} alpha={alpha} beta={beta} delta={delta}: independent of s: yes; matches corrected normaliser "
              f"(2beta+1)delta+1={right_den}: {ok_right}; printed normaliser 2(beta+1)delta+1={printed_den} sums to {total_printed} "
              f"({float(total_printed):.4f})")


if __name__ == "__main__":
    main()
