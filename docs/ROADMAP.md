# Roadmap

Ordered as in the dossier's ranked plan. The detailed stages, gates and paper framing are in `docs/PLAN.md` (stages A to G).

## 0. Setup
- [x] Pick language/tooling (Python + numpy/scipy). Sage and fpylll are NOT installed (checked 6 Oct); Docker is, so a Sage image is an option for the Mithril lattice-estimator stage
- [x] PLAN Stage A: NTT, SHAKE sampling, hints, full sign/verify with all attempts; byte-identical to dilithium-py oracle for -44/-65/-87 (6 Oct); passes 81 official NIST ACVP vectors (keyGen, pure sigGen, sigVer; 8 Oct). PreHash and external-mu not implemented
- [x] PLAN Stage B (13 Oct): `TalusBCCView`, `MithrilView` and adapter `observations_to_cb` in `harness/schemes/views.py`; estimators unchanged. Gate B passed end to end: real ML-DSA-44 attempts -> TalusBCCView -> edge estimator recovers s2 - t0 for 2/2 keys at N = 2e5 and 4e5 accepted, 0/2 at 1e5 (`experiments/gate_b_views.py`, seed 2029). Mithril view uses synthetic r1, r2 stand-ins
- [x] Fix stale line in DOSSIER and README ("no code has been run")
- [x] Verify dossier sources and recheck TCPT3 schedule / phase 3 list (13 Oct, docs/nist_call_and_sources_check.md; dates fixed in DOSSIER; open: recheck Quorus/Trilithium claims against their 2026 ePrint revisions, SplitKey writeup says CRP can be made malicious-secure)

## 1. Leakage-testing harness
- [x] ML-DSA reference primitives: params, rounding, ring mult, NTT, hints, SHAKE sampling, full sign/verify; NIST ACVP vectors pass (8 Oct)
- [x] Transcript simulator interface: `Attempt` records plus `SchemeView`; controls pass; TALUS, TALUS v0.1 and Mithril views added (13 Oct)
- [x] Estimators (13 Oct): least squares (`ilwe.py`), bounded-noise = Chebyshev LP (`edge.py`, `edge_gpu.py`), ILP finishing (`ilp.py`), theory curves (`fisher.py`: Gaussian CRB derived; uniform-noise 1/N oracle law derived and Monte-Carlo checked; coupling constant c ~ 0.76 tau^0.42 fitted). ILP lowers N50 by 1.0x/1.1x/1.1x/1.5x at n = 8/16/32/64 (`experiments/results/edge_theory_ilp_*`); n = 256 check: see section 2
- [x] Sanity check: Niot's attack 2 least squares on real no-r0-check ML-DSA-44 transcripts (11 Oct, `experiments/niot_sanity.py`): error = 0.97 x his formula gamma2/sqrt(3 tau N) (12 runs); edge estimator needs ~1,500x fewer signatures than his N

