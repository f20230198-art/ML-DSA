"""Tests for the theory curves in harness/estimators/fisher.py."""
import math

import numpy as np

from harness.estimators import fisher


def test_crb_matches_gamma2_law():
    g2, tau, N = 95232, 39, 10_000
    assert math.isclose(fisher.crb_rms(g2, tau, N), fisher.gamma2_law(g2, tau, N), rel_tol=1e-4)


def test_midrange_failure_equals_rho():
    rng = np.random.default_rng(7)
    for B, M in [(20, 41), (50, 150)]:
        mc = fisher.midrange_monte_carlo(B, M, 6000, rng)
        th = fisher.rho(B, 1, M)
        assert abs(mc - th) < 4 * math.sqrt(th * (1 - th) / 6000)


def test_edge_nstar_inverts_success():
    for n, B, tau, p, c in [(8, 95154, 1, 0.99, 1.0), (256, 95154, 39, 0.5, 3.0)]:
        N = fisher.edge_nstar(n, B, tau, p, c)
        assert math.isclose(fisher.edge_success(n, B, tau, N, c), p, rel_tol=1e-9)


def test_ls_nstar_inverts_success():
    N = fisher.ls_nstar(64, 1000, 10, 0.9)
    assert math.isclose(fisher.ls_success(64, 1000, 10, N), 0.9, rel_tol=1e-6)


def test_edge_is_one_over_n_and_ls_one_over_sqrt_n():
    assert math.isclose(fisher.edge_rms(100, 5, 1000) / fisher.edge_rms(100, 5, 4000), 4.0)
    assert math.isclose(fisher.crb_rms(100, 5, 1000) / fisher.crb_rms(100, 5, 4000), 2.0)


def test_fit_c_recovers_known_constant():
    rng = np.random.default_rng(3)
    c_true, n, B, tau, tr = 2.0, 32, 500, 5, 400
    pts = []
    for N in (600, 900, 1300, 2000):
        q = fisher.edge_success(n, B, tau, N, c_true)
        pts.append(dict(n=n, tau=tau, bound=B, N=N, trials=tr, succ=rng.binomial(tr, q) / tr))
    c, (lo, hi) = fisher.fit_c(pts)
    assert lo <= c_true <= hi and abs(c - c_true) < 0.2
