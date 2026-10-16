"""Kao Profile P2 (arXiv 2601.20917v6) at real ML-DSA size: end-to-end demo of the broadcast-W_i leak.

Paper plan item 7. Builds on the toy in kao_p2.py but uses the real ML-DSA parameter sets, real
ExpandA/SampleInBall/HighBits/hints from harness.mldsa, and a verifier that is the unmodified FIPS 204
Verify of this repository. The threshold layer follows Sec. 3.5-3.6 and Alg. 3 of the paper:

  * key: Shamir sharing of s1 over Z_q (degree T-1, uniform higher coefficients), points 1..N;
  * nonce: every party i picks a short constant term yhat_i (|.| <= floor(gamma1 / |S|)), shares it with a
    degree T-1 polynomial; party j's nonce share is y_j = sum_i f_i(j); y = sum_i yhat_i;
  * W_i = lambda_i * A * y_i + m_i with pairwise SHAKE-256 PRF masks m_i that cancel (Lemma 1);
    in P2 every W_i is BROADCAST (Fig. 1b, Remark 11, App. M.1);
  * combiner: w = sum W_i, w1 = HighBits(w), c~ = H(mu || w1), z_i = y_i + c s1_i, z = sum lambda_i z_i.

Simplification (stated, not hidden): the rejection checks (z norm, r0, ct0, hint weight) are evaluated in
the clear from the dealer's secret, standing in for the paper's r0-check MPC. Failed attempts are retried
with fresh nonces. This does not change the accepted transcript, which is all the attack uses.

The attacker sees only: pk, message, the FIPS 204 signature (c~, z, h) and the broadcast values W_i of the
accepted attempt. It computes w = sum W_i (= A y, masks cancel), solves A y = w slot by slot in the NTT
domain, then s1 = c^-1 (z - y).
"""
import hashlib
from dataclasses import dataclass

import numpy as np

from ..mldsa import dsa
from ..mldsa import sampling as smp
from ..mldsa.hints import make_hint
from ..mldsa.ntt import intt, ntt
from ..mldsa.params import N, Q
from ..mldsa.rounding import high_bits, low_bits, mod_pm


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


def shamir(secret, n_parties, T, rng):
    """secret (...,) int array -> dict party -> share (same shape), degree T-1 over Z_q."""
    coeffs = [rng.integers(0, Q, size=secret.shape, dtype=np.int64) for _ in range(T - 1)]
    out = {}
    for j in range(1, n_parties + 1):
        v = secret % Q
        for d, cf in enumerate(coeffs, start=1):
            v = (v + cf * pow(j, d, Q)) % Q
        out[j] = v
    return out


def prf_mask(seed, session, k):
    stream = hashlib.shake_256(seed + session).digest(k * N * 4)
    v = np.frombuffer(stream, dtype=np.uint32).astype(np.int64) % Q
    return v.reshape(k, N)


def mat_vec(a_hat, y):
    """A y mod q, a_hat (k,l,N) in NTT domain, y (l,N) coefficient domain."""
    return intt(dsa.mat_vec_hat(a_hat, ntt(y % Q)))


@dataclass
class Transcript:
    pk: bytes
    message: bytes
    signature: bytes
    broadcast: dict          # party -> W_i (k, N) mod q
    S: list
    attempts: int


