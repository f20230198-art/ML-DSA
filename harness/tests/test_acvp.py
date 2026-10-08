"""Official NIST ACVP vectors for ML-DSA (subset in vectors/acvp_mldsa.json, see extract_acvp.py).

Covers key generation, pure signing (deterministic and hedged; external interface with context and
internal interface) and verification including invalid signatures. PreHash and external-mu are not
covered because our implementation does not offer them.
"""
import json
import os

import pytest

from harness.mldsa import dsa
from harness.mldsa.params import ALL

with open(os.path.join(os.path.dirname(__file__), "vectors", "acvp_mldsa.json")) as f:
    V = json.load(f)

b = bytes.fromhex


def m_prime(t):
    if t["interface"] == "external":
        ctx = b(t["context"])
        return bytes([0, len(ctx)]) + ctx + b(t["message"])
    return b(t["message"])


@pytest.mark.parametrize("t", V["keyGen"], ids=lambda t: t["param"])
def test_keygen(t):
    pk, sk, _ = dsa.keygen_internal(b(t["seed"]), ALL[t["param"]])
    assert pk.hex().upper() == t["pk"] and sk.hex().upper() == t["sk"]


@pytest.mark.parametrize("t", V["sigGen"], ids=lambda t: t["param"] + "-" + t["interface"])
def test_siggen(t):
    sig, _ = dsa.sign_internal(b(t["sk"]), m_prime(t), b(t["rnd"]), ALL[t["param"]])
    assert sig.hex().upper() == t["signature"]


@pytest.mark.parametrize("t", V["sigVer"], ids=lambda t: t["param"] + "-" + t["reason"])
def test_sigver(t):
    assert dsa.verify_internal(b(t["pk"]), m_prime(t), b(t["signature"]), ALL[t["param"]]) == t["passed"]
