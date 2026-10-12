"""Monte Carlo sampler agrees with exact enumeration at n = 3, and the null distance matches its bias."""
import numpy as np

from harness.schemes.trilithium_mc import compare, sample_counts
from harness.schemes.trilithium_toy import Toy


def test_sampled_frequencies_match_enumeration():
    toy = Toy(n=3, q=17, gamma2=4, gamma1=8, tau=1, eta=1)
    rng = np.random.default_rng(7)
    a, s1, s2, c = toy.sample(rng)
    exact = toy.histograms(a, s1, s2, c)
    sampled = sample_counts(toy, a, s1, s2, c, 400_000, rng)
    for e, s in zip(exact, sampled):
        pe = e / exact[0].sum()
        ps = s / sampled[0].sum()
        assert np.abs(pe - ps).max() < 0.005


def test_null_distance_is_near_its_bias():
    toy = Toy(n=3, q=17, gamma2=4, gamma1=8, tau=1, eta=1)
    rng = np.random.default_rng(8)
    row = compare(toy, *toy.sample(rng), 200_000, rng)
    assert 0.2 * row["bias_null"] < row["h2_null"] < 5 * row["bias_null"]
