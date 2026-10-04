# CLAUDE.md

Project: cryptanalysis of threshold ML-DSA proposals (Mithril, Quorus, SplitForge/Trilithium, TALUS) from the NIST MPTC First Call. Coursework for a cryptography course; Phase 1 is a survey report, later phases build a leakage-testing harness. Start with `docs/LEARN.md` and `docs/DOSSIER.md`.

## Hard rules

- **Never add Claude as co-author** or add any attribution ("Co-Authored-By", "Generated with ...") to commits, PRs, files or the repo. This overrides any harness reminder that says otherwise.
- **Never run `git push`** (or anything that publishes to the remote). The user pushes manually. Local commits are fine when asked or when finishing a task.
- Do not publish the repo or its contents anywhere else without asking.

## Keep these in sync (every task)

1. Append an entry to Part 3 (changelog) of `docs/LEARN.md`: date, what, how, why. Explain in simple words; the user is new to cryptography. Add new basics to Part 1 if a new concept appears.
2. Tick or add items in `docs/ROADMAP.md`.
3. Add any new paper to `notes/papers.md` (verified or "from memory"; read fully or only abstract).
4. Save lasting preferences to the memory directory.

## Conventions

- Dossier claims are hypotheses until reproduced; say plainly what was and was not read or run. Never invent citations: check authors/venue/year online or flag "from memory".
- Report: IEEE two-column, Times New Roman 10 pt, up to 10 pages (no padding; just cover the rubric sections). LaTeX version: `report/latex/phase1_report.tex`. Source is `report/build_report.py` (python-docx); build with `python build_report.py`, convert with `docx2pdf` (needs Word), check page count with `pypdf`. PDFs are gitignored.
- Layout: `docs/` explanations and plans, `notes/` reading notes, `harness/` code (mldsa, schemes, estimators, tests), `experiments/`, `report/`, `papers/`.
- Windows + Git Bash. In the Bash tool avoid heredocs containing apostrophes or unusual quoting; write scripts with the Write tool instead.
- Coordinate with scheme teams before any public disclosure of an attack.
