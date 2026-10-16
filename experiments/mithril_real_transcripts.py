"""Paper plan item 5: run our Mithril view on real transcripts from the reference Go code.

Usage: python -m experiments.mithril_real_transcripts <dump.bin> [more dumps...]

For every slot where no signer rejected, from public data plus ground truth:
    u = A z - c t - w   which should equal -(c s2 + e) = -z2, the hidden second response part.
    b = A z - c t1 2^d - w = u + c t0   is what views.observations_to_cb feeds the estimators.
MithrilView's docstring models b = -c (s2 - t0) - r2 with r2 independent of the secret. The
reference code rejects on the joint vector (z1, c s2 + e), so after acceptance z2 may instead be
independent of s2. We measure the regression slope of u on -c s2: 1 under the view's model,
0 if acceptance removes the s2 dependence. Slope of (b - u) on c t0 is a sanity check (exactly 1).
"""
import sys

import numpy as np

from harness.mldsa.params import D, ML_DSA_44, Q
from harness.mldsa.rounding import mod_pm, power2round
from harness.schemes.mithril_go import load, matvec, ring_mul


class Slope:
    """Least-squares slope of y on x (no intercept), accumulated over chunks."""

    def __init__(self):
        self.xx = self.xy = self.yy = 0.0
        self.n = 0

    def add(self, y, x):
        x = x.astype(np.float64).ravel()
        y = y.astype(np.float64).ravel()
        self.xx += x @ x
        self.xy += x @ y
        self.yy += y @ y
        self.n += len(x)

    def result(self):
        b = self.xy / self.xx
        rss = self.yy - 2 * b * self.xy + b * b * self.xx
        return b, np.sqrt(rss / (self.n - 1) / self.xx)


TOTAL = dict(slots=0, acc=0, s2=Slope(), t0=Slope(), key=None)


def analyse(path):
    p = ML_DSA_44
    tr = load(path)
    a_hat = tr.a_hat()
    t_check = mod_pm(matvec(a_hat, tr.s1) + tr.s2 - tr.t, Q)
    print(f"{path}: T={tr.T} N={tr.Nparties} K={tr.K} seed={tr.seed} slots={len(tr.rej)}")
    print(f"  ExpandA cross-check A s1 + s2 == t: {'ok' if not t_check.any() else 'MISMATCH'}")

    per_party = [np.mean((tr.rej >> j) & 1) for j in range(tr.T)]
    acc = tr.accepted
    print(f"  per-party reject rate per slot: {', '.join(f'{r:.3f}' for r in per_party)}")
    print(f"  slots with no rejection: {acc.sum()} ({acc.mean():.3f})")
    if not acc.any():
        return

    c, z, w = tr.c[acc], tr.z[acc], tr.w[acc]
    zinf = np.abs(z).max()
    print(f"  max |z|_inf on accepted slots: {zinf} (gamma1 - beta = {p.gamma1 - p.beta})")

    az = matvec(a_hat, z)
    ct = ring_mul(c, tr.t)
    u = mod_pm(az - ct - w, Q)
    cs2 = ring_mul(c, tr.s2)
    t1, t0 = power2round(tr.t)
    b = mod_pm(az - ring_mul(c, t1 << D) - w, Q)
    ct0 = ring_mul(c, t0)

    s_s, s_t = Slope(), Slope()
    s_s.add(u, -cs2)
    s_t.add(mod_pm(b - u, Q), ct0)
    k_s, se_s = s_s.result()
    k_t, se_t = s_t.result()
    key = (tr.T, tr.Nparties, tr.seed)
    if TOTAL["key"] in (None, key):
        TOTAL["key"] = key
        TOTAL["slots"] += len(tr.rej)
        TOTAL["acc"] += int(acc.sum())
        TOTAL["s2"].add(u, -cs2)
        TOTAL["t0"].add(mod_pm(b - u, Q), ct0)
    e_if_view = u + cs2   # = -e if the view's model held
    print(f"  |u|_2 per slot mean {np.sqrt((u.astype(float) ** 2).sum(axis=(1, 2))).mean():.0f}, "
          f"|u|_inf max {np.abs(u).max()}, |c s2|_inf max {np.abs(cs2).max()}")
    print(f"  slope of u on -c s2: {k_s:+.4f} +/- {se_s:.4f}  (1 = view model, 0 = s2-independent)")
    print(f"  slope of (b - u) on c t0: {k_t:+.4f} +/- {se_t:.4f}  (sanity, expect 1)")
    print(f"  corr(u, -c s2) = {np.corrcoef(u.ravel(), -cs2.ravel())[0, 1]:+.4f}; "
          f"corr(u + c s2, c s2) = {np.corrcoef(e_if_view.ravel(), cs2.ravel())[0, 1]:+.4f}")


if __name__ == "__main__":
    for f in sys.argv[1:]:
        analyse(f)
    if len(sys.argv) > 2:
        k_s, se_s = TOTAL["s2"].result()
        k_t, se_t = TOTAL["t0"].result()
        print(f"POOLED (T, N, seed) = {TOTAL['key']}: {TOTAL['slots']} slots, {TOTAL['acc']} accepted")
        print(f"  slope of u on -c s2: {k_s:+.4f} +/- {se_s:.4f}  (1 = view model, 0 = s2-independent)")
        print(f"  slope of (b - u) on c t0: {k_t:+.4f} +/- {se_t:.4f}")
