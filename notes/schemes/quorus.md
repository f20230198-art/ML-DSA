# quorus

## Design summary

Source: Quorus, ePrint 2025/1163 (USENIX Security 2026), local `papers/quorus_2025-1163.pdf` (38 pages). Honest-majority (n = 2t+1) MPC over Shamir shares mod q, with edabits for small randomness, comparisons and Decompose.

- Algorithm 1 (MPC-friendly ML-DSA): w := A y + e_w with e_w uniform in [-eta, eta]^(kn); a single attempt; checks ||z|| < gamma1 - beta and ||w0 - c e|| < gamma2 - beta (line 3); hint MakeHint(-c t0, A z - c t + c t0), i.e. e_w deliberately left out (the "optimization"); line 6 checks ||c t0|| and hint weight.
- On a line-3 rejection the parties release (w1, c, bottom). On a line-6 failure, Protocol 5 releases (w1, c, z, bottom): z has passed both norm checks, so it is distributed like an accepted signature.
- Rejection is one bit: Pi_RejSamp feeds all comparison bits into a batched OR (lift to F_p with dabits, sum, multiply by a random u, open). The positions of failing coefficients stay hidden; the paper notes that leaking them together with c enables key recovery [ZWSY25 = Zhou, Wang, Sun, Yu, ePrint 2025/214, verified online 8 Oct].
- Security: Theorem 1 (UF-CMA-bottom in the QROM) from Theorem 2 (scHVZK under two MLWE assumptions, using del Pino-Niot for the rejection-conditioned MLWE). The distinguisher in scHVZK gets sk.

## Experiments and results

### 2026-10-08: correctness and rejection rates of Algorithm 1 (`harness/schemes/quorus.py`, `experiments/results/quorus_correctness*.txt`)

400,000 single attempts per parameter set, 20 keys (control without e_w: 200,000 attempts, 10 keys). Every released signature checked with our FIPS 204 verifier (which passes the NIST ACVP vectors).

| Set | M_rep (ours) | M_rep (Table 2) | line-6 failure given line 3 passed | signatures | failing FIPS 204 verification |
|---|---|---|---|---|---|
| ML-DSA-44 | 4.30 | 4.25 | 1.34% (hint weight) | 91,810 | 0 |
| ML-DSA-65 | 5.12 | 5.09 | 0.40% | 77,862 | 0 |
| ML-DSA-87 | 3.85 | 3.85 | 0.77% | 102,992 | 0 |

- e_w changes nothing measurable: control runs give the same rates (4.32 / 5.17 / 3.85; line 6 1.35% / 0.43% / 0.80%).
- The paper says the line-6 failure rate is "around 0.02"; we measure 0.4 to 1.3% (all from hint weight, none from ||c t0||). Same order, slightly lower.
- **Zero verification failures in 272,664 signatures.** This matches a one-line argument that the "skip e_w in the hint" optimization is exactly correct, not just empirically: the verifier recovers HighBits(w - c e - e_w) (since A z - c t1 2^d = w - c e + c t0 - e_w, and UseHint with the -c t0 hint removes c t0). Line 3 guarantees |LowBits(w) - c e| < gamma2 - beta coefficient-wise, and |e_w| <= eta < beta (beta = tau eta), so |LowBits(w) - c e - e_w| < gamma2 and the high bits are unchanged: HighBits(w - c e - e_w) = w1. (Decompose's wrap case at q-1 is also covered by the same margin; checked empirically, not separately proved.) So the paper's "empirically ... does not sacrifice correctness" can be replaced by a proof.

### Leakage tests (Gate F power statement)
- A purely statistical test on released rejected w1 cannot detect anything: w = A y + e_w mod q with y in a 2^18-wide box and A uniform is uniform mod q to extreme precision, whatever small secret-dependent shift the rejection conditioning adds. Any leak is computational (needs MLWE-type lattice work), which is what Theorem 2 claims to rule out. We did not run a lattice distinguisher.
- Not tested: the MPC layer (batched OR, comparisons) for implementation leakage; there is no code to test.

## Reading status

- 2026-10-08: Sec. 1.3, 2.1-2.3, 3 (Algorithm 1, Theorems 1-2 and sketches), 4.1-4.3 (rejection protocol, online protocol, offline phase start) read fully. Skimmed: Sec. 5 (performance), App. A. Not read: App. B proofs (simulator Algorithm 11 and hybrids), App. C-D.
