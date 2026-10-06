"""NTT over Z_q[X]/(X^256+1) (FIPS 204 Algorithms 41 and 42), vectorised over leading axes.

Arrays are int64 with last axis 256. Products stay below 2^47, so int64 never overflows.
"""
import numpy as np

from .params import N, Q

ROOT = 1753  # primitive 512th root of unity mod q
N_INV = pow(N, -1, Q)  # 8347681


def _brv8(m):
    return int(format(m, "08b")[::-1], 2)


ZETAS = np.array([pow(ROOT, _brv8(m), Q) for m in range(N)], dtype=np.int64)


def ntt(w):
    a = np.array(w, dtype=np.int64) % Q
    shape = a.shape
    m = 0
    length = N // 2
    while length >= 1:
        blocks = N // (2 * length)
        v = a.reshape(shape[:-1] + (blocks, 2, length))
        z = ZETAS[m + 1:m + 1 + blocks].reshape((blocks, 1))
        t = (z * v[..., 1, :]) % Q
        lo = v[..., 0, :].copy()
        v[..., 1, :] = (lo - t) % Q
        v[..., 0, :] = (lo + t) % Q
        m += blocks
        length //= 2
    return a.reshape(shape)


def intt(w):
    a = np.array(w, dtype=np.int64) % Q
    shape = a.shape
    m = N
    length = 1
    while length < N:
        blocks = N // (2 * length)
        v = a.reshape(shape[:-1] + (blocks, 2, length))
        z = (-ZETAS[m - blocks:m][::-1]).reshape((blocks, 1)) % Q
        lo = v[..., 0, :].copy()
        hi = v[..., 1, :].copy()
        v[..., 0, :] = (lo + hi) % Q
        v[..., 1, :] = (z * ((lo - hi) % Q)) % Q
        m -= blocks
        length *= 2
    return (a.reshape(shape) * N_INV) % Q


def poly_mul(a, b):
    """Product in Z_q[X]/(X^256+1) via the NTT."""
    return intt((ntt(a) * ntt(b)) % Q)
