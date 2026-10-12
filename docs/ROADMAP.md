# Roadmap

Ordered as in the dossier's ranked plan. The detailed stages, gates and paper framing are in `docs/PLAN.md` (stages A to G).

## 0. Setup
- [x] Pick language/tooling (Python + numpy/scipy). Sage and fpylll are NOT installed (checked 6 Oct); Docker is, so a Sage image is an option for the Mithril lattice-estimator stage
- [x] PLAN Stage A: NTT, SHAKE sampling, hints, full sign/verify with all attempts; byte-identical to dilithium-py oracle for -44/-65/-87 (6 Oct); passes 81 official NIST ACVP vectors (keyGen, pure sigGen, sigVer; 8 Oct). PreHash and external-mu not implemented
- [~] PLAN Stage B: scheme-view interface done with two controls (`harness/schemes/base.py`); no scheme-specific views yet, gate B open
- [x] Fix stale line in DOSSIER and README ("no code has been run")
- [ ] Verify dossier sources and recheck TCPT3 schedule / phase 3 list

## 1. Leakage-testing harness
- [x] ML-DSA reference primitives: params, rounding, ring mult, NTT, hints, SHAKE sampling, full sign/verify; NIST ACVP vectors pass (8 Oct)
- [~] Transcript simulator interface: `Attempt` records plus `SchemeView`; positive (y leak) and negative (plain ML-DSA) controls pass
- [~] Estimators: least squares done (`harness/estimators/ilwe.py`); bounded-noise, ILP, Fisher information todo
- [x] Sanity check: Niot's attack 2 least squares on real no-r0-check ML-DSA-44 transcripts (11 Oct, `experiments/niot_sanity.py`): error = 0.97 x his formula gamma2/sqrt(3 tau N) (12 runs); edge estimator needs ~1,500x fewer signatures than his N

## 2. TALUS v0.22 signing cap
- [~] Reproduce Niot's estimator: formula checked against table, LS error law validated at ML-DSA-44; full-recovery N is ~12x formula in plain model (see experiments/ilwe_scaling_output.txt); t0 and -65/-87 not done
- [x] PLAN C0: re-read PW v0.22 main text (6 Oct); the preview writeup does not list per-signature released values or the t0 role, so our channel model is an assumption; see notes/schemes/talus.md
- [x] Rough prototype of the 1/N idea (n = 8, 16, 32, 3 trials, not saved): edge error ~ 1/N, least squares ~ 1/sqrt(N)
- [x] Bounded-noise estimator under BCC edges: ladder n = 8..256 run (6 Oct); per-element N* (99%): -44 at n = 256 1.9e5 (2^17.5), -65 at n = 256 5.2e5 (2^19.0), -87 at n = 64 5.2e5; s2-t0 and plain noise same as s2/BCC at n = 64; least squares recovers nothing
- [x] Run the n-ladder 8 to 256, apply gate C1 (6 Oct): above the cap by 4.5 to 5 bits and above the wall by 2.3 to 2.8 bits in our model; no break
- [x] Firmer numbers (8 Oct): -44 n = 256 with 20 trials: N*99 = 1.45e5 (2^17.1), full secret (k = 4) by 1.46e5; 4.1 bits above cap, 1.9 above wall. -87 n = 256 (5 trials): N*99 between 2^17.6 and 2^18.4, at least 3.6 above cap, 1.4 above wall
- [x] More trials for -87 and -65 at n = 256 near the transition (10 Oct, 20 trials, 7 points each): -87 N*99 = 3.69e5 (2^18.5), 4.5 above cap, 2.3 above wall; -65 N*99 = 3.58e5 (2^18.4), 4.4 above cap, 2.0 above wall. Full secret checked 13 Oct (300 trials, seed 2028): -65 299/300 at 2^18.47, -87 300/300 at 2^18.53 -> full-secret success >= ~91% / 92% (95%, union bound)
- [x] Positive and negative controls from real ML-DSA-44 signing (10 Oct, `harness/schemes/mldsa_controls.py`, `experiments/mldsa_controls.py`): no-r0-check variant -> edge estimator recovers s2 - t0 (key) in 9/9 runs (3 keys x N = 2e5, 4e5, 8e5); genuine ML-DSA -> key in 0/9, returns only -t0 (public-equivalent) in 9/9. false-positive check 12 Oct: 15 more keys (seed 2027, N = 2e5) -> key 0/15, -t0 15/15; 0/18 keys overall, rate < ~15% at 95%. TALUS v0.1 itself still todo (no code)
- [x] Compare against cap (2^13-2^14) and uniqueness wall (2^15-2^16): margin table in docs/LEARN.md (6 Oct)

