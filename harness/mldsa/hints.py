"""Hint functions of FIPS 204 (Algorithms 39 and 40), vectorised."""
import numpy as np

from .params import Q
from .rounding import decompose, high_bits


def make_hint(z, r, gamma2):
    """1 where adding z to r changes the high bits."""
    return (high_bits(r, gamma2) != high_bits((np.asarray(r) + np.asarray(z)) % Q, gamma2)).astype(np.int64)


def use_hint(h, r, gamma2):
    m = (Q - 1) // (2 * gamma2)
    r1, r0 = decompose(r, gamma2)
    h = np.asarray(h)
    up = (r1 + 1) % m
    down = (r1 - 1) % m
    return np.where(h == 1, np.where(r0 > 0, up, down), r1)
