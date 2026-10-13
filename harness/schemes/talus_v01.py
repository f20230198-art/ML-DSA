"""TALUS v0.1 (arXiv 2603.22109v2, Kao and Chang, 24 Mar 2026): released values per signature.

This is the version attacked by Niot (ePrint 2026/1386, received 2026-07-07). We call it "v0.1"
in this project; the arXiv record itself only has version numbers v1..v5 (v1/v2 predate Niot's
note, v3 is 2026-07-08). v1 and v2 have the same protocols; v2 adds the second author.

What is modelled, with the protocol it comes from (section numbers of 2603.22109v2):

* Offline preprocessing (Protocol 6 TEE, Protocol 13/Round 1 MPC): each signer h in S samples
  y_h uniform in [-gamma1/|S|+1, gamma1/|S|]^{n l}; aggregate y = sum_h y_h (Irwin-Hall);
  w = A y, (w1, r0) = Decompose(w). BCC check ||r0||_inf < gamma2 - beta; a failing nonce is
  discarded before any challenge is formed (nothing about it reaches a signature).
* Online signing (Protocol 7 / Protocol 16): c_tilde = H(mu || w1Encode(w1)), c = SampleInBall,
  z = y + c s1 (Shamir reconstruction gives exactly this), z-bound check, hint computed from public
  data r = A z - c t1 2^d, hint-weight check, output (c_tilde, z, h). **No r0 / LowBits(w - c s2)
  check** (Remark 5: "In TALUS, we never perform the FIPS 204 r0-check").
* TALUS-MPC broadcasts (Protocol 11 step 2 and Protocol 13 step 4): Feldman commitments A s1_i
  (once, at key generation) and Phi_{h,0} = A y_h (every preprocessing round). These are what
  Niot's first attack inverts.

Simplifications (stated, not hidden): key generation is the plain ML-DSA keygen followed by a
Shamir sharing of s1 mod q (the distribution of s1, s2, t that the DKG of Protocol 11 aims at);
the per-party nonce is sampled with numpy, not a PRF; the masked broadcast / CarryCompare MPC that
computes w1 in TALUS-MPC is replaced by computing w1 = HighBits(A y) directly (its correct output);
the 2% q = 1 (mod alpha) correction failure of Theorem 14 is not modelled; the Shamir nonce
polynomials g_h of degree T-1 are not materialised because only g_h(0) = y_h and A y_h are used.
"""
from dataclasses import dataclass, field

import numpy as np

from ..mldsa import dsa
from ..mldsa import sampling as smp
from ..mldsa.dsa import Attempt, H, c_tilde_len, inf_norm, mat_vec_hat, w1_encode
from ..mldsa.ntt import intt, ntt
from ..mldsa.params import D, Params, Q
from ..mldsa.rounding import decompose, high_bits, mod_pm
from .base import Observation, SchemeView


@dataclass
class TalusAttempt(Attempt):
    """dsa.Attempt plus the per-party nonce pieces. failed in {"", "bcc", "z_norm", "hint_weight"}.
    For a "bcc" failure there is no challenge (c, c_tilde, z are None): the nonce is dropped offline."""
    y_parts: np.ndarray = field(repr=False, default=None)   # (|S|, l, 256) centered
    phi0: np.ndarray = field(repr=False, default=None)      # (|S|, k, 256) = A y_h mod q (MPC broadcast)
    r0_w: np.ndarray = field(repr=False, default=None)      # LowBits(w) (the BCC quantity)


class TalusV01:
    """One TALUS v0.1 key with signer set S of size n_signers (threshold T = n_signers)."""

    def __init__(self, p: Params, xi: bytes, n_signers=3, seed=0):
        self.p, self.S = p, n_signers
        self.pk, self.sk, self.sec = dsa.keygen_internal(xi, p)
        self.rng = np.random.default_rng(seed)
        self.a_hat = smp.expand_a(self.sec["rho"], p.k, p.l)
        self.tr = H(self.pk, 64)
        self.s1h = ntt(self.sec["s1"])
        self.t1d_h = ntt((self.sec["t1"] << D) % Q)
        # Shamir sharing of s1 mod q (degree S-1, evaluation points 1..S)
        coeffs = self.rng.integers(0, Q, size=(n_signers - 1,) + self.sec["s1"].shape)
        self.ids = np.arange(1, n_signers + 1)
        self.s1_shares = np.stack([(self.sec["s1"] + sum(coeffs[k] * pow(int(i), k + 1, Q)
                                                          for k in range(n_signers - 1))) % Q
                                   for i in self.ids])

    # ---- TALUS-MPC key-generation broadcast (Protocol 11, Round 2) ----
    def keygen_broadcast(self):
        """Feldman commitments A s1_i for every party (public to any observer)."""
        return np.stack([intt(mat_vec_hat(self.a_hat, ntt(s))) for s in self.s1_shares])

    def sign(self, message: bytes, max_attempts=1000):
        """Return (sig bytes or None, list of TalusAttempt)."""
        p = self.p
        mp = bytes([0, 0]) + message
        mu = H(self.tr + mp, 64)
        bound = p.gamma1 // self.S
        attempts = []
        for kappa in range(max_attempts):
            y_parts = self.rng.integers(-bound + 1, bound + 1, size=(self.S, p.l, 256), dtype=np.int64)
            y = y_parts.sum(axis=0)
            phi0 = intt(np.stack([mat_vec_hat(self.a_hat, ntt(yp)) for yp in y_parts]))
            w = phi0.sum(axis=0) % Q
            w1, r0w = decompose(w, p.gamma2)
            if int(np.abs(r0w).max()) >= p.gamma2 - p.beta:
                attempts.append(TalusAttempt(kappa, None, None, w1, None, "bcc", y, None, None,
                                             y_parts, phi0, r0w))
                continue
            c_tilde = H(mu + w1_encode(w1, p), c_tilde_len(p))
            c = smp.sample_in_ball(c_tilde, p.tau)
            ch = ntt(c)
            z = mod_pm((y + intt((ch[None, :] * self.s1h) % Q)) % Q, Q)
            failed, h = "", None
            if inf_norm(z) >= p.gamma1 - p.beta:
                failed = "z_norm"
            else:
                r = intt((mat_vec_hat(self.a_hat, ntt(z)) - (ch[None, :] * self.t1d_h) % Q) % Q)
                h = (high_bits(r, p.gamma2) != w1).astype(np.int64)
                if int(h.sum()) > p.omega:
                    failed = "hint_weight"
            attempts.append(TalusAttempt(kappa, c_tilde, c, w1, z, failed, y, None, h,
                                         y_parts, phi0, r0w))
            if not failed:
                return dsa.sig_encode(c_tilde, z, h, p), attempts
        return None, attempts


