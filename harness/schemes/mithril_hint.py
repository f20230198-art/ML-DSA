"""Mithril a posteriori key sharing (Sec. 3.3, App. E of ePrint 2026/013): hint accounting for T-1
corrupted parties, Stage E.

Setting (per coefficient of the ML-DSA secret (s1, s2)): the existing secret s is uniform on
[-eta, eta]. The user splits it into S = C(N, T-1) shares x_1..x_S, i.i.d. discrete Gaussian of
standard deviation sigma_share, conditioned on sum x_i = s. With replicated sharing, T-1 corrupted
parties hold every share except the one indexed by the N-T+1 honest parties, so they learn
h = x_1 + ... + x_{S-1} = s - x_S. Exactly:
    p(s, h) = U(s) * P_{S-1}(h) * D(s - h) / P_S(s),
where P_j is the j-fold convolution of D. We compute H(s | h) and the mean posterior variance, the
standard deviation of a discrete Gaussian with the same entropy (the paper says 0.74 for
sigma_share = sqrt(2)), and a primal-uSVP core-SVP estimate (2016 estimate, Python substitute for
the lattice estimator, which needs Sage) with and without the hint.

Run: python -m harness.schemes.mithril_hint
"""
import math
from math import comb

import numpy as np

from harness.mldsa.params import ALL

N_RING = 256
Q = 8380417


def dgauss(sigma, tail=12):
    """Discrete Gaussian on Z with parameter sigma (rho(x) = exp(-x^2 / (2 sigma^2))), as (support, probs)."""
    w = int(math.ceil(tail * sigma)) + 1
    xs = np.arange(-w, w + 1)
    p = np.exp(-xs.astype(float) ** 2 / (2 * sigma ** 2))
    return xs, p / p.sum()


def conv_power(p, j):
    """j-fold convolution of a centred pmf p (odd length); result is centred too."""
    out = np.array([1.0])
    for _ in range(j):
        out = np.convolve(out, p)
    return out


def entropy(p):
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def posterior_stats(eta, sigma_share, S):
    """Return (H(s), H(s|h), mean posterior variance) per coefficient, in bits / squared units."""
    xs, d = dgauss(sigma_share)
    w = len(xs) // 2
    p_sm1 = conv_power(d, S - 1)          # pmf of h, centred
    p_s = np.convolve(p_sm1, d)           # pmf of the full sum, centred
    ws1, ws = len(p_sm1) // 2, len(p_s) // 2
    svals = np.arange(-eta, eta + 1)
    hvals = np.arange(-ws1, ws1 + 1)
    joint = np.zeros((len(svals), len(hvals)))
    for i, s in enumerate(svals):
        diff = s - hvals                   # x_S = s - h
        ok = np.abs(diff) <= w
        joint[i, ok] = p_sm1[ok] * d[diff[ok] + w] / p_s[s + ws]
    joint /= len(svals)
    joint /= joint.sum()                   # tiny truncation error only
    ph = joint.sum(axis=0)
    keep = ph > 0
    post = joint[:, keep] / ph[keep]
    h_cond = float(sum(ph[keep][j] * entropy(post[:, j]) for j in range(post.shape[1])))
    mean = svals @ post
    var = (svals[:, None] ** 2 * post).sum(axis=0) - mean ** 2
    return math.log2(len(svals)), h_cond, float(ph[keep] @ var)


def sigma_same_entropy(h_bits):
    """Standard deviation parameter of the discrete Gaussian whose entropy is h_bits (bisection)."""
    lo, hi = 0.05, 50.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if entropy(dgauss(mid)[1]) < h_bits:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def log2_delta(beta):
    return math.log2((math.pi * beta) ** (1 / beta) * beta / (2 * math.pi * math.e)) / (2 * (beta - 1))


def primal_usvp_beta(n_secret, m_max, sigma_s, sigma_e, q=Q):
    """Smallest BKZ block size beta for the primal uSVP attack (ADPS16 2016 estimate), optimising
    the number of samples m <= m_max; secret coordinates rescaled by sigma_e / sigma_s."""
    lnu = math.log2(sigma_e / sigma_s)
    best = None
    for beta in range(50, 2000):
        ld = log2_delta(beta)
        lhs = 0.5 * math.log2(beta) + math.log2(sigma_e)
        for m in range(64, m_max + 1, 16):
            dim = n_secret + m + 1
            rhs = ld * (2 * beta - dim - 1) + (m * math.log2(q) + n_secret * lnu) / dim
            if lhs <= rhs:
                best = beta
                break
        if best:
            return best
    return None


def core_svp_bits(beta):
    return 0.292 * beta


def report(sigma_share=math.sqrt(2), Ns=(2, 3, 4, 5, 6)):
    lines = [f"Mithril a posteriori key sharing, T-1 corrupted parties, sigma_share = {sigma_share:.4f}",
             "S = C(N, T-1) shares; adversary learns h = s - x_S. Per coefficient of (s1, s2).",
             "Core-SVP: primal uSVP, 2016 estimate, 0.292 beta (Python substitute for the lattice estimator).",
             ""]
    for name, p in ALL.items():
        n_s, m_max = p.l * N_RING, p.k * N_RING
        sig0 = math.sqrt(p.eta * (p.eta + 1) / 3)
        b0 = primal_usvp_beta(n_s, m_max, sig0, sig0)
        lines.append(f"{name}: eta={p.eta}, H(s)={math.log2(2 * p.eta + 1):.3f} bits, sd {sig0:.3f}, "
                     f"no hint beta={b0} core-SVP {core_svp_bits(b0):.1f}")
        lines.append("   S   H(s|h)  sd_post  sd_sameH  beta(sd_post) bits  loss | beta(sd_sameH) bits  loss")
        seen = set()
        for N in Ns:
            for T in range(2, N + 1):
                S = comb(N, T - 1)
                if S in seen:
                    continue
                seen.add(S)
                _, hc, var = posterior_stats(p.eta, sigma_share, S)
                sd_post, sd_h = math.sqrt(var), sigma_same_entropy(hc)
                b1 = primal_usvp_beta(n_s, m_max, sd_post, sd_post)
                b2 = primal_usvp_beta(n_s, m_max, sd_h, sd_h)
                lines.append(f"{S:4d}  {hc:6.3f}  {sd_post:7.3f}  {sd_h:8.3f}  {b1:6d} {core_svp_bits(b1):6.1f} "
                             f"{core_svp_bits(b0) - core_svp_bits(b1):5.1f} | {b2:6d} {core_svp_bits(b2):6.1f} "
                             f"{core_svp_bits(b0) - core_svp_bits(b2):5.1f}")
        lines.append("")
    return "\n".join(lines)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sigma", type=float, default=math.sqrt(2))
    args = ap.parse_args()
    print(report(args.sigma))


if __name__ == "__main__":
    main()
