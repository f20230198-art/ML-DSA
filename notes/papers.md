# Papers reading table

Updated 2026-10-01 after downloading full texts. Reading depth:
- **Full**: read end to end.
- **Targeted**: downloaded the full PDF and read the abstract plus the passages that back the report's claims (found by search), not the whole paper.
- **Abstract**: only the abstract/metadata page.
- **Memory**: not checked.

| # | Paper | Venue / ID | What it gives us | Depth |
|---|-------|-----------|------------------|-------|
| 1 | NIST FIPS 204 | NIST, Aug 2024 | Standard; Table 1 parameters verified | Targeted (Table 1 only) |
| 2 | Ducas et al., Dilithium | TCHES 2018(1), pp. 238-268; ePrint 2017/633 | Original signing structure | Abstract (PDF downloaded) |
| 3 | NIST IR 8214C | NIST 2026 | The Call | Memory (cited via writeups) |
| 4 | Celi et al., Efficient Threshold ML-DSA (Mithril) | USENIX Security 2026; ePrint 2026/013 | Mithril: 1 MB up to 6 parties, 7-12 bit loss, Q_s = 2^50 | Main body read (Sec. 1-3, 3.3, 3.4, parts of 4); appendices and proofs skimmed by headings only |
| 5 | Borin et al., Threshold Signatures Reloaded | ePrint 2025/1166 (withdrawn) | Preliminary Mithril | Abstract (PDF unavailable, withdrawn) |
| 6 | Celi et al., Poster | ACM CCS 2025 | Early Mithril | Abstract |
| 7 | Mithril preview writeup v1.0 (2026-01-19) | NIST MPTC | Spec outline, N<=8, no identifiable aborts, float sampler | **Full** |
| 8 | Bienstock et al., Quorus | USENIX Security 2026; ePrint 2025/1163 | MPC-friendly variant, t<n/2, 16/29 rounds, 150 KB per round | Main body read (Sec. 1-5 incl. all protocols and benchmarks); appendix proofs not read |
| 9 | Dufka et al., Trilithium (+ SplitKey writeup v0.1) | ePrint 2025/675 | 3 keygen / 14 signing rounds, CRP, UC, MLWR-type assumption | Main body read (Sec. 1-5 start, App. D discussion); security proof appendices not read; SplitKey writeup first half |
| 10 | Kao and Chang, TALUS | arXiv 2603.22109 (v5) | BCC, ~2^30 lower bound, cap ~2^14 | Main text read (Sec. 1-12, App. A-C); App. D-I not read |
| 11 | TALUS preview writeup v0.22 (2026-08-11) | NIST MPTC | Cap, TEE not proposed, response to Niot | **Full** |
| 12 | Kao, Shamir Nonce DKG | arXiv 2601.20917 | P2 needs abs(S minus C) >= 2, disclosed; claims N-1 unforgeability | Verified by download 2026-10-06: arXiv:2601.20917v6 (3 Mar 2026), Leo Kao, Codebat Technologies, cs.CR. Read: abstract, Sec. 1-4.3 (Remarks 4, 10, 11, 15, Lemma 1, Lemma 2, Algorithm 3), Sec. 6.1, 6.3-6.4, Cor. 5 proof, App. B.1, M.1 start; the other appendices and all benchmarks not read line by line |
| 13 | Niot, Key-recovery attacks on TALUS | ePrint 2026/1386 | Two attacks, sample table | **Full** |
| 14 | del Pino et al., Threshold Raccoon | EUROCRYPT 2024; ePrint 2024/184 | Non-ML-DSA threshold lattice sig | Abstract (PDF downloaded) |
| 15 | del Pino et al., lattice TS with identifiable aborts | ePrint 2025/871 (withdrawn) | Short-share DKG | Abstract |
| 16 | Gur, Katz, Silde | PQCrypto 2024 (full version ePrint 2023/1318) | Threshold-HE approach | Abstract (PDF downloaded; venue confirmed) |
| 17 | Bootle et al., LWE without modular reduction | ASIACRYPT 2018 | ILWE; easy if sigma_e not superpolynomially larger than sigma_a; m >= C (sigma_e/sigma_a)^2 log n | Abstract and intro read |
| 18 | Zhou et al., Rejected signatures' challenges | TCHES 2025; ePrint 2025/214 | ILP on rejection leakage | Abstract and part of intro; needs rejected response z via side channel |
| 19 | Damm et al., Concealed ILWE | ASIACRYPT 2025; ePrint 2025/1629 | Huber/Cauchy regression | Abstract and Sec. 1 (introduction) read |
| 20 | Yates et al., ILWE with rejection sampling | arXiv 2512.08172 | Least squares on real signatures | Abstract and Conclusions; attack not effective at practical parameters |
| 21 | Shamir, How to Share a Secret | CACM 1979 | Secret sharing | Memory |
| 22 | Feldman, Verifiable Secret Sharing | FOCS 1987 | Commitment pattern TALUS copied | Memory |
| 23 | Komlo and Goldberg, FROST | SAC 2020, LNCS 12804, pp. 34-65 | Threshold Schnorr contrast | Abstract (PDF downloaded; pages cross-checked via TALUS writeup) |
| 24 | del Pino and Niot, Finally! | PKC 2025, LNCS 15676, pp. 169-199 | Compact Raccoon threshold sig, 2^64 cap, <=8 parties | Via citations in Quorus and Mithril writeup only |

