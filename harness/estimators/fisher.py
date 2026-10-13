"""Theory curves for the TALUS s2 channel b = -c*s + e, e uniform on the integers [-B, B].

Two noise models, two very different laws:

1. Plain / Gaussian approximation (what least squares sees). The noise variance is
   sigma^2 = ((2B+1)^2 - 1) / 12 ~ B^2 / 3. Each secret coefficient appears in exactly tau rows
   per signature with coefficient +-1, and E[A^T A] = N tau I, so the per-coefficient Fisher
   information under a Gaussian model with that variance is N tau / sigma^2. The Cramer-Rao
   bound on the RMS error is sigma / sqrt(N tau) ~ B / sqrt(3 tau N); least squares attains it
   (it is the Gaussian MLE). This is the 1/sqrt(N) law validated in experiments/ilwe_scaling.py.
   DERIVED.

2. Uniform noise (what the edge / Chebyshev LP uses). The uniform density has hard edges, so
   the model is non-regular: the Fisher information is infinite and the Cramer-Rao bound does
   not apply. The right tool is order statistics. For ONE coefficient with the other n-1 known
   (the "oracle" or decoupled case), the M = N tau rows touching it give M noisy copies of s_k
   with uniform noise; the best estimate is the midrange (max + min) / 2. The gaps
   G1 = B - max, G2 = min + B are (nearly independent) geometric with P(G >= g) = rho^g,
   rho = (1 - 1/(2B+1))^M ~ exp(-N tau / (2B+1)). Then D = G2 - G1 has
   P(|D| = d) = 2 (1-rho) rho^d / (1+rho), and the probability that rounding the midrange is
   wrong (ties at |D| = 1 counted as one half) is exactly
       P_fail = [2 rho^2 + (1 - rho) rho] / (1 + rho) = rho.
   So per coefficient P_fail = rho, the error is ~Laplace with scale (2B+1) / (N tau) on D,
   i.e. RMS error of the midrange = (2B+1) / (sqrt(2) N tau): the 1/N law. DERIVED (decoupled).

   Full recovery of n coefficients: P = (1 - rho)^n, so
       N*_p = (2B+1) / tau * ln(n / (1 - p))   (oracle, c = 1).
   The real LP solves all n coefficients jointly; every row mixes tau unknowns, so it needs more
   signatures. We model that by one constant c >= 1: rho -> exp(-N tau / (c (2B+1))).
   c is FITTED from Monte Carlo (fit_c below). For tau = 1 the rows are decoupled and c should be
   about 1; that is a check, not a fit.
"""
import math

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import norm


# ---------------------------------------------------------------- Gaussian / least squares

def noise_var(bound):
    """Variance of the uniform integer distribution on [-bound, bound]."""
    return ((2 * bound + 1) ** 2 - 1) / 12.0


def fisher_gaussian(bound, tau, N):
    """Per-coefficient Fisher information of the Gaussian model with the same variance."""
    return N * tau / noise_var(bound)


def crb_rms(bound, tau, N):
    """Cramer-Rao bound on the RMS error (Gaussian approximation) = least-squares RMS."""
    return 1.0 / math.sqrt(fisher_gaussian(bound, tau, N))


def gamma2_law(gamma2, tau, N):
    """The validated least-squares law gamma2 / sqrt(3 tau N) (plain noise, bound = gamma2)."""
    return gamma2 / math.sqrt(3 * tau * N)


def ls_success(n, bound, tau, N):
    """P(all n rounded LS coefficients correct), Gaussian error with the CRB variance."""
    sd = crb_rms(bound, tau, N)
    per = 1 - 2 * norm.sf(0.5 / sd)
    return per ** n


def ls_nstar(n, bound, tau, p=0.99):
    """Smallest N with ls_success >= p (closed form)."""
    per_fail = 1 - p ** (1.0 / n)
    z = norm.isf(per_fail / 2)
    return noise_var(bound) * (2 * z) ** 2 / tau


# ---------------------------------------------------------------- uniform noise / edge

def rho(bound, tau, N, c=1.0):
    """Per-coefficient rounding failure of the midrange: (1 - 1/(2B+1))^(N tau / c)."""
    return math.exp(N * tau / c * math.log1p(-1.0 / (2 * bound + 1)))


def edge_rms(bound, tau, N, c=1.0):
    """RMS error of the (oracle) midrange estimate, continuous approximation: 1/N law."""
    return c * (2 * bound + 1) / (math.sqrt(2) * N * tau)


def edge_success(n, bound, tau, N, c=1.0):
    return (1 - rho(bound, tau, N, c)) ** n


def edge_nstar(n, bound, tau, p=0.99, c=1.0):
    """Smallest N with edge_success >= p (exact inversion of (1-rho)^n = p)."""
    per_fail = 1 - p ** (1.0 / n)
    return c * math.log(per_fail) / (tau * math.log1p(-1.0 / (2 * bound + 1)))


def midrange_monte_carlo(bound, M, trials, rng, chunk=200):
    """Brute-force check of P_fail = rho for one coefficient: M uniform samples, midrange, round.

    Returns the failure rate with ties (|max+min| = 1, estimate exactly +-1/2) counted as 1/2.
    """
    fails = 0.0
    done = 0
    while done < trials:
        t = min(chunk, trials - done)
        e = rng.integers(-bound, bound + 1, size=(t, M))
        d = np.abs(e.max(axis=1) + e.min(axis=1))
        fails += np.sum(d >= 2) + 0.5 * np.sum(d == 1)
        done += t
    return fails / trials


def fit_c(points):
    """Binomial MLE of c from ladder points: iterable of dicts with n, tau, bound, N, trials, succ.

    Returns (c_hat, (lo, hi)) with a rough 95% interval from the likelihood-ratio (drop 1.92).
    """
    pts = [(p["n"], p["tau"], p["bound"], p["N"], p["trials"], p["succ"]) for p in points]

    def nll(logc):
        c = math.exp(logc)
        tot = 0.0
        for n, tau, bound, N, tr, s in pts:
            q = min(max(edge_success(n, bound, tau, N, c), 1e-12), 1 - 1e-12)
            k = s * tr
            tot -= k * math.log(q) + (tr - k) * math.log(1 - q)
        return tot

    res = minimize_scalar(nll, bounds=(math.log(0.05), math.log(50)), method="bounded")
    best = res.fun
    grid = np.linspace(res.x - 2, res.x + 2, 801)
    ok = [g for g in grid if nll(g) <= best + 1.92]
    return math.exp(res.x), (math.exp(min(ok)), math.exp(max(ok)))
