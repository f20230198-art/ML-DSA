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
