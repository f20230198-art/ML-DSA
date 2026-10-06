# PLAN: from the current harness to a defensible paper

Written 2026-10-06. This plan turns the dossier's "ranked plan" into concrete code, runs, decisions and paper figures. Everything marked **Hypothesis** is not yet tested. Dossier claims stay hypotheses until a run reproduces them.

## 0. Where we stand

| Have | Missing |
|---|---|
| ML-DSA params, rounding, negacyclic multiplication, challenge sampler (`harness/mldsa`) | NTT, SHAKE-based sampling, hints, a full sign/verify, known-answer tests |
| Plain-noise ILWE transcript and a least-squares estimator (`harness/estimators/ilwe.py`) | The real TALUS noise model (sharp edges under BCC), the t0 term, ML-DSA-65/-87 |
| One experiment: least-squares error follows theory within 3% at ML-DSA-44 | Any estimator that uses the bounded shape of the noise |
| 18 passing tests | Any test showing the harness can detect a leak, or stays silent when there is none |

**The central number.** Plain least squares needs about 3.6e9 signatures for full recovery at ML-DSA-44. TALUS v0.22 caps a key at 2^13 to 2^14 (about 8k to 16k) signatures. That is a gap of roughly 5 orders of magnitude. The whole TALUS question is whether a smarter estimator can close it.

**Why it might (Hypothesis H1).** Least squares treats the noise as Gaussian, so its error shrinks like 1/sqrt(N). The TALUS noise is uniform with hard edges (under BCC it lies in (-gamma2+beta, gamma2-beta)). For a uniform distribution the edges pin down the location. The error of an edge-based estimator shrinks like 1/N, not 1/sqrt(N). In plain words: the largest and smallest observed values trap the hidden number between two walls, and the walls close in fast. Then the sample count would scale roughly like gamma2 (about 1e5) instead of gamma2 squared (about 1e10). That would land near 2^17 to 2^20 signatures, uncomfortably close to the cap and the uniqueness wall. This is a guess from a one-dimensional analogy. The real problem has 1024 coupled unknowns and varying challenges, so the experiment decides.

**Why it might not (H0).** The coupled system may be far less informative than the 1-D analogy, and the authors' wall (2^15.2 to 2^16.4) may be right. Then the deliverable is a measured margin, which is still a result.

## 1. Guiding principles

1. **Every claim gets a control.** Positive control: the harness must flag a scheme known to leak. Negative control: it must stay quiet on plain ML-DSA. Without both, a "no leak found" means nothing.
2. **Cheap decisive experiments first.** Order by (value / cost), not by the dossier's order.
3. **Gates.** Each stage ends with a go/no-go decision written down before the run, so we cannot reinterpret results afterwards.
4. **Scale ladder.** Run the same experiment at ring dimension n = 16, 32, 64, 128, then 256, fit a scaling law, and only then extrapolate. Never extrapolate from one point.
5. **Honesty about reading.** Scheme-specific code is written only after the relevant paper section is read. Record it in `notes/papers.md`.
6. **Disclosure.** Any result that looks like a break is first re-run at full size, then reported to the scheme team before anything public (CLAUDE.md).

## 2. Stages

Effort is in working days for one person; rough, to be revised after stage A.

### Stage A: Foundations and hygiene (3 to 4 days)

Code:
- `harness/mldsa/ntt.py`: NTT and inverse NTT, tested against `negacyclic_mul`.
- `harness/mldsa/sampling.py`: add SHAKE-based ExpandA, ExpandS, SampleInBall, ExpandMask using `hashlib`.
- `harness/mldsa/hints.py`: Power2Round, MakeHint, UseHint.
- `harness/mldsa/dsa.py`: keygen, sign, verify for FIPS 204, where `sign` can return **every attempt** (accepted and rejected) with which check failed.
- Tests: FIPS 204 known-answer vectors. Check online which independent implementation to use as an oracle (candidates: `dilithium-py`, liboqs). Do not assume; verify before relying on it.

Run: full test suite; 1000 random sign/verify round trips.

Docs: fix the stale lines (DOSSIER says "no code has been run"; ROADMAP tooling item).

Gate A: our ML-DSA verifies its own signatures and matches the oracle. If not, stop and fix before any scheme work; every later result depends on it.

### Stage B: Transcript simulator interface (2 days)

Code, `harness/schemes/base.py`:
- `Attempt` record: challenge c, released values (w1, z, hint, v, ...), accepted flag, failed-check label.
- `SchemeView` interface: given keys and attempts, return exactly what an adversary sees. One subclass per scheme. The adversary model (passive, T-1 corrupted, corrupted coordinator) is a parameter.
- Move `ilwe_transcript.py` under this interface as `TalusV1View` (the broken early version, our positive control).

Gate B: the interface can express TALUS and one other scheme (Mithril) without changes to the estimators.

### Stage C: TALUS cap experiment (the headline; 8 to 12 days)

