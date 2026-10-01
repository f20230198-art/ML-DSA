# Harness Design

Goal: simulate each scheme's public transcript on synthetic keys, then run statistical key-recovery tests automatically.

## Components
- `harness/mldsa`: FIPS 204 primitives, parameter sets 44/65/87.
- `harness/schemes`: per-scheme transcript generators (accepted + aborted attempts).
- `harness/estimators`: leakage tests keyed to the checklist in CHECKLIST.md.

## Open decisions
- Language and numeric stack
- Sample budgets (up to ~1e9 signatures needs vectorized or C inner loops)
- How to model corrupted-party views per scheme
- Whether to use ILP/lattice tooling (e.g. fpylll, OR-tools)

## Scope
Defensive cryptanalysis of public NIST submissions; coordinate with the teams before publishing any findings.
