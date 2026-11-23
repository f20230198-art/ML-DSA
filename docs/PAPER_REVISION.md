# Paper revision plan (post-referee, 11 Nov 2026)

Audience: the two authors. This captures the code audit and drafts the three starting
deliverables the supervisor plan asked for. Scope decision (11 Nov): **lead with Kao P2;
present TALUS as a Level-2 discrepancy on a reconstructed channel.**

Evidence levels used throughout:
- **L1** demonstrated attack under a stated adversary model.
- **L2** statistical or proof discrepancy, no practical attack.
- **L3** open hypothesis.

## 0. Central research statement (one sentence)

> Of the four NIST MPTC First-Call threshold ML-DSA proposals, Kao's Profile P2 admits
> full single-signature recovery of the secret-key component s1 by a passive observer of
> the per-party commitment broadcast — because the pairwise masks that hide each W_i sum
> to zero and so expose the aggregate nonce image A*y — which we demonstrate end to end
> against an unmodified FIPS 204 verifier; the other three proposals leak only under
> stronger or model-dependent conditions.

## 1. Code audit findings (what the repo actually supports)

**Kao P2 (L1, strongest).** `harness/schemes/kao_p2_real.py` is sound. Masks cancel
(sum W_i = A*y), `_solve_slots` inverts A per NTT slot, s1 = c^-1(z - y), and the result
is checked against the public key *and* the dealer's secret: 15/15 keys per set, control
(one W_i withheld) 0/15, all signatures pass this repo's unmodified FIPS 204 Verify.
Honest caveats already recorded: our reimplementation (author code not public), recovers
s1 only (not s2/t0), rejection checks run in the clear as a stand-in for the MPC.

**TALUS cap (L2, not L1).** The headline margins come from `talus_bcc.py`, a synthetic
channel where the noise `e` is injected by hand as `rng.integers(-bound, bound+1)`,
`bound = gamma2 - beta`. The docstring itself says this is "our reading, not a quoted
spec". The v0.22 reference implementation is not out (expected March 2027) and the 9-page
writeup never states the per-signature release list or how t0 enters. So the cap result is
a property of a reconstructed channel, not of deployed TALUS. `gate_b_views.py` does run
real ML-DSA attempts through a modelled view and recover one ring element, which is good,
but the view still *models* the release (assumes w1 per attempt, no hint).

**Full-secret numbers (must fix).** Two problems, both confirmed in code:
1. `item8_full_secret.py` uses `P_full = P_elem^k` — an explicit independence assumption,
   labelled "extrapolated, not run". The 2^16.09 / 2^17.51 figures are extrapolations.
2. The one "real" full-secret run (`item8_full_analysis.py`) groups 4 consecutive element
   trials as one ML-DSA-44 secret, but `ilp_n256.py` reseeds per trial and calls
   `sample_target`, so those 4 elements are **4 independent random targets, not 4 elements
   of one key sharing one challenge set.** The experiment therefore measures P_elem^4 by
   construction — it is the independence assumption dressed as a measurement, not a test of
   it. This is the single most important fix and it is fixable (WP-T below).

**Statistics.** 20 trials/point, logistic fit, no CI on the fitted 95% threshold. Raw
points have Clopper-Pearson intervals; the threshold does not.

## 2. Deliverable A — Kao P2 formal attack (the lead result)

### Setting and notation
ML-DSA public key (A, t), A in R_q^{k x l}, t = A*s1 + s2, with (t1, t0) the Power2Round
split (t = t1*2^d + t0, t0 centered). Profile-P2 signing set S, |S| >= T, Lagrange
coefficients lambda_i at 0. Per attempt party i broadcasts
    W_i = lambda_i * A*y_i + m_i,
with pairwise PRF masks m_i summing to zero (Lemma 1). Published signature (c~, z, h) with
    z = sum_i lambda_i z_i = y_comb + c*s1,   y_comb = sum_i lambda_i y_i.

