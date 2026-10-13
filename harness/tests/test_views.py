"""Controls for the scheme-view interface (PLAN validation items 1 and 2, first version)."""
import numpy as np

from harness.mldsa import dsa
from harness.mldsa.params import ALL
from harness.schemes.base import PlainMLDSAView, YLeakView, recover_s1_from_y_leak


def _attempts(p, seed, n_sigs):
    _, sk, sec = dsa.keygen_internal(bytes([seed]) * 32, p)
    out = []
    for i in range(n_sigs):
        out += dsa.sign(sk, bytes([i]), p, rnd=bytes([seed, i]) + bytes(30), record=True)[1]
    return sec, out


def test_positive_control_y_leak_recovers_s1():
    p = ALL["ML-DSA-44"]
    sec, att = _attempts(p, 3, 3)
    obs = YLeakView().observe_all(att)
    assert obs and all(o.accepted for o in obs)
    got = next(r for r in map(recover_s1_from_y_leak, obs) if r is not None)
    assert (got == sec["s1"]).all()


def test_negative_control_plain_view_hides_nonce_and_rejections():
    p = ALL["ML-DSA-65"]
    _, att = _attempts(p, 5, 4)
    assert any(a.failed for a in att)            # the run did contain rejections
    obs = PlainMLDSAView().observe_all(att)
    assert len(obs) == sum(1 for a in att if not a.failed)
    for o in obs:
        assert set(o.fields) == {"c_tilde", "c", "z", "h"}   # no y, no w1, no r0
    try:
        recover_s1_from_y_leak(obs[0])
        raise AssertionError("leak estimator ran without y")
    except KeyError:
        pass


# ---- Stage B gate: TALUS and Mithril through the same interface, estimators unchanged ----
import pytest

from harness.estimators import edge
from harness.mldsa.ntt import intt, ntt
from harness.mldsa.params import Q
from harness.mldsa.ringn import get_ring
from harness.mldsa.rounding import mod_pm
from harness.mldsa.sampling import sample_challenges
from harness.schemes.mldsa_controls import Signer
from harness.schemes.views import (MithrilAttempt, MithrilView, PublicKey, TalusBCCView,
                                   observations_to_cb, raw_attempts)


@pytest.fixture(scope="module")
def talus_run():
    p = ALL["ML-DSA-44"]
    s = Signer(p, bytes(32))
    att = raw_attempts(s, np.random.default_rng(1), 6000)
    out = {}
    for t_public in (False, True):
        pk = PublicKey.from_signer(s, t_public=t_public)
        obs = TalusBCCView(pk).observe_all(att)
        out[t_public] = observations_to_cb(obs, pk)
    return p, s, out


def test_talus_bcc_view_gives_bounded_channel_on_real_attempts(talus_run):
    p, s, out = talus_run
    bound = p.gamma2 - p.beta
    for t_public, x in ((False, s.target(0, positive=True)), (True, s.sec["s2"][0])):
        c, b = out[t_public]
        assert 0.15 < len(c) / 6000 < 0.4                    # BCC x z-norm acceptance
        e = b + np.rint(get_ring(256).mul(c, x))
        assert np.abs(e).max() < bound                       # b = -c x + LowBits(w), |LowBits(w)| < gamma2 - beta
        assert np.abs(e).max() > 0.95 * bound
        assert edge.is_feasible(c, b, x.astype(float), bound)
        assert not edge.is_feasible(c, b, x.astype(float) + 1.0, bound)


def test_talus_bcc_view_feeds_edge_estimator_unchanged(talus_run):
    """Full recovery at n = 256 needs about 2^18 signatures (RUNBOOK); here we only check that the
    unchanged estimator runs on view output and returns a point consistent with the channel bound."""
    p, s, out = talus_run
    c, b = out[True]
    x, t, info = edge.chebyshev_cutting_plane(c, b, p.eta + 1, np.random.default_rng(0))
    assert info["converged"] and info["max_residual"] <= p.gamma2 - p.beta
    assert t <= edge.max_abs_residual(c, b, s.sec["s2"][0].astype(float)) + 1e-6


def test_plain_view_gives_nothing_to_the_adapter():
    p = ALL["ML-DSA-44"]
    s = Signer(p, bytes(32))
    _, att = _attempts(p, 7, 2)
    obs = PlainMLDSAView().observe_all(att)
    assert obs
    with pytest.raises(KeyError):
        observations_to_cb(obs, PublicKey.from_signer(s))


def test_mithril_view_and_adapter_algebra():
    """Synthetic Mithril-shaped attempts (r1, r2 small stand-ins for the hyperball sample) check that
    the adapter gives b = -c (s2 - t0) - r2 exactly and that rejected attempts carry only w."""
    p = ALL["ML-DSA-44"]
    s = Signer(p, bytes(32))
    pk = PublicKey.from_signer(s)
    rng = np.random.default_rng(3)
    att, r2s = [], []
    for i in range(6):
        r1 = rng.integers(-1000, 1001, (p.l, 256))
        r2 = rng.integers(-1000, 1001, (p.k, 256))
        c = sample_challenges(rng, 1, p.tau)[0]
        z = r1 + mod_pm(intt(ntt(c)[None] * s.s1h % Q), Q)
        w = (pk.matvec(r1) + r2) % Q
        att.append(MithrilAttempt(c, z, w, "" if i % 2 == 0 else "hrej"))
        r2s.append(r2)
    obs = MithrilView().observe_all(att)
    assert len(obs) == 6 and sum(o.accepted for o in obs) == 3
    assert all(set(o.fields) == {"w"} for o in obs if not o.accepted)
    c, b = observations_to_cb(obs, pk)
    assert c.shape == (3, 256)
    x = s.target(0, positive=True)
    e = b + np.rint(get_ring(256).mul(c, x))
    assert np.array_equal(e, -np.stack([r2s[i][0] for i in (0, 2, 4)]))