## 2. TALUS v0.22 signing cap
- [~] Reproduce Niot's estimator: formula checked against table, LS error law validated at ML-DSA-44; full-recovery N is ~12x formula in plain model (see experiments/ilwe_scaling_output.txt); t0 and -65/-87 not done
- [x] PLAN C0: re-read PW v0.22 main text (6 Oct); the preview writeup does not list per-signature released values or the t0 role, so our channel model is an assumption; see notes/schemes/talus.md
- [x] Rough prototype of the 1/N idea (n = 8, 16, 32, 3 trials, not saved): edge error ~ 1/N, least squares ~ 1/sqrt(N)
- [x] Bounded-noise estimator under BCC edges: ladder n = 8..256 run (6 Oct); per-element N* (99%): -44 at n = 256 1.9e5 (2^17.5), -65 at n = 256 5.2e5 (2^19.0), -87 at n = 64 5.2e5; s2-t0 and plain noise same as s2/BCC at n = 64; least squares recovers nothing
- [x] Run the n-ladder 8 to 256, apply gate C1 (6 Oct): above the cap by 4.5 to 5 bits and above the wall by 2.3 to 2.8 bits in our model; no break
- [x] Firmer numbers (8 Oct): -44 n = 256 with 20 trials: N*99 = 1.45e5 (2^17.1), full secret (k = 4) by 1.46e5; 4.1 bits above cap, 1.9 above wall. -87 n = 256 (5 trials): N*99 between 2^17.6 and 2^18.4, at least 3.6 above cap, 1.4 above wall
- [x] More trials for -87 and -65 at n = 256 near the transition (10 Oct, 20 trials, 7 points each): -87 N*99 = 3.69e5 (2^18.5), 4.5 above cap, 2.3 above wall; -65 N*99 = 3.58e5 (2^18.4), 4.4 above cap, 2.0 above wall. Full secret checked 13 Oct (300 trials, seed 2028): -65 299/300 at 2^18.47, -87 300/300 at 2^18.53 -> full-secret success >= ~91% / 92% (95%, union bound)
- [x] Positive and negative controls from real ML-DSA-44 signing (10 Oct, `harness/schemes/mldsa_controls.py`, `experiments/mldsa_controls.py`): no-r0-check variant -> edge estimator recovers s2 - t0 (key) in 9/9 runs (3 keys x N = 2e5, 4e5, 8e5); genuine ML-DSA -> key in 0/9, returns only -t0 (public-equivalent) in 9/9. false-positive check 12 Oct: 15 more keys (seed 2027, N = 2e5) -> key 0/15, -t0 15/15; 0/18 keys overall, rate < ~15% at 95%. TALUS v0.1 done 13 Oct (`harness/schemes/talus_v01.py`, arXiv 2603.22109v2 read in part): Niot attack 1 recovers s1 exactly from the keygen broadcast (3/3 keys) and from one MPC signature (60/60); attack 2 least squares on real signatures follows theory sigma_e/sqrt(N tau) up to N = 1e5, needs ~1.2e9 for recovery
- [x] ILP finishing at full size (13 Oct, ML-DSA-44, n = 256, one ring element, seed 2032, `experiments/ilp_n256.py`, results `ilp_n256*.json`): ILP success 1/8 at 5e4, 5/8 at 6e4, 8/8 at 7e4, 32/32 at 8e4-1.45e5 (plain rounding: 0/8 at 8e4, N*99 1.45e5). So N with ILP ~7e4 (2^16.1): about 3.1 bits above the cap and 0.9 above the wall (was 4.1 / 1.9). Still no break. Per element only (8 trials per point). -65/-87 with ILP (13 Oct, 4 trials/point, seed 2032, experiments/results/ilp_n256_summary.txt): -65 4/4 at 1.79e5 (2^17.45; +3.45 cap, +1.05 wall), -87 4/4 already at lowest N 1.48e5 (<= 2^17.18; +3.18, +0.98)
- [x] Compare against cap (2^13-2^14) and uniqueness wall (2^15-2^16): margin table in docs/LEARN.md (6 Oct)

