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

## 2026-10-14: rotation and rejections (PW v0.22 Sec. 2.2.1, 2.3, 4; re-read)

- Key rotation = fresh key generation. Share refresh (zero-share re-sharing of s1, same public key) explicitly "does not reset the accumulated signature leakage". Paper plan item 1: no hole.
- BCC filtering is offline on secret shares; w1 stays committed and only pooled (BCC-passing) nonces are opened. Rejected BCC trials release nothing (per writeup).
- Open: "rare residual rejections (z-bound, hint weight)" are caught by FIPS 204 Verify before release, i.e. after the z_i broadcast in Round 2. Unknown: their rate under the Irwin-Hall nonce, and whether such sessions count toward the cap. A rejected z = y + c s1 is the classic biased sample. Needs the Package spec; hypothesis only.
- Update same day (arXiv 2603.22109v5, Sec. 6, Alg. 2, Remark 7.1, first 100k characters of the HTML read via a fetch tool; Sec. 7.4 and 8.3 bodies not read): first signing attempt succeeds ~98.0% (-44), ~99.6% (-65, 12,645 attempts), ~99.2% (-87); the z-norm check "never fired" (Irwin-Hall nonce concentrated); the residual is the hint-weight check. Nonce marked consumed before z_i release. Whether failed sessions count toward q_s: not seen. Either way at most ~2% extra transcripts at -44, i.e. log2(1/0.98) ~ 0.03 bits: negligible against the ~3-bit margin. Item 2 closed, no hole.

## 2026-10-15: insider / corrupt party (paper plan item 3, first pass)

Source: arXiv 2603.22109v5 (downloaded 15 Oct, `papers/talus_v01_dl/talus_2603-22109v5.pdf`), read: Sec. 8 Theorem 4 paragraph, App. D "external view / insiders / malicious committee member" (text lines ~845-880, ~1725-1835). Rest of v5 not read in full.
- Authors' own position: external view certified ~114-121 bits up to the cap. MPC insider (corrupt minority t = T-1 of committee nu >= 2T-1, so m = nu - t >= T >= 2 honest nonce shares): only a ~4.4/5.1/6.0-bit distinguishing certificate; forgery hardness lambda/m is a conjecture. TEE coalition of T-1 signers (m = 1): "certifies nothing", attack exists for T >= 7-9; TEE not proposed.
- Insider de-shifts own nonce contributions: z' = y_h + c s1 with y_h ~ IH(m) (narrower, sharp/soft edge inside the box). Lemma 3 (fuzzy-r0 hiding): insider learns nothing extra about r0, so the s2 channel is the same as for an outsider.
- Malicious steering of BCC: authors measure no gain (max I ratio 1.0017; accepted noise stays uniform). Committed/range-checked contributions close it anyway. Not re-checked by us.
- Our rough walls (`experiments/talus_insider_wall.py`, results `experiments/results/talus_insider_wall.txt`): MPC insider m = T: 2^24.8-2^26.1 (-44), 2^28.5-2^29.7 (-65/-87), i.e. 12-16 bits above the cap. TEE m = 1: below cap from T = 7 (-44), 11 (-65), 9 (-87); paper says 7-9 (our -65 differs; not resolved). TEE margins at small T are only 0.1-2.4 bits.
- Conclusion: no hole in the proposed MPC profile from an honest-minority insider, by this estimate. Caveats: the m = 2 Fisher number cuts a log-divergent integral by hand; no simulation yet; corrupt coordinator rejected-response view (authors: ~19.5-22.6 bits certified, out-of-box events ~2^-19.4 per key lifetime) not checked.
