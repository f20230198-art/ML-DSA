"""Least-squares estimator for b_i = -c_i*s + e_i over Z[X]/(X^256+1).

The system matrix is stacked negacyclic matrices of c_i. Solved by conjugate
gradient on the normal equations using ring products, so no matrix is built.
"""
import numpy as np

from ..mldsa.ring import adjoint, negacyclic_mul


def _normal_apply(c, x, chunk):
    out = np.zeros_like(x, dtype=float)
    for i in range(0, len(c), chunk):
        ci = c[i:i + chunk]
        out += negacyclic_mul(adjoint(ci), negacyclic_mul(ci, x)).sum(axis=0)
    return out


def matched_filter(c, b, chunk=4096):
    """Plain correlation estimate: -(sum_i adj(c_i)*b_i) / (count * tau)."""
    tau = np.count_nonzero(c[0])
    acc = np.zeros(c.shape[1])
    for i in range(0, len(c), chunk):
        acc += negacyclic_mul(adjoint(c[i:i + chunk]), b[i:i + chunk]).sum(axis=0)
    return -acc / (len(c) * tau)


def least_squares(c, b, iters=15, chunk=4096):
    """Exact least squares (CG on the normal equations), started from the matched filter."""
    rhs = np.zeros(c.shape[1])
    for i in range(0, len(c), chunk):
        rhs -= negacyclic_mul(adjoint(c[i:i + chunk]), b[i:i + chunk]).sum(axis=0)
    x = matched_filter(c, b, chunk)
    r = rhs - _normal_apply(c, x, chunk)
    p = r.copy()
    rs = r @ r
    for _ in range(iters):
        if rs < 1e-12:
            break
        ap = _normal_apply(c, p, chunk)
        alpha = rs / (p @ ap)
        x = x + alpha * p
        r = r - alpha * ap
        rs_new = r @ r
        p = r + (rs_new / rs) * p
        rs = rs_new
    return x