### Assumptions (explicit)
- **A1** The adversary sees {W_i}_{i in S} of one accepted attempt. P2 broadcasts all W_i
  (Fig. 1b, Remark 11, App. M.1). Passive; no corruption required.
- **A2** The adversary knows pk = (rho, t1) and the signature (c~, z, h).
- **A3** A has full column rank in every NTT slot (holds whp for ExpandA; checkable).
- **A4** c = SampleInBall(c~) is NTT-invertible (no zero slot); else use the next signature.
- **A5** sum_i m_i = 0 (scheme correctness, Lemma 1 — not an adversary assumption).

### Algorithm (input: pk, msg, sig, {W_i}; output: s1 or FAIL)
1. Parse (rho, t1) <- pk; (c~, z, h) <- sig; A <- ExpandA(rho); c <- SampleInBall(c~).
2. w <- sum_{i in S} W_i mod q.                      # = A*y_comb, masks cancel (A5)
3. For each NTT slot solve A_slot * yhat_slot = what_slot over Z_q (Gaussian elim, k x l).
   Any singular or inconsistent slot -> FAIL (needs the next signature).
4. shat1 <- (NTT(z) - yhat) * c^-1   slot-wise;  s1 <- centered INTT.
5. **Public verification.** Accept s1 iff ||s1||_inf <= eta AND
   ||A*s1 - t1*2^d||_inf <= eta + 2^(d-1). Else FAIL.

### Why the output is the real key (not just a feasible value)
Step 5 is a *public* check: A*s1 - t1*2^d must equal s2 - t0, a short vector. Because A is
injective and under M-SIS two distinct short preimages of the same t yield a short M-SIS
solution, the only short s1 consistent with t is the true key component. A passing s1 *is*
the key. This makes the attack **L1** under the passive-broadcast model.

### Scope of the claim (state plainly)
- Recovers **s1 only**. s2 and t0 are not recovered, so this is key-secrecy breakage, not
  yet a full signing key. A standard forgery needs s2, t0 (the hint corrects c*t0 - c*s2).
- Breaks the paper's stated **key secrecy** (App. B.3: "any coalition of < T parties learns
  nothing about the secret") with **zero** corruptions — a clean contradiction.
- Only Profile P2. P1 (TEE coordinator) and P3+ (2PC) send W_i to a coordinator only and
  are unaffected.
- L3 open question for future work: recover s2 from w (now known) across many signatures
  via the LowBits(w - c*s2) relation — the same channel idea as TALUS. Not claimed.

### Security-model row (Kao P2 attack)
| Field | Value |
|---|---|
| Passive/active | passive (observe only) |
| Corrupted parties / threshold | 0 corruptions; any |S| >= T |
| Static/adaptive | n/a (passive) |
| Can abort sessions | no |
| Controls messages | no |
| Chooses signing queries | no |
| Accesses internal state | no (only the public broadcast) |
| Needs all broadcasts | **yes** — every W_i of the target attempt (control: one missing -> fail) |
| Budget | one signature + slot-wise linear algebra, O(n*k*l) |
| Success condition | public consistency check (step 5) passes |
| Success probability | ~1 (fails only on non-invertible c; retry next signature) |
| Consequence | full s1 recovery => breaks P2 key secrecy; forgery needs s2, t0 (open) |

### Disclosure gate (WP-B6) — blocking before any public posting
Coordinate with Leo Kao first: send the finding + minimal reproduction, ask whether our
reimplementation matches the published profile, allow response time, record the timeline.
Per project rules (`project-scope-decision`), draft only; do not send until the user says so.
Draft already in `docs/disclosure_drafts.md` section 1.

## 3. Deliverable B — TALUS leakage equation (L2, under the model)

For each accepted attempt the modelled adversary reconstructs, from public data only:
    w' = A*z - c * t1*2^d                       (exactly computable from pk + signature)
    b  = w' - 2*gamma2 * w1                      (one ring element; needs released w1)
Under the model (`talus_bcc.py`, `TalusBCCView`) this equals
    b = -c*(s2 - t0) + e,   e = LowBits(w),   |e| < gamma2 - beta under BCC.

