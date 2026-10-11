# Runs the Mithril authors' parameter script (GuilhemN/threshold-ml-dsa, params/hyperball.sage,
# commit 66e269e) and compares its Lemma 2.5 bound boundI with the exact incomplete beta value.
# Run from the repo's params/ directory inside the sagemath/sagemath:10.4 container.
load("hyperball.sage")
from mpmath import mp, betainc as mbetainc, log as mlog
mp.dps = 60

for name, prm, eta in (("ML-DSA-44", params_mldsa_44, eta44), ("ML-DSA-65", params_mldsa_65, eta65),
                       ("ML-DSA-87", params_mldsa_87, eta87)):
    dim = (prm.ell + prm.k) * prm.n
    bound = (1 - 1 / eta**2)**(dim - 1) * dim * (1 - 1 / eta)
    x = mp.mpf(1) - mp.mpf(1) / eta**2
    exact = mbetainc((dim + 1) / mp.mpf(2), mp.mpf(1) / 2, 0, x, regularized=True)
    print(f"{name}: phi={eta} dim={dim} log2 boundI={float(log(bound, 2)):.2f} log2 exact I={float(mlog(exact, 2)):.2f}")

print("Regenerate ML-DSA-44 (T,N)=(2,2), K=2 (paper App. A: r=252778, r'=252833):")
set_random_seed(2026)
evaluate_params_fixedK(2, 2, eta44, 2, 1.3, 3, sig_t, 200, params_mldsa_44, verb=1)
