# trilithium

## Design summary

Source: Dufka et al., Trilithium (ePrint 2025/675, 67 pages), local `papers/trilithium_2025-675.pdf`. Two-party (phone + server) UC-secure distributed ML-DSA with a trusted dealer of correlated randomness (Mithril's Table 1: 234 MB per party).

- Every signing attempt declassifies the commitment w_H = HighBits(A y) (Sec. 4.6), also for rejected attempts; rejected attempts reveal (w_H, c, bottom).
- Two variants: unmodified ML-DSA (Sec. 3), and the Bienstock et al. / Quorus-style variant that adds a small error to w (more standard zero-knowledge argument).

## Security argument for rejected transcripts (Sec. 3, read 2026-10-08)

- Alg. 4 reorders transcript generation into three branches: (1) z and r0 pass: simulatable without sk; (2) z passes, r0 fails: y uniform on {y in S_{gamma1-beta-1} - c s1 : ||LowBits(A y - c s2)|| >= gamma2 - beta}, output HighBits(A y); (3) z fails: y uniform on {y : ||c s1 + y|| >= gamma1 - beta}, output HighBits(A y).
- Branches 2 and 3 are argued with an MLWR-type assumption: (A, HighBits(A y)) for y uniform on a set S_A is indistinguishable from (A, HighBits(uniform)). The authors say reductions from MLWR to MLWE "do not really apply to the parameters of ML-DSA" and argue from conditional entropy of y and from MLWR-based KEMs using similar or more aggressive parameters (except q).
- Our note: the sets S_A depend on c s1 and c s2, and sHVZK gives the distinguisher sk, so it knows S_A. MLWR with a known secret distribution is the usual form, so this is consistent, but the bias in branch 3 (y pushed towards the edge in the coordinate where c s1 is large) is exactly the kind of secret-dependent shift a lattice distinguisher could look for.

## Attack surface / hypotheses

- H-F2: in branch 3, E[y | reject] is shifted by a vector delta(c, s1) supported where |c s1| is large; A delta is a secret-dependent shift of w before rounding. Statistically invisible (A y mod q is uniform to extreme precision), so any distinguisher must be lattice-based. Test only at toy sizes (small n, k, l, reduced gamma1) with exact likelihoods or lattice reduction; scaling unclear.

## Experiments and results

### Exact toy-size test of rejected w_H (10 Oct 2026)
- Code: `harness/schemes/trilithium_toy.py`, `experiments/trilithium_toy.py`; output `experiments/results/trilithium_toy.{txt,json}` (and `_q513`). 5 tests in `harness/tests/test_trilithium_toy.py`.
- Model: ring Z_q[X]/(X^4+1), k = l = 1, q = 257, gamma2 = 16 (8 HighBits values per coefficient), tau = 2, eta = 1, beta = 2; FIPS 204 Decompose. Every y in [-gamma1+1, gamma1]^4 is enumerated, so all distributions are exact. 5 random (A, s1, s2, c) per gamma1, seed 2026.
- Compared: real w_H after branch-3 rejection (z out of box) and after branch-2 rejection (z ok, r0 check fails) against the simulator HighBits(A y), y uniform on the box. Also branch 3 for two different s1 with the same A and c (does the rejected w_H depend on the key?). Metric: squared Hellinger H^2; about 1/H^2 samples distinguish.

| gamma1 | P(branch 3) | P(branch 2) | H^2 branch 3 vs sim | H^2 branch 2 vs sim | H^2 branch 3, s1 vs s1' |
|---|---|---|---|---|---|
| 4 | 0.98 | 0.011 | 5.1e-3 | 0.86 | 7.8e-3 |
| 8 | 0.78 | 0.11 | 2.0e-3 | 0.11 | 2.0e-3 |
| 16 | 0.49 | 0.25 | 1.8e-4 | 1.2e-3 | 1.4e-4 |
| 32 | 0.28 | 0.36 | 1.7e-5 | 7.1e-5 | 1.3e-5 |
| 48 | 0.19 | 0.41 | 8.7e-6 | 5.7e-5 | 2.3e-6 |

- Reading: at toy size the rejected w_H is NOT distributed like the simulator's and does depend on s1 (as expected: the box is tiny). Branch 3's gap shrinks steadily, roughly as gamma1^-2.7 between 16 and 48 at fixed n = 4. Branch 2's gap shrinks fast up to gamma1 = 32 and then flattens (7.1e-5 to 5.7e-5). A run with q = 513, gamma2 = 32 did not settle whether that floor is a small-q artefact (it also changes the gamma1/gamma2 ratio, the likely controlling parameter).
- What this does not show: anything at real size (n = 256, l = 4 to 7, gamma1 = 2^17 or 2^19). Extrapolating from n = 4 is not justified; dimension changes the picture completely. No attack. It is a sanity check that the hypothesis H-F2 is real at toy scale and that the effect shrinks with gamma1, consistent with the authors' heuristic.
- Next: vary gamma1/gamma2 at fixed ratio to explain the branch-2 floor; try n = 8 by sampling (no longer enumerable) with a likelihood-ratio distinguisher.

## Reading status

- 2026-10-08: Sec. 3 (zero-knowledge of the identification protocol, Alg. 4, MLWR discussion) read fully; table of contents and Sec. 4 headings mapped. Not read: Sec. 4 protocols in detail, Sec. 5 simulators, App. B proofs, App. D (literature on rejected transcripts).

### Fixed-ratio scan for the branch-2 floor (11 Oct 2026)
- Runs: q = 1025, gamma2 = 64, gamma1 = 32, 64 (`trilithium_toy_q1025.{txt,json}`); q = 513, gamma2 = 32, gamma1 = 64 (`trilithium_toy_q513_g64.*`). n = 4, 5 trials, seed 2026, exact enumeration as before.
- Branch-2 H^2 (vs simulator) by ratio gamma1/gamma2:

| gamma1/gamma2 | q = 257 | q = 513 | q = 1025 |
|---|---|---|---|
| 0.5 | - | 5.1e-3 | 5.7e-4 |
| 1 | 1.2e-3 | 1.3e-4 | 1.1e-4 |
| 2 | 7.1e-5 | 8.6e-5 | - |
| 3 | 5.7e-5 | - | - |

- Branch 3 keeps falling at every q (q = 513, gamma1 = 64: 1.7e-6; q = 1025, gamma1 = 64: 3.9e-6).
- Reading: the ratio alone does not explain the floor. Once gamma1 >= gamma2, branch 2 sits at about 0.6e-4 to 1.3e-4 for all three q, and it does not fall as q and gamma2 double. So the floor looks like a fixed feature of the branch-2 condition at n = 4, not a small-q artefact. Unverified guess: it comes from the special last HighBits cell (Decompose's q - 1 edge case) or from beta/gamma2 effects, either of which would persist as the box grows. Not tested. At n = 4 a 1e-4 gap needs about 1e4 rejected-in-branch-2 transcripts to see; says nothing about n = 256.

### Edge-cell test for the branch-2 floor (11 Oct 2026)
- `experiments/trilithium_edge_cell.py`, output `experiments/results/trilithium_edge_cell.{txt,json}`; n = 4, 5 trials, seed 2026 (reseeded per case, so full H^2 differs slightly from the earlier table). Branch-2 H^2 vs simulator, full and after removing every w_H with r1 = 0 in any coordinate (about 57% of mass kept):

| q | gamma2 | gamma1 | H^2 full | H^2 masked |
|---|---|---|---|---|
| 257 | 16 | 32 | 8.6e-5 | 3.6e-5 |
| 257 | 16 | 48 | 5.3e-5 | 1.8e-6 |
| 513 | 32 | 32 | 1.2e-4 | 3.8e-5 |
| 513 | 32 | 64 | 8.4e-5 | 1.3e-6 |
| 1025 | 64 | 64 | 1.2e-4 | 1.5e-5 |

- Reading: for gamma1 >= 2 gamma2 the masked gap is 30-65x smaller (about 1e-6, the size of branch 3) and keeps falling, so the floor comes mostly from the r1 = 0 cell (Decompose folds the values near q - 1 into it, making it wider). At gamma1 = gamma2 a smaller part (1.5e-5 to 3.8e-5) remains that still shrinks with gamma1. Caveat: the mask removes the whole r1 = 0 cell, not only the folded values, so this localises the effect to that cell rather than proving the fold is the cause.
- Relevance: real ML-DSA has the same folded cell (Decompose's q - 1 case), but at n = 256 with huge gamma1 the rejected w_H is statistically uniform anyway; this is a toy-size explanation, not an attack.

### Dimension trend by exact convolution (11 Oct 2026)
- n = 8 is out of reach for both methods we have: enumeration costs (2 gamma1)^n (10^12 at gamma1 = 16), and at q = 257 there are 8^8 HighBits cells, far too many to estimate gaps of 1e-5 by sampling. New exact method `harness/schemes/trilithium_conv.py`: build the distribution of w = A y on Z_q^n one coordinate at a time (memory q^n); branch 3 = box minus the z-ok product box; branch 2 = z-ok weighted by the r0 mask on the w grid. Matches enumeration bit for bit (`test_trilithium_conv.py`, 3 configurations).
- Run: `python -m experiments.trilithium_dim`, q = 17, gamma2 = 4 (2 HighBits values per coefficient), tau = 1, eta = 1, beta = 1, 5 trials, seed 2026 + n. Output `experiments/results/trilithium_dim.{txt,json}`. Squared Hellinger, means over trials:

| n | gamma1 | H^2 branch 3 vs sim | H^2 branch 2 vs sim | H^2 branch 3, s1 vs s1' |
|---|---|---|---|---|
| 2 | 8 | 2.6e-3 | 2.1e-3 | 1.0e-3 |
| 3 | 8 | 3.5e-5 | 1.8e-4 | 4.9e-5 |
| 4 | 8 | 5.4e-5 | 3.8e-4 | 2.2e-6 |
| 5 | 8 | 2.1e-7 | 1.4e-5 | 3.1e-7 |
| 6 | 8 | 9.1e-8 | 5.4e-6 | 6.7e-8 |
| 4 | 16 | 2.8e-5 | 8.6e-5 | 7.6e-7 |
| 5 | 16 | 7.0e-8 | 1.3e-5 | 3.0e-8 |
| 6 | 16 | 5.9e-8 | 5.0e-6 | 2.6e-8 |

- Reading: at fixed gamma1 both gaps fall as n grows, branch 3 by 2-3 orders of magnitude from n = 4 to 6, branch 2 by about 15-70x; the key dependence (s1 vs s1') falls too. Not monotone per step (n = 4 is above n = 3 for branch 3 at gamma1 = 8; 5 trials, random A), so no clean rate can be fitted. Branch 2 stays the larger gap (the r0-cell effect seen at q = 257). The direction supports the authors' heuristic: more dimension makes rejected w_H look more like the simulator, not less.
- Caveats: tiny q = 17 with only 2 HighBits values per coefficient, k = l = 1, tau = 1; a different regime from the q = 257 runs; 5 trials per point. n = 8 still not computed (q^8 = 7e9 states at q = 17).

### Declassified rejection bit and the CRP (Sec. 4.6-4.7, Alg. 11-14 read 11 Oct)
- What is declassified per attempt: w_H (both parties), then one bit b = rej_check(z, x) for the whole attempt (z and r0 checks combined), so rejected transcripts do not reveal which branch failed; our per-branch gaps are upper bounds for the mixture. On "OK", z goes to the Phone only, which verifies before sending it to the Server.
- rej_check (Alg. 13) is only AP-secure: a malicious Server can change its result. The paper argues (Sec. 4.7) the Server gains nothing: forcing "not OK" only hides a z it would have seen; forcing "OK" on a failing attempt is detected by the Phone's Verify.
- Our reading (hypothesis H-F3, analysis only, not run): tampering is additive on shares, so the Server can shift the interval tested for one coefficient (ineq(z_i + gamma1 - beta - 1 + delta, ...)). A shift that moves the interval also admits some honestly-failing z (|z_i| just over the bound): then the bit is "OK", the Phone's Verify fails and the Server is caught, but only after learning one bit about a rejected z_i, which depends on s1 (branch 3). Without detection the Server learns about rejected attempts only through "not OK" outcomes that would have been "not OK" anyway, which carry no information. So the leak looks bounded by roughly one bit per detected misbehaviour (a covert-security style trade-off), consistent with the paper's informal argument but not stated in it. Check what the Phone does after detection (stop forever, or retry) in Sec. 5 before claiming anything.
- CRP: honest CRP is an explicit assumption ("if CRP is honest"). In asymm_rp (Alg. 12) the CRP chooses the Phone's mask m, so a CRP colluding with the Server can unmask the Phone's shares of z and x. By design, not a finding. e_w generated by the CRP alone is argued safe via Bienstock et al. [11] (App. F not read).

### H-F3 checked against Sec. 5.2, Sec. 7 and App. F (11 Oct 2026, read fully)
- The UC proof does model tampering: a corrupted Server sends F_rej_check an arbitrary algorithm A, which the functionality applies to the honest Phone's shares of z and x (p. 23-24). Successful signing: simulator applies A to shares of the real z, fine. Unsuccessful signing: the simulator does not know the rejected z, so it applies A to made-up failing shares; "A may return b = 0 ... or b = 1, leading to the Phone determining that the Server has cheated in both systems".
- Sec. 7 / App. F: any detected cheating (failed MAC check or invalid signature) makes Phone and Server stop all further runs, so the adversary "would hence learn at most a single bit" (said of the CRP; the same logic applies to the Server).
- Our reading: the stop rule is what bounds the leak, as we guessed. But the simulation step above only matches the real world if A's output does not depend on the real rejected z. A Server that picks A = "1 iff z_0 = gamma1 - beta" (just outside the bound, a value whose probability depends on c s1) makes the Phone detect cheating with a different probability in the real and ideal worlds, and the environment sees when the stop happens. So the leak is the stopping time: at most about log2(number of attempts) bits, once, and the Server is exposed. Practically negligible and in line with the paper's "at most a single bit" spirit, but the proof text as written does not account for the detection probability differing (possible gap in the simulation argument, not an attack). Unverified: whether the formal F_ML-DSA allows selective abort; we did not read every functionality definition.
- CRP (App. F): the paper adds batched bit checks (about 2% extra communication) to stop a malicious CRP biasing y; e_w chosen by the CRP is argued safe via [11, Thm. 1]. Consistent with our earlier note.

## Full read (13 Oct 2026)

Read: all 67 pages of `papers/trilithium_2025-675.pdf` (text via pypdf), including App. A-F. Printed page numbers equal PDF page numbers. The reference list (p. 29-38) was scanned, not checked entry by entry. No proof re-derived; the claims below about gaps are our reading.

### Section-by-section summary (plain words)

- **Sec. 1 (p. 1-3).** Motivation: Smart-ID (phone + server RSA, millions of users) needs a post-quantum replacement. Contributions: two-party ML-DSA keygen and signing, UC proof, Rust implementation, an actively secure version of the Attrapadung et al. comparison, and a fast HighBits protocol.
- **Sec. 2 (p. 3-8).** Additive 2-out-of-2 sharing mod q between Phone (P) and Server (S), BeDOZa-style MACs (6 MACs per value for 2^-128 guessing, p. 25). "AA-secure" = active security against both; "AP-secure" = active against Phone, only *privacy* against Server (a malicious Server can change the output but learns nothing from messages). Everything is done for the "template" scheme (public key is the full t, signature (z, c)); hints are added afterwards from public data (p. 6). Func. 1 is the target functionality, with two switches: c = 1 means the commitment w_H of every attempt is given to the adversary, m = 1 means the Bienstock et al. e_w modification.
- **Sec. 3 (p. 8-10).** Zero-knowledge argument (read 8 Oct; re-read). Alg. 4 splits transcripts into three branches; branches 2 and 3 are covered by an "MLWR" assumption on (A, HighBits(A y)) with y uniform on a set S_A; the authors say known MLWR-to-MLWE reductions "do not really apply to the parameters of ML-DSA" (p. 10).
- **Sec. 4 (p. 10-18).** Building blocks: declassify (Alg. 5, Phone learns first), gen_small (Alg. 6, one-hot CR vector rotated by a public random), keygen (Alg. 7), zero_check (Alg. 8), symm_rp (Alg. 9, open w - s with CR mask s, then add digits with one-hot vectors), high_bits (Alg. 10, needs alpha to be smooth), gcom (Alg. 11: y from random bits, e_w from the CRP alone), asymm_rp (Alg. 12), rej_check (Alg. 13, AP-secure only), the full attempt (Alg. 14).
- **Sec. 5 (p. 18-24).** UC security: generic AA (Func. 3) and AP (Func. 4) functionalities; in Func. 4 a corrupted Server sends an *algorithm* A that the functionality applies to the honest Phone's shares (p. 20). Protocol 1 = Pi_ML-DSA. Simulators for corrupted Phone (5.1) and corrupted Server (5.2), including the "unsuccessful signing" argument (p. 24).
- **Sec. 6 (p. 24-27).** Costs: signing attempt 93-164 KiB each way, 14 rounds, CR to Server 55 / 71 / 96 MiB per attempt (Table 2; times M_rep = 4.25 gives the 234 MB per ML-DSA-44 signature quoted in Mithril's Table 1); keygen 3 rounds. e_w "decreases the probability of a signing attempt succeeding ... ca. 0.15 percentage points" (p. 27).
- **Sec. 7 (p. 28).** Deployment (Server and CRP in separate HSMs); malicious CRP can mount a selective-failure attack, but any detected failure stops all future runs, so "at most a single bit".
- **App. A (p. 38-39).** ineq / ch_vec / short_of / long_of algorithms. **App. B (p. 39-57).** Simulators for every subprotocol. **App. C (p. 58-60).** Correctness of zero_check, long overflow, inequality. **App. D (p. 60-62).** Literature on opening w_H in rejected runs (Cozzo-Smart, Barthe et al., Migliore et al., Azouaoui et al., Coron et al. who retracted their claim) and the derivation of Alg. 4 (Alg. 19-21). **App. E (p. 63-66).** Round / bit counts vs Bienstock et al. **App. F (p. 66-67).** Malicious CRP; batched polynomial check that CR bits are bits (under 2% extra traffic).

### Exactly what is released per signing attempt, and to whom

| When | Value | To whom | Notes |
|---|---|---|---|
| Keygen | A (public random), full t | P and S (t via AA declassify, P first) | template scheme: t, not t1, is the public key |
| Every attempt, masked | y' = w - s (symm_rp, p. 14), d = m + a v (zero_check), w = [v]_P - m (asymm_rp, P to S), f = v - r (ch_vec) | P and S | uniform if the CRP is honest; the CRP knows every mask |
| Every attempt | w_H = HighBits(A y [+ e_w]) | P and S (Protocol 1 step 3); also the adversary in Func. 1 with c = 1 ("com <- c * w_H", p. 7) | the H-F2 object |
| Every attempt | one bit b = rej_check(z, x), z and r0 checks combined | P and S (AP declassify, step 7) | which check failed is hidden |
| b = OK | Server's share of z to Phone; Phone verifies (template Verify); only then z to Server | P first, then S | if Verify fails the Phone stops forever |
| b = not OK | nothing else | | rejected z never leaves the MPC (in the honest case) |
| CRP | sends CR; receives nothing (Phone gets only a seed) | | |

### Adversary model

Static corruption of exactly one of Phone or Server; that party may be malicious (p. 1, p. 5). The CRP is trusted ("if CRP is honest", p. 5); Sec. 7 and App. F argue informally about a malicious but non-colluding CRP. CRP + Server collusion is out of scope (and fatal: the CRP knows the masks s and m, so with the Server's view it gets w = A y and the Phone's shares). UC with a global programmable random oracle G_pRO (p. 10); security with abort (any MAC failure stops). Some subprotocols (asymm_rp, ch_vec, ineq, rej_check) are only AP-secure: the Server can tamper with their outputs.

### Verdicts on the existing hypotheses

| Hypothesis (where listed) | Verdict | Evidence |
|---|---|---|
| "Trilithium heuristically assumes a rejected partial signature can be simulated as uniform; test whether rejected partial responses depend on s1 or s2" (DOSSIER 4.3 bullet 1, quoting Quorus p. 3) | **Revise.** What is released after a rejection is the commitment w_H, not a partial signature (no part of z leaves the MPC). The "heuristic" is an explicit MLWR-type assumption with sets S_A that depend on c s1, c s2 and (branch 2) on A itself. So the test target is rejected w_H, which is what H-F2 already does. | p. 9 ("we let the MLWR_{q,n,k,l,alpha,S}-assumption state ..."), p. 10 ("reductions from (M)LWR to (M)LWE ... do not really apply to the parameters of ML-DSA"). |
| H-F2: branch-3 (and branch-2) rejected w_H carries a secret-dependent shift; statistically invisible, needs a lattice distinguisher | **Confirmed as stated in the paper; one wording fix.** The branch-2 set {y' in S_{gamma1-beta-1} - c s1 : norm(LowBits(A y' - c s2)) >= gamma2 - beta} conditions directly on the rounding boundary, which is exactly where our toy found the larger (edge-cell) gap. Quorus's Lemma 8 (p. 24-25) shows that with a truly uniform a' the high bits after the shift do not depend on the shift, per coefficient; Trilithium has no e_w in the unmodified variant, so it cannot use that lemma and must assume A y behaves like uniform jointly. Wording fix: "A y mod q is uniform to extreme precision" is only true for low-order marginals; y has l N log2(2 gamma1) bits of entropy (ML-DSA-44: 18,432) against k N log2 q (23,552), so A y as a whole vector is not statistically uniform. Any leak needs a joint (lattice) distinguisher, as we said. | p. 9 Alg. 4; p. 10. Entropy count ours. |
| DOSSIER 4.3 bullet 2: rejection result is declassified to both; how many bits about c s2? | **Confirmed: one bit per attempt, z and r0 checks combined**, the same bit that the number of ML-DSA retries reveals. The authors claim "the frequency of retries is independent of the private key" (p. 6); this is exact for the z check (p_z depends only on parameters) and approximate for the r0 check (needs LowBits(A y - c s2) to be uniform per coefficient, true to high precision). | Alg. 13 (p. 18), Protocol 1 steps 6-8 (p. 21). |
| H-F3: a malicious Server can tamper with rej_check (AP-secure) and learn about rejected z | **Confirmed, and the paper's own simulator text shows the gap.** For unsuccessful signing the simulator applies the Server's algorithm A to made-up failing shares that "spell the message You're in a simulation" (p. 24) and argues A cannot communicate this back. But A's output b decides whether the Phone outputs bottom (b = 0) or detects cheating and stops (b = 1), and the environment sees which. A real rejected z depends on c s1 (branch 3), the simulated one does not, so A = "1 iff some coefficient of z equals a value whose probability depends on c s1" gives different stop probabilities in the real and ideal worlds. Also b = 0 outcomes are silent, so the Server can wait. Net leak: the stopping time, at most about log2(number of attempts) bits, once, after which the Server is exposed. The paper's informal bound for the CRP ("at most a single bit", p. 28) is in the same spirit. Severity: proof gap, not a practical attack. | p. 18 (informal argument "the Server's best tactic is to not tamper"), p. 20 (Func. 4 lets a corrupted S choose A), p. 24 (simulation of unsuccessful signing), p. 28 (stop rule). |
| DOSSIER 4.3 bullet 3: CRP is a trusted third party; what can it learn? | **Confirmed.** Passive CRP alone learns nothing (it gets no messages). CRP + Server collusion breaks everything (masks s, m known to the CRP). A malicious CRP can cause selective failures through wrong MACs on unused CR entries (App. F, p. 67: "Phone and Server not checking all MACs in the correlated randomness, e.g. the MACs of the unused elements of characteristic vectors"), bounded by the stop rule. In the modified variant the CRP alone chooses e_w (Alg. 11, p. 16); so towards the CRP the modified variant gives no more protection for rejected w_H than the unmodified one (the e_w noise is known to it). Only relevant if the CRP ever sees w_H, which the protocol does not give it. | p. 5, p. 16, p. 28, p. 66-67. |
| DOSSIER 4.3 bullet 4: two-party only, both must sign | **Confirmed.** Generalisation is only sketched (Sec. 7, p. 28: needs an ABB with mod-q / mod-2 conversion; the comparison would need replacing). | p. 28. |

### New observations (our reading)
1. **Hint failure is not handled.** p. 6 says "Given a public key and a signature of the template scheme, one can compute the hints for ML-DSA, resulting in a valid ML-DSA signature." That is not always true: if HW(h) > omega or norm(c t0) >= gamma2 the template signature cannot be turned into an ML-DSA signature (we measured 0.4-1.3% of line-3 passes in our Quorus runs, which use the same hint rule). Then z has already been revealed to both parties and a retry is needed. Harmless for security (z is accepted-distributed, same as Quorus's (w1, c, z, bottom) case), but missing from Func. 1 and from Alg. 14.
2. **Range of y differs from FIPS 204.** gcom builds y = -gamma1 + sum_{u=0}^{log gamma1} 2^u b_u, which is uniform on [-gamma1, gamma1 - 1] (App. F, p. 66 says the same), while Alg. 2 and FIPS 204 use [-gamma1 + 1, gamma1]. Accepted z is still uniform on the pass box (the shifted box still covers z - c s1 for all |c s1| <= beta) and p_z is unchanged, so no security effect; but the rejected-y sets of branch 3 are mirrored. Our toy (FIPS range) is equivalent up to the sign flip s1 -> -s1.
3. **Small typos:** Alg. 20, l. 13 (p. 62) has norm(c s1 + y') >= gamma1 + beta (should be gamma1 - beta); Alg. 4 branch 3 uses a tilde-S set that is defined as bar-S earlier.
4. **e_w and the success rate.** p. 27 claims e_w lowers the success probability by about 0.15 percentage points. In theory it should not change the line-3 pass rate (each coefficient of A y is already uniform, so the w0 marginal is unchanged). Our Quorus runs (same rule) gave M_rep 4.30 with e_w vs 4.32 without (400k vs 200k attempts, SE about 0.07 / 0.1 points on the success probability): a +0.1 point difference, about 2 sigma away from -0.15. Weak evidence against the paper's number; the paper gives no sample size.

### Comparison with `harness/schemes/trilithium_toy.py`
- Matches the paper: unmodified variant (no e_w), y uniform on [-gamma1 + 1, gamma1] (FIPS; Trilithium's implementation uses the mirrored range, see note 2), branch 3 = z check fails, branch 2 = z passes and LowBits(A y - c s2) fails, checked in that order as in Alg. 3. HighBits: the paper's definition (p. 6, w' = w + alpha/2 - 1, edge case w' = q - 1) is equivalent to FIPS Decompose, which the toy uses.
- One reporting point (no code bug): the paper's simulator (Alg. 21, p. 62) outputs HighBits of a *uniform* b in R_q^k, while our "H^2 vs sim" columns compare against HighBits(A y) with y uniform on the box. The toy already computes the distance from HighBits(A y) to HighBits(uniform) (`sd_sim_unif` in `trilithium_toy.txt`: 0.0015 at gamma1 = 32 and 0.00067 at gamma1 = 48, against the branch-3 conditioning gap `sd3_sim` 0.0046 and 0.0031) and `h2_3_unif`, but the notes only quote "vs sim". For the paper's exact assumption the relevant distance is rejected vs HighBits(uniform); by the triangle inequality it is at most the sum of the two gaps, and at toy size the two are of the same order. Suggest adding the `_unif` columns to the notes table; no code change required.
- The one-bit rejection (branches 2 and 3 are not distinguishable to the adversary) confirms what we already wrote: per-branch gaps are upper bounds for the released mixture.

### Reading status
- 2026-10-13: whole paper read (67 pages incl. App. A-F). Proofs in App. B read for structure; not re-derived.
