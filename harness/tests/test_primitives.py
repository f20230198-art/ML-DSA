import numpy as np
import pytest

from harness.mldsa.params import ALL, D, Q
from harness.mldsa.ring import adjoint, negacyclic_mul, negacyclic_mul_exact
from harness.mldsa.rounding import decompose, power2round
from harness.mldsa.sampling import sample_challenges

rng = np.random.default_rng(1)


@pytest.mark.parametrize("p", ALL.values(), ids=lambda p: p.name)
def test_decompose_reconstructs_and_bounds(p):
    r = np.concatenate([rng.integers(0, Q, 200000), [0, 1, Q - 1, Q - 2, p.gamma2, 2 * p.gamma2]])
    r1, r0 = decompose(r, p.gamma2)
    assert np.all((r1 * 2 * p.gamma2 + r0 - r) % Q == 0)
    assert np.all(np.abs(r0) <= p.gamma2)
    assert r1.min() >= 0 and r1.max() <= (Q - 1) // (2 * p.gamma2) - 1


@pytest.mark.parametrize("p", ALL.values(), ids=lambda p: p.name)
def test_decompose_edge_case_q_minus_1(p):
    r1, r0 = decompose(np.array([Q - 1]), p.gamma2)
    assert r1[0] == 0 and r0[0] == -1


def test_power2round():
    r = rng.integers(0, Q, 100000)
    r1, r0 = power2round(r)
    assert np.all((r1 * (1 << D) + r0 - r) % Q == 0)
    assert np.all((r0 > -(1 << (D - 1))) & (r0 <= (1 << (D - 1))))


def test_gamma2_values():
    assert ALL["ML-DSA-44"].gamma2 == 95232
    assert ALL["ML-DSA-65"].gamma2 == 261888
    assert ALL["ML-DSA-87"].gamma2 == 261888


def test_fft_mul_matches_schoolbook():
    a = sample_challenges(rng, 1, 39)[0]
    b = rng.integers(-5, 6, 256)
    assert np.array_equal(np.rint(negacyclic_mul(a, b)).astype(int), negacyclic_mul_exact(a, b))


def test_negacyclic_wraps_with_sign():
    x = np.zeros(256, dtype=np.int64); x[255] = 1
    y = np.zeros(256, dtype=np.int64); y[1] = 1
    out = negacyclic_mul_exact(x, y)  # X^255 * X = X^256 = -1
    assert out[0] == -1 and np.count_nonzero(out) == 1


def test_adjoint_is_transpose():
    a = sample_challenges(rng, 1, 39)[0]
    x = rng.integers(-5, 6, 256); y = rng.integers(-5, 6, 256)
    lhs = np.dot(negacyclic_mul(a, x), y)
    rhs = np.dot(x, negacyclic_mul(adjoint(a), y))
    assert abs(lhs - rhs) < 1e-6


def test_challenge_weight():
    c = sample_challenges(rng, 500, 49)
    assert np.all(np.count_nonzero(c, axis=1) == 49)
    assert set(np.unique(c)) == {-1, 0, 1}
