"""Positive and negative controls for the TALUS s2-channel estimators, built from real ML-DSA signing.

From any accepted ML-DSA signature (c, z, h) and the public key (A, t1), an attacker computes
    w' = A z - c t1 2^d   and   w1 = UseHint(h, w'),   then   b = w' - 2 gamma2 w1   (centred mod q).
Since A z = w + c (t1 2^d + t0 - s2):
  * Plain ML-DSA (negative control): the r0 check makes w1 = HighBits(w - c s2), so
        b = c t0 + r0,  r0 = LowBits(w - c s2), |r0| < gamma2 - beta.
    b only reveals t0, which ML-DSA's security analysis already treats as public. Estimators must not
    return s2 - t0 (from which A s1 = t1 2^d - (s2 - t0) and hence the key would follow).
  * "No r0 check" variant (positive control): a scheme that skips the r0 check and releases
    w1 = HighBits(w) gives b = LowBits(w) - c (s2 - t0), the plain-noise channel with target s2 - t0,
    i.e. a key-recovery channel. Estimators must recover s2 - t0 here.
Both cases are written as b = -c x + e for the estimator: x = -t0 (negative), x = s2 - t0 (positive).

Signing is batched numpy, faithful to FIPS 204 Alg. 7 except that y and c are drawn with numpy's RNG
instead of SHAKE (same distribution in the random-oracle model). The key is a genuine keygen_internal key.
"""
import numpy as np

from ..mldsa.dsa import keygen_internal
from ..mldsa.hints import make_hint, use_hint
from ..mldsa.ntt import intt, ntt
from ..mldsa.params import D, N, Q, Params
from ..mldsa.rounding import decompose, mod_pm
from ..mldsa.sampling import expand_a, sample_challenges


class Signer:
    def __init__(self, p: Params, xi: bytes):
        self.p = p
        _, _, sec = keygen_internal(xi, p)
        self.sec = sec
        self.a_hat = expand_a(sec["rho"], p.k, p.l)
        self.s1h, self.s2h, self.t0h = ntt(sec["s1"]), ntt(sec["s2"]), ntt(sec["t0"])
        self.t1h = ntt(sec["t1"] << D)

    def _matvec(self, vh):
        """A_hat (k,l,N) times a batch vh (B,l,N) in the NTT domain -> (B,k,N)."""
        out = np.zeros((vh.shape[0], self.p.k, N), dtype=np.int64)
        for j in range(self.p.l):
            out = (out + self.a_hat[None, :, j, :] * vh[:, None, j, :]) % Q
        return out

    def attempts(self, rng, batch, r0_check=True):
        """One batch of signing attempts. Returns (c, b, accepted_mask, r0) with b (B,k,N) the
        attacker's observable computed from public data only, and r0 = LowBits(w - c s2)."""
        p = self.p
        y = rng.integers(-p.gamma1 + 1, p.gamma1 + 1, size=(batch, p.l, N), dtype=np.int64)
        w = intt(self._matvec(ntt(y)))
        c = sample_challenges(rng, batch, p.tau)
        ch = ntt(c)[:, None, :]
        cs1 = mod_pm(intt(ch * self.s1h[None] % Q), Q)
        cs2 = mod_pm(intt(ch * self.s2h[None] % Q), Q)
        ct0 = mod_pm(intt(ch * self.t0h[None] % Q), Q)
        z = y + cs1
        ok = (np.abs(z) < p.gamma1 - p.beta).all(axis=(1, 2))
        w1_true, _ = decompose(w, p.gamma2)
        _, r0 = decompose(w - cs2, p.gamma2)
        if r0_check:
            ok &= (np.abs(r0) < p.gamma2 - p.beta).all(axis=(1, 2))
            ok &= (np.abs(ct0) < p.gamma2).all(axis=(1, 2))
            h = make_hint(-ct0 % Q, (w - cs2 + ct0) % Q, p.gamma2)
            ok &= h.sum(axis=(1, 2)) <= p.omega
        # attacker's view, public data only
        wp = (intt(self._matvec(ntt(z % Q))) - intt(ch * self.t1h[None] % Q)) % Q
        w1 = use_hint(h, wp, p.gamma2) if r0_check else w1_true
        b = mod_pm(wp - 2 * p.gamma2 * w1, Q)
        return c, b, ok, r0

    def transcript(self, rng, count, element=0, r0_check=True, batch=2048):
        """Accepted signatures only: (c int8 (count,N), b float32 (count,N)) for ring element `element`."""
        cs, bs, have = [], [], 0
        while have < count:
            c, b, ok, _ = self.attempts(rng, batch, r0_check)
            cs.append(c[ok].astype(np.int8))
            bs.append(b[ok, element].astype(np.float32))
            have += int(ok.sum())
        return np.concatenate(cs)[:count], np.concatenate(bs)[:count]

    def target(self, element=0, positive=True):
        """x with b = -c x + e: s2 - t0 for the positive control, -t0 for the negative one."""
        s2, t0 = self.sec["s2"][element], mod_pm(self.sec["t0"][element], Q)
        return (s2 - t0) if positive else -t0