C0, read first (0.5 day): re-read TALUS PW v0.22 and Niot's note for exactly which values still leak per signature at v0.22, and confirm the BCC noise range and how t0 enters. If v0.22 no longer releases the observable, the stage becomes a statement about what the cap protects. Note this in LEARN.

C1, noise model (1 day), `harness/schemes/talus.py`:
- Noise uniform on (-gamma2+beta, gamma2-beta) (BCC) and the plain model, switchable.
- Target s' = s2 - t0 (t0 up to 2^12 in size, much larger than s2), so test both small and large targets.
- ML-DSA-44, -65 and -87 parameters; reduced-dimension ring (X^n + 1, n < 256) for the ladder.

C2, estimators (3 to 4 days), `harness/estimators/`:
- `edge.py`: **bounded-noise feasibility estimator.** Find x with |b_i + c_i x|_inf <= gamma2 - beta for all i. Implement as a linear program (scipy HiGHS) for small n, then a faster cutting-plane or projected method for larger n. The constraint rows are sparse (tau = 39 nonzeros), which helps.
- `hybrid.py`: least-squares start, LP refinement, rounding to the known small range of s2.
- `fisher.py`: analytic and Monte Carlo information for the plain and edge noise models. Gives a theory curve to compare against, as `ilwe_scaling.py` already does for least squares.
- Optional later: ILP / lattice reduction on the residual ambiguity, only if the LP leaves a few coefficients undecided.
- Tests: on noiseless input the LP returns the secret exactly; on edge-noise input the feasible region always contains the true secret (soundness).

C3, runs (3 to 4 days), `experiments/talus_edge_scaling.py`:
1. n-ladder: for each n, find N*(n) = smallest N giving full recovery with probability 0.5 and 0.99 (bisection, at least 20 trials per point; fewer at large n, say so).
2. Sensitivity: vary gamma2, beta, tau separately at fixed n to separate their effects.
3. Compare edge vs least squares at every point.
4. Fit log N* against log n, log gamma2, log tau; check whether the fitted exponents match the 1/N law (H1) or the 1/sqrt(N) law.
5. Extrapolate to n = 256 and k rings (k = 4, 6, 8), all three parameter sets. Include fit uncertainty, not just a point value.
6. One full-size spot check at n = 256 near the predicted N* to confirm the extrapolation.

Gate C1 (written before the runs):
- If the extrapolated 99% N* (with its error bar) is **below 2^14**: possible break. Do not publish. Re-run at full size, re-read the spec for anything that blocks it, then contact the authors.
- If it is **between 2^14 and the uniqueness wall (2^15.2)**: report a thin margin with the exact bits.
- If it is **above the wall**: the cap holds against this attacker; report the margin and that the authors' wall is consistent with our measurement.
Any of the three is a publishable table.

Use of results: Gate C1 produces Table "margin in bits per parameter set", and figures F2 and F3 below.

### Stage D: Kao P2 check (2 to 3 days; cheap, run in parallel with C)

