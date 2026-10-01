"""Synthetic ILWE transcript for one ring element of the s2 channel.

Model of the observable in Niot's second TALUS attack (see docs/DOSSIER.md):
b = -c*s' + e over Z[X]/(X^256+1), with e = LowBits(w), w uniform mod q.
Here s' is the (small) target; the harness does not model t0 (so s' = s2).
"""
import numpy as np

from ..mldsa.params import N, Params, Q
from ..mldsa.ring import negacyclic_mul
from ..mldsa.rounding import low_bits
from ..mldsa.sampling import sample_challenges


def make_transcript(rng, params: Params, s, count):
    """Return (c, b): count challenges and the observations b_i = -c_i*s + e_i."""
    c = sample_challenges(rng, count, params.tau)
    w = rng.integers(0, Q, size=(count, N), dtype=np.int64)
    e = low_bits(w, params.gamma2)
    cs = np.rint(negacyclic_mul(c, s)).astype(np.int64)
    return c, -cs + e
