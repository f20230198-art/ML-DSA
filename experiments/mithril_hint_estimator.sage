# Mithril a posteriori sharing: re-run of the hint accounting with the lattice estimator
# (malb/lattice-estimator), replacing the Python core-SVP substitute of harness/schemes/mithril_hint.py.
# Run (Docker): see experiments/results/mithril_hint_estimator.txt header for the exact command.
# Secret and error both get the posterior sd from mithril_hint.py (exact per-coefficient posterior,
# sigma_share = sqrt(2)); baseline uses the true uniform distribution on [-eta, eta].
from estimator import *

q = 8380417
SETS = {  # name: (k, l, eta, {S: posterior sd})
    "ML-DSA-44": (4, 4, 2, {2: 1.149, 6: 1.033, 20: 0.999}),
    "ML-DSA-65": (6, 5, 4, {2: 1.543, 6: 1.281, 20: 1.216}),
    "ML-DSA-87": (8, 7, 2, {2: 1.149, 6: 1.033, 20: 0.999}),
}


def rop_bits(params):
    res = LWE.estimate.rough(params, jobs=1)
    return min(float(log(v["rop"], 2)) for v in res.values())


for name, (k, l, eta, post) in SETS.items():
    u = ND.Uniform(-eta, eta)
    base = LWE.Parameters(n=256 * l, q=q, Xs=u, Xe=u, m=256 * k, tag=name)
    b0 = rop_bits(base)
    print(f"{name}: no hint {b0:.1f} bits", flush=True)
    cases = list(post.items()) + [("paper 0.74", 0.74)]
    for S, sd in cases:
        g = ND.DiscreteGaussian(sd)
        p = LWE.Parameters(n=256 * l, q=q, Xs=g, Xe=g, m=256 * k, tag=f"{name} S={S}")
        b = rop_bits(p)
        print(f"   S={S}: sd {sd}: {b:.1f} bits, loss {b0 - b:.1f}", flush=True)
