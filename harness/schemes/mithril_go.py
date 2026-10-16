"""Reader for real Mithril transcripts dumped by harness/mithril_go/dump_test.go.

The Go dumper runs the reference code of Celi et al. (GuilhemN/threshold-ml-dsa, commit 66e269e,
ML-DSA-44 only). Unlike views.MithrilView, nothing here is modelled: c, w and z are the values the
reference signers compute. The full secret (s1, s2) and t are dumped too, as ground truth.
"""
from dataclasses import dataclass

import numpy as np

from ..mldsa.ntt import intt, ntt
from ..mldsa.params import ML_DSA_44, N, Q
from ..mldsa.rounding import mod_pm
from ..mldsa.sampling import expand_a


@dataclass
class MithrilTranscript:
    T: int
    Nparties: int
    K: int
    seed: int
    rho: bytes
    t: np.ndarray        # (k, N) in [0, q)
    s1: np.ndarray       # (l, N) centred
    s2: np.ndarray       # (k, N) centred
    rej: np.ndarray      # (S,) bit j set if signer j rejected the slot
    c: np.ndarray        # (S, N) centred, entries in {-1, 0, 1}
    w: np.ndarray        # (S, k, N) aggregated commitment in [0, q)
    z: np.ndarray        # (S, l, N) aggregated response, centred

    @property
    def accepted(self):
        return self.rej == 0

    def a_hat(self):
        p = ML_DSA_44
        return expand_a(self.rho, p.k, p.l)


def load(path):
    p = ML_DSA_44
    k, l = p.k, p.l
    raw = open(path, "rb").read()
    head = np.frombuffer(raw[:20], "<u4")
    T, Np, K, S, seed = (int(x) for x in head)
    rho = raw[20:52]
    body = np.frombuffer(raw[52:], "<u4").astype(np.int64)
    pos = 0

    def take(n):
        nonlocal pos
        out = body[pos:pos + n]
        pos += n
        return out

    t = take(k * N).reshape(k, N)
    s1 = mod_pm(take(l * N).reshape(l, N), Q)
    s2 = mod_pm(take(k * N).reshape(k, N), Q)
    rec = body[pos:].reshape(S, 1 + N + k * N + l * N)
    rej = rec[:, 0]
    c = mod_pm(rec[:, 1:1 + N], Q)
    w = rec[:, 1 + N:1 + N + k * N].reshape(S, k, N)
    z = mod_pm(rec[:, 1 + N + k * N:].reshape(S, l, N), Q)
    return MithrilTranscript(T, Np, K, seed, rho, t, s1, s2, rej, c, w, z)


def matvec(a_hat, v):
    """A v for v (..., l, N) coefficient domain -> (..., k, N) in [0, q)."""
    vh = ntt(np.asarray(v, dtype=np.int64) % Q)
    return intt(np.einsum("ijn,...jn->...in", a_hat, vh) % Q)


def ring_mul(c, v):
    """c (S, N) times v (..., N) broadcast over a vector axis -> centred."""
    ch = ntt(np.asarray(c, dtype=np.int64) % Q)
    vh = ntt(np.asarray(v, dtype=np.int64) % Q)
    return mod_pm(intt((ch[:, None, :] * vh[None]) % Q), Q)
