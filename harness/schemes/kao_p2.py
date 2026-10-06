"""Toy model of Kao's Profile P2 masking (arXiv 2601.20917v6, Sec 3.5-3.6, Remarks 11 and 15, Lemma 2).

Stage D of docs/PLAN.md. What is modelled (all over Z_q with the real ML-DSA q = 8380417, but a tiny
ring degree n and tiny module shape k x l, k > l like ML-DSA-65):

  * Shamir sharing of s1 (short) over Z_q^l, evaluation points 1..N, degree T-1.
  * Shamir nonce DKG: y = sum_i yhat_i, each party's share y_j = sum_i f_i(j); constant terms are
    short (range +-floor(gamma1/|S|)), higher coefficients are uniform in Z_q.
  * Pairwise PRF masks m_i = sum_{j>i} PRF(seed_ij) - sum_{j<i} PRF(seed_ji)   (paper Sec 3.5).
  * Round 2 value W_i = lambda_i * A * y_i + m_i, BROADCAST to everybody (the P2 model, Remark 11).
  * Round 3 response z_i = y_i + c * s1_i; the public signature carries z = sum_i lambda_i z_i.

What is NOT modelled: rejection sampling and the r0-check, hint/HighBits, the real SHAKE-based
ExpandA, the SPDZ/edaBits MPC, the blame protocol, the key DKG, multi-session statistics, and any
network or UC aspect. Challenge c is a random sparse {-1,0,1} polynomial, resampled until invertible
in R_q (the paper's protocol also retries on non-invertible c).

Two adversary views are implemented:
  * attack_individual_mask: the claim from the dossier / Remark 11. T-1 corrupted parties in S,
    so |S minus C| = 1, the honest party's mask is computable from corrupted seeds.
  * attack_aggregate: the extra observation made while building this toy. If every W_i is broadcast
    and masks cancel (Lemma 1), then anybody can sum them and obtain A*y exactly, for ANY |S minus C|.
"""
import hashlib
from dataclasses import dataclass

import numpy as np

Q = 8380417
GAMMA1 = 1 << 19


# ---------------------------------------------------------------------------------------------
# ring helpers (Z_q[X]/(X^n+1), exact integer arithmetic; n is tiny so schoolbook is fine)
# ---------------------------------------------------------------------------------------------
def pmul(a, b):
    """Negacyclic product of two length-n int arrays, reduced mod Q."""
    n = len(a)
    out = np.zeros(n, dtype=np.int64)
    for i in range(n):
        if a[i] == 0:
            continue
        for j in range(n):
            k = i + j
            term = (int(a[i]) * int(b[j])) % Q
            if k >= n:
                out[k - n] = (out[k - n] - term) % Q
            else:
                out[k] = (out[k] + term) % Q
    return out


def neg_matrix(a):
    """n x n matrix M over Z_q with M @ x = a*x (column m is a * X^m)."""
    n = len(a)
    M = np.zeros((n, n), dtype=np.int64)
    for j in range(n):
        for m in range(n):
            v = int(a[(j - m) % n])
            M[j, m] = v if m <= j else (-v) % Q
    return M % Q


def mat_vec(A, y):
    """A: (k, l, n) polynomials, y: (l, n) -> (k, n)."""
    k, l, n = A.shape
    out = np.zeros((k, n), dtype=np.int64)
    for r in range(k):
        for s in range(l):
            out[r] = (out[r] + pmul(A[r, s], y[s])) % Q
    return out


def big_matrix(A):
    """Block matrix over Z_q of the map y -> A*y, shape (k*n, l*n)."""
    k, l, n = A.shape
    B = np.zeros((k * n, l * n), dtype=np.int64)
    for r in range(k):
        for s in range(l):
            B[r * n:(r + 1) * n, s * n:(s + 1) * n] = neg_matrix(A[r, s])
    return B


def solve_mod(M, b):
    """Solve M x = b over the field Z_q. M: (rows, cols), rows >= cols. Returns x (int64) if the
    system has a unique solution (full column rank, consistent), else None."""
    rows, cols = M.shape
    aug = [[int(v) % Q for v in M[i]] + [int(b[i]) % Q] for i in range(rows)]
    piv_row = 0
    pivots = []
    for col in range(cols):
        sel = next((r for r in range(piv_row, rows) if aug[r][col]), None)
        if sel is None:
            return None                       # rank deficient: no unique solution
        aug[piv_row], aug[sel] = aug[sel], aug[piv_row]
        inv = pow(aug[piv_row][col], -1, Q)
        aug[piv_row] = [(v * inv) % Q for v in aug[piv_row]]
        for r in range(rows):
            if r != piv_row and aug[r][col]:
                f = aug[r][col]
                aug[r] = [(v - f * w) % Q for v, w in zip(aug[r], aug[piv_row])]
        pivots.append(col)
        piv_row += 1
    if any(aug[r][cols] for r in range(piv_row, rows)):
        return None                           # inconsistent
    x = np.zeros(cols, dtype=np.int64)
    for i, col in enumerate(pivots):
        x[col] = aug[i][cols]
    return x


