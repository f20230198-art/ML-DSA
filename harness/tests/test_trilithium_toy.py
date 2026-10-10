import numpy as np

from harness.schemes import trilithium_toy as tt


def test_negacyclic_matrix_matches_schoolbook():
    rng = np.random.default_rng(1)
    q, n = 257, 4
    a, b = rng.integers(0, q, n), rng.integers(-5, 6, n)
    want = np.zeros(n, dtype=np.int64)
    for i in range(n):
        for j in range(n):
            k = i + j
            want[k % n] += a[i] * b[j] * (1 if k < n else -1)
    assert np.array_equal(tt.negacyclic_matrix(a, q) @ b % q, want % q)


def test_decompose_reconstructs():
    q, g2 = 257, 16
    r = np.arange(q)
    r1, r0 = tt.decompose(r, q, g2)
    assert np.array_equal((r1 * 2 * g2 + r0) % q, r)
    assert r1.min() == 0 and r1.max() == (q - 1) // (2 * g2) - 1
    assert np.abs(r0).max() <= g2


def test_uniform_highbits_sums_to_one_and_branches_partition():
    toy = tt.Toy(n=2, gamma1=6)
    assert abs(toy.uniform_highbits().sum() - 1) < 1e-12
    a, s1, s2, c = toy.sample(np.random.default_rng(3))
    h_all, h2, h3 = toy.histograms(a, s1, s2, c, chunk=7)
    assert h_all.sum() == (2 * toy.gamma1) ** toy.n
    assert np.all(h2 + h3 <= h_all)


def test_same_secret_gives_zero_key_distance():
    toy = tt.Toy(n=2, gamma1=6)
    a, s1, s2, c = toy.sample(np.random.default_rng(4))
    _, _, h3 = toy.histograms(a, s1, s2, c)
    _, _, h3b = toy.histograms(a, s1.copy(), s2, c)
    assert tt.distances(h3, h3b) == (0.0, 0.0)


def test_c_times_s1_is_small_and_signed():
    toy = tt.Toy()
    for seed in range(20):
        a, s1, s2, c = toy.sample(np.random.default_rng(seed))
        assert np.abs(toy._mul(c, s1)).max() <= toy.beta
