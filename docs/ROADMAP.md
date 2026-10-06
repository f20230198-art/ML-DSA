# Roadmap

Ordered as in the dossier's ranked plan. The detailed stages, gates and paper framing are in `docs/PLAN.md` (stages A to G).

## 0. Setup
- [x] Pick language/tooling (Python + numpy/scipy). Sage and fpylll are NOT installed (checked 6 Oct); Docker is, so a Sage image is an option for the Mithril lattice-estimator stage
- [x] PLAN Stage A: NTT, SHAKE sampling, hints, full sign/verify with all attempts; byte-identical to dilithium-py oracle for -44/-65/-87 (6 Oct). Official NIST KAT files not yet run
- [~] PLAN Stage B: scheme-view interface done with two controls (`harness/schemes/base.py`); no scheme-specific views yet, gate B open
- [x] Fix stale line in DOSSIER and README ("no code has been run")
- [ ] Verify dossier sources and recheck TCPT3 schedule / phase 3 list

## 1. Leakage-testing harness
- [x] ML-DSA reference primitives: params, rounding, ring mult, NTT, hints, SHAKE sampling, full sign/verify (official KAT files still to run)
- [~] Transcript simulator interface: `Attempt` records plus `SchemeView`; positive (y leak) and negative (plain ML-DSA) controls pass
- [~] Estimators: least squares done (`harness/estimators/ilwe.py`); bounded-noise, ILP, Fisher information todo
- [ ] Sanity check: reproduce Niot's ILWE attack on TALUS-style transcripts

## 2. TALUS v0.22 signing cap
- [~] Reproduce Niot's estimator: formula checked against table, LS error law validated at ML-DSA-44; full-recovery N is ~12x formula in plain model (see experiments/ilwe_scaling_output.txt); t0 and -65/-87 not done
- [x] PLAN C0: re-read PW v0.22 main text (6 Oct); the preview writeup does not list per-signature released values or the t0 role, so our channel model is an assumption; see notes/schemes/talus.md
- [x] Rough prototype of the 1/N idea (n = 8, 16, 32, 3 trials, not saved): edge error ~ 1/N, least squares ~ 1/sqrt(N)
- [x] Bounded-noise estimator under BCC edges: ladder n = 8..256 run (6 Oct); per-element N* (99%): -44 at n = 256 1.9e5 (2^17.5), -65 at n = 256 5.2e5 (2^19.0), -87 at n = 64 5.2e5; s2-t0 and plain noise same as s2/BCC at n = 64; least squares recovers nothing
- [x] Run the n-ladder 8 to 256, apply gate C1 (6 Oct): above the cap by 4.5 to 5 bits and above the wall by 2.3 to 2.8 bits in our model; no break. Still to do: more trials near the transition, full-secret (k elements) check, -87 at n = 256
- [ ] Positive control (TALUS v0.1 recovery), negative control (plain ML-DSA), power analysis
- [x] Compare against cap (2^13-2^14) and uniqueness wall (2^15-2^16): margin table in docs/LEARN.md (6 Oct)

## 3. Mithril
- [ ] Accepted-z distribution and Rényi/Fisher loss at q_s = 2^64
- [ ] Hint accounting with exact T−1 share subset (lattice estimator)

## 4. Quorus and Trilithium
- [ ] Quorus reveal-on-reject leakage tests
- [ ] Trilithium rejected-partial uniformity test; CRP and declassified-bit analysis

## 5. Kao predecessor design (arXiv 2601.20917)
- [x] Confirm or refute P2 masked-commitment claim at |S∖C| = 1 (2026-10-06, Stage D, toy `harness/schemes/kao_p2.py`: algebra confirmed on a toy; the paper already states the |S∖C| >= 2 condition; open point is the N-1 unforgeability claim, see notes/schemes/kao-p2.md)
- [ ] Ask whether P2 really broadcasts every W_i (then the SUM A*y is public and the attack works at any |S∖C|); needs the Rust code or the authors
- [x] Read App. B.1 key DKG: Feldman-style commitment t(i) = A s1(i) + s2(i) (and the text says Feldman over g^a, i.e. not lattice-native); the specific A*s1,i pattern broken in TALUS is not checked
- [ ] Read remaining Kao appendices (A, H-M proofs) fully

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
