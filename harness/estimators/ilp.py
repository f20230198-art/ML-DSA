"""Integer finishing step after the edge (Chebyshev LP) estimator.

The LP gives a real vector x close to the secret s. Plain rounding fails as soon as one of the n
coefficients is off by more than 1/2. Here each coefficient k may take any integer in
[x_k - window, x_k + window] intersected with the known secret range [-T, T]; coefficients with a
single candidate are fixed ("decided"), the rest are solved by a mixed-integer program

    minimise t  subject to  |b + A z| <= t  (all rows),  z integer in the candidate box,

i.e. the integer Chebyshev fit. For uniform noise every integer point with t <= bound is equally
likely; picking the smallest t is a tie-break, so a finish can still be wrong if the integer
feasible set is not a single point. Rows are added by constraint generation (only violated rows
enter the MILP), so the big N*n system is never built.
"""

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from ..mldsa.ringn import constraint_rows
from .edge import residual


def candidate_box(x, target_max, window=1.0):
    lo = np.maximum(np.ceil(x - window - 1e-9), -target_max).astype(np.int64)
    hi = np.minimum(np.floor(x + window + 1e-9), target_max).astype(np.int64)
    r = np.clip(np.rint(x), -target_max, target_max).astype(np.int64)
    bad = lo > hi           # x far outside the range: fall back to the clipped rounding
    lo[bad] = r[bad]
    hi[bad] = r[bad]
    return lo, hi


def _worst_rows(c, b, z, k):
    n = c.shape[1]
    vals, ii, jj = [], [], []
    top = 0.0
    for start, r in residual(c, b, z.astype(float)):
        a = np.abs(r).ravel()
        top = max(top, float(a.max()))
        m = min(k, a.size)
        sel = np.argpartition(a, -m)[-m:]
        vals.append(a[sel])
        ii.append(start + sel // n)
        jj.append(sel % n)
    v = np.concatenate(vals)
    order = np.argsort(v)[-k:]
    return top, np.concatenate(ii)[order], np.concatenate(jj)[order]


def finish(c, b, x, target_max, bound, window=1.0, max_rounds=60, time_limit=60.0, max_free=None):
    """Return (z, info): the integer point closest to the LP output x (L1 distance) that explains
    every observation with noise in [-bound, bound], searched inside the candidate box.

    info: free (number of undecided coefficients), t (max residual of z over all rows; <= bound
    means z is a feasible explanation), rounds, status ("fixed", "optimal", "infeasible", ...).
    "infeasible" means no integer point in the box fits; z is then the plain rounding.
    """
    n = c.shape[1]
    x = np.asarray(x, float)
    lo, hi = candidate_box(x, target_max, window)
    free = np.flatnonzero(lo < hi)
    z0 = np.clip(np.rint(x), lo, hi).astype(np.int64)
    z = z0.copy()
    info = dict(free=int(len(free)), rounds=0, status="fixed")

    def tmax(v):
        return max(float(np.abs(r).max()) for _, r in residual(c, b, v.astype(float)))

    if len(free) == 0 or (max_free is not None and len(free) > max_free):
        info["t"] = tmax(z)
        if len(free):
            info["status"] = "too many free"
        return z, info

    fixed = np.setdiff1d(np.arange(n), free)
    nf = len(free)
    seen = set()
    rows_i, rows_j = [], []
    add = 4 * n
    for rnd in range(1, max_rounds + 1):
        top, ii, jj = _worst_rows(c, b, z, add)
        if top <= bound + 1e-6:
            info.update(t=top, rounds=rnd - 1, status="optimal")
            return z, info
        keep = [(a, q) for a, q in zip(ii.tolist(), jj.tolist()) if (a, q) not in seen]
        seen.update(keep)
        rows_i += [a for a, _ in keep]
        rows_j += [q for _, q in keep]
        R = constraint_rows(c, np.array(rows_i), np.array(rows_j))
        h = b[np.array(rows_i), np.array(rows_j)].astype(float) + R[:, fixed] @ z0[fixed]
        Af = R[:, free]
        m = len(h)
        # variables: z_free (integer, nf), u (continuous, nf) with u >= |z - x|
        # rows: -bound - h <= Af z <= bound - h;  z - u <= x;  -z - u <= -x
        eye = np.eye(nf)
        A = np.vstack([np.hstack([Af, np.zeros((m, nf))]),
                       np.hstack([eye, -eye]), np.hstack([-eye, -eye])])
        lb = np.concatenate([-bound - h, np.full(2 * nf, -np.inf)])
        ub = np.concatenate([bound - h, x[free], -x[free]])
        cost = np.concatenate([np.zeros(nf), np.ones(nf)])
        bnds = Bounds(np.concatenate([lo[free], np.zeros(nf)]),
                      np.concatenate([hi[free], np.full(nf, np.inf)]))
        integ = np.concatenate([np.ones(nf), np.zeros(nf)])
        res = milp(cost, constraints=LinearConstraint(A, lb, ub), bounds=bnds,
                   integrality=integ, options=dict(time_limit=time_limit, disp=False))
        if res.x is None:
            info.update(rounds=rnd, status="infeasible" if res.status == 2 else f"milp: {res.message}")
            info["t"] = tmax(z0)
            return z0, info
        z[free] = np.rint(res.x[:nf]).astype(np.int64)
    info.update(rounds=max_rounds, status="max rounds", t=tmax(z))
    return z, info
