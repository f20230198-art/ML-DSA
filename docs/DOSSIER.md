# Threshold ML-DSA in the NIST MPTC Call: cryptanalysis dossier

As of 2026-09-29.

## Bottom line

- Four threshold ML-DSA proposals are in the NIST First Call (IR 8214C): **Mithril**, **Quorus**, **SplitForge (Trilithium)** and **TALUS**. All aim for signatures that verify under an unmodified FIPS 204 verifier.
- **Practical key-recovery attacks exist on TALUS** (earlier versions), published by Guilhem Niot (PQShield) as ePrint 2026/1386. Two independent attacks: Gaussian elimination on broadcast commitments, and a statistical attack from a removed rejection check.
- I found **no public key-recovery attack on Mithril, Quorus or Trilithium**. They keep the s2 rejection logic and do not publish A·(secret), so the TALUS attacks do not transfer directly.
- Best open targets: (1) TALUS's current per-key signing cap, (2) the accepted-z distribution of Mithril and the reveal-on-reject tweak of Quorus (Fisher-information and ILWE-style tests), (3) the heuristic rejected-transcript simulation in Trilithium.
- Scope: literature-and-spec assessment (written before any code). Harness code and a first TALUS experiment now exist; see docs/ROADMAP.md and docs/RUNBOOK.md for status. Section 7 lists exactly what I did and did not read.

## ML-DSA in 60 seconds

Signing: sample nonce y; w = A·y; w1 = HighBits(w); c = H(msg, w1); z = y + c·s1. Two rejection checks: ‖z‖∞ < γ1−β (hides s1) and ‖LowBits(w − c·s2)‖∞ < γ2−β (hides s2 and keeps the hint small). Signature = (c̃, z, h).

Thresholding is hard because s1, s2 and y are shared, HighBits is not additive, and the s2 check needs the full secret. Each design picks a trick: replicated short shares with local rejection (Mithril), generic MPC (Quorus, Trilithium), or pre-filtering nonces so the check always passes (TALUS).

Two facts drive most attacks:

- A is tall (k ≥ ℓ in every parameter set), so **A·x is invertible by Gaussian elimination**. No lattice problem is involved.
- z = y + c·s1 holds over the integers, so **any leak of y gives s1 = c⁻¹(z − y)**.

## The submissions

