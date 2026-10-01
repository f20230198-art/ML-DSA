# Roadmap

Ordered as in the dossier's ranked plan.

## 0. Setup
- [ ] Pick language/tooling (suggest Python + numpy/sage for estimators)
- [ ] Verify dossier sources and recheck TCPT3 schedule / phase 3 list

## 1. Leakage-testing harness
- [ ] ML-DSA reference primitives (params, NTT, Power2Round, Decompose, hints, sampling)
- [ ] Transcript simulator interface (accepted and aborted attempts)
- [ ] Estimators: least squares, bounded-noise, ILP, Fisher information
- [ ] Sanity check: reproduce Niot's ILWE attack on TALUS-style transcripts

## 2. TALUS v0.22 signing cap
- [ ] Reproduce Niot's estimator (~3.1e8 / 1.9e9 / 1.5e9 samples)
- [ ] Bounded-noise / ILP estimator under BCC edges
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
- [ ] Confirm deadline extension (listed deadline 25.09.2026 has passed)
- [ ] Run Turnitin check and submit
- [ ] Re-verify citations 2, 16, 21-23 (cited from memory)
