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

## W_i question answered from the paper text (11 Oct 2026)
- PDF now local: `papers/kao_2601-20917v6.pdf` (arXiv v6, 112 pages; arXiv allows scripted download). Code still "released upon publication".
- Read fully on 11 Oct: Algorithm 3 (Sec. 3.6), Remark 11, Lemma 1 and Lemma 2, Theorem 2 and Corollary 1, App. A (A.1, A.2), App. I, App. J headings, App. M.1 (Simulator 17, Phases 0-2).
- The paper states P2 broadcasts every W_i: Fig. 1(b) "P2: all values broadcast"; Remark 11 profile paragraph "In Profile P2 (no designated coordinator), parties broadcast W_i directly and rely on mask hiding (Lemma 2)"; App. M.1 "in P2, each party broadcasts W_i = lambda_i A y_i + m_i to all other parties".
- Lemma 1 / Alg. 3 line 17: the masks cancel exactly, sum_i W_i = A y = w. So in P2 every participant (and anyone who sees the broadcast) learns the full w = A y, not just w1 = HighBits(w). With the public signature: A z - w = c A s1, so A s1 = c^{-1}(A z - w), and s1 follows by the left inverse of A that Remark 11 itself uses. Full key recovery from one P2 signature, with any number of honest parties. Our toy `attack_aggregate` (6 Oct) does exactly this; `test_aggregate_attack_recovers_key_for_any_honest_count` passes (rerun 11 Oct).
- Why the paper's proof misses it: Lemma 2 shows each individual W_i looks uniform when |S minus C| >= 2, which is true; but the sum of all W_i is not hidden. Simulator 17 Phase 2 makes honest W_i from its own simulated nonces, so their sum is A y~, inconsistent with the real signature (A z - sum W~ is not c times a short-plus-public value), which a distinguisher can check.
- Status: confirmed from the paper's own text plus our toy (small n, no rejection/hints/MPC). Not run on the author's code (not public). Only Profile P2; P1 (TEE) and P3+ send W_i to a coordinator only and are not affected. Possible escape we could not find in the text: an implementation that computes w inside the MPC. COORDINATE WITH THE AUTHOR (Leo Kao) BEFORE ANY DISCLOSURE.
- Also from Theorem 2 / Corollary 1 (author-stated, not our finding): the proven unforgeability bound is 96 - 0.0066 q_s bits for |S| <= 17, non-vacuous only for q_s < 16,000 signing queries (about 85 bits at q_s = 1,600). Far below the 2^50-2^64 query budgets of Mithril or NIST practice.
- Still not read: App. B.2-H, K, L, N, O in full (headings only). (Done 13 Oct, see below.)

## Appendices B.2-O read (13 Oct 2026)

Read in full from `papers/kao_2601-20917v6.pdf` (pypdf text, PDF pages 50-73; printed page numbers below). Also re-read the end of App. A.2 (p. 50). Not read: App. P onwards.

Findings checked: (1) P2 broadcast makes sum W_i = A y public, so s1 follows from one signature; (2) the N-1 unforgeability claim; (3) key-DKG commitment t(i) and the TALUS A*s1,i pattern.

