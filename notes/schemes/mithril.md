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
- Check the original lemma in Devevey et al. [27], Sec. A.6 (user to download ePrint 2023/245).
- Compute corrected parameters (phi from the exact I for Q_s = 2^50) and the cost in acceptance probability and communication.
- NIST writeup v1.0 (8 pages, read fully) has no parameters or Q_s statement, so nothing to compare.
- Hint accounting for T-1 corrupted shares (lattice estimator, Docker Sage).
- Check the preview writeup v1.0 parameter list against App. A.

## Reading status

- 2026-10-08: full version read: Sec. 1-3 (scheme, Thm. 3.1, 3.2, a posteriori sharing, parameter selection), App. A (all parameter tables), App. B (partition) and the Renyi part of App. G (Games 9-10, Thm. G.1 statement). Skimmed: Sec. 4 benchmarks, App. D (DKG), E (a posteriori sharing proofs), the remaining hybrids of App. G.
