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
- [ ] Sanity check: reproduce Niot's ILWE attack on TALUS-style transcripts

## 2. TALUS v0.22 signing cap
- [~] Reproduce Niot's estimator: formula checked against table, LS error law validated at ML-DSA-44; full-recovery N is ~12x formula in plain model (see experiments/ilwe_scaling_output.txt); t0 and -65/-87 not done
- [x] PLAN C0: re-read PW v0.22 main text (6 Oct); the preview writeup does not list per-signature released values or the t0 role, so our channel model is an assumption; see notes/schemes/talus.md
- [x] Rough prototype of the 1/N idea (n = 8, 16, 32, 3 trials, not saved): edge error ~ 1/N, least squares ~ 1/sqrt(N)
- [x] Bounded-noise estimator under BCC edges: ladder n = 8..256 run (6 Oct); per-element N* (99%): -44 at n = 256 1.9e5 (2^17.5), -65 at n = 256 5.2e5 (2^19.0), -87 at n = 64 5.2e5; s2-t0 and plain noise same as s2/BCC at n = 64; least squares recovers nothing
- [x] Run the n-ladder 8 to 256, apply gate C1 (6 Oct): above the cap by 4.5 to 5 bits and above the wall by 2.3 to 2.8 bits in our model; no break
- [x] Firmer numbers (8 Oct): -44 n = 256 with 20 trials: N*99 = 1.45e5 (2^17.1), full secret (k = 4) by 1.46e5; 4.1 bits above cap, 1.9 above wall. -87 n = 256 (5 trials): N*99 between 2^17.6 and 2^18.4, at least 3.6 above cap, 1.4 above wall
- [ ] More trials for -87 and -65 at n = 256 near the transition
- [ ] Positive control (TALUS v0.1 recovery), negative control (plain ML-DSA), power analysis
- [x] Compare against cap (2^13-2^14) and uniqueness wall (2^15-2^16): margin table in docs/LEARN.md (6 Oct)

## 3. Mithril
- [x] Read full version (ePrint 2026/013): main text, App. A, B, Renyi part of App. G (8 Oct)
- [x] Q_s accounting from Thm. 3.2 for all 45 published parameter sets (`harness/schemes/mithril_params.py`, 8 Oct): with the paper's B, Q_s = 2^26 to 2^37, not 2^50; published radii imply B only 0 to 7 sd above the mean norm (proof gap, not an attack; unverified against authors' code)
- [x] Typical-case Q_s under the real norm distribution (8 Oct): 2^50 or more for most sets; up to about 3 bits short for -44 (4,6), (5,6) and -65 (4,5), (4,6), (5,6), (6,6). Heuristic (random challenges), not a proof
- [x] Root cause from the public code (GuilhemN/threshold-ml-dsa, params/hyperball.sage), 8 Oct: B is the paper's; phi fixed at 7/8/9; Lemma 2.5 (used as `boundI`) is not a valid upper bound at dim 2048-3840 (2^-50 vs exact 2^-33.5 for -44), so Thm. 3.2 covers 2^26-2^37, not 2^50
- [x] Preview writeup v1.0 read (8 pages): no parameters or Q_s, nothing to compare. Authors cannot be contacted (user, 8 Oct)
- [ ] Check original lemma in Devevey et al. (ePrint 2023/245, Sec. A.6); needs manual download
- [ ] Corrected parameters (phi from exact I for Q_s = 2^50) and their cost in acceptance and communication
- [ ] Accepted-z distribution and Rényi/Fisher loss at q_s = 2^64
- [ ] Hint accounting with exact T−1 share subset (lattice estimator)

## 4. Quorus and Trilithium
- [x] Quorus Algorithm 1 implemented (`harness/schemes/quorus.py`), 8 Oct: M_rep matches Table 2; 0 of 272,664 signatures fail FIPS 204 verification; short proof that the skip-e_w hint optimization is always correct (eta < beta)
- [x] Quorus leakage, statistical level: nothing detectable by construction (w uniform mod q); lattice-level distinguisher not run
- [x] Trilithium Sec. 3 read (MLWR argument for rejected w_H), 8 Oct
- [ ] Trilithium toy-size lattice distinguisher for rejected w_H (H-F2)
- [ ] Trilithium rejected-partial uniformity test; CRP and declassified-bit analysis

## 5. Kao predecessor design (arXiv 2601.20917)
- [x] Confirm or refute P2 masked-commitment claim at |S∖C| = 1 (2026-10-06, Stage D, toy `harness/schemes/kao_p2.py`: algebra confirmed on a toy; the paper already states the |S∖C| >= 2 condition; open point is the N-1 unforgeability claim, see notes/schemes/kao-p2.md)
- [ ] Ask whether P2 really broadcasts every W_i (then the SUM A*y is public and the attack works at any |S∖C|); needs the Rust code or the authors
- [x] Read App. B.1 key DKG: Feldman-style commitment t(i) = A s1(i) + s2(i) (and the text says Feldman over g^a, i.e. not lattice-native); the specific A*s1,i pattern broken in TALUS is not checked
- [ ] Read remaining Kao appendices (A, H-M proofs) fully

## 6. Packages phase (from March 2027)
- [ ] Rerun harness on actual reference code

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
- [ ] Draft author-notification email template for any finding