- **A.2 end (p. 50), privacy simulator.** "The adversary observes only (w1, c~) broadcast by the coordinator (individual W_j are sent only to the coordinator; see Remark 11)". So this proof is written for P1/P3+, not P2. For |S\C| = 1 it claims s1,h stays private because z_h = y_h + c s1,h is a BDD instance; in P2 that fails once A y_h (or A y) is known. Impact: no rescue; the privacy proof does not cover P2 broadcast.
- **B.2 Nonce DKG (p. 51).** Short constant term in [-floor(gamma1/|S|), floor(gamma1/|S|)], uniform higher coefficients; y = sum of constant terms (Irwin-Hall); each honest y_h has high min-entropy (Thm 3). Impact on (1): none. Min-entropy of y_h does not help once A y is published: y is recovered by linear algebra, not guessed.
- **B.3 Security properties (p. 51).** Correctness, secrecy ("Any coalition of < T parties learns nothing about the secret beyond what is revealed by public commitments"), robustness (Feldman for key DKG; nonce DKG has no VSS, cheating caught at signing). Nonce share privacy "is the key enabler for eliminating the two-honest requirement ... in coordinator-based profiles (P1, P3+; see Remark 11)". Impact: the paper itself limits the |S| = T benefit to P1/P3+, consistent with (2).
- **C Proactive security (p. 51-52).** Refresh by adding random sharings of 0; forward secrecy for past signatures under M-LWE. Impact on (1): none; the attack recovers s1 itself, which refresh does not change.
- **D Renyi bounds (p. 52).** ML-DSA-65: per-coordinate R2 - 1 from 8.9e-6 (|S| = 4) to 4.1e-2 (|S| = 33); full-vector R2 about 25.4 (|S| = 17) to 275 (|S| = 33). Impact: none on (1)-(3).
- **E Rejection sampling (p. 53).** Single-signer about 20% per attempt (62% x 32%); threshold empirical 21-45%; parallel attempts, precomputed (y_i, w_i = A y_i). Impact: none (attack needs one accepted signature).
- **F Naive comparison (p. 53).** Table 13: naive 0.2^T vs measured 23-32%. Impact: none.
- **G Nonce range rounding (p. 53-54).** Range shrinks by r < |S|; harmless for |S| <= 196. Impact: none.
- **H UC framework (p. 54-56).** Remark 23: "This appendix proves UC security for the r0-check subprotocol (Profile P2, Theorem 7) ... realization of the full F_ThreshSig ... follows by UC composition with the nonce DKG and signing-step sub-protocols." H.1/H.2 recall UC definitions and SPDZ, edaBits, binary-circuit functionalities. Impact: supports (2): the N-1 UC theorems cover only the r0-check.
- **K Simulator 15 (p. 58-60).** Simulates the r0-check MPC: random SPDZ shares, one-time-padded masked_j = w'_j + r_j (edaBit r_j), uniform Beaver (d, e), backward-simulated AND tree. Impact: none on (1); W_i never appears. These values are padded by a fresh secret r_j, so their sum does not leak (unlike W_i, whose PRF masks cancel).
- **L Hybrid argument (p. 60-64).** H0-H6 for the r0-check only: SPDZ eps < 2^-54 with a 64-bit MAC field (Remark 26: only 2^-12.4 with MACs over F_q), edaBits < 2^-53.9, then perfect steps. Impact: none on (1)-(3).
- **M Main theorem (p. 64-66), beyond M.1.** Thm 16: Pi_r0 UC-realizes F_r0-check against "up to N-1 parties". Corollary 5 item 2: "Note: unforgeability and key secrecy require |C| <= T-1 ... The N-1 bound here refers to the r0-check subprotocol's leakage, not the full signing protocol's security model." Corollary 5 privacy proof (p. 65-66): for failed attempts "the result bit is determined by the public broadcast (c~, w)". Corollary 6 (p. 66): Pi_P2 UC-realizes F_ThreshSig with eps <= eps_SPDZ + eps_edaBits + (N-1) eps_PRF, no |H| >= 2 condition stated, while Simulator 17 "assumes |H| >= 2".
  - Impact on (1): SUPPORTS. The paper's own proof calls the full w (not only w1) a "public broadcast" in P2; with w public, A z - w = c A s1 gives s1.
  - Impact on (2): clarifies, does not rescue. N-1 in Thm 16 is now explicitly r0-check leakage only, but unforgeability is still claimed for |C| <= T-1, which includes |S\C| = 1 (and at T = N that is N-1). Corollary 6 claims the full protocol with no |H| >= 2 condition, contradicting Simulator 17. Since w is public at any |H|, Simulator 17 Phase 2 is wrong even with |H| >= 2.