## 3. Mithril
- [x] Read full version (ePrint 2026/013): main text, App. A, B, Renyi part of App. G (8 Oct)
- [x] Q_s accounting from Thm. 3.2 for all 45 published parameter sets (`harness/schemes/mithril_params.py`, 8 Oct): with the paper's B, Q_s = 2^26 to 2^37, not 2^50; published radii imply B only 0 to 7 sd above the mean norm (proof gap, not an attack; unverified against authors' code)
- [x] Typical-case Q_s under the real norm distribution (8 Oct): 2^50 or more for most sets; up to about 3 bits short for -44 (4,6), (5,6) and -65 (4,5), (4,6), (5,6), (6,6). Heuristic (random challenges), not a proof
- [x] Root cause from the public code (GuilhemN/threshold-ml-dsa, params/hyperball.sage), 8 Oct: B is the paper's; phi fixed at 7/8/9; Lemma 2.5 (used as `boundI`) is not a valid upper bound at dim 2048-3840 (2^-50 vs exact 2^-33.5 for -44), so Thm. 3.2 covers 2^26-2^37, not 2^50
- [x] Preview writeup v1.0 read (8 pages): no parameters or Q_s, nothing to compare. Authors cannot be contacted (user, 8 Oct)
- [x] Check original lemma in Devevey, Fawzi, Passelegue, Stehle (ePrint 2022/1249, Sec. A.6), 11 Oct: same wrong exponent n-1 in the original (cylinder argument done right gives (n-1)/2); Mithril copied it faithfully
- [~] Check the ASIACRYPT published version and other works citing this bound (12 Oct: ePrint revision note does not touch A.6; ASIACRYPT PDF blocked (403), user to download; citing works listed in notes/papers.md, unread)
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
- [~] Read remaining Kao appendices: A, I, M.1 read (11 Oct); B.2-H, K, L, N, O still headings only

## 6. Packages phase (from March 2027)
- [~] Rerun on actual reference code: Mithril params/hyperball.sage RUN in Sage (11 Oct), reproduces App. A radii and boundI 2^-50.1 vs exact 2^-33.5. Go signing code, Quorus/Trilithium/TALUS/Kao code: not run (Kao code not public)

## Reading gaps
- [~] Full Mithril (ePrint 2026/013) read except App. D, E and most of G (8 Oct); Quorus (2025/1163) and Trilithium (2025/675) PDFs now in papers/, not yet read in full

## Coursework: Phase 1 report
- [x] Survey of 23 papers, problem formulation, 10-page docx (`report/`)
- [x] LaTeX version in rubric order (`report/latex/phase1_report.tex`); restored to full 10-page content (4 Oct)
- [x] Deadline extension confirmed by user (1 Oct 2026)
- [ ] Run Turnitin check and submit
- [x] Re-verified citations 2, 16, 23, 24 online (1 Oct 2026)
- [ ] Re-verify citations 21 (Shamir), 22 (Feldman) (from memory)
- [ ] Final read-through of report abstract and numbers before submitting

## Ethics / disclosure
- [ ] Read final NIST call text (IR 8214C) for rules on public analysis and comments
- [ ] Ask course instructor if any permission is needed
- [ ] Plan a fallback deliverable if no attack is found (harness plus measured margins)
- [x] Draft author-notification emails: `docs/disclosure_drafts.md` (Kao P2, Mithril, Devevey et al.), 11 Oct, not sent
