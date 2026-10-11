"""Trilithium rejected w_H, exact in a larger dimension n by convolution (H-F2 dimension trend).

Enumerating y (cost (2 gamma1)^n) stops at n = 4. Here we build the exact distribution of
w = A y mod q on Z_q^n instead (cost q^n memory): y has independent coordinates on intervals, so
w = sum_j y_j a_j (a_j = column j of the negacyclic matrix of a) is a sum of independent terms and
its distribution is obtained by adding shifted copies, one coordinate at a time. With k = l = 1:
  - simulator: y uniform on the box [-gamma1 + 1, gamma1]^n;
  - z ok: y in the box with |y_j + (c s1)_j| < gamma1 - beta for all j (a product of intervals);
  - branch 3 (z fails) = box minus z ok; branch 2 = z ok and the r0 check on w - c s2 fails, which
    is a function of w alone, so it is a mask on the w grid.
All counts are exact integers. Cross-checked against trilithium_toy.Toy.histograms at n = 4.
"""
import numpy as np

from harness.schemes.trilithium_toy import Toy, decompose, distances, negacyclic_matrix


def w_counts(amat, intervals, q):
    """Exact counts of w = A y mod q over Z_q^n, y_j uniform on the integer interval intervals[j]."""
    n = amat.shape[0]
    p = np.zeros((q,) * n, dtype=np.int64)
    p[(0,) * n] = 1
    axes = tuple(range(n))
    for j, (lo, hi) in enumerate(intervals):
        col = amat[:, j]
        acc = np.zeros_like(p)
        for t in range(lo, hi + 1):
            acc += np.roll(p, tuple(int(x) for x in (t * col) % q), axis=axes)
        p = acc
    return p


def histograms_conv(toy, a, s1, s2, c):
    """Same output as Toy.histograms (h_all, h2, h3 over w_H cells), computed by convolution."""
    n, q, g1, beta = toy.n, toy.q, toy.gamma1, toy.beta
    amat = negacyclic_matrix(np.mod(a, q), q)
    cs1, cs2 = toy._mul(c, s1), toy._mul(c, s2)
    box = [(-g1 + 1, g1)] * n
    ok = [(max(-g1 + 1, -(g1 - beta - 1) - int(cs1[j])), min(g1, g1 - beta - 1 - int(cs1[j]))) for j in range(n)]
    p_all = w_counts(amat, box, q).ravel()
    p_ok = w_counts(amat, ok, q).ravel()
    grid = np.array(np.unravel_index(np.arange(q ** n), (q,) * n)).T      # w coordinates, row-major
    r1, _ = decompose(grid, q, toy.gamma2)
    cell = toy._cell(r1)
    _, r0 = decompose(grid - cs2, q, toy.gamma2)
    r0_fail = (np.abs(r0) >= toy.gamma2 - beta).any(axis=1)
    cells = toy.m ** n
    h_all = np.bincount(cell, weights=p_all, minlength=cells)
    h_ok = np.bincount(cell, weights=p_ok, minlength=cells)
    h2 = np.bincount(cell, weights=p_ok * r0_fail, minlength=cells)
    return h_all, h2, h_all - h_ok


def run(n_list, gamma1_list, q=17, gamma2=4, tau=1, eta=1, trials=5, seed=2026):
    rows = []
    for n in n_list:
        rng = np.random.default_rng(seed + n)
        for g1 in gamma1_list:
            toy = Toy(n=n, q=q, gamma2=gamma2, gamma1=g1, tau=tau, eta=eta)
            for t in range(trials):
                a, s1, s2, c = toy.sample(rng)
                h_all, h2, h3 = histograms_conv(toy, a, s1, s2, c)
                s1b = rng.integers(-eta, eta + 1, n)
                _, _, h3b = histograms_conv(toy, a, s1b, s2, c)
                tot = h_all.sum()
                row = dict(n=n, gamma1=g1, trial=t, p_rej3=h3.sum() / tot, p_rej2=h2.sum() / tot)
                row["sd3_sim"], row["h2_3_sim"] = distances(h3, h_all)
                row["sd2_sim"], row["h2_2_sim"] = distances(h2, h_all) if h2.sum() else (np.nan, np.nan)
                row["sd3_key"], row["h2_3_key"] = distances(h3, h3b)
                rows.append(row)
    return rows