def poly_div(num, c):
    """Solve c * x = num in R_q for a vector num of shape (m, n); None if c not invertible."""
    n = len(c)
    Mc = neg_matrix(c)
    rows = []
    for v in num:
        x = solve_mod(Mc, v)
        if x is None:
            return None
        rows.append(x)
    return np.array(rows, dtype=np.int64)


def center(x):
    x = np.asarray(x) % Q
    return np.where(x > Q // 2, x - Q, x)


# ---------------------------------------------------------------------------------------------
# protocol model
# ---------------------------------------------------------------------------------------------
def lagrange_at_zero(S):
    lam = {}
    for i in S:
        num, den = 1, 1
        for j in S:
            if j != i:
                num = num * j % Q
                den = den * (j - i) % Q
        lam[i] = num * pow(den, -1, Q) % Q
    return lam


def shamir_share(secret, N, T, rng):
    """Degree T-1 Shamir sharing of a (l, n) secret over Z_q; returns {j: share} for j = 1..N."""
    coeffs = [secret % Q] + [rng.integers(0, Q, size=secret.shape).astype(np.int64) for _ in range(T - 1)]
    out = {}
    for j in range(1, N + 1):
        acc = np.zeros_like(secret, dtype=np.int64)
        for d, cf in enumerate(coeffs):
            acc = (acc + cf * pow(j, d, Q)) % Q
        out[j] = acc
    return out


def prf(seed, session, k, n):
    stream = hashlib.shake_256(seed + session).digest(8 * k * n)
    vals = np.frombuffer(stream, dtype=np.uint64) % Q
    return vals.astype(np.int64).reshape(k, n)


def pair_masks(seeds, S, session, k, n):
    """m_i = sum_{j>i} PRF(seed_ij) - sum_{j<i} PRF(seed_ji). seeds[(i,j)] with i<j."""
    m = {i: np.zeros((k, n), dtype=np.int64) for i in S}
    for a in S:
        for b in S:
            if a < b:
                p = prf(seeds[(a, b)], session, k, n)
                m[a] = (m[a] + p) % Q
                m[b] = (m[b] - p) % Q
    return m


@dataclass
class Session:
    n: int
    k: int
    l: int
    N: int
    T: int
    S: list
    A: np.ndarray
    s1: np.ndarray            # true secret (l, n), short
    s1_sh: dict               # key shares
    seeds: dict               # pairwise seeds
    y: np.ndarray             # true nonce (secret to adversary)
    y_sh: dict                # nonce shares of parties in S
    lam: dict
    c: np.ndarray
    W: dict                   # broadcast masked commitments, party -> (k, n)
    z: np.ndarray             # public aggregate response
    session: bytes


def make_session(n=8, k=4, l=3, N=4, T=3, S=None, eta=4, tau=3, seed=0):
    """Honest execution of Kao's P2 signing transcript (no rejection sampling)."""
    rng = np.random.default_rng(seed)
    S = list(S) if S is not None else list(range(1, T + 1))
    assert len(S) >= T and len(set(S)) == len(S) and max(S) <= N
    A = rng.integers(0, Q, size=(k, l, n)).astype(np.int64)
    s1 = rng.integers(-eta, eta + 1, size=(l, n)).astype(np.int64)
    s1_sh = shamir_share(s1 % Q, N, T, rng)
    seeds = {(a, b): rng.bytes(32) for a in range(1, N + 1) for b in range(a + 1, N + 1)}
    lam = lagrange_at_zero(S)

    # Shamir nonce DKG: constant terms short in +-floor(gamma1/|S|), higher coefficients uniform
    rng_range = GAMMA1 // len(S)
    y = np.zeros((l, n), dtype=np.int64)
    y_sh = {j: np.zeros((l, n), dtype=np.int64) for j in S}
    for _ in S:
        yhat = rng.integers(-rng_range, rng_range + 1, size=(l, n)).astype(np.int64)
        y = (y + yhat) % Q
        sh = shamir_share(yhat % Q, N, T, rng)
        for j in S:
            y_sh[j] = (y_sh[j] + sh[j]) % Q
    # check: Lagrange reconstruction of the shares equals y
    rec = sum(lam[j] * y_sh[j] for j in S) % Q
    assert (rec == y % Q).all()

    session = b"toy-session-0"
    m = pair_masks(seeds, S, session, k, n)
    W = {i: (lam[i] * mat_vec(A, y_sh[i]) + m[i]) % Q for i in S}

    # challenge: sparse, resampled until invertible in R_q
    while True:
        c = np.zeros(n, dtype=np.int64)
        pos = rng.choice(n, size=tau, replace=False)
        c[pos] = rng.choice([-1, 1], size=tau)
        if poly_div(np.zeros((1, n), dtype=np.int64), c % Q) is not None:
            break
    c = c % Q
    zi = {i: (y_sh[i] + np.array([pmul(c, s1_sh[i][r]) for r in range(l)])) % Q for i in S}
    z = sum(lam[i] * zi[i] for i in S) % Q
    assert (z == (y + np.array([pmul(c, s1[r] % Q) for r in range(l)])) % Q).all()
    return Session(n, k, l, N, T, S, A, s1, s1_sh, seeds, y, y_sh, lam, c, W, z, session)


# ---------------------------------------------------------------------------------------------
# adversaries
# ---------------------------------------------------------------------------------------------
def _recover_from_Ay(sess, Ay):
    """Given exact A*y over Z_q (A injective as a Z_q-linear map), return y (l, n) or None."""
    B = big_matrix(sess.A)
    x = solve_mod(B, Ay.reshape(-1))
    return None if x is None else x.reshape(sess.l, sess.n)


def attack_aggregate(sess):
    """Uses only public broadcast data: all W_i (masks cancel in the sum), c, z, A.
    Returns recovered s1 (centered) or None."""
    Ay = sum(sess.W[i] for i in sess.S) % Q
    y = _recover_from_Ay(sess, Ay)
    if y is None:
        return None
    s1 = poly_div(((sess.z - y) % Q), sess.c)
    return None if s1 is None else center(s1)


def attack_individual_mask(sess, corrupted):
    """Remark 11 / dossier claim. `corrupted` subset of S with |S minus C| = 1 (or more; then the
    mask of an honest party is NOT computable and the attack should fail). Uses only: own key
    shares and nonce shares, seeds involving corrupted parties, broadcast W_h, c, z, A.
    Returns (s1_h_recovered, s1_recovered) or (None, None)."""
    S, C = sess.S, list(corrupted)
    H = [i for i in S if i not in C]
    h = H[0]
    k, n = sess.k, sess.n
    # adversary's best-effort mask for h: only seeds with a corrupted counterparty are known;
    # an unknown honest-honest seed is replaced by zero (adversary cannot compute it).
    known = {p: s for p, s in sess.seeds.items() if p[0] in C or p[1] in C}
    mh = np.zeros((k, n), dtype=np.int64)
    for j in S:
        if j == h:
            continue
        pair = (min(h, j), max(h, j))
        if pair not in known:
            continue
        p = prf(known[pair], sess.session, k, n)
        mh = (mh + p) % Q if h < j else (mh - p) % Q
    lam_h_Ay_h = (sess.W[h] - mh) % Q
    lam_h_y_h = _recover_from_Ay(sess, lam_h_Ay_h)
    if lam_h_y_h is None:
        return None, None
    inv_lam = pow(sess.lam[h], -1, Q)
    y_h = (lam_h_y_h * inv_lam) % Q
    # z_h from the public z and the corrupted parties' own z_j = y_j + c s1_j
    zc = np.zeros((sess.l, n), dtype=np.int64)
    for j in C:
        zj = (sess.y_sh[j] + np.array([pmul(sess.c, sess.s1_sh[j][r]) for r in range(sess.l)])) % Q
        zc = (zc + sess.lam[j] * zj) % Q
    z_h = ((sess.z - zc) % Q) * inv_lam % Q
    s1_h = poly_div((z_h - y_h) % Q, sess.c)
    if s1_h is None:
        return None, None
    # with s1_h plus the T-1 corrupted shares, interpolate s1 (needs |S| = T shares)
    pts = C + [h]
    lam_pts = lagrange_at_zero(pts)
    shares = {j: sess.s1_sh[j] for j in C}
    shares[h] = s1_h
    s1 = sum(lam_pts[j] * shares[j] for j in pts) % Q
    return s1_h, center(s1)


def share_of_true_key(sess, h):
    return sess.s1_sh[h] % Q
