"""Mithril (Celi, del Pino, Espitau, Niot, Prest; USENIX Security 2026, ePrint 2026/013 full version)
parameter accounting, Stage E.

Recomputes, from the published parameters (App. A, Figs. 9-11), the number of signing queries Q_s
the proof covers (Thm. 3.2): Q_s = 2 / (K * I_{1-1/phi^2}((n(k+l)+1)/2, 1/2)), where phi is the
smallest value allowed by Lemma 2.4's condition r'^2 >= r^2 + B^2 + 2 r B / phi, and B is the
paper's heuristic norm bound of Sec. 3.4:
    B = 1.3 * sqrt(tau) * sqrt(n (k + l / nu^2)) * sqrt(Var U(-eta, eta)) * sqrt(ceil(C(N, T-1) / T)).
Also measures the real distribution of ||(c u1 / nu, c u2)||_2 to test the "13 standard deviations"
footnote, and the per-party rejection parameter M = (r'/r)^(n(k+l)).
"""
import math

import numpy as np
from scipy.special import betainc

from harness.mldsa.params import ALL
from harness.mldsa.ring import negacyclic_mul

N_RING = 256

# (T, N): (r, r', K), copied from App. A of the full version (Figs. 9, 10, 11).
TABLES = {
    "ML-DSA-44": (3, {
        (2, 2): (252778, 252833, 2), (2, 3): (310060, 310138, 3), (3, 3): (246490, 246546, 4),
        (2, 4): (305919, 305997, 3), (3, 4): (279235, 279314, 7), (4, 4): (243463, 243519, 8),
        (2, 5): (285363, 285459, 3), (3, 5): (282800, 282912, 14), (4, 5): (259427, 259526, 30),
        (5, 5): (239924, 239981, 16), (2, 6): (300265, 300362, 4), (3, 6): (277014, 277139, 19),
        (4, 6): (268705, 268831, 74), (5, 6): (250590, 250686, 100), (6, 6): (219245, 219301, 37)}),
    "ML-DSA-65": (6, {
        (2, 2): (501495, 501613, 3), (2, 3): (540212, 540378, 5), (3, 3): (510387, 510504, 9),
        (2, 4): (540212, 540378, 6), (3, 4): (506761, 506928, 20), (4, 4): (433594, 433711, 26),
        (2, 5): (552371, 552575, 8), (3, 5): (552909, 553145, 62), (4, 5): (474331, 474535, 205),
        (5, 5): (425914, 426032, 78), (2, 6): (571208, 571412, 8), (3, 6): (536793, 537058, 95),
        (4, 6): (488704, 488969, 804), (5, 6): (461324, 461529, 1200), (6, 6): (414896, 415013, 250)}),
    "ML-DSA-87": (7, {
        (2, 2): (503119, 503192, 3), (2, 3): (631601, 631703, 4), (3, 3): (483107, 483180, 6),
        (2, 4): (632903, 633006, 4), (3, 4): (551752, 551854, 11), (4, 4): (487958, 488031, 14),
        (2, 5): (607694, 607820, 5), (3, 5): (577400, 577546, 26), (4, 5): (518384, 518510, 70),
        (5, 5): (468214, 468287, 35), (2, 6): (665106, 665232, 5), (3, 6): (577541, 577704, 39),
        (4, 6): (517689, 517853, 208), (5, 6): (479692, 479819, 295), (6, 6): (424124, 424197, 87)}),
}


def shares_per_party(T, N):
    return math.ceil(math.comb(N, T - 1) / T)


def bound_B(p, nu, T, N, n=N_RING):
    var = p.eta * (p.eta + 1) / 3
    return 1.3 * math.sqrt(p.tau) * math.sqrt(n * (p.k + p.l / nu ** 2)) * math.sqrt(var) \
        * math.sqrt(shares_per_party(T, N))


def log2_qs(p, nu, T, N, r, rp, K, B=None, n=N_RING):
    """Returns (log2 Q_s, phi, log2 M). Q_s = 0 if Lemma 2.4 cannot be met."""
    B = bound_B(p, nu, T, N, n) if B is None else B
    slack = rp * rp - r * r - B * B
    dim = n * (p.k + p.l)
    log2_m = dim * math.log2(rp / r)
    if slack <= 0:
        return -math.inf, math.inf, log2_m
    phi = 2 * r * B / slack
    if phi <= 1:
        phi = 1.0 + 1e-12
    i_val = betainc((dim + 1) / 2, 0.5, 1 - 1 / phi ** 2)
    return math.log2(2 / (K * i_val)), phi, log2_m


