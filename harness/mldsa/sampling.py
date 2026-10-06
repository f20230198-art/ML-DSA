"""Samplers for synthetic keys and challenges (uniform stand-ins, not SHAKE-based)."""
import numpy as np

from .params import N, Params


def sample_challenges(rng, count, tau):
    """`count` sparse challenges: exactly tau coefficients in {-1,+1}, rest 0."""
    c = np.zeros((count, N), dtype=np.int64)
    pos = np.argsort(rng.random((count, N)), axis=1)[:, :tau]
    signs = rng.integers(0, 2, size=(count, tau)) * 2 - 1
    np.put_along_axis(c, pos, signs, axis=1)
    return c


def sample_secret(rng, eta, shape=(N,)):
    """Coefficients uniform in [-eta, eta] (ML-DSA secret distribution)."""
    return rng.integers(-eta, eta + 1, size=shape, dtype=np.int64)


# ---- SHAKE-based samplers of FIPS 204 (Algorithms 29-34); use hashlib ----
import hashlib

from .params import Q


def _xof(kind, data):
    h = hashlib.shake_128(data) if kind == 128 else hashlib.shake_256(data)
    return h


def _stream(kind, data, start=0, size=1024):
    """Generator of bytes from a SHAKE XOF, reading in growing chunks."""
    h = _xof(kind, data)
    pos = 0
    while True:
        chunk = h.digest(pos + size)[pos:]
        for b in chunk:
            yield b
        pos += size
        size *= 2


def rej_ntt_poly(rho34):
    """RejNTTPoly: 256 coefficients uniform mod q from SHAKE128(rho||s||r)."""
    out = []
    it = _stream(128, rho34)
    while len(out) < N:
        b0, b1, b2 = next(it), next(it), next(it)
        z = ((b2 & 127) << 16) | (b1 << 8) | b0
        if z < Q:
            out.append(z)
    return np.array(out, dtype=np.int64)


def expand_a(rho, k, l):
    """A_hat (already in NTT domain), shape (k, l, N)."""
    a = np.zeros((k, l, N), dtype=np.int64)
    for r in range(k):
        for s in range(l):
            a[r, s] = rej_ntt_poly(rho + bytes([s, r]))
    return a


def rej_bounded_poly(rho66, eta):
    out = []
    it = _stream(256, rho66)
    while len(out) < N:
        z = next(it)
        for half in (z & 15, z >> 4):
            if len(out) == N:
                break
            if eta == 2 and half < 15:
                out.append(2 - (half % 5))
            elif eta == 4 and half < 9:
                out.append(4 - half)
    return np.array(out, dtype=np.int64)


def expand_s(rho64, k, l, eta):
    s1 = np.stack([rej_bounded_poly(rho64 + r.to_bytes(2, "little"), eta) for r in range(l)])
    s2 = np.stack([rej_bounded_poly(rho64 + (r + l).to_bytes(2, "little"), eta) for r in range(k)])
    return s1, s2


def sample_in_ball(c_tilde, tau):
    h = hashlib.shake_256(c_tilde)
    stream = h.digest(8 + 4096)
    signs = int.from_bytes(stream[:8], "little")
    pos = 8
    c = np.zeros(N, dtype=np.int64)
    for i in range(N - tau, N):
        while True:
            j = stream[pos]
            pos += 1
            if j <= i:
                break
        c[i] = c[j]
        c[j] = 1 - 2 * ((signs >> (i + tau - N)) & 1)
    return c


def bit_unpack(data, a, b, count=N):
    """BitUnpack: values w = b - z with z read as bitlen(a+b)-bit little-endian chunks."""
    width = (a + b).bit_length()
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8), bitorder="little")[: width * count]
    z = bits.reshape(count, width) @ (1 << np.arange(width, dtype=np.int64))
    return b - z


def expand_mask(rho64, mu, l, gamma1):
    width = (2 * gamma1 - 1).bit_length()
    out = []
    for r in range(l):
        v = hashlib.shake_256(rho64 + (mu + r).to_bytes(2, "little")).digest(32 * width)
        out.append(bit_unpack(v, gamma1 - 1, gamma1))
    return np.stack(out)
