"""Trilithium rejected w_H at n = 8 by Monte Carlo sampling (H-F2, beyond the exact range).

The exact methods stop at n = 6 (enumeration: (2 gamma1)^n; convolution: q^n memory). Here y is
sampled uniformly from the box and classified exactly as in trilithium_toy.Toy.histograms. Two
independent streams are drawn: stream A gives the branch histograms h2, h3 (and its own full
histogram), stream B gives an independent simulator histogram h_sim. The plug-in Hellinger distance
has a positive bias of about cells / (8 M); to show it, we also report the "null" distance between
stream A's full histogram and stream B (same distribution, so any value there is sampling noise).
A branch gap is only resolved where it is well above that null value.
"""
import numpy as np

from harness.schemes.trilithium_toy import decompose, distances, negacyclic_matrix


def sample_counts(toy, a, s1, s2, c, samples, rng, chunk=1 << 20):
    """Counts over w_H cells from `samples` uniform y: (h_all, h2, h3), same meaning as Toy.histograms."""
    n, q, g1, beta = toy.n, toy.q, toy.gamma1, toy.beta
    amat = negacyclic_matrix(np.mod(a, q), q)
    cs1, cs2 = toy._mul(c, s1), toy._mul(c, s2)
    cells = toy.m ** n
    h_all, h2, h3 = (np.zeros(cells, dtype=np.int64) for _ in range(3))
    left = samples
    while left > 0:
        b = min(chunk, left)
        left -= b
        y = rng.integers(-g1 + 1, g1 + 1, size=(b, n), dtype=np.int64)
        w = (y @ amat.T) % q
        r1, _ = decompose(w, q, toy.gamma2)
        cell = toy._cell(r1)
        h_all += np.bincount(cell, minlength=cells)
        z_fail = (np.abs(y + cs1) >= g1 - beta).any(axis=1)
        _, r0 = decompose(w - cs2, q, toy.gamma2)
        r0_fail = (np.abs(r0) >= toy.gamma2 - beta).any(axis=1)
        h3 += np.bincount(cell[z_fail], minlength=cells)
        h2 += np.bincount(cell[~z_fail & r0_fail], minlength=cells)
    return h_all, h2, h3


def compare(toy, a, s1, s2, c, samples, rng):
    """Branch-vs-simulator Hellinger distances from two independent streams, plus the null value."""
    h_a, h2, h3 = sample_counts(toy, a, s1, s2, c, samples, rng)
    h_sim, _, _ = sample_counts(toy, a, s1, s2, c, samples, rng)
    tot = h_a.sum()
    row = dict(p_rej3=h3.sum() / tot, p_rej2=h2.sum() / tot, samples=int(samples))
    row["h2_3_sim"] = distances(h3, h_sim)[1]
    row["h2_2_sim"] = distances(h2, h_sim)[1] if h2.sum() else np.nan
    row["h2_null"] = distances(h_a, h_sim)[1]
    # expected plug-in bias for two histograms of sizes m1, m2 over K cells: (K - 1)/8 (1/m1 + 1/m2)
    k = toy.m ** toy.n - 1
    row["bias_null"] = k / 8.0 * (2.0 / samples)
    row["bias3"] = k / 8.0 * (1.0 / max(h3.sum(), 1) + 1.0 / samples)
    row["bias2"] = k / 8.0 * (1.0 / max(h2.sum(), 1) + 1.0 / samples)
    return row
