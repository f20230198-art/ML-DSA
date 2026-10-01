"""Rounding functions of FIPS 204 (Algorithms 35-37), vectorised over numpy int64 arrays."""
import numpy as np

from .params import D, Q


def mod_pm(a, m):
    """Centered remainder in (-m/2, m/2], as in FIPS 204 'mod+-'."""
    a = np.asarray(a, dtype=np.int64)
    r = a % m
    return np.where(r > m // 2, r - m, r)


def power2round(r):
    r = np.asarray(r, dtype=np.int64) % Q
    r0 = mod_pm(r, 1 << D)
    r1 = (r - r0) >> D
    return r1, r0


def decompose(r, gamma2):
    r = np.asarray(r, dtype=np.int64) % Q
    r0 = mod_pm(r, 2 * gamma2)
    edge = (r - r0) == Q - 1
    r1 = np.where(edge, 0, (r - r0) // (2 * gamma2))
    r0 = np.where(edge, r0 - 1, r0)
    return r1, r0


def high_bits(r, gamma2):
    return decompose(r, gamma2)[0]


def low_bits(r, gamma2):
    return decompose(r, gamma2)[1]