def lemma25_bound_log2(dim, phi):
    """log2 of the paper's Lemma 2.5 bound (1 - 1/phi^2)^(dim-1) * dim * (1 - 1/phi), as stated and as
    used (`boundI`) in the authors' params/hyperball.sage. Compare with exact_I_log2."""
    return (dim - 1) * math.log2(1 - 1 / phi ** 2) + math.log2(dim * (1 - 1 / phi))


def exact_I_log2(dim, phi):
    return math.log2(betainc((dim + 1) / 2, 0.5, 1 - 1 / phi ** 2))


def implied_B(p, K, r, rp, log2_target=50, n=N_RING):
    """Largest B for which Thm. 3.2 still gives Q_s >= 2^log2_target with the published r, r', K."""
    dim = n * (p.k + p.l)
    i_target = 2 / (K * 2.0 ** log2_target)
    lo, hi = 1.0 + 1e-9, 1e3                      # I(1 - 1/phi^2) increases with phi; bisect
    for _ in range(200):
        mid = (lo + hi) / 2
        if betainc((dim + 1) / 2, 0.5, 1 - 1 / mid ** 2) <= i_target:
            lo = mid
        else:
            hi = mid
    phi = lo
    # phi B^2 + 2 r B - phi (r'^2 - r^2) = 0
    return (-2 * r + math.sqrt(4 * r * r + 4 * phi * phi * (rp * rp - r * r))) / (2 * phi)


def eps_of_norm(p, r, rp, norm, n=N_RING):
    """Smallest smoothing eps allowed by Lemma 2.4 for one session whose secret-dependent shift has
    Euclidean norm `norm`, at the published radii (so M = (r'/r)^(n(k+l)) is fixed). 1/2 if none."""
    dim = n * (p.k + p.l)
    slack = rp * rp - r * r - norm * norm
    if slack <= 0:
        return 0.5
    phi = max(2 * r * norm / slack, 1.0 + 1e-12)
    return 0.5 * betainc((dim + 1) / 2, 0.5, 1 - 1 / phi ** 2)


def log2_qs_typical(p, K, r, rp, mu, sd, n=N_RING, width=20.0, points=4001):
    """Heuristic Q_s = 1 / (K * E[eps(||v||)]) with ||v|| ~ Normal(mu, sd) (fit to samples).
    Treats each session's challenge as random (no grinding), unlike Thm. 3.2's worst case."""
    x = np.linspace(max(mu - width * sd, 0.0), mu + width * sd, points)
    w = np.exp(-0.5 * ((x - mu) / sd) ** 2)
    w /= w.sum()
    e = np.array([eps_of_norm(p, r, rp, v, n) for v in x])
    return -math.log2(K * float((w * e).sum()))


def sample_norms(p, nu, T, N, trials, rng, n=N_RING):
    """||(c u1 / nu, c u2)||_2 for u the sum of m = ceil(C(N,T-1)/T) secrets from U[-eta, eta]."""
    m = shares_per_party(T, N)
    out = np.empty(trials)
    for t in range(trials):
        u = rng.integers(-p.eta, p.eta + 1, size=(m, p.k + p.l, n)).sum(axis=0)
        c = np.zeros(n, dtype=np.int64)
        pos = rng.choice(n, p.tau, replace=False)
        c[pos] = rng.choice([-1, 1], p.tau)
        cu = np.array([negacyclic_mul(c, u[j]) for j in range(p.k + p.l)], dtype=float)
        cu[:p.l] /= nu
        out[t] = np.sqrt((cu ** 2).sum())
    return out


def phi_for_target(dim, K, log2_target=50):
    """Largest phi with 2 / (K * exact I) >= 2^log2_target (I increases with phi; bisect)."""
    i_target = 2 / (K * 2.0 ** log2_target)
    lo, hi = 1.0 + 1e-9, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2
        if betainc((dim + 1) / 2, 0.5, 1 - 1 / mid ** 2) <= i_target:
            lo = mid
        else:
            hi = mid
    return lo


def success_prob(log2_m, T, K):
    """Chance that at least one of K parallel attempts is accepted by all T parties (each 1/M)."""
    p = 2.0 ** (-T * log2_m)
    return -math.expm1(K * math.log1p(-p))


