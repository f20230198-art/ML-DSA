"""Reference ML-DSA (FIPS 204) for leakage experiments. Not constant time, not for production.

`sign_internal(..., record=True)` returns every signing attempt (accepted and rejected) with the
check that failed, which is what the threshold-scheme transcript models need.
"""
import hashlib
from dataclasses import dataclass, field

import numpy as np

from . import sampling as smp
from .hints import make_hint, use_hint
from .ntt import intt, ntt
from .params import D, N, Params, Q
from .rounding import high_bits, low_bits, mod_pm, power2round


def H(data, n):
    return hashlib.shake_256(data).digest(n)


def c_tilde_len(p: Params):
    return {"ML-DSA-44": 32, "ML-DSA-65": 48, "ML-DSA-87": 64}[p.name]


# ---- bit packing ----
def bit_pack(w, a, b):
    """BitPack: coefficients in [-a, b], stored as b - w in bitlen(a+b) bits, little-endian."""
    width = (a + b).bit_length()
    z = (b - np.asarray(w, dtype=np.int64).ravel()).astype(np.int64)
    bits = ((z[:, None] >> np.arange(width)) & 1).astype(np.uint8).ravel()
    return np.packbits(bits, bitorder="little").tobytes()


def simple_bit_pack(w, b):
    width = b.bit_length()
    z = np.asarray(w, dtype=np.int64).ravel()
    bits = ((z[:, None] >> np.arange(width)) & 1).astype(np.uint8).ravel()
    return np.packbits(bits, bitorder="little").tobytes()


def simple_bit_unpack(data, b, count=N):
    width = b.bit_length()
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8), bitorder="little")[: width * count]
    return bits.reshape(count, width) @ (1 << np.arange(width, dtype=np.int64))


def hint_bit_pack(h, p: Params):
    y = bytearray(p.omega + p.k)
    index = 0
    for i in range(p.k):
        for j in np.nonzero(h[i])[0]:
            y[index] = int(j)
            index += 1
        y[p.omega + i] = index
    return bytes(y)


def hint_bit_unpack(y, p: Params):
    """Returns the hint array, or None if the encoding is malformed."""
    h = np.zeros((p.k, N), dtype=np.int64)
    index = 0
    for i in range(p.k):
        end = y[p.omega + i]
        if end < index or end > p.omega:
            return None
        first = index
        while index < end:
            if index > first and y[index - 1] >= y[index]:
                return None
            h[i, y[index]] = 1
            index += 1
    if any(y[index:p.omega]):
        return None
    return h


def w1_encode(w1, p: Params):
    b = (Q - 1) // (2 * p.gamma2) - 1
    return b"".join(simple_bit_pack(w1[i], b) for i in range(p.k))


def pk_encode(rho, t1):
    return rho + b"".join(simple_bit_pack(t1[i], (1 << 10) - 1) for i in range(len(t1)))


def pk_decode(pk, p: Params):
    rho = pk[:32]
    sz = 320
    t1 = np.stack([simple_bit_unpack(pk[32 + i * sz:32 + (i + 1) * sz], (1 << 10) - 1) for i in range(p.k)])
    return rho, t1


def sk_encode(rho, K, tr, s1, s2, t0, p: Params):
    out = rho + K + tr
    out += b"".join(bit_pack(s, p.eta, p.eta) for s in s1)
    out += b"".join(bit_pack(s, p.eta, p.eta) for s in s2)
    out += b"".join(bit_pack(t, (1 << (D - 1)) - 1, 1 << (D - 1)) for t in t0)
    return out


def sk_decode(sk, p: Params):
    rho, K, tr = sk[:32], sk[32:64], sk[64:128]
    pos = 128
    w = (2 * p.eta).bit_length()
    sl = 32 * w
    s1 = np.stack([smp.bit_unpack(sk[pos + i * sl:pos + (i + 1) * sl], p.eta, p.eta) for i in range(p.l)])
    pos += p.l * sl
    s2 = np.stack([smp.bit_unpack(sk[pos + i * sl:pos + (i + 1) * sl], p.eta, p.eta) for i in range(p.k)])
    pos += p.k * sl
    tl = 32 * D
    t0 = np.stack([smp.bit_unpack(sk[pos + i * tl:pos + (i + 1) * tl], (1 << (D - 1)) - 1, 1 << (D - 1))
                   for i in range(p.k)])
    return rho, K, tr, s1, s2, t0


def sig_encode(c_tilde, z, h, p: Params):
    return c_tilde + b"".join(bit_pack(z[i], p.gamma1 - 1, p.gamma1) for i in range(p.l)) + hint_bit_pack(h, p)


def sig_decode(sig, p: Params):
    ct = c_tilde_len(p)
    c_tilde = sig[:ct]
    zl = 32 * (2 * p.gamma1 - 1).bit_length()
    z = np.stack([smp.bit_unpack(sig[ct + i * zl:ct + (i + 1) * zl], p.gamma1 - 1, p.gamma1)
                  for i in range(p.l)])
    h = hint_bit_unpack(sig[ct + p.l * zl:], p)
    return c_tilde, z, h


