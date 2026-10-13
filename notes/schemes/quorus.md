# quorus

## Design summary

Source: Quorus, ePrint 2025/1163 (USENIX Security 2026), local `papers/quorus_2025-1163.pdf` (38 pages). Honest-majority (n = 2t+1) MPC over Shamir shares mod q, with edabits for small randomness, comparisons and Decompose.

- Algorithm 1 (MPC-friendly ML-DSA): w := A y + e_w with e_w uniform in [-eta, eta]^(kn); a single attempt; checks ||z|| < gamma1 - beta and ||w0 - c e|| < gamma2 - beta (line 3); hint MakeHint(-c t0, A z - c t + c t0), i.e. e_w deliberately left out (the "optimization"); line 6 checks ||c t0|| and hint weight.
- On a line-3 rejection the parties release (w1, c, bottom). On a line-6 failure, Protocol 5 releases (w1, c, z, bottom): z has passed both norm checks, so it is distributed like an accepted signature.
- Rejection is one bit: Pi_RejSamp feeds all comparison bits into a batched OR (lift to F_p with dabits, sum, multiply by a random u, open). The positions of failing coefficients stay hidden; the paper notes that leaking them together with c enables key recovery [ZWSY25 = Zhou, Wang, Sun, Yu, ePrint 2025/214, verified online 8 Oct].
- Security: Theorem 1 (UF-CMA-bottom in the QROM) from Theorem 2 (scHVZK under two MLWE assumptions, using del Pino-Niot for the rejection-conditioned MLWE). The distinguisher in scHVZK gets sk.

## Experiments and results

### 2026-10-08: correctness and rejection rates of Algorithm 1 (`harness/schemes/quorus.py`, `experiments/results/quorus_correctness*.txt`)

400,000 single attempts per parameter set, 20 keys (control without e_w: 200,000 attempts, 10 keys). Every released signature checked with our FIPS 204 verifier (which passes the NIST ACVP vectors).

| Set | M_rep (ours) | M_rep (Table 2) | line-6 failure given line 3 passed | signatures | failing FIPS 204 verification |
|---|---|---|---|---|---|
| ML-DSA-44 | 4.30 | 4.25 | 1.34% (hint weight) | 91,810 | 0 |
| ML-DSA-65 | 5.12 | 5.09 | 0.40% | 77,862 | 0 |
| ML-DSA-87 | 3.85 | 3.85 | 0.77% | 102,992 | 0 |