def corrected_params(p, nu, T, N, r, rp, K, log2_target=50, n=N_RING):
    """Keeps r and the paper's B, sets phi from the exact I so Thm. 3.2 gives 2^log2_target, and
    raises K until the session success probability is at least the published one.
    Returns (phi, r'_new, log2 M_new, K_new, success_old, success_new)."""
    dim = n * (p.k + p.l)
    B = bound_B(p, nu, T, N, n)
    s_old = success_prob(dim * math.log2(rp / r), T, K)
    k_new = K
    for _ in range(100):
        phi = phi_for_target(dim, k_new, log2_target)
        rp_new = math.sqrt(r * r + B * B + 2 * r * B / phi)
        lm = dim * math.log2(rp_new / r)
        s_new = success_prob(lm, T, k_new)
        if s_new >= s_old:
            return phi, rp_new, lm, k_new, s_old, s_new
        k_new = max(k_new + 1, math.ceil(k_new * math.log1p(-s_old) / math.log1p(-s_new)))
    raise RuntimeError("K did not converge")


def corrected_report(log2_target=50):
    print(f"\nCorrected parameters (exact I, Q_s = 2^{log2_target} by Thm. 3.2, paper's B and r kept):")
    for name, (nu, table) in TABLES.items():
        p = ALL[name]
        print(f"\n{name}")
        print("  (T,N)   K_pub  log2M_pub  phi_new  r'_pub   r'_new  log2M_new  K_new  K_new/K_pub"
              "  success_pub  success_new")
        for (T, N), (r, rp, K) in sorted(table.items(), key=lambda x: (x[0][1], x[0][0])):
            dim = N_RING * (p.k + p.l)
            phi, rpn, lm, kn, so, sn = corrected_params(p, nu, T, N, r, rp, K, log2_target)
            print(f"  ({T},{N}) {K:6d} {dim * math.log2(rp / r):9.3f} {phi:8.2f} {rp:8d} {rpn:8.0f}"
                  f" {lm:9.3f} {kn:6d} {kn / K:11.2f} {so:12.3f} {sn:12.3f}")


def lemma25_report():
    """Authors' script fixes phi = 7, 8, 9 (variables eta44/eta65/eta87) for ML-DSA-44/65/87."""
    print("Lemma 2.5 check (bound must be >= exact I for an upper bound):")
    for name, phi in (("ML-DSA-44", 7), ("ML-DSA-65", 8), ("ML-DSA-87", 9)):
        p = ALL[name]
        dim = N_RING * (p.k + p.l)
        print(f"  {name} dim={dim} phi={phi}: log2 exact I = {exact_I_log2(dim, phi):7.2f}, "
              f"log2 Lemma 2.5 bound = {lemma25_bound_log2(dim, phi):7.2f}")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=2000, help="samples per (T,N) for the norm check")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--corrected", action="store_true", help="only print corrected parameters")
    ap.add_argument("--target", type=int, default=50, help="log2 Q_s target for --corrected")
    args = ap.parse_args()
    if args.corrected:
        corrected_report(args.target)
        return
    rng = np.random.default_rng(args.seed)
    lemma25_report()
    for name, (nu, table) in TABLES.items():
        p = ALL[name]
        print(f"\n{name} nu={nu}")
        print("  (T,N)     K  log2M  B_paper  log2Qs(B_paper) | B_for_2^50  emp_mean  emp_sd  z(B_paper)"
              "  z(B_for_2^50)  frac>B_for_2^50 | log2Qs_typ(fit) log2Qs_typ(emp)")
        for (T, N), (r, rp, K) in sorted(table.items(), key=lambda x: (x[0][1], x[0][0])):
            B = bound_B(p, nu, T, N)
            lq, phi, lm = log2_qs(p, nu, T, N, r, rp, K, B)
            b50 = implied_B(p, K, r, rp)
            norms = sample_norms(p, nu, T, N, args.trials, rng)
            mu, sd = norms.mean(), norms.std()
            print(f"  ({T},{N}) {K:5d} {lm:6.3f} {B:8.1f} {lq:10.2f}       | {b50:9.1f} {mu:9.1f} {sd:7.1f}"
                  f" {(B - mu) / sd:9.1f} {(b50 - mu) / sd:12.1f} {np.mean(norms > b50):12.3f}"
                  f" | {log2_qs_typical(p, K, r, rp, mu, sd):10.2f}"
                  f" {-math.log2(K * np.mean([eps_of_norm(p, r, rp, v) for v in norms])):10.2f}")


if __name__ == "__main__":
    main()
