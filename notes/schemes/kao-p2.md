# kao-p2

Source: Leo Kao, "FIPS 204-Compatible Threshold ML-DSA via Shamir Nonce DKG", arXiv 2601.20917v6 (3 Mar 2026), downloaded and text-extracted on 2026-10-06.

## Design summary

- Key and nonce are both degree-(T-1) Shamir sharings over Z_q. Response z_i = y_i + c*s1,i (no mask); the combiner computes z = sum lambda_i z_i (Alg. 3, lines 25 and 29).
- Commitment masking (Sec. 3.5, Alg. 3 line 13): W_i = lambda_i * A * y_i + m_i^(w), where m_i = sum_{j>i} PRF(seed_ij, ctx) - sum_{j<i} PRF(seed_ji, ctx). Lemma 1: masks sum to zero.
- Three profiles. P1 (TEE coordinator) and P3+ (2PC) send W_i only to a coordinator that publishes (w1, c~). P2 (no coordinator) "parties broadcast W_i directly and rely on mask hiding (Lemma 2, requiring |S minus C| >= 2)" (Remark 11, last paragraph).

## Exact claim tested

Dossier 4.5: in P2, with |S| = T and T-1 corrupted parties in S, |S minus C| = 1, the honest party's mask m_h is computable from the corrupted parties' seeds, so lambda_h*A*y_h is exposed, then y_h by linear algebra (A is k x l with k > l, injective), then s1,h = c^-1 (z_h - y_h), with z_h from the public signature minus the corrupted parties' own z_j. Plus the T-1 corrupted shares this gives s1.

## What the paper itself says (quoted, section numbers from v6)

- Remark 11 (Sec. 3.6): "if W_h were broadcast and the adversary controls all other parties in S, the pairwise mask m_h^(w) would be fully computable ... revealing lambda_h A y_h", with recovery y_h = (A^T A)^-1 A^T (lambda_h A y_h)/lambda_h, and "revealing A y_h enables key extraction via z_h = y_h + c s1,h".
- Remark 15 (Sec. 4.1): "if broadcast with |S minus C| = 1, the adversary could recover y_h from lambda_h A y_h ... then extracts s1,h". "In P2, mask hiding (Lemma 2) protects broadcast W_i under the existing |S minus C| >= 2 condition".
- Lemma 2 (Sec. 4.3): masked values are computationally uniform "provided |S minus C| >= 2".
- Table 1 footnote and Sec. 7 ("Commitment mask hiding for T = N"): "At T = N with N-1 corruptions, mask hiding does not hold in P2"; "a single honest party's commitment and r0-check values are not hidden in P2".
- Abstract, Sec. 1, Sec. 6.3: P2 "tolerates N-1 corruptions"; Theorem 7 / Theorem 16 are only about UC realization of the r0-check functionality F_r0 (they do not cover W_i). Appendix M.1 (Simulator 17): "The proof assumes |H| >= 2".
- Corollary 5 (App.), item 1: P2 has "EUF-CMA security under Module-SIS (inherited from single-signer ML-DSA, Theorem 2)"; Theorem 2 Game 4 step 4 uses Lemma 2 to simulate W_j, V_j.

## Experiment (toy) and result

`harness/schemes/kao_p2.py`, tests `harness/tests/test_kao_p2.py` (5 tests, about 1 s). Toy: real q = 8380417, n = 8, k = 4, l = 3, Shamir over Z_q, nonce DKG with short constant terms plus uniform higher coefficients, real pairwise PRF masks (SHAKE-256), sparse invertible challenge.

1. Individual-mask attack (the dossier claim): recovers the honest party's key share s1,h exactly and then the whole s1, from ONE signature, for (N,T) = (3,3) and (5,3). Control with |S minus C| = 2: fails (the honest-honest seed is unknown), as the paper says.
2. Extra observation (not in the dossier): the sum of all broadcast W_i is exactly A*y because masks cancel (Lemma 1). So if every W_i is broadcast in P2, anyone, including an outside eavesdropper, gets A*y, then y, then s1 = c^-1 (z - y), with NO corruption and for any |S minus C|. The toy confirms this algebra (tests pass for (3,3), (4,3), (5,4)). Whether the real P2 broadcasts every W_i is NOT settled by what I read (see below).

## Gate D verdict (2026-10-06)

- Branch (a): concrete recovery on the toy, but it re-derives what Remarks 11 and 15 and the Table 1 footnote already state; it is NOT a new weakness of the |S minus C| = 1 case taken alone. The authors disclose that P2 mask hiding fails at |S minus C| = 1.
- What may be a real inconsistency: the paper still claims EUF-CMA / dishonest-majority unforgeability in P2 up to N-1 (Def. 4 allows the adversary to corrupt T-1 parties and sit in a signing set with one honest party; Corollary 5 item 1 inherits Theorem 2, whose Game 4 step 4 needs Lemma 2, which needs |S minus C| >= 2). A one-signature key recovery contradicts that claim. The paper's wording separates "unforgeability" from "privacy", but key recovery is a forgery. So: the N-1 unforgeability claim for P2 contradicts the paper's own Remark 11 unless it is restated as |S minus C| >= 2, i.e. at most T-2 corruptions inside signing sets. This is a statement about the paper's text, not about a deployed system (P2 is not a Call submission; TALUS uses a different, BCC-based design).
- Stronger point to put to the authors: aggregate A*y is public if W_i are broadcast. If so, P2 leaks at every |S minus C|, and Lemma 2 (individual uniformity) does not help because the sum is not hidden. The proofs only simulate each W_j as uniform and do not account for the sum. Unconfirmed.

## What was NOT read / NOT modelled

- Not read line by line: Appendices A, C-L, N, O except the pieces quoted above, benchmark sections, proofs of Theorems 2 and 3 beyond Game 4. The Rust code is "released upon publication" and was not available.
- Possible escape: the 5-round P2 (Sec. 6.3, App. O) may hold the masked values inside the MPC/combiner so that only the combiner sees W_i; I found the combiner step described for the r0-check shares only, and the main-text Remarks say "parties broadcast W_i directly". Not resolved.
- Toy does not model rejection sampling, the r0-check, HighBits and hints, the MPC, the blame protocol, the key DKG, multiple signatures, or real ExpandA. A is uniform random; full column rank holds. n = 8 only, so no claim about timing at n = 256.
- Coordinate with the author (Leo Kao / Codebat) before any disclosure. Nothing has been published.

## Reading status

- arXiv v6 PDF downloaded, 98 pages, extracted with pypdf. Read the parts listed in notes/papers.md row 12.
- Appendix B.1 key DKG: each party shares local s1(i), s2(i), broadcasts Feldman-style commitment t(i) = A s1(i) + s2(i). The TALUS-type A*s1,i leak pattern is not checked here.
