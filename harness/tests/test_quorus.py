"""Quorus single-attempt signer (harness/schemes/quorus.py): released signatures verify under FIPS 204."""
import collections

import numpy as np
import pytest

from harness.mldsa.params import ALL
from harness.schemes.quorus import QuorusSigner


@pytest.mark.parametrize("name", list(ALL))
@pytest.mark.parametrize("add_ew", [True, False])
def test_signatures_verify(name, add_ew):
    rng = np.random.default_rng(7)
    signer = QuorusSigner(ALL[name], bytes(range(32)), add_ew=add_ew)
    sigs = 0
    for _ in range(300):
        a = signer.attempt(rng.bytes(8), rng)
        if a.failed == "":
            sigs += 1
            assert a.verifies
    assert sigs > 10


def test_rejection_rate_close_to_table2():
    # Table 2: M_rep = 4.25 for ML-DSA-44 (expected repetitions from the line-3 checks).
    rng = np.random.default_rng(8)
    signer = QuorusSigner(ALL["ML-DSA-44"], bytes(32))
    cnt = collections.Counter(signer.attempt(rng.bytes(8), rng).failed for _ in range(3000))
    m_rep = 3000 / (3000 - cnt["z_norm"] - cnt["w0_norm"])
    assert 3.6 < m_rep < 4.9
