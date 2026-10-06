"""Scheme-view interface (PLAN stage B): what an adversary sees of each signing attempt.

A `SchemeView` turns a full signing attempt (`harness.mldsa.dsa.Attempt`, which includes secret
internals such as y) into an `Observation` holding only the fields that scheme releases to the
modelled adversary. Estimators consume Observations and never touch secrets, so the same
estimator can be pointed at different schemes, and at a plain ML-DSA control that must leak nothing.

Views here are for CONTROLS. Scheme-specific views (Mithril, Quorus, Trilithium, TALUS) are to be
written only after the relevant paper section is read (PLAN principle 5); the TALUS s2 channel
lives in `talus_bcc.py` and `ilwe_transcript.py` as synthetic channels and is not yet wired in here.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np

from ..mldsa.dsa import Attempt


@dataclass
class Observation:
    scheme: str
    adversary: str              # label only: "passive", "corrupt-T-1", "coordinator", ...
    accepted: bool
    fields: dict = field(default_factory=dict)   # name -> numpy array or bytes


class SchemeView(ABC):
    name = "abstract"

    def __init__(self, adversary="passive"):
        self.adversary = adversary

    @abstractmethod
    def observe(self, attempt: Attempt):
        """Return an Observation, or None if nothing about this attempt is released."""

    def observe_all(self, attempts):
        return [o for o in map(self.observe, attempts) if o is not None]


class PlainMLDSAView(SchemeView):
    """Negative control: single-signer ML-DSA. Only accepted signatures (c_tilde, z, h) are public;
    rejected attempts release nothing. Any estimator that finds a leak here has a bug."""
    name = "plain-ml-dsa"

    def observe(self, a: Attempt):
        if a.failed:
            return None
        return Observation(self.name, self.adversary, True,
                           dict(c_tilde=a.c_tilde, c=a.c, z=a.z, h=a.h))


class YLeakView(SchemeView):
    """Positive control: toy scheme that also releases the nonce y of every attempt.
    Then z - y = c*s1 exactly, and s1 follows by dividing by c; the harness must recover it."""
    name = "toy-y-leak"

    def observe(self, a: Attempt):
        if a.failed:
            return None
        return Observation(self.name, self.adversary, True,
                           dict(c=a.c, z=a.z, y=a.y))


def recover_s1_from_y_leak(obs: Observation):
    """Positive-control estimator: s1 = c^-1 * (z - y) over Z_q, NTT domain. Returns None if c is
    not invertible (some NTT coefficient is 0), in which case another signature is needed."""
    from ..mldsa.ntt import intt, ntt
    from ..mldsa.params import Q

    f = obs.fields
    ch = ntt(f["c"])
    if (ch == 0).any():
        return None
    inv = np.array([pow(int(x), -1, Q) for x in ch], dtype=np.int64)
    cs1_hat = ntt((f["z"] - f["y"]) % Q)
    s1 = intt((cs1_hat * inv[None, :]) % Q)
    return np.where(s1 > Q // 2, s1 - Q, s1)