Read the mask construction of profile P2 (arXiv 2601.20917) and Remarks 11 and 15.
Code: `harness/schemes/kao_p2.py` on a toy ring: simulate T = N-1+1 parties with T-1 corrupted and |S minus C| = 1, compute the masks from the adversary's own shares, and test whether lambda_h * A * y_h is recoverable and then s1 = c^-1 (z - y).
Gate D: either a concrete one-signature recovery on the toy (then confirm against the paper's footnote and text, because the authors already note the limitation, so the question is whether the N-1 claim contradicts it) or a precise statement of why it does not apply. A confirmed or refuted note either way.

### Stage E: Mithril (6 to 8 days)

Read first: Mithril security proof sections and PW v1.0 parameters (success probability about 1/2).
Code:
- `harness/schemes/mithril.py`: replicated shares, hyperball sampling, local rejection; output the full view including rejected attempts' noisy commitments.
- `harness/estimators/renyi.py`: Monte Carlo and analytic Renyi divergence / Fisher information of the accepted z about c*s1 at the real parameters.
- Hint accounting: if Sage is available, use the lattice estimator (`malb/lattice-estimator`) with the exact share subset of T-1 parties; otherwise a documented core-SVP calculator in Python and say it is a rougher substitute. Check Sage availability first (Stage A).
Run: information per signature I; wall estimate about 4/(I*tau) (dossier formula, verify its derivation before use) against q_s = 2^50 (proved) and 2^64 (NIST-style).
Gate E: wall above 2^64 means no problem found; between 2^50 and 2^64 means a proof gap with a concrete number; below 2^50 means it contradicts the paper and needs checking.

### Stage F: Quorus and Trilithium rejected transcripts (5 to 7 days)

Read first: the full Quorus and Trilithium papers (currently only the main text of some sections).
Code:
- `harness/schemes/quorus.py`: reveal-on-reject view (w1, c, bottom).
- `harness/schemes/trilithium.py`: rejected partial responses; plus the version with the Quorus-style added noise.
- `harness/estimators/two_sample.py`: KS and chi-squared tests of "rejected partial vs uniform", and a regression of released values against c*s1, c*s2.
- ILP leakage test using rejected-signature challenges, following the published attacks cited in the Quorus paper (confirm the exact reference first; the dossier names ZWSY25).
Gate F: power analysis first. State the smallest leak the test could detect at N samples. A non-detection is reported as "no leak above X", never as "no leak".

### Stage G: Cross-scheme matrix and packages (ongoing)

Fill the 10-point checklist matrix (scheme by item: tested, leak found, not leaking at tested strength, not tested). When NIST packages appear (from late Nov 2026, deadline not before March 2027), rerun the harness on the real reference code.

## 3. Validation: how we "prove it out"

These are the arguments a reviewer will want. Build each one into the code, not just the text.

1. **Positive control.** Run the full harness on TALUS v0.1 transcripts (Niot's broken versions) and on a toy with `y` leaked. The harness must recover the key. Report how many signatures it needs; compare with Niot's numbers.
2. **Negative control.** Run on genuine single-signer ML-DSA transcripts, including rejected attempts. Every estimator must find nothing. Measure the false-positive rate across many seeds.
3. **Calibration.** Show measured error against theory (already true for least squares at 3%; repeat for the edge estimator).
4. **Power.** For each test, the smallest leakage it can detect at a given N. This turns "nothing found" into a quantified statement.
5. **Scaling law.** Results at several n and a fitted exponent, not one data point.
6. **Independence.** Key recovery counted only if the recovered key verifies the public key relation, not just if the estimate is close.
7. **Reproducibility.** Fixed seeds, one command (`python -m experiments.run_all`), outputs saved as JSON/CSV in `experiments/results/`, Python and package versions recorded.

Threats to validity to state openly: reduced-ring extrapolation; adversary model simplifications; schemes read from preview writeups that may change; no appendix proofs read; our ML-DSA is not constant-time and not meant for production.

## 4. Paper and presentation framing

**One-sentence claim to aim for (depends on Gate C1).** "We build a reusable leakage-testing harness for threshold ML-DSA, validate it on a known-broken scheme, and use it to measure how many signatures a bounded-noise attacker needs against TALUS v0.22's cap, plus leakage margins for Mithril, Quorus and Trilithium."

**Contributions, in order of strength.**
1. A validated, open test harness with positive and negative controls (this survives any outcome).
2. A measured margin for the TALUS cap with an edge-aware estimator (either outcome is a result).
3. Mithril accepted-z information at q_s = 2^64 versus the proved 2^50.
4. Kao P2 confirm-or-refute note.
5. Rejected-transcript tests for Quorus and Trilithium with stated power.

**Figures and tables.**
- F1: harness architecture (scheme view, estimators, controls).
- F2: error versus N, log-log: least squares, edge estimator, theory curves (shows 1/sqrt(N) versus 1/N).
- F3: N* versus ring dimension with fitted line, extrapolated to n = 256, with the cap and the uniqueness wall drawn as bands.
- T1: margin in bits per scheme and parameter set (cap, wall, measured N*, gap).
- T2: checklist matrix (scheme by item) with the status of each test.
- T3: controls table (positive: recovered at N signatures; negative: false positive rate; power).

**Presentation outline (about 12 minutes).** 1) Why threshold ML-DSA and the four proposals (2 min). 2) The two facts that cause most attacks: A is left-invertible, and z = y + c*s1 over the integers (2 min). 3) The harness and its controls (2 min). 4) TALUS cap: the 1/sqrt(N) versus 1/N idea and F2/F3 (3 min). 5) Other schemes and the matrix T2 (2 min). 6) Limits and disclosure (1 min).

**Fallback if nothing breaks.** The paper's thesis becomes "measured security margins and a validated methodology", with T1 as the main result. The report already says this is acceptable.

## 5. Timeline (proposal; adjust to the real Phase 2/3 deadlines)

| Window | Work |
|---|---|
| 6 to 12 Oct | Stage A; start reading for C0 and D |
| 13 to 19 Oct | Stage B; Stage C0 and C1; Stage D |
| 20 Oct to 2 Nov | Stage C2 and C3; Gate C1 decision |
| 3 to 16 Nov | Stage E; controls and power analysis |
| 17 to 30 Nov | Stage F; matrix; start writing |
| Dec | Rerun on packages if available; figures; presentation |

## 6. Open questions that change the plan

1. What are the deadlines and deliverable format of Phases 2 and 3 (paper, code, talk)?
2. Is Sage available (for the lattice estimator in Stage E)? If not, Stage E uses the rougher substitute.
3. Team split: C (estimators) and D/E/F (scheme models) can run in parallel with two people.
4. Compute: laptop only? Stage C at n = 256 may need long LP runs; the ladder is designed to keep most runs small.

## 7. Immediate next actions

1. Stage A: NTT, SHAKE sampling, hints, full sign/verify, KATs.
2. Stage C0: re-read the v0.22 release and BCC noise range.
3. Stage D: read Kao P2 masks (cheap, independent).
4. A 1-D toy of H1 (uniform noise, midrange versus mean estimator) as a one-hour sanity check before building the LP.
