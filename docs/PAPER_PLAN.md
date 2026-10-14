# Paper plan: from Phase 2 results to a conference paper

Written 2026-10-13. Status: agreed with the user; work starts next session. Items 1-4 are untested hypotheses.

## Where we stand
- Kao P2: key from one signature (real break; Kao is not a Call submission).
- Mithril: Thm. 3.2 covers 2^26-2^37 signing queries, not 2^50 (wrong exponent from Devevey A.6, ePrint only); a-posteriori sharing hint loss 18-24 bits for ML-DSA-65 (paper says 7-12). Proof gaps, not key recovery: typical-case leaking sessions are about 1 in 2^50 or rarer, and 158 bits remain after the hint loss.
- TALUS v0.22: with edge + ILP, N ~ 2^16.1 / 2^17.45 / <= 2^17.18 (-44/-65/-87): ~3.1-3.5 bits above the cap, ~1 bit above the uniqueness wall. No break. Our channel model, not their code.
- Quorus/Trilithium: no leak found; paper errata only.

## Tier 1: could create a headline
1. **TALUS rotation = refresh?** Read the v0.22 spec: does "key rotation" create an independent key, or refresh the shares of the same secret (as in Kao App. C)? If refresh, the cap does not bound total leakage and our attack (~2^16-2^17.5 total) applies: a break of a Call submission. Effort: half a day of reading.
2. **Rejected attempts leak?** Does a rejected TALUS attempt release w1 (the crumb)? About 2.3 attempts per signature would give ~1.2 bits more data per counted signature, against a ~1 bit margin over the wall. Effort: spec reading, then about 1 day of reruns.
3. **Corrupt party / coordinator.** Model T-1 corrupted parties or a corrupt coordinator (e.g. selective acceptance narrowing the noise). Effort: 1-2 weeks.
4. **Stronger estimator.** Joint solving across ring elements, use hint h, lattice-reduction finish. Effort: about 1 week.

## Tier 2: rigour
5. Check whether GuilhemN/threshold-ml-dsa has the Mithril Go signing code; if yes, run our views on real Mithril transcripts.
6. Mithril ML-DSA-65 a-posteriori sharing: full lattice-estimator run (not rough) against the NIST Category 3 threshold; plain yes/no answer.
7. Kao P2 full end-to-end demo on real ML-DSA-44 (not toy).
8. TALUS statistics: >= 20 trials per point with confidence intervals, full-secret recovery with ILP, fitted scaling law. Run with at most 1-2 processes (laptop overheats).
9. Corrected Devevey A.6 bound with a short proof.

## Tier 3: paper craft
10. Framing: "first systematic leakage evaluation of NIST MPTC threshold ML-DSA submissions"; threat model; scorecard table; harness with controls as a contribution.
11. Disclosure: ask the instructor, then send the Kao and Mithril emails (docs/disclosure_drafts.md); include author responses.
12. Open artifact: one command per table/figure (USENIX open-science appendix is mandatory).
13. Rewrite for venue format (USENIX 13 pages body; PQCrypto LNCS).

## Timeline (deadlines checked 13 Oct 2026; confirm on official pages)
| When | Do | Target |
|---|---|---|
| Next session / week 1 | 1, 2, 6; 11 (ask instructor, send emails) | Decide whether TALUS has a real hole |
| Weeks 2-5 | 5, 7, 8, 9, 12; write paper | PQCrypto 2027: abstract 17 Nov, paper 24 Nov 2026 |
| Nov-Jan | Build out any hit from 1-3 | USENIX Security '27 cycle 2: register 19 Jan, paper 26 Jan 2027 |
| From Mar 2027 | Run on official packages | Later USENIX cycle / CCS / S&P |

Fallbacks: ACNS 2027 cycle 2 (21 Jan 2027); IACR CiC (next issue deadline 26 Oct 2026, too soon).

**Start next session with item 1 (TALUS rotation), then item 2.**