- e_w changes nothing measurable: control runs give the same rates (4.32 / 5.17 / 3.85; line 6 1.35% / 0.43% / 0.80%).
- The paper says the line-6 failure rate is "around 0.02"; we measure 0.4 to 1.3% (all from hint weight, none from ||c t0||). Same order, slightly lower.
- **Zero verification failures in 272,664 signatures.** This matches a one-line argument that the "skip e_w in the hint" optimization is exactly correct, not just empirically: the verifier recovers HighBits(w - c e - e_w) (since A z - c t1 2^d = w - c e + c t0 - e_w, and UseHint with the -c t0 hint removes c t0). Line 3 guarantees |LowBits(w) - c e| < gamma2 - beta coefficient-wise, and |e_w| <= eta < beta (beta = tau eta), so |LowBits(w) - c e - e_w| < gamma2 and the high bits are unchanged: HighBits(w - c e - e_w) = w1. (Decompose's wrap case at q-1 is also covered by the same margin; checked empirically, not separately proved.) So the paper's "empirically ... does not sacrifice correctness" can be replaced by a proof.

### Leakage tests (Gate F power statement)
- A purely statistical test on released rejected w1 cannot detect anything: w = A y + e_w mod q with y in a 2^18-wide box and A uniform is uniform mod q to extreme precision, whatever small secret-dependent shift the rejection conditioning adds. Any leak is computational (needs MLWE-type lattice work), which is what Theorem 2 claims to rule out. We did not run a lattice distinguisher.
- Not tested: the MPC layer (batched OR, comparisons) for implementation leakage; there is no code to test.

## Reading status

- 2026-10-08: Sec. 1.3, 2.1-2.3, 3 (Algorithm 1, Theorems 1-2 and sketches), 4.1-4.3 (rejection protocol, online protocol, offline phase start) read fully. Skimmed: Sec. 5 (performance), App. A. Not read: App. B proofs (simulator Algorithm 11 and hybrids), App. C-D.

## Full read (13 Oct 2026)

Read: all 38 pages of `papers/quorus_2025-1163.pdf` (USENIX Security 2026 full version), text extracted with pypdf, including App. A-D and every boxed algorithm. Page numbers below are the printed page numbers (they equal the PDF page numbers). Not done: no proof was re-derived line by line except Lemma 8 (checked numerically, see below); App. D cost formulas only skimmed for correctness of arithmetic.

### Section-by-section summary (plain words)

- **Sec. 1 (p. 1-4).** Goal: n parties hold shares of an ML-DSA key and jointly produce a normal FIPS 204 signature. Problem: the hash c = H(mu, w1) is far too expensive to compute inside MPC. Trick: open w1 in the clear and hash outside MPC. That is only safe if w1 from a *rejected* attempt leaks nothing, so they change signing slightly (add a small error e_w to w) and prove rejected attempts can be simulated. They also say Trilithium "heuristically assumes" this (p. 3).
- **Sec. 2 (p. 4-6).** ML-DSA background (Table 2 parameters, M_rep), MLWE definition, honest-majority Shamir sharing over F_q and over F_{2^k}, list of ideal building blocks (F_Open, F_Mult, F_Coin, F_Rand, F_edabits, F_dabits). n = 2t + 1, static corruption, active security with abort (p. 5).
- **Sec. 3 (p. 6-9).** Algorithm 1 (the "MPC-friendly" ML-DSA). Correctness argued for a variant whose hint includes e_w, then the "skip e_w in the hint" optimisation is justified only empirically (p. 7). UF-CMA-bottom game (Alg. 2): the oracle returns rejected transcripts too, and a message only counts as "signed" if z was returned. Theorem 1 (UF-CMA-bottom in the QROM) is reduced to Theorem 2 (scHVZK: the distinguisher is given sk). Simulator sketch: Mode 1-A (z passes, w0 check fails), Mode 1-B (full passing transcript, perfect), Mode 2 (z fails; uses e_w plus the del Pino-Niot [PN25, PKC 2025] reduction).
- **Sec. 4.1 (p. 10-11).** Rejection sampling inside MPC: every coefficient comparison gives a shared bit (F_LTC); Pi_BatchedOR combines all bits into ONE opened value y = (sum of kappa random parity bits) * u, which is 0 iff all checks passed. The paper says hiding *which* coefficient failed is "crucial" because together with c it enables key recovery [ZWSY25] (p. 10).
- **Sec. 4.2 (p. 11).** Protocol 5 (online signing): open w1, hash locally, compute shares of z and w0bar locally, call F_RejSamp, open z only if the bit says pass, then hint.
- **Sec. 4.3 (p. 11-12).** Offline phase: Pi_Prep makes shares of y, e_w, w0, w1 (DecomposeMod via bit decomposition; ML-DSA-44 needs a separate discrete-log trick, Pi_Prep-44, because 44 is not a power of two).
- **Sec. 5 (p. 12-14).** Costs: 16 (round-optimised) or 29 (communication-optimised) online rounds per attempt; kappa = 40; parallel SIGN attempts (Table 5) where only the first passing z is opened and other passing attempts are discarded.
- **App. A (p. 19-23).** ML-DSA details, Lemmas 3-5 from the Dilithium spec, UC primer, instantiations of Open/Coin/Rand/Mult (PRF-expanded coins are admitted to be "not a valid instantiation of F_Coin", p. 21, but argued fine for their use).
- **App. B.1 (p. 23-27).** Full hybrid proof of Theorem 2 (H0-H7, Alg. 11-13), Lemma 7 (adapted PN25 Lemma 5), Lemma 8 (exact distribution of HighBits(a' + s) when a' is uniform with large low bits; it does not depend on s). Concrete bound: eps_A <= eps_B1 + p_z (eps_B2 + eps_B3) + 2^-2lambda.
- **App. B.2 (p. 28-31).** Proof of Theorem 1 via adaptive reprogramming [GHHM21]; rejected attempts do not reprogram the oracle. Loss is linear in Q_s.
- **App. C (p. 32-36).** Missing functionalities (F_T-MLDSA, F_LTC, F_BitDec, F_RejSamp, F_BitLTC), Rabbit comparison, bit decomposition, UC proofs of Lemmas 1-2 and Theorems 3-5.
- **App. D (p. 36-38).** Communication cost of dabits / edabits.

### Exactly what is released per signing attempt, and to whom

All n parties (so the adversary, who controls t of them) see every opened value.

| Phase | Opened value | Leaks? |
|---|---|---|
| Keygen (Prot. 5, l. 4) | full t = A s + e (so t0 too; footnote 5, p. 9; F_T-MLDSA sends (pk, tr, t, t0) to the adversary, p. 32) | public by design |
| Prep (Prot. 6 / 8) | masked bits c_i = s_i XOR r_i, masked a = s + r, d | uniform masks, no |
| Sign, every attempt | w1 (Prot. 5, l. 2); c is then computed by everyone | the object of Theorem 2 |
| Sign, inside F_RejSamp | masked a = x + r per comparison (Prot. 18), masked parity bits c(i) (Prot. 3, l. 4), y = b*u (l. 9) | only the single bit b = "some check failed" |
| Rejected at line 3 | (w1, c, bottom) | |
| Passed line 3, failed line 6 | (w1, c, z, bottom): z IS opened (Prot. 5, l. 7; F_T-MLDSA l. 11) | z is distributed like an accepted z |
| Accepted | (w1, c, z, h) | signature |
| Parallel SIGN (Sec. 5.1, p. 13) | w1 and b for every parallel attempt; z only for the first passing one | a passing-but-discarded attempt releases (w1, c, b = pass) with no z, a transcript type that is NOT in F_T-MLDSA |

### Adversary model

Honest majority n = 2t + 1, static corruption of up to t parties, active (malicious) adversary, security with abort (no guaranteed output), UC with ideal building blocks; computational only because of PRF-expanded coins (p. 5, p. 21). Unforgeability game: UF-CMA-bottom in the QROM, classical signing queries (Def. 2, p. 8). Remark 1 (p. 6) says the "N parties run DKG, n of them sign" setting is a "trivial" extension; it is not written out.

### Verdicts on the existing hypotheses

| Hypothesis (where listed) | Verdict | Evidence |
|---|---|---|
| Reveal-on-reject (w1, c, bottom) is proven simulatable (DOSSIER 4.2 bullet 1) | **Confirmed, with refinement.** Proof is computational (MLWE), not statistical. | Thm. 2 (p. 9), full hybrids App. B.1 (p. 23-27). Mode 1-A uses Lemma 8 (exact, statistical); Mode 2 uses MLWE with secret y conditioned on rejection, reduced to two standard MLWE instances via PN25 Lemma 5 (Lemma 7, p. 24). The sk-holding distinguisher is part of the definition (Def. 3, p. 8). |
| Our note "a purely statistical test on rejected w1 cannot detect anything because A y + e_w mod q is uniform to extreme precision" (Leakage tests, above) | **Revise.** A y + e_w is not statistically close to uniform as a whole vector: y has l*N*log2(2 gamma1) bits of entropy (ML-DSA-44: 4*256*18 = 18,432) but w lives in Z_q^{kN} (4*256*23 = 23,552 bits). Only low-order marginals (single coefficients, small groups) are uniform to extreme precision. The released w1 is compressed to kN*log2(44) = 5,591 bits, so near-uniformity of w1 is plausible but not proven statistically; the paper relies on MLWE (computational). Correct wording: "no low-order statistical test can see anything; any leak must be found by a lattice (joint) distinguisher". | p. 9 ("Thanks to the additional noise e_w, this mode computationally simulates", Mode 2). Entropy count is ours. |
| Which check failed must stay hidden (DOSSIER 4.2 bullet 2) | **Confirmed by design.** Only one bit leaves F_RejSamp; positions and the z-vs-w0 distinction are hidden. **New caveat:** Pi_BatchedOR has soundness error 2^-kappa+1 with kappa = 40 (p. 12; Lemma 1 proof, p. 36): about one rejected attempt in 2^39 is wrongly declared "pass" and then z (a failing, key-dependent z) is opened. 2^39 attempts is roughly 10^11 signatures, so not practical, but 40-bit statistical security is lower than usual. | p. 10 ("hiding the position of out-of-bound coefficients in z is crucial ... key recovery attack is possible [ZWSY25]"); p. 12 ("We set the statistical security parameter kappa to 40"); p. 36 ("real and ideal world distributions are 2^-kappa+1-close"). |
| Building blocks are where mistakes hide (DOSSIER 4.2 bullet 3) | **Confirmed; two concrete inconsistencies found in the paper text.** (1) F_RejSamp (Func. 6, p. 32) checks norm(w0bar) < gamma2 - beta - eta, but Alg. 1 (p. 7), Prot. 4 (p. 11) and F_T-MLDSA (p. 32) all use gamma2 - beta, so Lemma 2 ("Pi_RejSamp UC-realizes F_RejSamp") is false as written when norm(w0bar) is in [gamma2-beta-eta, gamma2-beta). Looks like a typo; an implementer could pick either bound. (2) Lemma 8, eq. (2) (p. 24): the normaliser 2(beta+1)delta+1 is wrong; the support size is (2 beta + 1) delta + 1 (the probabilities as printed do not sum to 1). The lemma itself (output independent of the shift s) is correct. The min-entropy formula in G5 (p. 29) reuses the wrong normaliser (harmless, entropy is still far above 1028). (3) Parallel SIGN releases (w1, c, pass) without z, which F_T-MLDSA does not model; it is easy to simulate (run Mode 1-B and drop z), so a formal gap, not a leak. (4) PRF-expanded coins are not a valid F_Coin (p. 21), argued informally. | Func. 6 l. 2 (p. 32): "if norm(z) < gamma1 - beta and norm(w0bar) < gamma2 - beta - eta then set b <- 0". Lemma 8 check: short exhaustive enumeration over all a in Z_q, run 13 Oct, script not kept in the repo (5 toy (q, alpha, beta) sets: support = (2beta+1)delta+1, cell 0 count 2beta+2, others 2beta+1, identical for every s in [-beta, beta]). |
| Honest majority is a hard assumption; check N = 2T-1 boundaries (DOSSIER 4.2 bullet 4) | **Confirmed, narrowed.** The paper only treats n = 2t + 1 with all n signing; the N-party DKG / n-signer case is asserted "trivial" (Remark 1, p. 6) and not specified. Security is with abort only (no robustness), so t corrupt parties can stop every signing. There is nothing more to test at "boundaries" in the paper; it would have to be in the submission package. | p. 5, p. 6. |
| "e_w changes nothing" / "skip e_w in hint is exactly correct" (our 8 Oct result) | **Confirmed and consistent with the paper.** The paper proves correctness only for the variant with e_w in the hint and calls the optimisation empirical (p. 7); our one-line proof still stands. Theoretical support for "e_w does not change rejection rates": each coefficient of A y is already uniform, so adding e_w does not change the w0 marginal. | p. 6-7. |
| Line-6 failure rate "around 0.02" vs our 0.4-1.3% | **Unchanged.** The paper gives no data for this number. | p. 7. |

### New observation (our analysis, not run)
- **Concrete MLWE hardness for Theorem 2 is not quantified in the paper.** Our rough reduction: for square A (ML-DSA-44) multiply by A^-1, giving LWE with secret e_w (eta = 2, dimension 1024) and "error" y of width 2^18 mod q = 2^23, i.e. q/sigma about 2^7, far harder than Kyber-like parameters. For tall A (-65, -87) eliminate y with the left kernel of A: the remaining problem is LWE of the same shape as ML-DSA key recovery but with a uniform secret, so roughly as hard as the public key. So the assumption looks as strong as ML-DSA itself; a lattice-estimator run would make this a number. Not done.

### Comparison with `harness/schemes/quorus.py`
- Matches Alg. 1: y in [-gamma1 + 1, gamma1], e_w uniform in [-eta, eta]^{kN}, w0bar = LowBits(w) - c s2 without re-decomposing, line-3 bound gamma2 - beta (as Alg. 1 and Prot. 4, not F_RejSamp), hint MakeHint(-c t0, A z - c t + c t0), line-6 checks.
- Difference that matters only for future transcript tests: on a line-6 failure the paper releases z, but `QuorusAttempt` stores only (w1, c_tilde, failed). If a leakage test ever treats line-6 failures as "rejected", it must add z. No change needed for the correctness / rate experiments.
- The 1-bit rejection model (we never use which check failed for anything the adversary sees) matches Prot. 4; the `failed` field is for our bookkeeping only.

### Reading status
- 2026-10-13: whole paper read (38 pages incl. App. A-D). Lemma 8 checked numerically; other proofs read but not re-derived.
