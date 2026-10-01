"""Samplers for synthetic keys and challenges (uniform stand-ins, not SHAKE-based)."""
import numpy as np

from .params import N, Params


def sample_challenges(rng, count, tau):
    """`count` sparse challenges: exactly tau coefficients in {-1,+1}, rest 0."""
    c = np.zeros((count, N), dtype=np.int64)
    pos = np.argsort(rng.random((count, N)), axis=1)[:, :tau]
    signs = rng.integers(0, 2, size=(count, tau)) * 2 - 1
    np.put_along_axis(c, pos, signs, axis=1)
    return c


def sample_secret(rng, eta, shape=(N,)):
    """Coefficients uniform in [-eta, eta] (ML-DSA secret distribution)."""
    return rng.integers(-eta, eta + 1, size=shape, dtype=np.int64)
