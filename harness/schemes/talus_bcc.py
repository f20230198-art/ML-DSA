"""Synthetic TALUS-style s2 channel with bounded (uniform, hard-edged) noise, any ring size n.

Observable (Niot's second attack, see docs/DOSSIER.md):  b = -c*s' + e  over Z[X]/(X^n+1),
with e = LowBits(w), w uniform mod q. LowBits of a uniform w is uniform on a symmetric
interval, so e is uniform on [-bound, bound]:

  * plain model:  bound = gamma2            (no rejection check at all)
  * BCC model:    bound = gamma2 - beta     (Boundary Clearance Condition keeps e off the edges)

The target s' is either s2 (|s'| <= eta) or s2 - t0 (t0 uniform in the Power2Round range,
|t0| <= 2^(d-1)). Not modelled: the hint/high-bits side information, the real LowBits
wrap-around at q-1, and anything TALUS v0.22 changed about what is released. Check
docs/PLAN.md stage C0 before quoting a result for v0.22.
"""
from dataclasses import dataclass

import numpy as np

from ..mldsa.params import D, Params
from ..mldsa.ringn import get_ring, sample_challenges_n, scaled_tau


@dataclass(frozen=True)
class Channel:
    n: int
    tau: int
    bound: int        # noise is uniform on the integers [-bound, bound]
    target_max: int   # secret coefficients are uniform on [-target_max, target_max]


def make_channel(p: Params, n, noise="bcc", target="s2"):
    if noise not in ("bcc", "plain"):
        raise ValueError(noise)
    if target not in ("s2", "s2-t0"):
        raise ValueError(target)
    bound = p.gamma2 - p.beta if noise == "bcc" else p.gamma2
    target_max = p.eta if target == "s2" else (1 << (D - 1)) + p.eta
    return Channel(n=n, tau=scaled_tau(n, p.tau), bound=bound, target_max=target_max)


def sample_target(rng, ch: Channel):
    return rng.integers(-ch.target_max, ch.target_max + 1, size=ch.n, dtype=np.int64)


def make_transcript(rng, ch: Channel, s, count, chunk=4096):
    """Return (c, b): c int8 (count, n), b float32 (count, n) with b_i = -c_i*s + e_i.

    float32 holds every value exactly (|b| < 2^24), which halves memory at large count.
    """
    ring = get_ring(ch.n)
    c = sample_challenges_n(rng, count, ch.n, ch.tau, chunk)
    b = np.empty((count, ch.n), dtype=np.float32)
    for start in range(0, count, chunk):
        sl = slice(start, min(start + chunk, count))
        cs = np.rint(ring.mul(c[sl], s))
        e = rng.integers(-ch.bound, ch.bound + 1, size=cs.shape)
        b[sl] = (-cs + e).astype(np.float32)
    return c, b
