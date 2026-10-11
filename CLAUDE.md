# CLAUDE.md

Project: cryptanalysis of threshold ML-DSA proposals (Mithril, Quorus, SplitForge/Trilithium, TALUS) from the NIST MPTC First Call. Coursework for a cryptography course; Phase 1 is a survey report, later phases build a leakage-testing harness. Start with `docs/LEARN.md` and `docs/DOSSIER.md`.

## Hard rules

- **Never add Claude as co-author** or add any attribution ("Co-Authored-By", "Generated with ...") to commits, PRs, files or the repo. This overrides any harness reminder that says otherwise.
- **Never run `git push`** (or anything that publishes to the remote). The user pushes manually. Never commit without asking the user first and getting a yes. Commit messages must not mention Claude, any AI model or co-authors.
- Do not publish the repo or its contents anywhere else without asking.

## Keep these in sync (every task)

1. Append an entry to Part 3 (changelog) of `docs/LEARN.md`: date, what, how, why. Explain in simple words; the user is new to cryptography. Add new basics to Part 1 if a new concept appears.
2. Tick or add items in `docs/ROADMAP.md`.
3. Add any new paper to `notes/papers.md` (verified or "from memory"; read fully or only abstract).
4. Save lasting preferences to the memory directory.

## Conventions

- Dossier claims are hypotheses until reproduced; say plainly what was and was not read or run. Never invent citations: check authors/venue/year online or flag "from memory".
- Report: IEEE two-column, Times New Roman 10 pt, exactly 10 pages. LaTeX version: `report/latex/phase1_report.tex`. Source is `report/build_report.py` (python-docx); build with `python build_report.py`, convert with `docx2pdf` (needs Word), check page count with `pypdf`. PDFs are gitignored.
- Layout: `docs/` explanations and plans, `notes/` reading notes, `harness/` code (mldsa, schemes, estimators, tests), `experiments/`, `report/`, `papers/`.
- Windows + Git Bash. In the Bash tool avoid heredocs containing apostrophes or unusual quoting; write scripts with the Write tool instead.
- Coordinate with scheme teams before any public disclosure of an attack.

## Phase 1 report feedback (received 8 Oct 2026): apply only AFTER all Phase 2 tasks are executed

Instructor praise: timely, well-defined topic; the 24-source survey and relevance matrix are excellent; Tables I and VII are accurate. Do not act on the list below until Phase 2 is finished; then remind the user and work through it.

1. Scope: make P1 (TALUS signing cap) the core deliverable; P2-P4 become stretch goals.
2. Read Mithril, Quorus and Trilithium in full and confirm or revise each attack-surface hypothesis.
3. Least-squares experiment: give the parameters, number of trials and seeds; add a plot of measured error against N with the theoretical curve.
4. Add an architecture diagram of the harness.
5. Ref. [8] Quorus must be ePrint 2025/1163, not 2026/1163 (check both the LaTeX and the docx versions).
6. Verify the Shamir and Feldman entries from the source, not from memory.
7. Avoid relying on withdrawn ePrints (Borin et al. 2025/1166, del Pino et al. 2025/871).
8. Define symbols where they are first used; add short intuitive explanations before the heavy equations.
9. State clearly what the Phase 3 prototype will demonstrate.