class TalusV01SigView(SchemeView):
    """Any observer (TALUS-TEE and TALUS-MPC): the signature (c_tilde, z, h) plus the broadcast w1.
    Failed attempts release nothing (BCC failures are offline; z/hint aborts restart preprocessing)."""
    name = "talus-v0.1-sig"

    def observe(self, a: Attempt):
        if a.failed:
            return None
        return Observation(self.name, self.adversary, True,
                           dict(c_tilde=a.c_tilde, c=a.c, z=a.z, h=a.h, w1=a.w1))


class TalusV01MPCView(TalusV01SigView):
    """Passive observer of TALUS-MPC: additionally the Round-1 Feldman commitments Phi_{h,0} = A y_h."""
    name = "talus-v0.1-mpc"

    def observe(self, a: Attempt):
        o = super().observe(a)
        if o is not None:
            o.fields["phi0"] = a.phi0
        return o


# ---------------------------------------------------------------- Niot attack 1 (linear algebra)
def _solve_mod_q(M, b):
    """Solve M x = b over Z_q for M (k, l) of full column rank; returns x (l,) or None."""
    k, l = M.shape
    A = np.concatenate([M % Q, (b % Q)[:, None]], axis=1).astype(object)
    row = 0
    piv = []
    for col in range(l):
        r = next((i for i in range(row, k) if A[i, col] % Q), None)
        if r is None:
            return None
        A[[row, r]] = A[[r, row]]
        inv = pow(int(A[row, col]), -1, Q)
        A[row] = (A[row] * inv) % Q
        for i in range(k):
            if i != row and A[i, col]:
                A[i] = (A[i] - A[i, col] * A[row]) % Q
        piv.append(col)
        row += 1
    if any(A[i, l] % Q for i in range(row, k)):
        return None    # inconsistent: b not in the image of M
    return np.array([int(A[i, l]) for i in range(l)], dtype=np.int64)


def invert_A(a_hat, v):
    """Given v = A x (normal domain, (k, 256)), return x mod q (l, 256) or None (A not left-invertible
    in some NTT slot; Niot bounds this by 2^-15 at ML-DSA-44)."""
    vh = ntt(v)
    xh = np.zeros((a_hat.shape[1], 256), dtype=np.int64)
    for j in range(256):
        sol = _solve_mod_q(a_hat[:, :, j], vh[:, j])
        if sol is None:
            return None
        xh[:, j] = sol
    return intt(xh)


def attack1_keygen(a_hat, commitments, ids):
    """Recover s1 from the KeyGen broadcast {A s1_i}: invert each, Lagrange-interpolate at 0."""
    shares = [invert_A(a_hat, v) for v in commitments]
    if any(s is None for s in shares):
        return None
    s1 = np.zeros_like(shares[0])
    for i, si in zip(ids, shares):
        lam = 1
        for j in ids:
            if j != i:
                lam = lam * j * pow(int(j - i), -1, Q) % Q
        s1 = (s1 + lam * si) % Q
    return mod_pm(s1, Q)


def attack1_nonce(a_hat, obs: Observation):
    """Recover s1 from ONE MPC signature: y = sum_h A^+ Phi_{h,0}, then s1 = c^-1 (z - y)."""
    ys = [invert_A(a_hat, phi) for phi in obs.fields["phi0"]]
    if any(v is None for v in ys):
        return None
    y = mod_pm(sum(ys) % Q, Q)
    ch = ntt(obs.fields["c"])
    if (ch == 0).any():
        return None
    inv = np.array([pow(int(x), -1, Q) for x in ch], dtype=np.int64)
    s1 = intt((ntt((obs.fields["z"] - y) % Q) * inv[None, :]) % Q)
    return mod_pm(s1, Q)


# ---------------------------------------------------------------- Niot attack 2 (ILWE on s2 - t0)
def s2_channel(p: Params, a_hat, t1, obs: Observation):
    """Public observable b = (A z - c t1 2^d) - 2 gamma2 w1 (centered mod q), shape (k, 256).
    Algebra: b = r0 - c (s2 - t0) with r0 = LowBits(w) uniform on (-(gamma2-beta), gamma2-beta)
    under BCC. Because v0.1 has no r0-check, every BCC nonce gives a signature."""
    f = obs.fields
    ch = ntt(f["c"])
    r = intt((mat_vec_hat(a_hat, ntt(f["z"] % Q)) - (ch[None, :] * ntt((t1 << D) % Q)) % Q) % Q)
    return mod_pm(r - 2 * p.gamma2 * f["w1"], Q)