| Scheme | Team | Design | Online rounds | Trust model | Known attacks |
|---|---|---|---|---|---|
| Mithril | PQShield, Brave, Bristol (Celi, Delerue, del Pino, Espitau, Niot, Prest) | Replicated secret sharing with short shares, local per-party rejection sampling (hyperball), T ≤ N ≤ 6 (8 planned) | 3 per attempt, ~6 on average | Dishonest majority (T−1 corrupt), static; no identifiable aborts | None public |
| Quorus | J.P. Morgan (Bienstock, de Castro, Escudero, Polychroniadou, Takahashi) | MPC-friendly ML-DSA variant, UC-secure, n up to 64 | 16–29 broadcast rounds (per TALUS paper's table) | Honest majority | None public |
| SplitForge / Trilithium | Cybernetica (Dufka, Kravtšenko, Laud, Snetkov) | 2-party ML-DSA plus a correlated randomness provider (CRP) | 14 per attempt | CRP honest; active security against one party | None public; relies on a heuristic (see 4.3) |
| TALUS | Codebat (Kao, Chang) | Boundary Clearance Condition (BCC) nonce filtering, Shamir nonce DKG | 2 (PW v0.22); earlier versions claimed 1 | Honest majority N ≥ 2T−1 (MPC); TEE variant only as contrast | **Broken in earlier versions (Niot)** |

Related lattice signatures in the call but not ML-DSA-compatible: Tanuki, Hermine, Lemur, LoTRS. Out of scope unless wanted.

Timeline:

- TCPT3 preview talks: Sep 30 and Oct 5–7, 2026 (NIST pages disagree on exact days). The phase 3 list had no ML-DSA entry when I checked; recheck.
- Preliminary packages: Nov 30 – Dec 17, 2026 (expected).
- Package deadline: not before 2027-03-01.

## Published attacks on TALUS (Niot, ePrint 2026/1386)

**Attack 1: non-hiding commitments (passive, no corruption).** TALUS-MPC used Feldman-style commitments A·x, copying the discrete-log pattern. A is left-invertible (failure probability ≤ 2⁻¹⁵ for ML-DSA-44 and ≤ 2⁻³⁸ for -65/-87, by a union bound over the 256 NTT slots), so x = A⁺(A·x).

- Key generation broadcast A·s1,i, so every key share falls out.
- The blame phase broadcast A·ŷ_h. Summing gives the aggregate nonce ŷ, then s1 = c⁻¹(z − ŷ) from **one signature**.

**Attack 2: removed s2 rejection check (TALUS-TEE and TALUS-MPC).** Each signature releases v = Az − c·t1·2^d = w − c(s2 − t0). With HighBits(w) known from the hint, the observable is b = −c·s′ + e, where s′ = s2 − t0 and e = LowBits(w) is roughly uniform on [−γ2, γ2]. This is LWE without modular reduction (ILWE; Bootle et al., ASIACRYPT 2018). Least squares plus rounding recovers s′, then s1 = A⁺(t1·2^d − s′).

- Sample estimate: N ≳ 4γ2² / (3τ). The note's table: ~3.1×10⁸ (ML-DSA-44), 1.9×10⁹ (-65), 1.5×10⁹ (-87). The abstract says "a few hundred million"; the table is the safer number.
- The estimate ignores the bounded (not Gaussian) noise and lattice reduction, which Niot expects would cut it substantially.

**Niot's remark on fixing it.** Reinstating the check is not enough: a corrupted party can bias its nonce contribution (e.g. y_i = 0) so the check always passes, restoring the statistical attack.

**Authors' response (arXiv note 2026-07-09, PW v0.22 dated 2026-08-11).** They acknowledge both attacks. Commitments are replaced by zero-knowledge well-formedness proofs (the only public lattice output of the DKG is t). The s2 channel is handled by a **mandatory per-key signing cap** of about 2¹³ / 2¹⁴ / 2¹⁴ signatures (ML-DSA-44/65/87), enforced by key rotation, against a claimed integer-uniqueness wall q_uniq of about 2¹⁵·² / 2¹⁶·⁴ / 2¹⁶·². Each preprocessed nonce is bound to one quorum and erased after use.

TALUS's own paper also proves a lower bound: any FIPS-exact scheme that reveals a summed (Irwin–Hall) nonce leaks Fisher information about s1 per signature, giving key recovery after ~2³⁰ signatures at ML-DSA-65. They claim Quorus and Trilithium avoid this because they reveal an internally uniform nonce.

## Per-scheme attack surface

### 4.1 Mithril

Replicated sharing of a short key, per-party local rejection with hyperball sampling, so no global abort MPC. Security is a game-based reduction (ROM) to MLWE and ML-DSA unforgeability under static corruption of up to T−1 parties.

To test (hypotheses until checked against the full paper, ePrint 2026/013):

- **Accepted-z distribution.** Parameters target success probability 1/2 per attempt (single-signer ML-DSA is ~1/4), so the nonce distribution and rejection region differ from FIPS 204. Compute the concrete Rényi or Fisher-information loss at q_s = 2⁶⁴ and compare against the lower-bound style attack TALUS proves.
- **A posteriori key sharing.** The adversary gets a noisy hint on the existing ML-DSA secret; the team quantifies the loss at 7–12 bits. Re-derive with the lattice estimator using the exact share subset T−1 corrupted parties hold.
- **Adaptive corruption.** Not proven; argued heuristically with loss ≤ 5 bits for N ≤ 6. A proof gap, not an attack.
- **Selective aborts.** No identifiable aborts, so corrupted parties can abort after seeing honest contributions. Check whether aborted-attempt transcripts leak anything the proof does not cover.
- **Implementation.** The Go proof of concept uses floating point for hyperball sampling; a fixed-point C reference is planned. Look for sampler bias and timing leakage.

Context: Niot is on the Mithril team and wrote the TALUS attack, so expect this design to have been stress-tested against those patterns.

### 4.2 Quorus

MPC-friendly variant of ML-DSA signing (still verifies under the standard verifier) with a UF-CMA⊥ proof in the QROM, honest majority, UC-realized.

- **Reveal-on-reject tweak.** The variant releases (w1, c, ⊥) for rejected attempts and proves this simulatable. Test empirically: run rejected-attempt transcripts through least-squares and ILP leakage tests against c·s1 and c·s2.
- **Which check failed.** The paper itself cites a key-recovery attack (ZWSY25) that works when this bit leaks; other work recovers keys from rejected-signature challenges via integer linear programming. Verify any implementation reveals only ⊥.
- **Building blocks.** F_RejSamp, BatchedOR and offline preprocessing (F_Prep, F_LTC) are where implementation mistakes would hide.
- **Honest majority** is a hard assumption. Check behavior at N = 2T−1 boundaries.

### 4.3 SplitForge / Trilithium

- Quorus's authors state Trilithium heuristically assumes a rejected partial signature can be simulated as uniform. This is the most attackable statement in the design: test whether the distribution of rejected partial responses depends on s1 or s2.
- The rejection-check result is declassified to both parties; look at how many bits per attempt that reveals about c·s2.
- The correlated randomness provider is a trusted third party; check what it can learn from its own correlated values.
- Two-party only, and both parties must sign (2-of-2).

### 4.4 TALUS v0.22

- **The signing cap is the whole security argument for the s2 channel.** It sits ~2 bits under the authors' uniqueness wall and ~14–17 bits under Niot's unoptimized estimate. The gap is bridged by an information-theoretic argument; an optimized attack (bounded-noise estimator, ILP, lattice reduction) is what could close it.
- Under BCC the noise e = LowBits(w) is restricted to (−γ2+β, γ2−β), so it has sharp edges. Sharp edges carry more information per sample than variance alone.
- **Practicality.** A cap of ~8–16k signatures per key, enforced by rotating the public key, undermines FIPS-compatible threshold signing: certificates and pinned keys cannot rotate every few thousand signatures.
- Other surfaces: ZK share well-formedness, the blame procedure, quorum binding (a reuse observation was reported by Sunghyeon Jo on an earlier version), malicious nonce bias (Niot's y_i = 0 point).

### 4.5 Kao's predecessor design (arXiv 2601.20917, Shamir nonce DKG)

Not itself a Call submission, but TALUS builds on it and it shows the same patterns:

- **Profile P2 (fully distributed) broadcasts masked commitments W_i.** The paper's own Remarks 11 and 15 show an exposed λ_h·A·y_h gives y_h and then the key. Masks only hide W_i when |S∖C| ≥ 2. With |S| = T and T−1 corrupted parties inside S, |S∖C| = 1, so the masks are computable by the adversary. The paper's footnote admits this at T = N; the same holds for any |S| = T. Yet the headline claim is UC security against up to N−1 corruptions. Confirm carefully; if right, it is a one-signature key recovery.
- **Profile P1 (TEE)** reconstructs c·s2 inside the enclave; with c, that gives s2 outright, so the design rests on the enclave.
- **Key DKG uses Feldman-style commitments.** Check Appendix B.1 for the A·s1,i pattern Niot broke in TALUS.
- **Nonce loss bound.** The paper says the Irwin–Hall loss is < 0.013 bits per signature and fine for any polynomial q_s, but its theorem is non-vacuous only for q_s < 16,000, and the TALUS paper later proves an attack at ~2³⁰.

## Systematic checklist (reusable across all schemes)

1. **Published A·x of a secret or nonce?** Left-invertible, so x = A⁺(A·x). Check DKG broadcasts, blame and identifiable-abort data, commitments.
2. **Any nonce leak?** Then s1 = c⁻¹(z − y). Check masks, broadcasts to coordinators, what a corrupted coordinator or combiner sees.
3. **Rejection checks removed, moved or altered?** Regress released values against c·s1 and c·s2 (ILWE, least squares, then bounded-noise and ILP refinements).
4. **Non-uniform accepted-z distribution?** Compute Fisher information about s1 per signature; the wall is ~4/(I·τ) signatures.
5. **Rejected-attempt transcripts.** What is revealed, and does the proof or simulator cover it? Do implementations leak which check failed?
6. **Malicious nonce contributions.** Can a corrupted party bias the aggregate nonce (e.g. y_i = 0) so a check always passes or a distribution shifts?
7. **Quorum and session binding.** Nonce reuse across quorums or sessions, unique session identifiers, erasure.
8. **Corruption model gaps.** Static-only proofs, honest-majority boundaries (N = 2T−1), conditions like |S∖C| ≥ 2 hiding in footnotes.
9. **A posteriori key sharing and hints.** Quantify lattice hardness loss with the shares an adversary actually holds.
10. **Implementation.** Floating-point samplers, timing, test vectors, whether reference code matches the spec.

## Ranked plan

1. **Build a leakage-testing harness.** Simulate each scheme's public transcripts (including aborted attempts) on synthetic keys, then run the checklist tests (least squares, ILP, Fisher information) automatically. This is the reusable contribution.
2. **TALUS v0.22 cap.** Reproduce Niot's estimator, replace least squares with a bounded-noise or ILP estimator, and measure samples needed against the cap (2¹³–2¹⁴) and the uniqueness wall (2¹⁵–2¹⁶). Either outcome is publishable: recovery below the cap breaks the design; recovery only above it gives a concrete margin.
3. **Mithril accepted-z and hint accounting** at q_s = 2⁶⁴, plus exact share-subset analysis.
4. **Quorus reveal-on-reject and Trilithium rejected-partial** statistical tests.
5. **Kao's P2 and DKG claims** as a confirmed-or-refuted note, since they may carry into TALUS's package.
6. **Packages phase.** When packages appear (from March 2027), rerun the harness on the actual reference code.

If you publish, contact the teams first (standard practice) and post to ePrint (attacks category); NIST's MPTC forum is where the Call's discussion happens.

## What I read and what I did not

- Read in full: Niot's note, TALUS preview writeup v0.22, Kao's arXiv 2601.20917, Mithril preview writeup v1.0.
- Read partly: TALUS arXiv (abstract, the added note, sections through 7.4).
- Not opened: full Mithril, Quorus and Trilithium papers, any implementation code. Quorus and Trilithium claims come from abstracts and other papers' descriptions.
- No experiments run. Section 4 suggestions are hypotheses, not results.
- Niot's abstract and table disagree slightly on sample counts; the table is used above.

## Sources

- [NIST Threshold Call submissions page](https://csrc.nist.gov/Projects/threshold-cryptography/tcall-1)
- [Niot, Key-Recovery Attacks on TALUS (ePrint 2026/1386)](https://eprint.iacr.org/2026/1386)
- [TALUS preview writeup v0.22](https://csrc.nist.gov/csrc/media/Projects/threshold-cryptography/documents/TCall-1/TALUS-PW02.pdf)
- [TALUS (arXiv 2603.22109)](https://arxiv.org/abs/2603.22109)
- [Kao, Threshold ML-DSA via Shamir Nonce DKG (arXiv 2601.20917)](https://arxiv.org/abs/2601.20917)
- [Mithril preview writeup](https://csrc.nist.gov/csrc/media/Projects/threshold-cryptography/documents/TCall-1/Mithril-PW01.pdf) and [Efficient Threshold ML-DSA (ePrint 2026/013)](https://eprint.iacr.org/2026/013)
- [Quorus preview writeup](https://csrc.nist.gov/csrc/media/Projects/threshold-cryptography/documents/TCall-1/Quorus-PW01.pdf) and [Quorus (ePrint 2025/1163)](https://eprint.iacr.org/2025/1163)
- [SplitForge preview writeup](https://csrc.nist.gov/csrc/media/Projects/threshold-cryptography/documents/TCall-1/SplitForge-PW01.pdf) and [Trilithium (ePrint 2025/675)](https://eprint.iacr.org/2025/675)
- [NIST IR 8214C announcement](https://www.nist.gov/news-events/news/2026/01/nist-first-call-multi-party-threshold-schemes-nist-ir-8214c)
