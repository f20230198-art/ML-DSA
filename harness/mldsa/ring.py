"""Arithmetic in Z[X]/(X^256+1) for small-coefficient leakage experiments.

Products here are over the integers (no mod q), which is what ILWE-style
estimators see. `negacyclic_mul_exact` is the slow reference; the FFT version
is used in bulk and is accurate for the magnitudes used here.
"""
import numpy as np

from .params import N

_PSI = np.exp(1j * np.pi * np.arange(N) / N)
_PSI_INV = np.conj(_PSI)


def negacyclic_mul_exact(a, b):
    a = np.asarray(a, dtype=np.int64)
    b = np.asarray(b, dtype=np.int64)
    out = np.zeros(N, dtype=np.int64)
    for i in range(N):
        if a[i] == 0:
            continue
        rolled = np.roll(b, i)
        rolled[:i] *= -1
        out += a[i] * rolled
    return out


def negacyclic_mul(a, b):
    """FFT product; a, b are (..., N) real arrays, broadcasting allowed."""
    fa = np.fft.fft(np.asarray(a) * _PSI, axis=-1)
    fb = np.fft.fft(np.asarray(b) * _PSI, axis=-1)
    return (np.fft.ifft(fa * fb, axis=-1) * _PSI_INV).real


def adjoint(a):
    """Ring adjoint a*(X) = a(X^-1); multiplying by it is the transpose of mult-by-a."""
    a = np.asarray(a)
    out = np.empty_like(a)
    out[..., 0] = a[..., 0]
    out[..., 1:] = -a[..., :0:-1]
    return out
