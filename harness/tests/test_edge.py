"""Tests for the reduced-ring helpers, the TALUS bounded-noise channel and the edge estimators.

Small sizes only. Written before first execution; run with
  python -m pytest harness/tests/test_edge.py -q
"""
import numpy as np
import pytest

from harness.estimators import edge
from harness.mldsa.params import ML_DSA_44, ML_DSA_65
from harness.mldsa.ringn import Ring, constraint_rows, get_ring, sample_challenges_n, scaled_tau
from harness.schemes.talus_bcc import make_channel, make_transcript, sample_target


def exact_mul(a, b):
    n = len(a)
    out = np.zeros(n, dtype=np.int64)
    for i in range(n):
        for k in range(n):
            j = i + k
            out[j % n] += a[i] * b[k] * (-1 if j >= n else 1)
    return out


def test_ring_mul_matches_exact():
    rng = np.random.default_rng(0)
    for n in (8, 16, 64):
        a = rng.integers(-3, 4, n)
        b = rng.integers(-50, 51, n)
        assert (np.rint(get_ring(n).mul(a, b)).astype(np.int64) == exact_mul(a, b)).all()


def test_adjoint_is_transpose():
    rng = np.random.default_rng(1)
    n = 16
    a = rng.integers(-3, 4, n)
    x = rng.integers(-5, 6, n)
    y = rng.integers(-5, 6, n)
    ring = get_ring(n)
    lhs = ring.mul(a, x) @ y
    rhs = x @ ring.mul(Ring.adjoint(a), y)
    assert lhs == pytest.approx(rhs)


def test_challenge_weight_and_values():
    rng = np.random.default_rng(2)
    c = sample_challenges_n(rng, 500, 32, 5)
    assert c.dtype == np.int8
    assert ((c != 0).sum(axis=1) == 5).all()
    assert set(np.unique(c)) <= {-1, 0, 1}


def test_scaled_tau_keeps_density():
    assert scaled_tau(256, 39) == 39
    assert scaled_tau(32, 39) == 5
    assert scaled_tau(8, 39) >= 1


def test_constraint_rows_match_ring_product():
    rng = np.random.default_rng(3)
    n = 16
    c = sample_challenges_n(rng, 10, n, 4)
    x = rng.integers(-5, 6, n)
    prod = np.rint(get_ring(n).mul(c, x))
    i = rng.integers(0, 10, 40)
    j = rng.integers(0, n, 40)
    rows = constraint_rows(c, i, j)
    assert np.allclose(rows @ x, prod[i, j])


def test_channel_noise_range_and_models():
    bcc = make_channel(ML_DSA_44, 16, "bcc")
    plain = make_channel(ML_DSA_44, 16, "plain")
    assert bcc.bound == ML_DSA_44.gamma2 - ML_DSA_44.beta
    assert plain.bound == ML_DSA_44.gamma2
    assert make_channel(ML_DSA_65, 16, "bcc", "s2-t0").target_max == (1 << 12) + ML_DSA_65.eta
    with pytest.raises(ValueError):
        make_channel(ML_DSA_44, 16, "nope")


def test_transcript_noise_stays_inside_bound():
    rng = np.random.default_rng(4)
    ch = make_channel(ML_DSA_44, 16)
    s = sample_target(rng, ch)
    c, b = make_transcript(rng, ch, s, 300)
    r = b.astype(float) + get_ring(16).mul(c, s)  # = e
    assert np.abs(r).max() <= ch.bound
    assert np.abs(r).max() > 0.9 * ch.bound  # edges are actually reached


def test_true_secret_is_feasible_soundness():
    rng = np.random.default_rng(5)
    ch = make_channel(ML_DSA_44, 16)
    s = sample_target(rng, ch)
    c, b = make_transcript(rng, ch, s, 200)
    assert edge.is_feasible(c, b, s.astype(float), ch.bound)
    assert not edge.is_feasible(c, b, s.astype(float) + 5000.0, ch.bound)


