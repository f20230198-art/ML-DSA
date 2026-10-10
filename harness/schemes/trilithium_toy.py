"""Trilithium (Dufka et al., ePrint 2025/675) rejected-attempt test at toy size, Stage F, hypothesis H-F2.

Every Trilithium attempt declassifies w_H = HighBits(A y), also when the attempt is rejected. Sec. 3
(Alg. 4) argues that rejected w_H can be simulated as HighBits(A y') with y' uniform on the whole box,
via an MLWR-type assumption. Rejection biases y in a way that depends on c s1 (branch 3: z = y + c s1
leaves the box) or on c s2 (branch 2: r0 check fails), so the question is how far the real rejected
w_H distribution is from the simulated one.

At real size this cannot be computed. Here the ring is Z_q[X]/(X^n + 1) with tiny n, k = l = 1, and
every y in the box [-gamma1 + 1, gamma1]^n is enumerated, so all distributions are exact (no sampling
noise). We report statistical distance and squared Hellinger distance; about 1 / H^2 samples are
needed to tell two distributions apart with constant advantage.
"""
import math

import numpy as np


def negacyclic_matrix(a, q=None):
    """Matrix M with M @ y = a * y in Z_q[X]/(X^n + 1); over the integers if q is None."""
    n = len(a)
    m = np.zeros((n, n), dtype=np.int64)
    for j in range(n):
        for i in range(n):
            k = i + j
            m[k % n, j] += a[i] if k < n else -a[i]
    return m if q is None else m % q


def decompose(r, q, gamma2):
    """FIPS 204 Decompose, vectorised: returns (r1, r0) with r = r1 * 2 gamma2 + r0 mod q."""
    rp = np.mod(r, q)
    r0 = np.mod(rp, 2 * gamma2)
    r0 = np.where(r0 > gamma2, r0 - 2 * gamma2, r0)
    edge = (rp - r0) == q - 1
    r1 = np.where(edge, 0, (rp - r0) // (2 * gamma2))
    r0 = np.where(edge, r0 - 1, r0)
    return r1, r0


class Toy:
    def __init__(self, n=4, q=257, gamma2=16, gamma1=16, tau=2, eta=1):
        assert (q - 1) % (2 * gamma2) == 0
        self.n, self.q, self.gamma2, self.gamma1, self.tau, self.eta = n, q, gamma2, gamma1, tau, eta
        self.beta = tau * eta
        self.m = (q - 1) // (2 * gamma2)          # number of HighBits values per coefficient

    def sample(self, rng):
        n, q = self.n, self.q
        a = rng.integers(0, q, n)
        s1 = rng.integers(-self.eta, self.eta + 1, n)
        s2 = rng.integers(-self.eta, self.eta + 1, n)
        c = np.zeros(n, dtype=np.int64)
        pos = rng.choice(n, self.tau, replace=False)
        c[pos] = rng.choice([-1, 1], self.tau)
        return a, s1, s2, c

    def _mul(self, a, b):
        """Exact integer product in Z[X]/(X^n + 1) (no reduction mod q), for short a and b."""
        return negacyclic_matrix(np.asarray(a)) @ np.asarray(b)

    def _cell(self, r1):
        return (r1 * self.m ** np.arange(self.n)).sum(axis=1)

    def histograms(self, a, s1, s2, c, chunk=1 << 20):
        """Exact counts of w_H cells for: all y (simulator), branch 2 (z ok, r0 fails), branch 3 (z fails)."""
        n, q, g1 = self.n, self.q, self.gamma1
        amat = negacyclic_matrix(np.mod(a, q), q)
        cs1 = self._mul(c, s1)                      # integer, |.| <= beta
        cs2 = self._mul(c, s2)
        cells = self.m ** n
        h_all, h2, h3 = (np.zeros(cells, dtype=np.int64) for _ in range(3))
        side = 2 * g1
        total = side ** n
        for start in range(0, total, chunk):
            idx = np.arange(start, min(start + chunk, total))
            y = np.empty((len(idx), n), dtype=np.int64)
            rest = idx
            for j in range(n):
                y[:, j] = rest % side - g1 + 1
                rest = rest // side
            w = (y @ amat.T) % q
            r1, _ = decompose(w, q, self.gamma2)
            cell = self._cell(r1)
            h_all += np.bincount(cell, minlength=cells)
            z_fail = (np.abs(y + cs1) >= g1 - self.beta).any(axis=1)
            _, r0 = decompose(w - cs2, q, self.gamma2)
            r0_fail = (np.abs(r0) >= self.gamma2 - self.beta).any(axis=1)
            h3 += np.bincount(cell[z_fail], minlength=cells)
            h2 += np.bincount(cell[~z_fail & r0_fail], minlength=cells)
        return h_all, h2, h3

    def uniform_highbits(self):
        """Exact distribution of HighBits(u) for u uniform in Z_q^n."""
        r1, _ = decompose(np.arange(self.q), self.q, self.gamma2)
        one = np.bincount(r1, minlength=self.m) / self.q
        p = one
        for _ in range(self.n - 1):
            p = np.outer(one, p).ravel()           # cell index = sum r1_j m^j, coefficient 0 fastest
        return p


def distances(p, r):
    p = p / p.sum()
    r = r / r.sum()
    sd = 0.5 * np.abs(p - r).sum()
    h2 = 1.0 - np.sqrt(p * r).sum()
    return float(sd), float(max(h2, 0.0))


def run(gamma1_list, n=4, q=257, gamma2=16, trials=5, seed=2026):
    rng = np.random.default_rng(seed)
    rows = []
    for g1 in gamma1_list:
        toy = Toy(n=n, q=q, gamma2=gamma2, gamma1=g1)
        pu = toy.uniform_highbits()
        for t in range(trials):
            a, s1, s2, c = toy.sample(rng)
            h_all, h2, h3 = toy.histograms(a, s1, s2, c)
            # a second secret with the same A and c: does the rejected w_H depend on the secret?
            s1b = rng.integers(-toy.eta, toy.eta + 1, n)
            _, _, h3b = toy.histograms(a, s1b, s2, c)
            tot = h_all.sum()
            row = dict(gamma1=g1, trial=t, p_rej3=h3.sum() / tot, p_rej2=h2.sum() / tot)
            row["sd3_sim"], row["h2_3_sim"] = distances(h3, h_all)
            row["sd3_unif"], row["h2_3_unif"] = distances(h3, pu)
            row["sd_sim_unif"], row["h2_sim_unif"] = distances(h_all, pu)
            row["sd3_key"], row["h2_3_key"] = distances(h3, h3b) if h3b.sum() else (math.nan, math.nan)
            if h2.sum():
                row["sd2_sim"], row["h2_2_sim"] = distances(h2, h_all)
            else:
                row["sd2_sim"], row["h2_2_sim"] = math.nan, math.nan
            rows.append(row)
    return rows
