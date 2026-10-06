# Roadmap

Ordered as in the dossier's ranked plan. The detailed stages, gates and paper framing are in `docs/PLAN.md` (stages A to G).

## 0. Setup
- [x] Pick language/tooling (Python + numpy/scipy; Sage availability still to check for the lattice estimator)
- [ ] PLAN Stage A: NTT, SHAKE sampling, hints, full sign/verify with all attempts, FIPS 204 known-answer tests
- [ ] PLAN Stage B: scheme-view interface (`harness/schemes/base.py`)
- [x] Fix stale line in DOSSIER and README ("no code has been run")
- [ ] Verify dossier sources and recheck TCPT3 schedule / phase 3 list

## 1. Leakage-testing harness
- [~] ML-DSA reference primitives: params, rounding, ring mult, challenge sampling done; NTT, hints, SHAKE sampling, KATs still missing
- [ ] Transcript simulator interface (accepted and aborted attempts)
- [~] Estimators: least squares done (`harness/estimators/ilwe.py`); bounded-noise, ILP, Fisher information todo
- [ ] Sanity check: reproduce Niot's ILWE attack on TALUS-style transcripts

## 2. TALUS v0.22 signing cap
- [~] Reproduce Niot's estimator: formula checked against table, LS error law validated at ML-DSA-44; full-recovery N is ~12x formula in plain model (see experiments/ilwe_scaling_output.txt); t0 and -65/-87 not done
- [x] PLAN C0: re-read PW v0.22 main text (6 Oct); the preview writeup does not list per-signature released values or the t0 role, so our channel model is an assumption; see notes/schemes/talus.md
- [x] Rough prototype of the 1/N idea (n = 8, 16, 32, 3 trials, not saved): edge error ~ 1/N, least squares ~ 1/sqrt(N)
- [~] Bounded-noise estimator under BCC edges: 30 tests pass; ladder n = 8..128 run (6 Oct): per-element N* (50%/99%) 1.4e5/1.9e5 at n = 128, flattening near 2^17 to 2^18, least squares recovers nothing; provisional: about 3-4 bits above the cap, 1-2 bits above the wall; n = 256 still to run (`docs/RUNBOOK.md`)
- [ ] Run the n-ladder 8 to 256, fit the law, apply gate C1
- [ ] Positive control (TALUS v0.1 recovery), negative control (plain ML-DSA), power analysis
- [ ] Compare against cap (2^13–2^14) and uniqueness wall (2^15–2^16)

## 3. Mithril
- [ ] Accepted-z distribution and Rényi/Fisher loss at q_s = 2^64
- [ ] Hint accounting with exact T−1 share subset (lattice estimator)

## 4. Quorus and Trilithium
- [ ] Quorus reveal-on-reject leakage tests
- [ ] Trilithium rejected-partial uniformity test; CRP and declassified-bit analysis

## 5. Kao predecessor design (arXiv 2601.20917)
- [ ] Confirm or refute P2 masked-commitment claim at |S∖C| = 1
- [ ] Check DKG Feldman-style commitments (App. B.1)

## 6. Packages phase (from March 2027)
- [ ] Rerun harness on actual reference code

## Reading gaps
- [ ] Full Mithril (ePrint 2026/013), Quorus (2025/1163), Trilithium (2025/675) papers

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