def test_noiseless_recovery_exact_both_solvers():
    rng = np.random.default_rng(6)
    n = 8
    s = rng.integers(-2, 3, n)
    c = sample_challenges_n(rng, 60, n, 2)
    b = (-np.rint(get_ring(n).mul(c, s))).astype(np.float32)
    A = edge.negacyclic_rows(c.astype(np.int64))
    x_lp, t = edge.chebyshev(A, b.astype(float).ravel())
    assert t == pytest.approx(0.0, abs=1e-6)
    assert np.allclose(x_lp, s, atol=1e-6)
    x_cp, _, info = edge.chebyshev_cutting_plane(c, b, box=3, rng=rng)
    assert info["converged"]
    assert np.allclose(x_cp, s, atol=1e-5)


def test_cutting_plane_matches_full_lp_objective():
    rng = np.random.default_rng(7)
    ch = make_channel(ML_DSA_44, 8)
    s = sample_target(rng, ch)
    c, b = make_transcript(rng, ch, s, 400)
    A = edge.negacyclic_rows(c.astype(np.int64))
    _, t_lp = edge.chebyshev(A, b.astype(float).ravel())
    # huge box: the full LP above is unboxed, so the optima only agree if the box is inactive
    x_cp, t_cp, info = edge.chebyshev_cutting_plane(c, b, 10**6, rng)
    assert info["converged"]
    assert t_cp == pytest.approx(t_lp, rel=1e-6, abs=1e-3)
    assert edge.max_abs_residual(c, b, x_cp) == pytest.approx(t_lp, rel=1e-6, abs=1e-3)


def test_chebyshev_optimum_never_exceeds_noise_bound():
    # the true secret is feasible, so the minimal sup residual is at most the noise bound
    rng = np.random.default_rng(8)
    ch = make_channel(ML_DSA_44, 8)
    s = sample_target(rng, ch)
    c, b = make_transcript(rng, ch, s, 300)
    _, t, _ = edge.chebyshev_cutting_plane(c, b, ch.target_max + 1, rng)
    assert t <= ch.bound + 1e-6


def test_edge_beats_least_squares_on_uniform_noise():
    rng = np.random.default_rng(9)
    ch = make_channel(ML_DSA_44, 8)
    s = sample_target(rng, ch)
    c, b = make_transcript(rng, ch, s, 6000)
    x_cp, _, _ = edge.chebyshev_cutting_plane(c, b, ch.target_max + 1, rng)
    x_ls = edge.least_squares_cg(c, b)
    assert np.abs(x_cp - s).max() < 0.2 * np.abs(x_ls - s).max()


def test_least_squares_fft_matches_cg():
    rng = np.random.default_rng(11)
    ch = make_channel(ML_DSA_44, 16, "bcc", "s2")
    s = sample_target(rng, ch)
    c, b = make_transcript(rng, ch, s, 3000)
    assert np.allclose(edge.least_squares_fft(c, b), edge.least_squares_cg(c, b, iters=60), atol=1e-6)


def test_gpu_matches_cpu():
    import pytest
    edge_gpu = pytest.importorskip("harness.estimators.edge_gpu")
    if not edge_gpu.available():
        pytest.skip("no CUDA device")
    rng = np.random.default_rng(12)
    ch = make_channel(ML_DSA_44, 16, "bcc", "s2")
    s = sample_target(rng, ch)
    c, b = make_transcript(rng, ch, s, 4000)
    obs = edge_gpu.GpuObs(c, b)
    assert np.allclose(obs.least_squares(), edge.least_squares_fft(c, b), atol=1e-8)
    x1, t1, _ = edge.chebyshev_cutting_plane(c, b, ch.target_max + 1, np.random.default_rng(3))
    x2, t2, _ = edge_gpu.chebyshev_cutting_plane_gpu(c, b, ch.target_max + 1, np.random.default_rng(3), obs=obs)
    assert abs(t1 - t2) < 1e-6 and np.allclose(x1, x2, atol=1e-5)
