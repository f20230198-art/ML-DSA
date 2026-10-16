"""Paper plan item 3: independent check of the TALUS corrupt-coordinator "out-of-box" numbers.

Source (arXiv 2603.22109v5, Sec. 8 Theorem 4 item 3 and the paragraph on the revealed-rejected response):
the coordinator sees z = y + c s1 BEFORE the z-norm and hint-weight checks. Per session the bad event "a
coordinate lands beyond the box, excess attributable to c s1" has probability 2^-32.5 / 2^-34.7 / 2^-36.6
(ML-DSA-44/65/87, nu = 3), i.e. expected 2^-19.5 / 2^-20.7 / 2^-22.6 occurrences over Q_cap sessions, and a
z-norm-rejected coordinate (|z| >= gamma1 - beta) occurs once per 2^22-2^25 sessions.

Model (ours): y = sum of nu independent uniform integer variables, each on w = 2 gamma1 / nu consecutive integers,
centred so the support is [-gamma1, gamma1]-ish; (c s1)_j = sum of tau independent +-s, s uniform on
[-eta, eta] (i.i.d. across the tau positions: exact for a random key, an approximation for a fixed key).
Per-coordinate:
  p_edge = P(y + x > gamma1)           (beyond the box; informative if x>0)
  p_norm = P(|y + x| >= gamma1 - beta) (z-norm rejection region)
per session multiply by n * l (union bound over coordinates). Compared to the cap Q_cap = 2^13 / 2^14 / 2^14.
"""
import math

import numpy as np

LEVELS = [("ML-DSA-44", 2 ** 17, 39, 4, 2, 78, 13, -32.5), ("ML-DSA-65", 2 ** 19, 49, 5, 4, 196, 14, -34.7),
          ("ML-DSA-87", 2 ** 19, 60, 7, 2, 120, 14, -36.6)]
NU = 3
N = 256


def conv(a, b):
    n = len(a) + len(b) - 1
    size = 1 << (n - 1).bit_length()
    f = np.fft.irfft(np.fft.rfft(a, size) * np.fft.rfft(b, size), size)[:n]
    return np.maximum(f, 0.0)


def pmf_cs1(tau, eta):
    u = np.full(2 * eta + 1, 1 / (2 * eta + 1))
    out = np.array([1.0])
    for _ in range(tau):
        out = conv(out, u)
    return out / out.sum(), tau * eta        # support -tau*eta .. tau*eta


def pmf_nonce(gamma1, nu):
    w = 2 * gamma1 // nu
    u = np.full(w, 1.0 / w)
    out = u
    for _ in range(nu - 1):
        out = conv(out, u)
    out /= out.sum()
    # support is 0 .. nu*(w-1); centre it on 0
    return out, (nu * (w - 1)) / 2.0


def main():
    print("TALUS coordinator out-of-box tail, our exact convolution vs paper (nu = 3)")
    for name, g1, tau, l, eta, beta, cap, paper in LEVELS:
        px, xmax = pmf_cs1(tau, eta)
        py, centre = pmf_nonce(g1, NU)
        ys = np.arange(len(py)) - centre              # float centred support
        # tail function T(t) = P(y > t)
        tail = np.cumsum(py[::-1])[::-1]              # P(y >= idx)
        def p_y_gt(t):
            idx = np.floor(t + centre).astype(int) + 1
            return np.where(idx >= len(py), 0.0, np.where(idx <= 0, 1.0, tail[np.clip(idx, 0, len(py) - 1)]))
        xs = np.arange(len(px)) - xmax
        p_edge = float((px * p_y_gt(g1 - xs)).sum())
        # symmetric z-norm region: |y+x| >= g1-beta -> twice the one-sided P(y+x >= g1-beta)
        p_norm = 2 * float((px * p_y_gt(g1 - beta - 1 - xs)).sum())
        per_sess = N * l * p_edge
        per_norm = N * l * p_norm
        print(f"{name}: per-coordinate p_edge 2^{math.log2(p_edge):.1f}; per-session (x n l) 2^{math.log2(per_sess):.1f} "
              f"[paper 2^{paper}]; over Q_cap=2^{cap}: expected 2^{math.log2(per_sess) + cap:.1f}")
        print(f"      z-norm region: once per 2^{-math.log2(per_norm):.1f} sessions [paper: 2^22-2^25]")


if __name__ == "__main__":
    main()
