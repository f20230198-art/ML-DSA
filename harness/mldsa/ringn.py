"""Arithmetic in Z[X]/(X^n+1) for any power-of-two n (reduced rings for scaling ladders).

Same idea as ring.py (FFT product, no mod q) but with n as a parameter. Rows and
challenge samplers here are used by the edge-aware estimators.
"""
from functools import lru_cache

import numpy as np


class Ring:
    def __init__(self, n):
        self.n = n
        self._psi = np.exp(1j * np.pi * np.arange(n) / n)
        self._psi_inv = np.conj(self._psi)

    def mul(self, a, b):
        """FFT negacyclic product; (..., n) real arrays, broadcasting allowed."""
        fa = np.fft.fft(np.asarray(a, dtype=float) * self._psi, axis=-1)
        fb = np.fft.fft(np.asarray(b, dtype=float) * self._psi, axis=-1)
        return (np.fft.ifft(fa * fb, axis=-1) * self._psi_inv).real

    @staticmethod
    def adjoint(a):
        """a*(X) = a(X^-1); multiplying by it is the transpose of multiplying by a."""
        a = np.asarray(a)
        out = np.empty_like(a)
        out[..., 0] = a[..., 0]
        out[..., 1:] = -a[..., :0:-1]
        return out


@lru_cache(maxsize=None)
def get_ring(n):
    return Ring(n)


def sample_challenges_n(rng, count, n, tau, chunk=4096):
    """`count` sparse challenges in Z[X]/(X^n+1): exactly tau entries in {-1,+1}. int8 output."""
    out = np.zeros((count, n), dtype=np.int8)
    for start in range(0, count, chunk):
        m = min(chunk, count - start)
        pos = np.argpartition(rng.random((m, n)), tau - 1, axis=1)[:, :tau]
        signs = (rng.integers(0, 2, size=(m, tau)) * 2 - 1).astype(np.int8)
        block = np.zeros((m, n), dtype=np.int8)
        np.put_along_axis(block, pos, signs, axis=1)
        out[start:start + m] = block
    return out


def scaled_tau(n, tau_full, n_full=256):
    """Keep the challenge density tau/n of the full-size parameter set when n is reduced."""
    return max(1, int(round(tau_full * n / n_full)))


def constraint_rows(c, i, j):
    """Dense rows a with (c_i * x)_j = a . x, for index arrays i, j (negacyclic matrix rows).

    M[j, k] = c[(j - k) mod n] * (+1 if k <= j else -1).
    """
    n = c.shape[1]
    i = np.asarray(i)
    j = np.asarray(j)
    k = np.arange(n)
    idx = (j[:, None] - k[None, :]) % n
    sign = np.where(k[None, :] <= j[:, None], 1.0, -1.0)
    return c[i[:, None], idx].astype(float) * sign
