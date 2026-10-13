"""Tests for the integer finishing step harness/estimators/ilp.py (small sizes, seconds)."""
import numpy as np

from harness.estimators import edge, ilp
from harness.mldsa.params import ML_DSA_44
from harness.schemes.talus_bcc import make_channel, make_transcript, sample_target


def _setup(n, N, seed):
    ch = make_channel(ML_DSA_44, n, "bcc", "s2")
    rng = np.random.default_rng(seed)
    s = sample_target(rng, ch)
    c, b = make_transcript(rng, ch, s, N)
    return ch, s, c, b


def test_noiseless_perturbed_start_recovers_secret():
    n, eta = 16, 2
    rng = np.random.default_rng(1)
    s = rng.integers(-eta, eta + 1, n)
    from harness.mldsa.ringn import get_ring, sample_challenges_n
    c = sample_challenges_n(rng, 40, n, 2)
    b = -np.rint(get_ring(n).mul(c, s))
    x = s + rng.uniform(-0.9, 0.9, n)          # rounding alone would often be wrong
    z, info = ilp.finish(c, b, x, eta, bound=0, window=1.0)
    assert (z == s).all() and info["t"] <= 1e-6


def test_result_is_feasible_and_in_range():
    ch, s, c, b = _setup(8, 20_000, 2)
    x, _, _ = edge.chebyshev_cutting_plane(c, b, ch.target_max + 1, np.random.default_rng(0))
    z, info = ilp.finish(c, b, x, ch.target_max, ch.bound)
    assert np.abs(z).max() <= ch.target_max
    if info["status"] in ("optimal", "fixed") and info["free"]:
        assert info["t"] <= ch.bound + 1e-6


def test_true_secret_feasible_so_finish_never_infeasible_when_window_covers_it():
    ch, s, c, b = _setup(8, 5_000, 4)
    x = s + 0.4                                  # true secret is inside the window
    z, info = ilp.finish(c, b, x, ch.target_max, ch.bound, window=1.0)
    assert info["status"] != "infeasible"
    assert info["t"] <= ch.bound + 1e-6


def test_candidate_box_clips_to_range():
    lo, hi = ilp.candidate_box(np.array([2.7, -0.2, 9.0]), 2, 1.0)
    assert list(lo) == [2, -1, 2] and list(hi) == [2, 0, 2]