**What is sound:** every symbol on the right of the first two lines (A, z, c, t1, w1) is
public or reconstructible, so *if* w1 is released the equation is adversary-computable and
exact. **What is the reconstruction (the L2 caveat):** that TALUS v0.22 releases w1 per
attempt, and that e is independent and uniform under the joint law P(e | c, s2) with BCC.
Neither is validated against a spec or reference code. Honest statement for the paper:

> Given the modelled release, the leakage equation is exact and every variable is
> observable; whether deployed TALUS v0.22 releases these quantities, and whether the noise
> follows the modelled law, is pending the March 2027 reference package.

This fails referee gate 2 ("no major claim resting only on reconstructed protocol
behaviour") if presented as L1 — hence it is presented as L2, a discrepancy in a
reconstructed channel, with the validation explicitly deferred.

## 4. Deliverable C — experiment matrix to validate the thresholds (WP-T)

### The fix
Replace the grouped-independent-trials construction with a genuine full-key experiment:
- Draw **R >= 30 independent real ML-DSA keys** per parameter set; take the true s2
  (k ring elements) from keygen.
- For each key, generate **one** transcript of N signatures with the **same challenge set c
  shared across all k elements** (as in reality — every element sees the same c per
  signature). Run edge+ILP recovery on all k elements of that *one* transcript and AND the
  per-element successes.
- This captures the real positive correlation (shared c) instead of assuming independence.
- Report full-secret success vs N with a **bootstrap CI over the R keys**; fit the 95%
  threshold with profile-likelihood or bootstrap, not a bare logistic point.
- Directly compare measured P_full against P_elem^k to **validate or refute** the
  independence assumption (WP-A5), instead of assuming it.

Expected direction: shared c makes the events positively correlated, so P_full > P_elem^k
and the true threshold is **lower** (attack easier) than the current pessimistic
extrapolation. Worth stating either way, because now it is measured.

### Matrix
| Set | k | N grid (around per-element transition) | Keys R | Element recoveries per set |
|---|---|---|---|---|
| ML-DSA-44 | 4 | 50k,55k,60k,65k,70k,80k | >=30 | 30*4*6 = 720 |
| ML-DSA-65 | 6 | 130k,143k,160k,179k,215k | >=30 | 30*6*5 = 900 |
| ML-DSA-87 | 8 | 120k,135k,148k,165k,184k | >=30 | 30*8*5 = 1200 |

Seeds recorded per (key, N). Each element recovery is GPU edge + CPU ILP; **one GPU job at
a time, few CPU jobs** (`feedback-parallel-runs`, `feedback-subagents-and-checks`). This is
a multi-day run; budget it before week 5-6 of the schedule.

### Implementation note
`talus_bcc.make_transcript` draws its own c per call (one element). A new helper is needed
that draws c **once** (count x n) and produces b for all k elements of a real key's s2, so
the k recoveries share the challenge set. New script, e.g. `experiments/full_secret_real.py`,
with its own seed; leave the old extrapolation files in place but mark their numbers
"extrapolated, superseded".

## 5. Gate status against the referee

- Gate 1 (no unsupported math assumptions): **failing** until WP-T replaces P_elem^k.
- Gate 2 (no claim on reconstructed protocol only): **failing for TALUS as L1** -> fixed by
  demoting TALUS to L2; **passing for Kao P2** (real verifier, author text pinned).
- Gate 3 (no unqualified security claim without adversary model): fixed by the security-model
  rows (Kao P2 row above; TALUS/others to follow).

## 6. Next actions, in order
1. Implement WP-T (`full_secret_real.py`) and launch the ML-DSA-44 run first (cheapest).
2. Write the Kao P2 section from Deliverable A (theorem + algorithm + security row).
3. Draft the restructured outline (Abstract last, survey cut, Phase-3 framing removed).
4. Hold the TALUS section at L2 with the validation-pending note until March 2027.
5. Disclosure: keep drafting only; do not send (user decision pending).
