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
