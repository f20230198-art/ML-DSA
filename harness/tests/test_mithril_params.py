"""Checks of the Mithril parameter accounting (harness/schemes/mithril_params.py)."""
import numpy as np

from harness.mldsa.params import ALL
from harness.schemes import mithril_params as mp


def test_footnote_13_sigma():
    # Sec. 3.4 footnote: B = 1.3 ||s|| ||c|| is about 13 standard deviations above the typical norm.
    p, (nu, table) = ALL["ML-DSA-44"], mp.TABLES["ML-DSA-44"]
    norms = mp.sample_norms(p, nu, 2, 2, 300, np.random.default_rng(1))
    z = (mp.bound_B(p, nu, 2, 2) - norms.mean()) / norms.std()
    assert 9 < z < 18


def test_implied_B_round_trip():
    p, (nu, table) = ALL["ML-DSA-65"], mp.TABLES["ML-DSA-65"]
    r, rp, K = table[(3, 4)]
    b = mp.implied_B(p, K, r, rp, log2_target=50)
    lq, _, _ = mp.log2_qs(p, nu, 3, 4, r, rp, K, b)
    assert abs(lq - 50) < 1e-3


def test_more_slack_more_queries():
    p, (nu, table) = ALL["ML-DSA-44"], mp.TABLES["ML-DSA-44"]
    r, rp, K = table[(2, 2)]
    small = mp.log2_qs(p, nu, 2, 2, r, rp, K, 300.0)[0]
    large = mp.log2_qs(p, nu, 2, 2, r, rp, K, 400.0)[0]
    assert small > large


def test_eps_of_norm_matches_log2_qs():
    # At a fixed norm B, 1 / (K eps(B)) must equal the Thm. 3.2 value from log2_qs.
    p, (nu, table) = ALL["ML-DSA-44"], mp.TABLES["ML-DSA-44"]
    r, rp, K = table[(2, 3)]
    b = 450.0
    lq = mp.log2_qs(p, nu, 2, 3, r, rp, K, b)[0]
    import math
    assert abs(-math.log2(K * mp.eps_of_norm(p, r, rp, b)) - lq) < 1e-9


def test_typical_between_worst_and_mean():
    # Averaging eps over a spread of norms gives fewer queries than at the mean, more than at mean + 5 sd.
    import math
    p, (nu, table) = ALL["ML-DSA-44"], mp.TABLES["ML-DSA-44"]
    r, rp, K = table[(2, 2)]
    typ = mp.log2_qs_typical(p, K, r, rp, 298.0, 7.0)
    at_mean = -math.log2(K * mp.eps_of_norm(p, r, rp, 298.0))
    at_5sd = -math.log2(K * mp.eps_of_norm(p, r, rp, 333.0))
    assert at_5sd < typ < at_mean


def test_lemma25_bound_is_not_an_upper_bound_at_mithril_dims():
    # The bound as stated (exponent dim-1) is below the exact value at the dimensions Mithril uses,
    # so it cannot be an upper bound; it is fine at small dimensions.
    for dim, phi in ((2048, 7), (2816, 8), (3840, 9)):
        assert mp.lemma25_bound_log2(dim, phi) < mp.exact_I_log2(dim, phi) - 15
    assert mp.lemma25_bound_log2(64, 7) > mp.exact_I_log2(64, 7)
