# Paper outline and scorecard (paper plan item 10, draft 16 Oct 2026)

Working claim: **a first systematic leakage evaluation of the threshold ML-DSA proposals in the NIST MPTC first call, with a reusable test harness that has positive and negative controls.** Not a break of an official submission. Every cell below points to the file that holds the evidence; anything marked "not read / not run" is stated plainly.

## Threat model (one paragraph for the paper)
Passive observer of signing transcripts (outsider), plus the insider/coordinator variants where a scheme's own text defines them. Question asked per scheme: does the published transcript carry bounded-noise or rejection-bias information about the long-term secret, and how many signatures until it is recoverable, compared with the scheme's own signing cap or proof bound?

## Scorecard (draft)

| Scheme | Channel tested | Result | Margin / status | Evidence |
|---|---|---|---|---|
| TALUS (arXiv v5, PW v0.22) | s2 via bounded noise, outsider | full-secret ILP recovery at 95% needs 2^16.01 / 2^17.40 / 2^17.30 signatures (-44/-65/-87), one ring element, 20 trials | +3.0 / +3.4 / +3.3 bits over the cap | `experiments/results/item8/summary.txt` |
| TALUS | key rotation | rotation is fresh keygen; share refresh would not reset leakage but is not what is specified | no hole | `notes/schemes/talus.md` (14 Oct) |
| TALUS | rejected attempts | first attempt succeeds ~98.0 / 99.6 / 99.2%; z-norm check never fired | extra data <= ~0.03 bits | `notes/schemes/talus.md` |
| TALUS | MPC insider (m >= T >= 2) | rough wall 2^24.8-2^29.7; m = 2 Fisher number re-checked exactly (within 1%) | 12-16 bits above cap; simulated at n = 8: attacker needs 1.5-2x (50%) / 4-6x (95%) the formula, so margin stands (`experiments/results/talus_m2_sim.txt`) | `experiments/results/talus_insider_wall.txt`, `talus_m2_fisher.txt` |
| TALUS | TEE coalition (m = 1) | below cap from T = 7 / 11 / 9 | authors concede; TEE not proposed | same |
| TALUS | below-wall partial recovery | 43-48% of s2 right at the cap (2 trials) | soft hint only, no attack shown | `experiments/results/partial_recovery.json` |
| TALUS | corrupt coordinator (rejected z) | authors' out-of-box tail probabilities reproduced by exact convolution: per session 2^-33.1 / 2^-35.5 / 2^-37.3 (paper 2^-32.5 / -34.7 / -36.6) | empty view except with prob 2^-9 over the key lifetime; checks their numbers, not their conclusion | `experiments/results/talus_coordinator_tail.txt` |
| Mithril (ePrint 2026/013) | s2 in hidden part, real Go transcripts (ML-DSA-44, (2,3)) | slope 0.004 +/- 0.10 on 39461 kept sessions | no s2 leak; only c t0 | `experiments/results/mithril_real_transcripts.txt` |
| Mithril | -65 a-posteriori sharing vs Category 3 | 203.8 bits baseline, 182.5-189.0 with hint; hint loss 14.8-21.3 (paper: 7-12) | proof-claim gap, not practical | `experiments/results/mithril_hint_estimator_full65.txt` |
| Mithril | Devevey et al. App. A.6 bound | printed bound invalid (below exact at 149 of 320 checked points); corrected bound proved | sessions 2^26-2^37 rather than 2^50 | `docs/a6_corrected_bound.md` |
| Kao P2 | W_i broadcast | sum W_i = A y is public, so s1 follows from one signature (text + toy test) | author contact first; real-size demo done 16 Oct: s1 from one signature, 15/15 keys at each of -44/-65/-87 (re-implementation, rejection checks in the clear) | `experiments/results/kao_p2_real_demo.txt`, `notes/schemes/kao-p2.md`, `docs/disclosure_drafts.md` |
| Quorus, Trilithium | read in full | hypotheses confirmed; paper inconsistencies noted (Quorus Func. 6 bound, Lemma 8 constant; Trilithium H-F3 simulation gap) | no attack claimed | `notes/schemes/*.md` |

Caveats to print under the table: toy and scaled-down rings are labelled as such; single ring element, not full secret; Sage lattice estimator replaced by a Python core-SVP estimate for hint accounting only where noted; Mithril Go code is the authors' repository, not an official submission package.

## Harness-as-contribution (controls)
Positive control: toy schemes with known leaks recovered (`harness/schemes/kao_p2.py`, edge/ILP estimators on synthetic bounded noise). Negative control: plain ML-DSA transcripts and ACVP pass (`experiments/mldsa_controls.py`, ACVP result in project-phase2-status). Architecture figure: `experiments/results/harness_architecture.png`.

## Section plan
1. Introduction and contribution list (survey, harness, per-scheme leakage margins, corrected bound).
2. Background: ML-DSA, rejection sampling, threshold constructions (short, with symbols defined at first use).
3. Threat model and method (edge estimator, ILP finish, Fisher walls, hint accounting).
4. Results per scheme (the scorecard, one subsection each).
5. Controls and validation.
6. Limits and what was not run (packages phase from March 2027).
7. Disclosure and responsible handling (item 11).

## Before submission
- [ ] Ask instructor about permission/disclosure; send emails only on the user's decision.
- [ ] Open-artifact script: one command per table/figure (item 12).
- [ ] Venue rewrite (item 13): PQCrypto 2027 LNCS, abstract 17 Nov, paper 24 Nov 2026.
- [ ] Re-verify every number above against its file before it enters the paper.
