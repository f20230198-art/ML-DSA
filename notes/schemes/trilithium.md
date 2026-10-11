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
