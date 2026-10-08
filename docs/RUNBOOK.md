# RUNBOOK: TALUS edge-estimator experiment

Status 2026-10-08: 133 tests pass. Dense -44 run at n = 256 (20 trials) and -87 at n = 256 added; see LEARN changelog 8 Oct. Earlier status 2026-10-06: Ladder run for ML-DSA-44 (n = 8..256), ML-DSA-65 (n = 64, 256), ML-DSA-87 (n = 64), s2-t0 and plain noise (n = 64). Margin table and caveats in docs/LEARN.md. Use `--device gpu` for n = 256 (about 3x faster).

## What the experiment tests
Hypothesis H1 (docs/PLAN.md): with hard-edged noise, an edge-aware estimator has error ~ 1/N (least squares: 1/sqrt(N)), so full recovery of the TALUS s2 channel needs roughly 2^18 signatures at ML-DSA-44 instead of 3.6e9. The TALUS v0.22 cap is 2^13 to 2^14, the authors' uniqueness wall about 2^15.2.

Prototype evidence (not saved, 3 trials per point, reduced rings, first session): error x N / bound ~ 1.1 to 1.9 for n = 8, 16, 32.

## Code map
| File | Role |
|---|---|
| `harness/mldsa/ringn.py` | Z[X]/(X^n+1) for any n: FFT product, adjoint, sparse challenge sampler, dense constraint rows |
| `harness/schemes/talus_bcc.py` | Channel model: uniform noise in [-bound, bound]; plain (gamma2) or BCC (gamma2-beta); target s2 or s2-t0 |
| `harness/estimators/edge.py` | `chebyshev` (full sparse LP, small n), `chebyshev_cutting_plane` (memory-light, any n), `least_squares_cg`, feasibility certificate |
| `experiments/talus_edge_scaling.py` | Sweeps N per n, saves JSON in `experiments/results/`, prints summary and fitted slopes |
| `harness/tests/test_edge.py` | 12 unit tests (ring math, soundness, LP vs cutting plane, edge beats LS) |

## Steps (run from the repo root)
1. **Tests first:** `python -m pytest harness/tests -q` (old 18 plus the new ones). Fix failures before anything else.
2. **Small ladder (minutes):** `python -m experiments.talus_edge_scaling --n 8 16 32 --trials 20`
   Check: fitted slope for the edge estimator near -1 and for least squares near -0.5; `K_hat` roughly constant across n; `true_feasible` = 1.00 everywhere (if not, there is a bug).
3. **Medium (tens of minutes, watch memory):** `--n 64 --trials 10 --steps 6`, then `--n 128`. Use `--solver cp`. Do **not** use `--solver lp` above n = 32 (it ran out of memory at n = 64).
4. **Full size spot check:** `--n 256 --trials 3 --steps 5` near the predicted N*; also `--params ML-DSA-65` and `ML-DSA-87`, and `--target s2-t0`, and `--noise plain` for comparison.
5. **Full-secret success:** per ring element success p(N) must hold for all k elements: use p^k (k = 4, 6, 8). The summary prints per-element N*; pick N where p >= 0.5^(1/k) and 0.99^(1/k).
6. **Compare** the resulting N* with the cap (2^13 to 2^14) and wall (2^15.2 to 2^16.4); fill the margin table in the report.

## Decision gate C1 (fixed in advance)
- extrapolated 99% N* (with error bar) below 2^14: possible break; do not publish; re-run at full size, re-read the spec, contact the authors first
- between 2^14 and 2^15.2: thin margin, report it in bits
- above the wall: cap holds against this attacker, report the margin

## Known limits of the model (state them in any write-up)
- Noise independent uniform per coefficient; the real LowBits wrap at q-1 and the hint side-information are not modelled.
- What TALUS v0.22 actually releases per signature must be re-read first (PLAN stage C0). If the observable is gone, this is a statement about the earlier versions and the cap's purpose, not about v0.22.
- Reduced rings keep the challenge density tau/n; extrapolating to n = 256 needs the n = 64/128/256 points.
- The estimator uses the known range of the secret as a box prior (valid information; keep it identical across methods).
- Rounded estimate counts as recovered only if it equals the secret; `feasible_rounded` additionally says whether it explains all observations.