- **N Complexity (p. 68-69).** 8 rounds, O(n m log q) bits, about 30 KB per party. Impact: none.
- **O 5-round P2 (p. 69-73).** Combiner-mediated commit-then-open of the r0-check shares [masked_j]_i = [w'_j]_i + [r_j]_i; the combiner "performs no cryptographic operations" and releases all openings to everyone; Thm 22 eps < 2^-53. Impact on (1): does NOT rescue. Only r0-check shares go through the combiner; nothing says W_i stops being broadcast. This closes the "possible escape" listed above as far as the text goes (an implementation could differ; code not public).
- **Finding (3), key DKG (B.1, B.3).** The broadcast is t(i) = A s1(i) + s2(i) of each party's own short contribution, with fresh short noise s2(i): an MLWE sample; the sum is the public key t. The TALUS pattern (noiseless A s1,i of the Shamir shares, DOSSIER line 45) does not appear in App. B-O. Caveats: the text names Feldman but gives no per-coefficient commitments, so how party j checks its received share s1,j(i) against t(i) is unspecified (a verifiability gap, not a leak); "for lattice-specific VSS/DKG, see [ENP24]" is only a pointer.

**Verdict (13 Oct).** No appendix contradicts finding (1); Corollary 5 (p. 65-66) strengthens it by calling (c~, w) "the public broadcast", and App. O removes the 5-round combiner as a textual escape. Finding (2) stands, sharper: the Corollary 5 note restricts N-1 to r0-check leakage, but Corollary 6 claims full F_ThreshSig with no |H| >= 2 condition while Simulator 17 needs it. Finding (3): no A*s1,i-type leak; t(i) carries noise s2(i). Still not run on the author's code (not public).

**Suggested edits to docs/disclosure_drafts.md (NOT applied).** In section 1, after "Lemma 2 hides each individual W_i, but not their sum.", add: "Your own proof of Corollary 5 (p. 65-66) also treats (c~, w) as the public broadcast in P2, and the 5-round combiner of App. O handles only the r0-check shares, so it does not seem to change this." After the Simulator 17 sentence, add: "Corollary 6 states that P2 realizes F_ThreshSig with no |H| >= 2 condition, while Simulator 17 assumes |H| >= 2."

## 2026-10-16: end-to-end at real ML-DSA size (paper plan item 7)

`harness/schemes/kao_p2_real.py`, `experiments/kao_p2_real_demo.py`, results `experiments/results/kao_p2_real_demo.txt` (+ per-parameter JSON), tests `harness/tests/test_kao_p2_real.py`.
- Model: real ML-DSA-44/65/87 keygen, ExpandA, SampleInBall, HighBits, hints; Shamir key and nonce DKG over Z_q; pairwise SHAKE-256 masks that cancel; every W_i broadcast (the P2 profile). Combined signature passes this repository's unmodified FIPS 204 Verify.
- Attack (outsider, public data only: pk, message, signature, all W_i of the accepted attempt): w = sum W_i = A y, solve A y = w per NTT slot, s1 = c^-1 (z - y). Result: s1 recovered exactly from ONE signature in 15/15 keys per parameter set (configs (N,T) = (5,3), (3,2), (5,5); 5 keys each); pk consistency check passes. Control with one W_i withheld: 0/15 per set.
- Not modelled / caveats: rejection checks run in the clear from the dealer's secret (stand-in for the paper's r0-check MPC; the accepted transcript is unchanged); no real network, blame protocol or key DKG (key is dealt, then Shamir-shared); the demo recovers s1 only, not s2/t0 (a forgery would still need them); only the P2 profile with W_i broadcast, which is what the paper text says (Fig. 1b, Remark 11, App. M.1). The author's code is not public, so this is a re-implementation of the paper's description, not a test of the code. Contact the author before any disclosure.
