"""Bounded-noise (edge-aware) estimators for b = -A x + e with |e_i| <= B.

Works over Z[X]/(X^n+1) for any n so the ring dimension can be scaled down.
`chebyshev` solves min_x max_i |b_i + (A x)_i| as one linear program: for
uniform noise this is the maximum-likelihood estimate and it uses the hard
edges of the noise, which least squares ignores.
"""
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog

from ..mldsa.ringn import Ring, constraint_rows, get_ring


def negacyclic_rows(c):
    """Stack the n x n negacyclic matrices of the challenges c (count, n) into a sparse (count*n, n)."""
    count, n = c.shape
    rows, cols, vals = [], [], []
    for i in range(count):
        nz = np.flatnonzero(c[i])
        for p in nz:
            # coefficient c[p] * X^p maps s_k to row (k+p) mod n with sign -1 on wrap
            k = np.arange(n)
            r = (k + p) % n
            sign = np.where(k + p >= n, -1, 1)
            rows.append(i * n + r)
            cols.append(k)
            vals.append(c[i, p] * sign)
    return sp.csr_matrix(
        (np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
        shape=(count * n, n),
    )


def least_squares_dense(A, b):
    x, *_ = np.linalg.lstsq(A.toarray(), b, rcond=None)
    return x


def residual(c, b, x, chunk=2048):
    """Yield (start, r) blocks of r = b + c*x (ring product), without forming the big matrix."""
    ring = get_ring(c.shape[1])
    for start in range(0, len(c), chunk):
        sl = slice(start, start + chunk)
        yield start, b[sl].astype(float) + ring.mul(c[sl], x)


def max_abs_residual(c, b, x, chunk=2048):
    return max(float(np.abs(r).max()) for _, r in residual(c, b, x, chunk))


def is_feasible(c, b, x, bound, chunk=2048):
    """True if x explains every observation with noise inside [-bound, bound] (certificate check)."""
    return max_abs_residual(c, b, x, chunk) <= bound + 1e-6


def least_squares_cg(c, b, iters=25, chunk=2048):
    """min ||b + c*x||_2 by conjugate gradient on the normal equations (ring products only)."""
    ring = get_ring(c.shape[1])
    adj = Ring.adjoint

    def normal(v):
        out = np.zeros_like(v)
        for i in range(0, len(c), chunk):
            ci = c[i:i + chunk]
            out += ring.mul(adj(ci), ring.mul(ci, v)).sum(axis=0)
        return out

    rhs = np.zeros(c.shape[1])
    for i in range(0, len(c), chunk):
        rhs -= ring.mul(adj(c[i:i + chunk]), b[i:i + chunk].astype(float)).sum(axis=0)
    x = np.zeros_like(rhs)
    r = rhs.copy()
    p = r.copy()
    rs = r @ r
    for _ in range(iters):
        if rs < 1e-12:
            break
        ap = normal(p)
        alpha = rs / (p @ ap)
        x += alpha * p
        r -= alpha * ap
        rs_new = r @ r
        p = r + (rs_new / rs) * p
        rs = rs_new
    return x


def chebyshev_cutting_plane(c, b, box, rng, init_rows=None, add=None, max_iter=80,
                            tol=1e-6, chunk=2048):
    """Memory-light min_x max |b + c*x| (Chebyshev / uniform-noise MLE) by constraint generation.

    Solves the LP on a small working set of rows, evaluates the true residual with ring
    products, adds the most violated rows, repeats. Only O(n) rows are ever stored, so the
    full-size ring (n = 256, N in the hundreds of thousands) fits in memory.

    box: |x_k| <= box (keeps the LP bounded; use the secret's range, e.g. eta or 2^12 + eta).
    Returns (x, t, info) with t the working-set optimum (a lower bound on the true optimum),
    info = dict(iters, converged, rows, max_residual).
    """
    count, n = c.shape
    init_rows = init_rows or 8 * n
    add = add or 2 * n
    seen = set()

    def new_rows(i, j):
        keep = [(a, b_) for a, b_ in zip(i.tolist(), j.tolist()) if (a, b_) not in seen]
        seen.update(keep)
        if not keep:
            return None, None
        ii = np.array([a for a, _ in keep])
        jj = np.array([b_ for _, b_ in keep])
        return constraint_rows(c, ii, jj), b[ii, jj].astype(float)

    i0 = rng.integers(0, count, size=init_rows)
    j0 = rng.integers(0, n, size=init_rows)
    rows, rhs = new_rows(i0, j0)
    x = np.zeros(n)
    t = 0.0
    for it in range(1, max_iter + 1):
        m = len(rows)
        ones = np.ones((m, 1))
        a_ub = np.vstack([np.hstack([rows, -ones]), np.hstack([-rows, -ones])])
        b_ub = np.concatenate([-rhs, rhs])
        cost = np.zeros(n + 1)
        cost[-1] = 1.0
        bounds = [(-box, box)] * n + [(0, None)]
        res = linprog(cost, A_ub=a_ub, b_ub=b_ub, bounds=bounds, method="highs")
        if res.status != 0:
            raise RuntimeError(res.message)
        x, t = res.x[:n], res.x[-1]

        # find the most violated rows over all observations
        cand_val, cand_i, cand_j = [], [], []
        top = 0.0
        for start, r in residual(c, b, x, chunk):
            a = np.abs(r)
            top = max(top, float(a.max()))
            flat = a.ravel()
            k = min(add, flat.size)
            sel = np.argpartition(flat, -k)[-k:]
            cand_val.append(flat[sel])
            cand_i.append(start + sel // n)
            cand_j.append(sel % n)
        if top <= t + tol:
            return x, t, dict(iters=it, converged=True, rows=len(rows), max_residual=top)
        vals = np.concatenate(cand_val)
        order = np.argsort(vals)[-add:]
        new_r, new_h = new_rows(np.concatenate(cand_i)[order], np.concatenate(cand_j)[order])
        if new_r is None:
            return x, t, dict(iters=it, converged=True, rows=len(rows), max_residual=top)
        rows = np.vstack([rows, new_r])
        rhs = np.concatenate([rhs, new_h])
    return x, t, dict(iters=max_iter, converged=False, rows=len(rows), max_residual=top)


def round_to_range(x, target_max):
    """Round to integers and clip to the known range of the secret."""
    return np.clip(np.rint(x), -target_max, target_max)


def chebyshev(A, b):
    """min_x ||b + A x||_inf via LP. Returns (x, t) with t the minimal sup residual."""
    m, n = A.shape
    ones = sp.csr_matrix(np.ones((m, 1)))
    a_ub = sp.vstack([sp.hstack([A, -ones]), sp.hstack([-A, -ones])]).tocsr()
    b_ub = np.concatenate([-b, b])
    cost = np.zeros(n + 1)
    cost[-1] = 1.0
    bounds = [(None, None)] * n + [(0, None)]
    res = linprog(cost, A_ub=a_ub, b_ub=b_ub, bounds=bounds, method="highs")
    if res.status != 0:
        raise RuntimeError(res.message)
    return res.x[:n], res.x[-1]


def least_squares_fft(c, b, chunk=4096):
    """Exact min ||b + c*x||_2 in one pass. In the twisted-FFT domain the normal equations are
    diagonal: x_hat_k = -sum_i conj(c_hat_ik) b_hat_ik / sum_i |c_hat_ik|^2. No iteration."""
    count, n = c.shape
    psi = get_ring(n)._psi
    m = np.zeros(n)
    r = np.zeros(n, dtype=complex)
    for start in range(0, count, chunk):
        ch = np.fft.fft(c[start:start + chunk].astype(float) * psi, axis=-1)
        bh = np.fft.fft(b[start:start + chunk].astype(float) * psi, axis=-1)
        m += (ch.real ** 2 + ch.imag ** 2).sum(axis=0)
        r += (ch.conj() * bh).sum(axis=0)
    return (np.fft.ifft(-r / m) * np.conj(psi)).real
