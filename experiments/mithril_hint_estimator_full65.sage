# Mithril a posteriori sharing, ML-DSA-65 only: full LWE.estimate (all attacks), not .rough.
# Paper plan item 6. Same parameters as mithril_hint_estimator.sage (posterior sd from
# harness/schemes/mithril_hint.py). Run (Docker), from the repo root:
# docker run --rm -e PYTHONPATH=/est -v <lattice-estimator>:/est -v <repo>/experiments:/exp -w /est \
#   sagemath/sagemath:10.4 sage /exp/mithril_hint_estimator_full65.sage
from estimator import *

q = 8380417
k, l, eta = 6, 5, 4
CASES = [("no hint", None), ("S=2", 1.543), ("S=6", 1.281), ("S=20", 1.216), ("paper 0.74", 0.74)]

base_bits = None
for label, sd in CASES:
    X = ND.Uniform(-eta, eta) if sd is None else ND.DiscreteGaussian(sd)
    p = LWE.Parameters(n=256 * l, q=q, Xs=X, Xe=X, m=256 * k, tag=label)
    res = LWE.estimate(p, jobs=1, deny_list=("arora-gb",))
    bits = min(float(log(v["rop"], 2)) for v in res.values())
    best = min(res, key=lambda a: res[a]["rop"])
    if base_bits is None:
        base_bits = bits
    print(f"RESULT ML-DSA-65 {label}: {bits:.1f} bits (best attack {best}), loss {base_bits - bits:.1f}", flush=True)
