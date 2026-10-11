"""Checks of the Mithril a posteriori sharing hint accounting (harness/schemes/mithril_hint.py)."""
import math

from harness.mldsa.params import ALL
from harness.schemes import mithril_hint as mh


def test_baseline_beta_matches_dilithium_round3():
    # Dilithium round-3 spec primal block sizes: 423, 623, 862 (we get +-1).
    for name, ref in (("ML-DSA-44", 423), ("ML-DSA-65", 623), ("ML-DSA-87", 862)):
        p = ALL[name]
        sd = math.sqrt(p.eta * (p.eta + 1) / 3)
        assert abs(mh.primal_usvp_beta(p.l * 256, p.k * 256, sd, sd) - ref) <= 2


def test_hint_reduces_entropy_and_more_shares_leak_more():
    h0, h2, _ = mh.posterior_stats(2, math.sqrt(2), 2)
    _, h20, _ = mh.posterior_stats(2, math.sqrt(2), 20)
    assert abs(h0 - math.log2(5)) < 1e-12
    assert h20 < h2 < h0


def test_wide_shares_leak_almost_nothing():
    h0, hc, _ = mh.posterior_stats(2, 30.0, 3)
    assert h0 - hc < 0.01


def test_same_entropy_sigma_round_trip():
    h = mh.entropy(mh.dgauss(0.9)[1])
    assert abs(mh.sigma_same_entropy(h) - 0.9) < 1e-6
