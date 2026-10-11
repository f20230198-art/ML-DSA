import numpy as np

from harness.mldsa.params import ALL
from harness.mldsa.ring import negacyclic_mul
from harness.schemes.mldsa_controls import Signer


def _noise(signer, r0_check):
    c, b, ok, r0 = signer.attempts(np.random.default_rng(5), 256, r0_check)
    x = signer.target(0, positive=not r0_check)
    e = b[:, 0] + np.rint(negacyclic_mul(c, x)).astype(np.int64)
    return e, ok, r0


def test_negative_control_channel_is_t0_plus_r0():
    p = ALL["ML-DSA-44"]
    s = Signer(p, bytes(32))
    e, ok, r0 = _noise(s, True)
    assert ok.any()
    assert np.array_equal(e[ok], r0[ok, 0])
    assert np.abs(e[ok]).max() < p.gamma2 - p.beta


def test_positive_control_channel_is_lowbits_w():
    p = ALL["ML-DSA-44"]
    s = Signer(p, bytes(32))
    e, ok, _ = _noise(s, False)
    assert ok.any()
    assert np.abs(e[ok]).max() <= p.gamma2
