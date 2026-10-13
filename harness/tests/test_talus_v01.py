"""TALUS v0.1 (arXiv 2603.22109v2) transcripts: validity, released fields, Niot's attacks 1 and 2."""
import numpy as np

from harness.estimators.ilwe import least_squares
from harness.mldsa import dsa
from harness.mldsa.ntt import intt, ntt
from harness.mldsa.params import ALL, Q
from harness.mldsa.rounding import mod_pm
from harness.schemes.talus_v01 import (TalusV01, TalusV01MPCView, TalusV01SigView, attack1_keygen,
                                       attack1_nonce, s2_channel)


def _signer(name="ML-DSA-44", seed=1):
    return TalusV01(ALL[name], bytes([seed]) * 32, n_signers=3, seed=seed)


def _sigs(t, n):
    out = []
    for i in range(n):
        sig, att = t.sign(i.to_bytes(4, "little"))
        assert sig is not None
        out.append((i, sig, att))
    return out


def test_signatures_verify_with_unmodified_mldsa_verifier():
    for name in ("ML-DSA-44", "ML-DSA-65"):
        t = _signer(name, 2)
        for i, sig, att in _sigs(t, 3):
            assert dsa.verify(t.pk, i.to_bytes(4, "little"), sig, t.p)
            assert all(a.failed in ("bcc", "z_norm", "hint_weight") for a in att[:-1])


def test_view_fields_and_bcc_failures_hidden():
    t = _signer()
    att = [a for _, _, at in _sigs(t, 4) for a in at]
    assert any(a.failed == "bcc" for a in att)
    obs = TalusV01SigView().observe_all(att)
    assert len(obs) == 4
    assert all(set(o.fields) == {"c_tilde", "c", "z", "h", "w1"} for o in obs)


def test_s2_channel_algebra_exact_on_real_transcripts():
    t = _signer()
    p = t.p
    sp = mod_pm(t.sec["s2"] - t.sec["t0"], Q)
    for _, _, att in _sigs(t, 5):
        a = att[-1]
        o = TalusV01SigView().observe(a)
        b = s2_channel(p, t.a_hat, t.sec["t1"], o)
        cs = mod_pm(intt((ntt(o.fields["c"])[None, :] * ntt(sp)) % Q), Q)
        assert (b + cs == a.r0_w).all()                       # b = r0 - c (s2 - t0)
        assert np.abs(a.r0_w).max() < p.gamma2 - p.beta       # BCC noise bound


def test_niot_attack1_keygen_commitments_give_s1():
    t = _signer(seed=4)
    got = attack1_keygen(t.a_hat, t.keygen_broadcast(), t.ids)
    assert got is not None and (got == t.sec["s1"]).all()


def test_niot_attack1_one_mpc_signature_gives_s1():
    t = _signer(seed=5)
    _, _, att = _sigs(t, 1)[0]
    o = TalusV01MPCView().observe(att[-1])
    got = attack1_nonce(t.a_hat, o)
    assert got is not None and (got == t.sec["s1"]).all()


def test_niot_attack2_least_squares_error_shrinks():
    t = _signer(seed=6)
    obs = TalusV01SigView().observe_all([a for _, _, at in _sigs(t, 300) for a in at])
    c = np.stack([o.fields["c"] for o in obs]).astype(float)
    b = np.stack([s2_channel(t.p, t.a_hat, t.sec["t1"], o)[0] for o in obs]).astype(float)
    target = mod_pm(t.sec["s2"][0] - t.sec["t0"][0], Q)
    err = np.sqrt(np.mean((least_squares(c, b) - target) ** 2))
    sigma_e = (t.p.gamma2 - t.p.beta) / np.sqrt(3)
    theory = sigma_e / np.sqrt(len(obs) * t.p.tau)
    assert err < 2 * theory and err < np.std(target)   # estimator beats the prior spread
