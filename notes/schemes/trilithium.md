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

None yet.

## Reading status

- 2026-10-08: Sec. 3 (zero-knowledge of the identification protocol, Alg. 4, MLWR discussion) read fully; table of contents and Sec. 4 headings mapped. Not read: Sec. 4 protocols in detail, Sec. 5 simulators, App. B proofs, App. D (literature on rejected transcripts).
