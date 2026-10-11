# mithril

## Design summary

Source: Celi, del Pino, Espitau, Niot, Prest, "Efficient Threshold ML-DSA", full version, ePrint 2026/013 (USENIX Security 2026). Local PDF `papers/mithril_2026-013.pdf` (37 pages).

- Short replicated secret sharing: one ML-DSA secret s_I per set I of N-T+1 parties; any T parties together know all s_I; a fixed partition (RSSRecover, App. B) gives each signer m = ceil(C(N,T-1)/T) secrets.
- Each signer commits w_i = [A | I] r_i with r_i uniform in a hyperball of radius r' (first l coordinates scaled by nu); 3 rounds (hash commit, reveal w_i, response).
- Local rejection HRej (Fig. 4): accept z_i = (c s_part / nu, c s_part) + r_i if ||z_i||_2 <= r. Per-party rejection constant M = (r'/r)^(n(k+l)).
- K parallel sessions per attempt; global check at Combine (infinity norm, hint weight) is only for ML-DSA format compatibility.
- Rejected w_i are revealed (proof Game 9 replaces them by uniform under MLWE with Gaussian-like chi_r).

## Security statement checked here

Theorem 3.2: secure for Q_s = 2 / (K * I_{1-1/phi^2}((n(k+l)+1)/2, 1/2)) signing queries, where phi must satisfy r'^2 >= r^2 + B^2 + 2 r B / phi (Lemma 2.4 / 3.1) and B bounds ||(c u1 / nu, c u2)||_2 for every partial secret "with overwhelming probability". Sec. 3.4: target Q_s = 2^50; B = 1.3 sqrt(tau) sqrt(n(k + l/nu^2)) sqrt(Var U(-eta,eta)) sqrt(ceil(C(N,T-1)/T)), described in a footnote as about 13 standard deviations. App. G: the full proof is for K = 1 with Q'_s = K Q_s.

## Experiments and results

### 2026-10-08: does the published parameter table meet Q_s = 2^50? (`harness/schemes/mithril_params.py`, output `experiments/results/mithril_params.txt`)

- Our B formula reproduces the footnote: B is 11 to 17 empirical standard deviations above the mean of ||c s_part|| (2000 samples per (T,N)).
- With that B and the published (r, r', K) of App. A (Figs. 9-11, all 45 rows), Theorem 3.2 gives log2 Q_s = 26.0 to 37.3, not 50.
- Turned around: to reach Q_s = 2^50 with the published radii, B can only be the value in column `B_for_2^50`, which is 0 to 2 standard deviations above the mean for ML-DSA-44, 0 to 4 for -65, 2.5 to 7 for -87. For some rows it is at or below the mean: ML-DSA-44 (5,6) and ML-DSA-65 (5,6) have about 55 to 60% of sessions with ||c s_part|| above it; 44 (4,6) 32%, 65 (4,6) 47%.
- Reading: the published parameters seem to have been computed with B close to the typical norm, not with the overwhelming bound the proof needs (Game 8 / Game 1 assert ||c s_part|| <= B). For sessions above B, Lemma 3.1 does not apply, so the proof as written does not cover them. This is a gap in the parameter/proof accounting, **not an attack**: exceeding B by one or two standard deviations makes the per-session Renyi divergence somewhat larger than M, it does not obviously reveal s.
- Hypothesis H-E1 (open): the true per-signature Renyi divergence with the published radii, averaged over the actual distribution of ||c s_part||, still gives about 2^50 (that is presumably what the authors meant by the footnote "only a small loss in the number of queries"). Our numbers say the loss is 13 to 24 bits if one applies Theorem 3.2 literally.

### Caveats (say these whenever the result is quoted)
- We did not run the authors' Go code or read their parameter script; they may compute B or phi differently (e.g. a smaller B from the measured Gaussian fit, or rounding of r, r').
- The table values r, r' are integers in the paper; rounding by 1 changes phi by a few percent, far from the 13 to 24 bit gap.
- Var(U(-eta,eta)) taken as the discrete variance eta(eta+1)/3; the continuous eta^2/3 would make B 10 to 20% smaller, which still leaves Q_s far below 2^50.
- Not checked: the NIST MPTC preview writeup v1.0 parameters (may differ from the paper), and App. G's version of the bound (it uses (1 + 2 eps/(1-eps))^Q_s, the main text (1 + eps/(M-1))^Q_s).
- Disclosure: before anything public, contact the authors (CLAUDE.md). This is coursework analysis only.

### 2026-10-08 (later): typical-case Q_s (columns `log2Qs_typ` in `experiments/results/mithril_params.txt`)

- Method: for each session the shift v = (c u1 / nu, c u2) has its own norm; Lemma 2.4 at the published radii (M fixed) gives the smallest eps(||v||). Averaged over the real norm distribution (Gaussian fit and the 2000 raw samples, which agree within 0.3 bits): Q_s = 1 / (K E[eps]).
- Result: 2^50 or more for most settings: ML-DSA-44 46.7 to 53.5, -65 47.4 to 56.6, -87 53.7 to 60.6. Below 2^50: -44 (4,6) 48.6, (5,6) 47.0, (3,6) 49.9 to 50.2; -65 (4,5) 49.4, (4,6) 47.9, (5,6) 47.6, (6,6) 49.2. These are the sets with the largest K.
- Reading: the published radii look tuned to the typical case, which roughly delivers the claimed 2^50 (except up to about 3 bits short for the largest-K sets). The 13 to 24 bit gap only appears when Theorem 3.2 is applied literally with the worst-case B the proof needs. So the finding is: (1) the rigorous statement does not cover the claimed Q_s at the published parameters; (2) a typical-case heuristic does, up to about 3 bits short for some (T,N).
- Why typical case is only a heuristic: it treats the challenge c of every session as random, but Theorem 3.2 needs a bound for every session; an adversary chooses messages (so it can try many c), though it cannot see s, so it cannot easily pick the c with large ||c s||. Making this rigorous (for example a smooth-Renyi argument over the challenge) is the authors' job, or a possible contribution.

### 2026-10-08 (evening): root cause found in the authors' public code

Sources (public): GitHub `GuilhemN/threshold-ml-dsa` (commit 66e269e, 5 Sep 2026), files `params/hyperball.sage` and `implementation/sign/thmldsa/thmldsa44/internal/dilithium.go`; cloned to the scratchpad and read, not run.
- B in the script is exactly the paper's (1.3 * sqrt(n (k + l/nu^2) ceil(C(N,T-1)/T)) * sig_t * sqrt(tau), sig_t^2 = eta(eta+1)/3). So B is NOT the explanation.
- phi is fixed by hand: phi = 7, 8, 9 for ML-DSA-44, -65, -87 (variables confusingly named `eta44`, `eta65`, `eta87`). Our recomputation from the tables gave phi = 7.0, 8.0, 9.0: the tables follow the script exactly. The Go code hard-codes the same r, r', K as App. A.
- The script's security figure is `boundI = (1-1/phi^2)^((l+k)n-1) * (l+k)n * (1-1/phi)`, i.e. the paper's Lemma 2.5 with n = dim. At phi = 7, dim = 2048 this is 2^-50.1 (2^-52.7 for -65, 2^-57.1 for -87): this is where 2^50 comes from.
- **But the exact value is larger:** I_{1-1/phi^2}((dim+1)/2, 1/2) = 2^-33.5, 2^-35.1, 2^-37.6 (scipy, checked with mpmath at 60 digits). An upper bound cannot be smaller than the exact value, so Lemma 2.5 as printed (exponent n-1) is false at these dimensions. With exponent (n-1)/2 it would be a valid (loose) bound. Asymptotically I_x(a, 1/2) behaves like x^a with a = (dim+1)/2, so the exponent must be about dim/2, not dim. Likely a transcription error of [27, Sec. A.6] (Devevey et al.; original not yet checked, ePrint blocks our download).
- **Consequence:** the published parameters satisfy Theorem 3.2 for Q_s = 2/(K I) = 2^26 to 2^37 (by parameter set, `log2Qs(B_paper)` column), not 2^50: a shortfall of about 13 to 24 bits in what the theorem guarantees. This replaces the earlier "B was computed differently" hypothesis.
- **What it is not:** not an attack. The extra leakage is in a proof budget (Renyi divergence), and the typical-case average still gives about 2^50 for most sets (previous section), because real norms are well below the 13-sigma B. Fixing it means a smaller phi (about 5.4 for -44), i.e. slightly larger r'/r, lower acceptance and more communication; not computed yet.
- **Test:** `test_lemma25_bound_is_not_an_upper_bound_at_mithril_dims`.

## Next
- Check the original lemma in Devevey et al. [27], Sec. A.6 (user to download ePrint 2022/1249; 2023/245 was a mix-up, see notes/papers.md).
- Compute corrected parameters (phi from the exact I for Q_s = 2^50) and the cost in acceptance probability and communication.
- NIST writeup v1.0 (8 pages, read fully) has no parameters or Q_s statement, so nothing to compare.
- Hint accounting for T-1 corrupted shares (lattice estimator, Docker Sage).
- Check the preview writeup v1.0 parameter list against App. A.

## Reading status

- 2026-10-08: full version read: Sec. 1-3 (scheme, Thm. 3.1, 3.2, a posteriori sharing, parameter selection), App. A (all parameter tables), App. B (partition) and the Renyi part of App. G (Games 9-10, Thm. G.1 statement). Skimmed: Sec. 4 benchmarks, App. D (DKG), E (a posteriori sharing proofs), the remaining hybrids of App. G.

## Corrected parameters (10 Oct 2026)
- `python -m harness.schemes.mithril_params --corrected`, output in `experiments/results/mithril_corrected.txt`.
- Method: keep the paper's r and B; choose phi from the exact incomplete beta I so Thm. 3.2 gives Q_s = 2^50; set r'^2 = r^2 + B^2 + 2rB/phi; then raise K until the chance that some of the K parallel attempts is accepted by all T parties (1 - (1 - M^-T)^K) is at least the published value. K and phi are solved together because Q_s depends on K.
- Result: phi 5.3-5.6 (-44, was 7), 5.9-6.6 (-65, was 8), 7.1-7.7 (-87, was 9). r' grows by only 12-89, but log2 M grows by 0.13-0.74, so M^-T falls. K grows 1.3x (small sets) to 8.5x (-65 (5,6): 1200 -> 10234; -65 (4,6): 804 -> 6256). Communication per session scales roughly with K.
- Caveats: success model assumes independent per-party acceptance with probability exactly 1/M (the paper's own approximation); we did not rerun the authors' script with the fix; other choices (e.g. larger r instead of K) might be cheaper.

## Accepted-z and Renyi loss at Q_s = 2^64 (11 Oct 2026)
- Accepted z_i in one session is uniform on B_r intersected with B_{r'}(v), v = (c u1 / nu, c u2); the ideal (simulated) z is uniform on B_r. With P supported inside Q's support, every Renyi divergence of order alpha equals 1/(1 - delta), delta = fraction of B_r outside B_{r'}(v); the other direction is infinite (support mismatch), so a Fisher-information treatment does not apply. Over Q_s sessions the loss multiplies, so the proof needs Q_s * K * eps << 1, which is what Thm. 3.2 / our typical-case column already measure.
- Consequence at 2^64 (direct from the 8 Oct table): Thm. 3.2 at published parameters covers 2^26-2^37 (27-38 bits short); the typical-case heuristic gives 46.7-60.7, so every set is 3-17 bits short. Mithril only claims 2^50; 2^64 is the del Pino-Niot / NIST-style figure we compare against.
- Corrected parameters for 2^64 (`python -m harness.schemes.mithril_params --corrected --target 64`, `experiments/results/mithril_corrected_2e64.txt`): phi 4.7-4.95 (-44), 5.3-5.8 (-65), 6.3-6.7 (-87); K grows 1.7x to 23x (worst -65 (5,6): 1200 -> 27806; (4,6): 804 -> 16630), against 1.3x-8.5x for 2^50.
- What it means: the leakage per accepted z is a thin missing cap of the ball, opposite v. An attacker could in principle use "no z ever lands there" like our TALUS edge estimator, but each session leaks with probability only about eps, so the attack cost tracks 1/(K E[eps]), the same number as the proof. No sign of a cheaper attack; not tested by simulation (r' - r is 50-120 units on radius ~250k in dimension 2048-3840, far beyond exact computation).

## A posteriori key sharing: hint from T-1 corrupted parties (11 Oct 2026)
- Source: Sec. 3.3 read fully (and the Thm. 3.3 / App. E.3 game list skimmed). Claim: sharing an existing ML-DSA key with share sd sqrt(2) leaks a hint; "effective entropy equals that of a secret with standard deviation 0.74"; lattice estimator: loss "at most 12 bits"; summary "7 to 12 bits". No parameter set or S is named.
- Code: `harness/schemes/mithril_hint.py` (`python -m harness.schemes.mithril_hint`, output `experiments/results/mithril_hint.txt`), 4 tests. Exact per-coefficient posterior: s uniform on [-eta, eta], S = C(N, T-1) discrete-Gaussian shares conditioned on summing to s; T-1 corrupted parties miss exactly one share (the one of the N-T+1 honest parties), so they learn h = s - x_S. Security: primal uSVP core-SVP (2016 estimate, 0.292 beta), our Python substitute for the lattice estimator (Sage not installed); baselines 424 / 624 / 863 match Dilithium round-3 (423 / 623 / 862).
- Results (sd_share = sqrt(2), S = 2..20), loss in core-SVP bits using the exact posterior sd (and, in brackets, the sd of a Gaussian with the same entropy, a more pessimistic proxy):
  - ML-DSA-44: posterior sd 1.15 -> 1.00, loss 4.1-7.0 (7.3-9.6).
  - ML-DSA-65 (eta = 4): posterior sd 1.54 -> 1.22, loss 14.6-20.7 (18.4-23.7).
  - ML-DSA-87: loss 7.6-12.8 (13.1-17.8).
- Where 0.74 comes from (hypothesis): Thm. 3.3's hint sd 2^(-1/2) (1/sigma_ML^2 + (S-1)/(S sigma_share^2))^(-1/2) with sigma_ML = sqrt(2) (eta = 2) gives 0.74 at S = 6. Our exact posterior sd at the same S is 1.03, about sqrt(2) larger; the 2^(-1/2) may be a width-vs-sd convention. Plugging 0.74 into our estimate for ML-DSA-44 gives 12.6 bits: the paper's "at most 12 bits" reproduces for ML-DSA-44 only.
- Reading: for ML-DSA-44 the paper is conservative (exact loss 4-7 bits). For ML-DSA-65 the loss is larger than "7 to 12 bits" because eta = 4 shares with sd sqrt(2) hide far less of a wider secret (14.6-20.7 bits with the exact posterior); -87 up to about 13. The paper's statement seems to have been computed for eta = 2 only.
- Caveats: core-SVP primal only (no dual, hybrid or hint-aware estimator); models the hinted secret as Gaussian with the posterior sd after centring on the posterior mean, which the attacker can compute; does not use the non-Gaussian shape of the posterior; sigma_share = sqrt(2) read as a standard deviation (if it were a GPV width s, sd 0.56, losses are larger still: about 15-18 bits for -44). Not run with the real lattice estimator (Docker Sage is possible). Not an attack on the default key generation, only on a posteriori sharing. Contact authors before anything public.

## Lemma 2.5 traced to its source (11 Oct 2026)
- Source: Devevey, Fawzi, Passelegue, Stehle, ePrint 2022/1249 (local `papers/devevey_2022-1249.pdf`, 50 pages), App. A.6 read fully (Def. A.12, Lemma A.13 and the two bounds after it).
- The original states the same upper bound as Mithril: I_{1-1/eta^2}((n+1)/2, 1/2) < (1 - 1/eta^2)^(n-1) * n * (1 - 1/eta), justified "by placing the hyperspherical cap into a cylinder of 1-dimensional height 1 - 1/eta". Mithril copied it correctly; the error is in the source.
- Doing that cylinder argument exactly gives I <= 2 V_{n-1}/V_n * (1 - 1/eta^2)^((n-1)/2) * (1 - 1/eta): the cylinder base has radius sqrt(1 - 1/eta^2), so its (n-1)-volume carries exponent (n-1)/2. `mithril_params.cylinder_bound_log2`, test `test_cylinder_bound_done_exactly_is_a_valid_upper_bound`. Numbers (log2): n = 2048, eta = 7: exact -33.5, printed -50.1 (invalid), corrected -25.5 (valid); the printed bound is already invalid at n = 100 (-10.76 vs exact -10.75).
- The derived consequence 1/eta^2 < 1 - (eps/n)^(1/(n-1)) in the same appendix inherits the error. Their lower bound (cone, exponent (n-1)/2) looks fine. The ASIACRYPT published version was not checked (only the ePrint).
- Consequence for Mithril unchanged (already used the exact I): Thm. 3.2 covers 2^26-2^37. New: other works that cite this bound (e.g. hyperball variants of Lyubashevsky / Dilithium) may inherit it; not checked. Contact authors before anything public.
