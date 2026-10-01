# Threshold ML-DSA Cryptanalysis

Research project assessing the threshold ML-DSA proposals in the NIST MPTC First Call (IR 8214C): **Mithril**, **Quorus**, **SplitForge/Trilithium** and **TALUS**. The goal is to build a reusable leakage-testing harness and use it to test each scheme's public transcripts against known attack patterns (see the dossier's checklist).

Status: literature-and-spec assessment done; no code or experiments yet.

## Layout

| Path | Purpose |
|------|---------|
| `docs/LEARN.md` | Beginner-friendly explanation of the project plus running changelog (start here) |
| `report/` | Phase 1 coursework report (docx built by `build_report.py`) |
| `notes/papers.md` | Reading table of all cited papers |
| `docs/DOSSIER.md` | Source assessment (as of 2026-09-29): schemes, known attacks, checklist, ranked plan |
| `docs/ROADMAP.md` | Task checklist derived from the dossier's ranked plan |
| `docs/CHECKLIST.md` | The 10-point reusable attack checklist |
| `docs/DESIGN.md` | Harness design and open decisions |
| `notes/schemes/` | One note per scheme (attack surface, open questions, reading status) |
| `harness/mldsa/` | Reference ML-DSA primitives (params, NTT, rounding, sampling) |
| `harness/schemes/` | Transcript simulators per scheme (incl. aborted attempts) |
| `harness/estimators/` | Leakage tests: least squares, bounded-noise, ILP, Fisher information |
| `harness/tests/` | Tests and sanity checks |
| `experiments/` | Experiment scripts and results |
| `papers/` | Local reading copies (untracked PDFs are ignored) |

## Conventions

See [CONTRIBUTING.md](CONTRIBUTING.md). Dossier claims are hypotheses until reproduced; record results in `notes/`.