# ---- helpers ----
def mat_vec_hat(a_hat, v_hat):
    """A_hat (k,l,N) times v_hat (l,N), all in the NTT domain, result in the NTT domain mod q."""
    return ((a_hat * v_hat[None, :, :]) % Q).sum(axis=1) % Q


def inf_norm(v):
    return int(np.abs(mod_pm(v, Q)).max())


def keygen_internal(xi, p: Params):
    """Returns (pk, sk, secret) where secret holds the unpacked values for experiments."""
    seed = H(xi + bytes([p.k, p.l]), 128)
    rho, rho_p, K = seed[:32], seed[32:96], seed[96:]
    a_hat = smp.expand_a(rho, p.k, p.l)
    s1, s2 = smp.expand_s(rho_p, p.k, p.l, p.eta)
    t = (intt(mat_vec_hat(a_hat, ntt(s1))) + s2) % Q
    t1, t0 = power2round(t)
    pk = pk_encode(rho, t1)
    tr = H(pk, 64)
    sk = sk_encode(rho, K, tr, s1, s2, t0, p)
    return pk, sk, dict(rho=rho, K=K, tr=tr, s1=s1, s2=s2, t0=t0, t1=t1, t=t)


@dataclass
class Attempt:
    kappa: int
    c_tilde: bytes
    c: np.ndarray
    w1: np.ndarray
    z: np.ndarray            # y + c*s1 over Z_q (centered)
    failed: str              # "" if accepted, else "z_norm", "r0_norm", "ct0_norm" or "hint_weight"
    y: np.ndarray = field(repr=False, default=None)
    r0: np.ndarray = field(repr=False, default=None)  # LowBits(w - c*s2)
    h: np.ndarray = field(repr=False, default=None)


def sign_internal(sk, m_prime, rnd, p: Params, record=False, max_attempts=10000):
    rho, K, tr, s1, s2, t0 = sk_decode(sk, p)
    s1h, s2h, t0h = ntt(s1), ntt(s2), ntt(t0)
    a_hat = smp.expand_a(rho, p.k, p.l)
    mu = H(tr + m_prime, 64)
    rho2 = H(K + rnd + mu, 64)
    kappa = 0
    attempts = []
    for _ in range(max_attempts):
        y = smp.expand_mask(rho2, kappa, p.l, p.gamma1)
        w = intt(mat_vec_hat(a_hat, ntt(y)))
        w1 = high_bits(w, p.gamma2)
        c_tilde = H(mu + w1_encode(w1, p), c_tilde_len(p))
        c = smp.sample_in_ball(c_tilde, p.tau)
        ch = ntt(c)
        cs1 = intt((ch[None, :] * s1h) % Q)
        cs2 = intt((ch[None, :] * s2h) % Q)
        z = (y + cs1) % Q
        r0 = low_bits((w - cs2) % Q, p.gamma2)
        failed, h = "", None
        if inf_norm(z) >= p.gamma1 - p.beta:
            failed = "z_norm"
        elif int(np.abs(r0).max()) >= p.gamma2 - p.beta:
            failed = "r0_norm"
        else:
            ct0 = intt((ch[None, :] * t0h) % Q)
            h = make_hint((-ct0) % Q, (w - cs2 + ct0) % Q, p.gamma2)
            if inf_norm(ct0) >= p.gamma2:
                failed = "ct0_norm"
            elif int(h.sum()) > p.omega:
                failed = "hint_weight"
        if record:
            attempts.append(Attempt(kappa, c_tilde, c, w1, mod_pm(z, Q), failed, y, r0, h))
        kappa += p.l
        if not failed:
            return sig_encode(c_tilde, mod_pm(z, Q), h, p), attempts
    raise RuntimeError("no accepted attempt")


def verify_internal(pk, m_prime, sig, p: Params):
    if len(sig) != c_tilde_len(p) + p.l * 32 * (2 * p.gamma1 - 1).bit_length() + p.omega + p.k:
        return False
    rho, t1 = pk_decode(pk, p)
    c_tilde, z, h = sig_decode(sig, p)
    if h is None:
        return False
    a_hat = smp.expand_a(rho, p.k, p.l)
    tr = H(pk, 64)
    mu = H(tr + m_prime, 64)
    c = smp.sample_in_ball(c_tilde, p.tau)
    zm = z % Q
    wa = intt((mat_vec_hat(a_hat, ntt(zm)) - (ntt(c)[None, :] * ntt((t1 << D) % Q)) % Q) % Q)
    w1 = use_hint(h, wa, p.gamma2)
    ok_norm = int(np.abs(z).max()) < p.gamma1 - p.beta
    return ok_norm and c_tilde == H(mu + w1_encode(w1, p), c_tilde_len(p))


def keygen(p: Params, rng_bytes):
    return keygen_internal(rng_bytes(32), p)


def sign(sk, message, p: Params, ctx=b"", rnd=bytes(32), record=False):
    """Pure ML-DSA signing; rnd = 32 zero bytes gives the deterministic variant."""
    mp = bytes([0, len(ctx)]) + ctx + message
    return sign_internal(sk, mp, rnd, p, record)


def verify(pk, message, sig, p: Params, ctx=b""):
    return verify_internal(pk, bytes([0, len(ctx)]) + ctx + message, sig, p)
