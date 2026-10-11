"""The convolution method must reproduce the brute-force enumeration exactly."""
import numpy as np

from harness.schemes.trilithium_conv import histograms_conv
from harness.schemes.trilithium_toy import Toy


def test_conv_matches_enumeration():
    rng = np.random.default_rng(7)
    for n, q, g2, g1, tau in ((3, 17, 4, 4, 1), (4, 17, 4, 6, 1), (2, 257, 16, 16, 2)):
        toy = Toy(n=n, q=q, gamma2=g2, gamma1=g1, tau=tau, eta=1)
        for _ in range(3):
            a, s1, s2, c = toy.sample(rng)
            for x, y in zip(toy.histograms(a, s1, s2, c), histograms_conv(toy, a, s1, s2, c)):
                assert np.array_equal(x, y)
