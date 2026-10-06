"""Tests for the NTT, SHAKE samplers, hints and the full ML-DSA (Stage A, gate A).

The cross-check against dilithium-py (an independent pure-Python FIPS 204 implementation, pip
package `dilithium-py`) is skipped if that package is not installed. Its own conformance to the
official NIST vectors is taken from its documentation, not re-verified here.
"""
import os

import numpy as np
import pytest

from harness.mldsa import dsa, ring
from harness.mldsa.hints import make_hint, use_hint
from harness.mldsa.ntt import intt, ntt, poly_mul
from harness.mldsa.params import ALL, Q
from harness.mldsa.rounding import high_bits

PARAMS = list(ALL.values())


def test_ntt_roundtrip_and_product():
    rng = np.random.default_rng(0)
    a = rng.integers(0, Q, size=(3, 256))
    assert (intt(ntt(a)) == a).all()
    x = rng.integers(-6, 7, 256)
    y = rng.integers(-6, 7, 256)
    assert (poly_mul(x, y) == ring.negacyclic_mul_exact(x, y) % Q).all()


def test_hints_recover_high_bits():
    rng = np.random.default_rng(1)
    for p in PARAMS:
        r = rng.integers(0, Q, 4096)
        z = rng.integers(-p.gamma2 // 2, p.gamma2 // 2, 4096)
        h = make_hint(z, r, p.gamma2)
        assert (use_hint(h, r, p.gamma2) == high_bits((r + z) % Q, p.gamma2)).all()


@pytest.mark.parametrize("p", PARAMS, ids=lambda p: p.name)
def test_sign_verify_roundtrip(p):
    pk, sk, _ = dsa.keygen_internal(bytes(range(32)), p)
    msg = b"hello threshold world"
    sig, att = dsa.sign(sk, msg, p, record=True)
    assert dsa.verify(pk, msg, sig, p)
    assert not dsa.verify(pk, msg + b"!", sig, p)
    bad = bytearray(sig)
    bad[0] ^= 1
    assert not dsa.verify(pk, msg, bytes(bad), p)
    assert att[-1].failed == "" and all(a.failed for a in att[:-1])


def test_attempt_records_are_consistent():
    p = ALL["ML-DSA-65"]
    _, sk, sec = dsa.keygen_internal(b"\x07" * 32, p)
    allowed = {"z_norm", "r0_norm", "ct0_norm", "hint_weight", ""}
    seen = set()
    for i in range(6):
        _, att = dsa.sign(sk, bytes([i]), p, rnd=bytes([i]) * 32, record=True)
        for a in att:
            assert a.failed in allowed
            seen.add(a.failed)
    assert "" in seen


def test_z_equals_y_plus_cs1_over_integers_when_accepted():
    p = ALL["ML-DSA-44"]
    _, sk, sec = dsa.keygen_internal(b"\x09" * 32, p)
    _, att = dsa.sign(sk, b"m", p, record=True)
    a = att[-1]
    cs1 = np.stack([ring.negacyclic_mul_exact(a.c, sec["s1"][j]) for j in range(p.l)])
    assert (a.z == a.y + cs1).all()


@pytest.mark.parametrize("p", PARAMS, ids=lambda p: p.name)
def test_matches_independent_implementation(p):
    dp = pytest.importorskip("dilithium_py.ml_dsa")
    ora = {"ML-DSA-44": dp.ML_DSA_44, "ML-DSA-65": dp.ML_DSA_65, "ML-DSA-87": dp.ML_DSA_87}[p.name]
    for i in range(3):
        xi = os.urandom(32)
        pk, sk, _ = dsa.keygen_internal(xi, p)
        pk_o, sk_o = ora._keygen_internal(xi)
        assert pk == pk_o and sk == sk_o
        msg, rnd = os.urandom(33), os.urandom(32)
        sig, _ = dsa.sign_internal(sk, bytes([0, 0]) + msg, rnd, p)
        assert sig == ora._sign_internal(sk_o, bytes([0, 0]) + msg, rnd)
        assert ora.verify(pk, msg, sig)
