# talus

## Design summary

See docs/DOSSIER.md.

## Stage C0: what the v0.22 preview writeup says (re-read 2026-10-06)

Source: TALUS-PW02.pdf (9 pages, text extracted locally and read, sections 2.2 to 2.3.1 and the trade-offs paragraph). Not the full version, appendices or code.

- BCC: a nonce y passes if every coefficient of r0 (the low part of w = A y) satisfies |r0| < gamma2 - beta. Then the LowBits check on w - c s2 passes for any s2 and c. Acceptance 43.2% (ML-DSA-44), 31.7% (-65), 39.1% (-87).
- The writeup itself says "a passive attack recovers the key after about 2^30 signatures under one key (ML-DSA-65)", hence the per-key cap 2^13 / 2^14 / 2^14 by mandatory key rotation. So the authors agree the s2 channel is still open at v0.22; the cap is the defence. Our experiment is therefore about v0.22, not only about older versions.
- Integer-uniqueness wall q_uniq about 2^15.2 / 2^16.4 / 2^16.2; the cap sits about 2.18 / 2.4 / 2.15 bits below it.
- NOT stated in the preview writeup: the exact list of values released per signature, and how t0 enters. The 9-page text only says the threshold nonce is a sum of party shares and that the "revealed summed nonce" leakage is bounded in the full version. The model in `harness/schemes/talus_bcc.py` (uniform noise in (-(gamma2-beta), gamma2-beta), target s2 or s2 - t0) is our reading, not a quoted spec. Still to check: the full version / package spec when available.

## Attack surface / hypotheses

- H1: edge-aware estimator closes much of the gap between least squares (about 3.6e9 signatures at -44) and the cap (2^13 to 2^14). See docs/PLAN.md stage C and docs/RUNBOOK.md.

## Experiments and results

See docs/RUNBOOK.md and experiments/results/.

## Reading status

- Preview writeup v0.22: main text read. Full version and appendices: not read.
