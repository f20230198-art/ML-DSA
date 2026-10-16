"""Scheme-specific views (PLAN stage B) and the adapter from Observations to estimator input.

`observations_to_cb` turns Observations into the (c, b) arrays that `harness.estimators.edge`,
`edge_gpu` and `ilwe` already take, so the estimators stay unchanged. For every accepted
observation it computes, from public data only,
    w' = A z - c * t_pub        (t_pub = t1 2^d, or the full t if the view says t is public)
and then
    b = w' - 2 gamma2 w1        if the view released high bits w1   (TALUS-style channel)
    b = w' - w                  if the view released the full commitment w  (Mithril-style)
centred mod q, for one ring element. In both cases b = -c x + e for a secret target x.

What is MODELLED rather than quoted from a spec is said in each class docstring.
"""
from dataclasses import dataclass

import numpy as np

from ..mldsa.dsa import Attempt
from ..mldsa.ntt import intt, ntt
from ..mldsa.params import D, N, Q, Params
from ..mldsa.rounding import decompose, mod_pm
from .base import Observation, SchemeView


@dataclass
class PublicKey:
    """What the adversary knows: parameters, A (NTT domain) and the public part of t."""
    p: Params
    a_hat: np.ndarray            # (k, l, N)
    t_pub: np.ndarray            # (k, N) coefficient domain: t1 2^d, or full t if modelled public

    @classmethod
    def from_signer(cls, signer, t_public=False):
        sec = signer.sec
        t = sec["t"] if t_public else (sec["t1"] << D)
        return cls(signer.p, signer.a_hat, np.asarray(t, dtype=np.int64) % Q)

    def matvec(self, v):
        """A v for v (l, N) in the coefficient domain -> (k, N) mod q."""
        vh = ntt(np.asarray(v, dtype=np.int64) % Q)
        out = np.zeros((self.p.k, N), dtype=np.int64)
        for j in range(self.p.l):
            out = (out + self.a_hat[:, j, :] * vh[j][None, :]) % Q
        return intt(out)


class TalusBCCView(SchemeView):
    """TALUS v0.22 with the Boundary Clearance Condition, as modelled in notes/schemes/talus.md.

    Quoted from the preview writeup: a nonce passes BCC iff every coefficient of r0 = LowBits(w),
    w = A y, satisfies |r0| < gamma2 - beta; then the LowBits check on w - c s2 passes for any c, s2.
    Real-signer part: y, c, z = y + c s1 and the z-norm check are genuine ML-DSA.

    MODELLED (not stated in the 9-page writeup):
      * per accepted attempt the adversary sees (c, z, w1 = HighBits(w)); w1 stands for the
        "revealed summed nonce" high part. No hint h is released or used.
      * rejected attempts (BCC or z-norm failure) release nothing.
      * whether t0 is public: by default only t1 is public, so the channel target is s2 - t0;
        with `t_public=True` (PublicKey.from_signer(..., t_public=True)) the target is s2.
    Under this model b = LowBits(w) - c (s2 - t0), noise uniform-ish in (-(gamma2-beta), gamma2-beta).
    """
    name = "talus-bcc"

    def __init__(self, pk: PublicKey, adversary="passive"):
        super().__init__(adversary)
        self.pk = pk

    def observe(self, a: Attempt):
        p = self.pk.p
        w = self.pk.matvec(a.y)
        w1, r0 = decompose(w, p.gamma2)
        if (np.abs(r0) >= p.gamma2 - p.beta).any():
            return None                                   # BCC rejects the nonce
        if (np.abs(a.z) >= p.gamma1 - p.beta).any():
            return None                                   # ordinary z-norm rejection
        return Observation(self.name, self.adversary, True, dict(c=a.c, z=a.z, w1=w1))


@dataclass
class MithrilAttempt:
    """One Mithril signing attempt in ML-DSA format (Celi et al., ePrint 2026/013).
    w is the aggregated commitment [A | I] r = A r1 + r2; z is the combined first part c s1 + r1."""
    c: np.ndarray
    z: np.ndarray
    w: np.ndarray
    failed: str = ""


class MithrilView(SchemeView):
    """Mithril passive view, following notes/schemes/mithril.md.

    From the paper: commitments w_i are revealed in round 2 for every attempt, including rejected
    ones (proof Game 9 replaces rejected w_i by uniform under MLWE). Accepted attempts give the
    ML-DSA-format signature (c, z, h).

    MODELLED / simplified:
      * we release the aggregate w = sum_i w_i, not the per-party w_i (a passive outsider who sees
        the broadcast can sum them; per-party structure is not used by the (c, b) adapter).
      * rejected attempts: only w (no c, no z); they are kept as non-accepted Observations so a
        later estimator can use them, but the (c, b) adapter skips them.
      * the second part z2 = c s2 + r2 is not transmitted; the adapter yields
        b = c t0 - z2. Checked on the reference Go code (15 Oct 2026,
        experiments/mithril_real_transcripts.py, 39461 accepted slots): after acceptance z2 is
        independent of s2 (slope 0.004 +/- 0.10), so b carries c t0 only, not s2. Earlier versions of
        this docstring modelled b = -c (s2 - t0) - r2 with r2 secret-independent; that was wrong.
    """
    name = "mithril"

    def observe(self, a):
        if a.failed:
            return Observation(self.name, self.adversary, False, dict(w=a.w))
        return Observation(self.name, self.adversary, True, dict(c=a.c, z=a.z, w=a.w))


def observations_to_cb(obs, pk: PublicKey, element=0):
    """Accepted Observations -> (c int8 (M,N), b float32 (M,N)) for ring element `element`."""
    p = pk.p
    t_hat = ntt(pk.t_pub)
    cs, bs = [], []
    for o in obs:
        if not o.accepted:
            continue
        f = o.fields
        c = np.asarray(f["c"], dtype=np.int64)
        ct = intt((ntt(c % Q)[None, :] * t_hat) % Q)
        wp = (pk.matvec(f["z"]) - ct) % Q
        if "w1" in f:
            b = wp - 2 * p.gamma2 * np.asarray(f["w1"], dtype=np.int64)
        elif "w" in f:
            b = wp - np.asarray(f["w"], dtype=np.int64)
        else:
            raise KeyError(f"observation from {o.scheme} has neither w1 nor w")
        cs.append(c.astype(np.int8))
        bs.append(mod_pm(b[element], Q).astype(np.float32))
    if not cs:
        return np.zeros((0, N), np.int8), np.zeros((0, N), np.float32)
    return np.stack(cs), np.stack(bs)


def raw_attempts(signer, rng, count):
    """Real ML-DSA nonces and responses (y, c, z = y + c s1) as dsa.Attempt objects, no rejection
    applied (the view applies its own). y and c come from numpy's RNG, as in mldsa_controls."""
    p = signer.p
    y = rng.integers(-p.gamma1 + 1, p.gamma1 + 1, size=(count, p.l, N), dtype=np.int64)
    from ..mldsa.sampling import sample_challenges
    c = sample_challenges(rng, count, p.tau)
    cs1 = mod_pm(intt(ntt(c)[:, None, :] * signer.s1h[None] % Q), Q)
    z = y + cs1
    return [Attempt(i, b"", c[i], None, z[i], "", y[i]) for i in range(count)]
