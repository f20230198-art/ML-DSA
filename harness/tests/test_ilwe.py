import numpy as np
import pytest

from harness.estimators.ilwe import least_squares, matched_filter
from harness.mldsa.params import ALL, ML_DSA_44
from harness.mldsa.sampling import sample_secret
from harness.schemes.ilwe_transcript import make_transcript


@pytest.mark.parametrize("p,expected", [("ML-DSA-44", 3.1e8), ("ML-DSA-65", 1.9e9), ("ML-DSA-87", 1.5e9)])
def test_dossier_sample_formula_matches_table(p, expected):
    """Dossier: N >~ 4*gamma2^2/(3*tau); Niot's table 3.1e8 / 1.9e9 / 1.5e9."""
    q = ALL[p]
    n = 4 * q.gamma2 ** 2 / (3 * q.tau)
    assert n == pytest.approx(expected, rel=0.05)


def test_noise_is_roughly_uniform_with_variance_gamma2_sq_over_3():
    rng = np.random.default_rng(2)
    s = sample_secret(rng, ML_DSA_44.eta)
    c, b = make_transcript(rng, ML_DSA_44, np.zeros(256, dtype=np.int64), 400)
    var = b.var()
    assert var == pytest.approx(ML_DSA_44.gamma2 ** 2 / 3, rel=0.02)


def test_least_squares_error_matches_theory():
    """Per-coefficient error std should be ~ gamma2 / sqrt(3 * tau * N)."""
    rng = np.random.default_rng(3)
    p = ML_DSA_44
    s = sample_secret(rng, p.eta)
    n = 20000
    c, b = make_transcript(rng, p, s, n)
    err = least_squares(c, b) - s
    theory = p.gamma2 / np.sqrt(3 * p.tau * n)
    assert err.std() == pytest.approx(theory, rel=0.12)
    mf_err = matched_filter(c, b) - s
    assert err.std() <= mf_err.std() * 1.05


def test_recovery_improves_with_samples():
    rng = np.random.default_rng(4)
    p = ML_DSA_44
    s = sample_secret(rng, p.eta)
    c, b = make_transcript(rng, p, s, 60000)
    e_small = np.abs(least_squares(c[:2000], b[:2000]) - s).mean()
    e_big = np.abs(least_squares(c, b) - s).mean()
    assert e_big < e_small / 3