## Corrections found by reading (already applied to the report)

- Quorus online communication is about 150 KB per party per round in the paper (the website abstract said 100 KB); 0.31-0.59 MB per signature; tolerates t < n/2.
- TALUS TEE variant is not proposed in v0.22; BCC rates are 43.2% / 31.7% / 39.1%.
- Least-squares variance is sigma_e^2 / (N tau), not what the first draft said.
- Kao's paper itself discloses the abs(S minus C) >= 2 requirement and the failure at T = N, while still claiming N-1 dishonest-majority unforgeability. The open question is whether that failure gives key recovery.
- Mithril and Quorus are both USENIX Security 2026 papers.
- Added reference 24 (Finally!).
- Mithril's writeup compares: Quorus at least 24 rounds, Trilithium about 60 rounds on average (different counting from Trilithium's own 14 per attempt).

## Still to read in full

Mithril full paper (security proof, Sec. 3 and appendix), Quorus (simulatability proof), Trilithium (rejection-check security argument), Kao Lemma 2 and Remarks 11 and 15, TALUS Sections 7-8, Damm and Zhou bodies. IR 8214C not downloaded.

## Second pass (Mithril proof, Trilithium rejection argument)

- **Mithril** (Sec. 3, Theorem 3.2, Sec. 3.4): security proof uses Renyi divergence and holds only for Q_s = 2^50 signing queries (not 2^64, which my dossier-based draft assumed). K parallel repetitions amplify success probability; imbalanced hyperball sampling; success probability target 1/2. Game 9 replaces commitments of rejected attempts by uniform values under MLWE.
- **Trilithium** (Sec. 3 discussion and App. D): publishes w_H even in rejected runs and relies on an MLWR-type assumption, explicitly called non-standard for ML-DSA parameters. Related work either adds noise (Quorus), assumes a new problem (Barthe et al.), or treats it as open (Coron et al.). The "heuristic" wording comes from the Quorus paper.
- Report problems P2 and P3 were rewritten to match.

## Third pass (full reading of main bodies, 2026-10-01)

Read the main bodies of Quorus, Trilithium, TALUS, Mithril (Sec. 3) and Kao (Sec. 1-4.2). New facts, all applied to the report:
- **Quorus:** its variant adds a noise term e_w to w, removes the signing loop, always outputs w1; proof in the QROM, scHVZK from MLWE; cites ZWSY25 (Zhou et al.) as a key-recovery attack if positions of failing coefficients leak together with c.
- **Trilithium:** also supports the Quorus-style e_w variant; the unmodified variant relies on an MLWR-type assumption for publishing w_H in rejected runs.
- **Mithril:** full MLWE-sample commitments (not bare A.x), hyperball rejection sampling, K parallel repetitions, Q_s = 2^50.
- **TALUS:** the authors already price the s2 channel: q_uniq about 2^15.2-2^16.4, cap 2^14, syndrome meet-in-the-middle with modelled cost about 2^160 but proven floor only about 2^58 / 2^49; they call the shield "model-supported, not proven"; ML-DSA-44 has no cokernel (k = l). Also cites a sign-leakage attack (BKM26, about 190,000 signatures) that is not yet in our list.
- **Kao:** P2 broadcasts commitments; by its own Remark 15 an exposed lambda*A*y_h gives the key, hidden only if abs(S minus C) >= 2; with abs(S) = T and T-1 corruptions that fails, yet Table 1 credits P2 with dishonest-majority unforgeability. Uses a trusted dealer for keys. Its theorem is stated non-vacuous for q_s < 16,000.

## Not read at all (still)

Appendix proofs of every paper above; Raccoon, Gur-Katz-Silde, Dilithium, FROST beyond abstracts; FIPS 204 beyond Table 1; IR 8214C; the Damm and Zhou bodies beyond their introductions.