## 3. Mithril
- [x] Read full version (ePrint 2026/013): main text, App. A, B, Renyi part of App. G (8 Oct)
- [x] Q_s accounting from Thm. 3.2 for all 45 published parameter sets (`harness/schemes/mithril_params.py`, 8 Oct): with the paper's B, Q_s = 2^26 to 2^37, not 2^50; published radii imply B only 0 to 7 sd above the mean norm (proof gap, not an attack; unverified against authors' code)
- [x] Typical-case Q_s under the real norm distribution (8 Oct): 2^50 or more for most sets; up to about 3 bits short for -44 (4,6), (5,6) and -65 (4,5), (4,6), (5,6), (6,6). Heuristic (random challenges), not a proof
- [x] Root cause from the public code (GuilhemN/threshold-ml-dsa, params/hyperball.sage), 8 Oct: B is the paper's; phi fixed at 7/8/9; Lemma 2.5 (used as `boundI`) is not a valid upper bound at dim 2048-3840 (2^-50 vs exact 2^-33.5 for -44), so Thm. 3.2 covers 2^26-2^37, not 2^50
- [x] Preview writeup v1.0 read (8 pages): no parameters or Q_s, nothing to compare. Authors cannot be contacted (user, 8 Oct)
- [x] Check original lemma in Devevey, Fawzi, Passelegue, Stehle (ePrint 2022/1249, Sec. A.6), 11 Oct: same wrong exponent n-1 in the original (cylinder argument done right gives (n-1)/2); Mithril copied it faithfully
- [x] ASIACRYPT published version (Springer, 13 Oct): no appendix, only the exact formula, so the bad bound is ePrint-only. Citing works checked (13 works, targeted search): only Mithril uses it; HAETAE computes the exact value. Table in notes/schemes/mithril.md
- [x] Corrected parameters (10 Oct, `--corrected`, experiments/results/mithril_corrected.txt): phi drops to 5.3-5.6 (-44), 5.9-6.6 (-65), 7.1-7.7 (-87); r' grows by 12 to 89; to keep the same session success rate K grows 1.3x to 8.5x (worst -65 (5,6): 1200 -> 10234). Communication scales with K
- [x] Accepted-z distribution and Rényi loss at q_s = 2^64 (11 Oct): closed form (uniform on ball intersection, Rényi = 1/(1-delta) any order, Fisher n/a); at 2^64 all published sets short (Thm: 27-38 bits; typical: 3-17 bits); corrected params for 2^64 need K x1.7 to x23 (`mithril_corrected_2e64.txt`). Not simulated
- [x] Hint accounting with exact T−1 share subset (11 Oct, `harness/schemes/mithril_hint.py`, Python core-SVP substitute): -44 loss 4-7 bits (paper's 12 reproduces with its 0.74), -65 14.6-20.7 bits (above the claimed 7-12), -87 7.6-12.8
- [x] Re-run with the real lattice estimator (11 Oct, Docker Sage 10.4, rough mode): -44 loss 4.9-7.7, -65 17.7-23.9, -87 8.6-14.4 bits; paper's 0.74 gives 14.1 for -44

## 4. Quorus and Trilithium
- [x] Quorus Algorithm 1 implemented (`harness/schemes/quorus.py`), 8 Oct: M_rep matches Table 2; 0 of 272,664 signatures fail FIPS 204 verification; short proof that the skip-e_w hint optimization is always correct (eta < beta)
- [x] Quorus leakage, statistical level: nothing detectable by construction (w uniform mod q); lattice-level distinguisher not run
- [x] Trilithium Sec. 3 read (MLWR argument for rejected w_H), 8 Oct
- [x] Trilithium toy-size test for rejected w_H (H-F2): exact enumeration at n = 4 done (10 Oct, `harness/schemes/trilithium_toy.py`): gap to simulator real at toy size, shrinks with gamma1 (branch 3 ~gamma1^-2.7); branch-2 floor at gamma1 = 32-48 unexplained; fixed-ratio scan done 11 Oct (q = 257/513/1025): branch-2 floor ~1e-4 for gamma1 >= gamma2 at all q, so not a small-q artefact; edge-cell test (11 Oct): masking r1 = 0 removes it for gamma1 >= 2 gamma2 (30-65x smaller); n = 8 Monte Carlo done 12 Oct (`trilithium_mc.py`, 2e8 samples x 3 trials): branch 3 gap below the sampling floor (~1e-7), branch 2 gap 3e-5 (gamma1 = 4) to 7e-7 (gamma1 = 8, 16)
- [x] Trilithium dimension trend (11 Oct, exact convolution `trilithium_conv.py`, n = 2..6 at q = 17): both gaps fall with n (branch 3 by 2-3 orders from n = 4 to 6); n = 8 still infeasible exactly
- [x] Declassified rejection bit and CRP read (Sec. 4.6-4.7, 11 Oct): paper's argument mostly holds; H-F3: tampered rej_check can leak about one bit per detected misbehaviour; CRP+Server collusion breaks privacy by design
- [x] H-F3 checked (11 Oct, Sec. 5.2, 7, App. F): detection stops all runs, so the leak is bounded by the stopping time (about log2(attempts) bits, once); the unsuccessful-signing simulation does not account for detection probability depending on the real z (possible proof gap, not an attack)

## 5. Kao predecessor design (arXiv 2601.20917)
- [x] Confirm or refute P2 masked-commitment claim at |S∖C| = 1 (2026-10-06, Stage D, toy `harness/schemes/kao_p2.py`: algebra confirmed on a toy; the paper already states the |S∖C| >= 2 condition; open point is the N-1 unforgeability claim, see notes/schemes/kao-p2.md)
- [x] Does P2 broadcast every W_i? YES per the paper (Fig. 1b, Remark 11, App. M.1), and masks cancel (Lemma 1), so sum W_i = A y is public and s1 follows from one P2 signature at any |S∖C| (11 Oct, text + toy test). Contact the author before disclosure
- [x] Draft the author-notification email for the Kao P2 finding: `docs/disclosure_drafts.md` (11 Oct, NOT sent; user decides)
- [x] Read App. B.1 key DKG: Feldman-style commitment t(i) = A s1(i) + s2(i) (and the text says Feldman over g^a, i.e. not lattice-native); the specific A*s1,i pattern broken in TALUS is not checked
- [x] Read remaining Kao appendices B.2-O (13 Oct): nothing rescues P2; Cor. 5 proof itself calls (c~, w) the public broadcast; App. O 5-round combiner does not move W_i; Cor. 6 drops the |H| >= 2 condition Simulator 17 needs. Disclosure draft updated. App. P onwards not read

## 6. Packages phase (from March 2027)
- [~] Rerun on actual reference code: Mithril params/hyperball.sage RUN in Sage (11 Oct), reproduces App. A radii and boundI 2^-50.1 vs exact 2^-33.5. Go signing code, Quorus/Trilithium/TALUS/Kao code: not run (Kao code not public)

## Reading gaps
- [x] Full Mithril (ePrint 2026/013) read (App. D, E, G read 16 Oct at hybrid level; see notes/schemes/mithril.md)
- [x] Quorus and Trilithium read in full (13 Oct, notes/schemes/*.md): hypotheses confirmed; our note that A y + e_w is "uniform" holds per coefficient only; paper errors found: Quorus Func. 6 bound gamma2-beta-eta vs gamma2-beta elsewhere (checked in PDF p. 32), Lemma 8 constant; Trilithium H-F3 simulation gap visible in p. 24 text

## Coursework: Phase 1 report
- [x] Survey of 23 papers, problem formulation, 10-page docx (`report/`)
- [x] LaTeX version in rubric order (`report/latex/phase1_report.tex`); restored to full 10-page content (4 Oct)
- [x] Deadline extension confirmed by user (1 Oct 2026)
- [ ] Run Turnitin check and submit
- [x] Re-verified citations 2, 16, 23, 24 online (1 Oct 2026)
- [x] Re-verify citations 21 (Shamir), 22 (Feldman): checked against Crossref 13 Oct (report notes)
- [x] Bring the report up to date with the 14-16 Oct results (29 Oct): Table IX now whole-secret 95% points with ILP (3.1/3.5/3.5 bits over the cap), other TALUS routes closed, Mithril Go transcripts and corrected A.6 bound, Kao P2 at full size, Quorus Lemma 8 denominator, Phase 3 list and plan table; docx and LaTeX both edited; PDF still 10 pages
- [x] Withdrawn ePrints [5], [15] (feedback item 7): checked 29 Oct, no claim rests on them; [5] downgraded M -> L in the matrix, counts now 13/5/6
- [x] Success-vs-N figure (Phase 1 promised "recovery-vs-samples curves"): `experiments/talus_success_plot.py`, Fig. 3 in both report versions; 5 terms (MLWR, TEE, NTT, r0 check, core-SVP) defined at first use; factor-12 LS gap explained (29 Oct); docx 10 pages
- [x] Student IDs: both versions use "Ashmit Dhown 2023A7PS0205U, Srivathsa H Honyal 2023A7PS0198U" (29 Oct, user)
- [x] Updated literature survey (rubric 1 mark), 29 Oct: new Sec. II-F "Recent work 2024-2026" with 9 verified sources [26]-[34] (Ringtail, AOM-MLWE TS, Tanuki, TOPCOAT, ML-DSaaS, Meng fault paper, two 2026 ML-DSA leakage estimators, HAETAE); matrix now 33 sources; docx now 11 pages (user: do not trim)
- [ ] Optional: user downloads ePrint 2026/2566 (Meng, fault attack on Mithril/TALUS/Trilithium) for a full read; only the abstract page was read
- [x] Title "Phase 2 Report - Cryptography" in both versions; LaTeX contribution table split half and half (user: assume, same account used by both), 29 Oct
- [x] Overleaf package `report/latex/overleaf_upload.zip` (main.tex + figures/); \graphicspath now also searches ./ and figures/
- [x] Rubric check (29 Oct): intro updated with 2026 context and proposed method; Section IV titled Proposed Solution
- [x] Results strengthened from saved data (29 Oct): Tables X-XII, XIV and Figs. 4-5 via experiments/report_extras.py; wording fixes (controls = one element; TEE T = 7/11/9)
- [ ] Compile on Overleaf (upload all 5 PNGs) (pdfLaTeX) and check page count; page target still open (brief once said 20)
- [ ] Rubric note: "AI-generated content will not be evaluated": report prose to be rewritten by the students in their own words
- [ ] Final read-through of report abstract and numbers before submitting

## Ethics / disclosure
- [x] Read final NIST call text (IR 8214C), selectively (13 Oct): public analysis allowed and expected; NIST does not require notifying teams first (our own policy); forum is MPTC-forum
- [x] Ask course instructor if any permission is needed (16 Oct: instructor says fine; continue as a university project; email authors and choose a venue only after the project is done)
- [x] Fallback deliverable if no attack is found: the harness plus the measured-margin scorecard, `docs/PAPER_OUTLINE.md` (16 Oct)
- [x] Draft author-notification emails: `docs/disclosure_drafts.md` (Kao P2, Mithril, Devevey et al.), 11 Oct, not sent

## 7. Paper (plan in docs/PAPER_PLAN.md, agreed 13 Oct 2026)
- [x] 1. TALUS: is key rotation a fresh key or a share refresh? Answered 14 Oct from PW v0.22 Sec. 2.3: fresh key generation; the writeup says share refresh does not reset leakage. No hole.
- [x] 2. TALUS: do rejected attempts release w1? Closed 14 Oct: BCC rejects stay committed offline; residual online failures are rare (arXiv v5 Sec. 6: first attempt succeeds ~98.0/99.6/99.2%, z-norm check never fired, hint weight dominates). Even if uncounted toward the cap, at most ~0.03 bits extra data vs a ~3-bit margin. No hole.
- [x] 3. (finished 16 Oct) TALUS: corrupt party / coordinator model. First pass 15 Oct (v5 App. D): proposed MPC profile has m >= T >= 2 honest nonce shares; our rough insider wall 2^24.8-2^29.7, 12-16 bits above cap, no hole. TEE coalition (m = 1) below cap from T = 7/11/9, as authors concede (TEE not proposed). m = 2 Fisher number checked exactly 16 Oct (within 1% of the hand formula, `experiments/talus_m2_fisher.py`). m = 2 simulated 16 Oct (`experiments/talus_m2_sim.py`: ML needs 1.5-2x the formula at 50%, 4-6x at 95%, n = 8); coordinator tail probabilities reproduced within 1 bit (`experiments/talus_coordinator_tail.py`). Former open note: corrupt-coordinator rejected-response view. `experiments/talus_insider_wall.py`
- [x] 4. (closed 16 Oct: lattice finish worth 3.2 bits at the cap, 9.9 bits at 2^15, `experiments/soft_hint_lwe.py`; joint solving adds nothing; hint h not separately evaluated) Stronger estimator (joint, hint h, lattice finish). Step 1 done 16 Oct: at the cap the edge estimate gets 43-48% of s2 right (2 trials, soft hint only), so no hard hints for a lattice finish; open: per-coordinate posterior + LWE with soft hints. `experiments/partial_recovery.py`
- [x] 5. Mithril Go code: run views on real transcripts. Done 15 Oct: reference code (ML-DSA-44, (T,N)=(2,3)) dumped via `harness/mithril_go/dump_test.go`; 110000 slots, 39461 with no party rejecting. Slope of u = A z - c t - w on -c s2: 0.004 +/- 0.10, so the hidden part z2 is independent of s2 after acceptance; the view's channel b carries only c t0. MithrilView model corrected. `experiments/results/mithril_real_transcripts.txt`
- [x] 6. Mithril -65 a-posteriori sharing vs NIST Category 3 (full estimator). Done 14 Oct: baseline 203.8 bits, with hint 189.0/184.3/182.5 (S = 2/6/20), loss 14.8-21.3 (paper: 7-12). Below the baseline's Category 3 level, far above Category 1. Proof-claim gap, not practical. `experiments/results/mithril_hint_estimator_full65.txt`
- [x] 7. Kao P2 end-to-end demo on real ML-DSA-44/65/87 (16 Oct: s1 recovered from one signature, 15/15 keys per set; re-implementation of the paper, rejection checks in the clear; `experiments/kao_p2_real_demo.py`)
- [~] 8. TALUS statistics. Done 14 Oct for one ring element: 20 trials per point, Clopper-Pearson CIs, logistic fit; 95% success at 2^16.01 / 2^17.40 / 2^17.30 (-44/-65/-87), +3.0/+3.4/+3.3 bits over the cap, +0.8/+1.0/+1.1 over the wall (`experiments/results/item8/summary.txt`). Full secret (16 Oct, extrapolated P_elem^k, not run): 95% at 2^16.09 / 2^17.51 / 2^17.51 = +3.1 / +3.5 / +3.5 bits over the cap (`experiments/item8_full_secret.py`). Real full-secret ILP run for ML-DSA-44 (16 Oct, 20 whole secrets per N, seed 2081): 3/20 at 2^15.92, 15/20 at 2^16.01, 18/20 at 2^16.10, matching the extrapolation (`experiments/results/item8_full/summary.txt`). -65 and -87 not run.
- [x] 9. Corrected Devevey A.6 bound with proof. Done 14 Oct: `docs/a6_corrected_bound.md` (part a: cylinder, exponent (n-1)/2; part b: sharp, within 0.04 bits of exact at Mithril sizes); 320-point check, 0 violations, printed bound invalid at 149 (`experiments/a6_corrected_bound.py`)
- [~] 10. Framing and scorecard draft: `docs/PAPER_OUTLINE.md` (16 Oct)
- [~] 11. Disclosure: instructor OK (16 Oct). Emails and venue decided only after the project ends; nothing sent
- [x] 12. Open artifact driver `experiments/reproduce.py` (16 Oct; fast items verified identical, heavy items listed only)
- [ ] 13. Venue rewrite (deferred by user, 16 Oct: decide after the project is done)
- Targets: PQCrypto 2027 (paper 24 Nov 2026); USENIX Security '27 cycle 2 (26 Jan 2027) if items 1-3 find a hole