class KaoP2:
    def __init__(self, p, n_parties, T, seed):
        assert 2 <= T <= n_parties
        self.p, self.n, self.T = p, n_parties, T
        self.rng = np.random.default_rng(seed)
        xi = bytes(self.rng.integers(0, 256, 32, dtype=np.uint8))
        self.pk, self.sk, self.secret = dsa.keygen_internal(xi, p)
        s = self.secret
        self.a_hat = smp.expand_a(s["rho"], p.k, p.l)
        self.s1_shares = shamir(s["s1"] % Q, n_parties, T, self.rng)
        self.seeds = {(i, j): bytes(self.rng.integers(0, 256, 32, dtype=np.uint8))
                      for i in range(1, n_parties + 1) for j in range(i + 1, n_parties + 1)}
        self.sessions = 0

    def _nonce_dkg(self, S):
        p = self.p
        rng = self.rng
        bound = p.gamma1 // len(S)
        y = np.zeros((p.l, N), dtype=np.int64)
        shares = {j: np.zeros((p.l, N), dtype=np.int64) for j in S}
        for _ in S:
            yhat = rng.integers(-bound, bound + 1, size=(p.l, N), dtype=np.int64)
            y += yhat
            sh = shamir(yhat % Q, self.n, self.T, rng)
            for j in S:
                shares[j] = (shares[j] + sh[j]) % Q
        return y, shares

    def sign(self, message, S, max_attempts=500):
        p = self.p
        S = sorted(S)
        assert len(S) >= self.T
        lam = lagrange_at_zero(S)
        sec = self.secret
        mu = dsa.H(sec["tr"] + bytes([0, 0]) + message, 64)
        for attempt in range(1, max_attempts + 1):
            self.sessions += 1
            session = self.sessions.to_bytes(8, "little")
            y, ysh = self._nonce_dkg(S)
            W = {}
            for i in S:
                m = np.zeros((p.k, N), dtype=np.int64)
                for j in S:
                    if j > i:
                        m = (m + prf_mask(self.seeds[(i, j)], session, p.k)) % Q
                    elif j < i:
                        m = (m - prf_mask(self.seeds[(j, i)], session, p.k)) % Q
                W[i] = (lam[i] * mat_vec(self.a_hat, ysh[i]) + m) % Q
            w = sum(W.values()) % Q
            w1 = high_bits(w, p.gamma2)
            c_tilde = dsa.H(mu + dsa.w1_encode(w1, p), dsa.c_tilde_len(p))
            c = smp.sample_in_ball(c_tilde, p.tau)
            ch = ntt(c)
            z = np.zeros((p.l, N), dtype=np.int64)
            for i in S:
                zi = (ysh[i] + intt((ch[None, :] * ntt(self.s1_shares[i])) % Q)) % Q
                z = (z + lam[i] * zi) % Q
            # rejection checks in the clear (stand-in for the r0-check MPC)
            cs2 = intt((ch[None, :] * ntt(sec["s2"] % Q)) % Q)
            ct0 = intt((ch[None, :] * ntt(sec["t0"] % Q)) % Q)
            if dsa.inf_norm(z) >= p.gamma1 - p.beta:
                continue
            if int(np.abs(low_bits((w - cs2) % Q, p.gamma2)).max()) >= p.gamma2 - p.beta:
                continue
            if dsa.inf_norm(ct0) >= p.gamma2:
                continue
            h = make_hint((-ct0) % Q, (w - cs2 + ct0) % Q, p.gamma2)
            if int(h.sum()) > p.omega:
                continue
            sig = dsa.sig_encode(c_tilde, mod_pm(z, Q), h, p)
            return Transcript(self.pk, message, sig, W, S, attempt)
        raise RuntimeError("no accepted attempt")


def _solve_slots(a_hat, w_hat):
    """For each NTT slot solve A_slot y_slot = w_slot over Z_q (k x l, k >= l). Returns (l, N) or None."""
    k, l, n = a_hat.shape
    out = np.zeros((l, n), dtype=np.int64)
    for s in range(n):
        aug = [[int(a_hat[r, c, s]) for c in range(l)] + [int(w_hat[r, s])] for r in range(k)]
        row = 0
        for col in range(l):
            sel = next((r for r in range(row, k) if aug[r][col] % Q), None)
            if sel is None:
                return None
            aug[row], aug[sel] = aug[sel], aug[row]
            inv = pow(aug[row][col], -1, Q)
            aug[row] = [v * inv % Q for v in aug[row]]
            for r in range(k):
                if r != row and aug[r][col] % Q:
                    f = aug[r][col]
                    aug[r] = [(v - f * u) % Q for v, u in zip(aug[r], aug[row])]
            row += 1
        if any(aug[r][l] % Q for r in range(l, k)):
            return None
        for c in range(l):
            out[c, s] = aug[c][l]
    return out


def attack_from_broadcast(p, tr, broadcast_values):
    """Recover s1 from public data only. broadcast_values: iterable of the observed W_i.
    Returns centered s1 (l, N) or None (non-invertible slot / inconsistent)."""
    rho, t1 = dsa.pk_decode(tr.pk, p)
    a_hat = smp.expand_a(rho, p.k, p.l)
    c_tilde, z, h = dsa.sig_decode(tr.signature, p)
    c = smp.sample_in_ball(c_tilde, p.tau)
    w = sum(broadcast_values) % Q
    y_hat = _solve_slots(a_hat, ntt(w))
    if y_hat is None:
        return None
    cs1_hat = (ntt(z % Q) - y_hat) % Q
    ch = ntt(c)
    if (ch % Q == 0).any():
        return None
    inv = np.array([pow(int(v), -1, Q) for v in ch], dtype=np.int64)
    s1 = intt((cs1_hat * inv[None, :]) % Q)
    return mod_pm(s1, Q)


def consistent_with_pk(p, pk, s1):
    """Public check that s1 is the key: A s1 - t1 2^d must be s2 - t0, so within eta + 2^(d-1)."""
    rho, t1 = dsa.pk_decode(pk, p)
    a_hat = smp.expand_a(rho, p.k, p.l)
    r = mod_pm((mat_vec(a_hat, s1 % Q) - (t1 << 13)) % Q, Q)
    return int(np.abs(r).max()) <= p.eta + (1 << 12), (int(np.abs(s1).max()) <= p.eta)
