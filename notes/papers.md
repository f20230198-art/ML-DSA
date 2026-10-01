# Papers reading table

Updated 2026-10-01 after downloading full texts. Reading depth:
- **Full**: read end to end.
- **Targeted**: downloaded the full PDF and read the abstract plus the passages that back the report's claims (found by search), not the whole paper.
- **Abstract**: only the abstract/metadata page.
- **Memory**: not checked.

| # | Paper | Venue / ID | What it gives us | Depth |
|---|-------|-----------|------------------|-------|
| 1 | NIST FIPS 204 | NIST, Aug 2024 | Standard; Table 1 parameters verified | Targeted (Table 1) |
| 2 | Ducas et al., Dilithium | TCHES 2018(1), pp. 238-268; ePrint 2017/633 | Original signing structure | Abstract (PDF downloaded) |
| 3 | NIST IR 8214C | NIST 2026 | The Call | Memory (cited via writeups) |
| 4 | Celi et al., Efficient Threshold ML-DSA (Mithril) | USENIX Security 2026; ePrint 2026/013 | Mithril: 1 MB up to 6 parties, 7-12 bit loss, success prob 1/2 | Targeted |
| 5 | Borin et al., Threshold Signatures Reloaded | ePrint 2025/1166 (withdrawn) | Preliminary Mithril | Abstract (PDF unavailable, withdrawn) |
| 6 | Celi et al., Poster | ACM CCS 2025 | Early Mithril | Abstract |
| 7 | Mithril preview writeup v1.0 (2026-01-19) | NIST MPTC | Spec outline, N<=8, no identifiable aborts, float sampler | **Full** |
| 8 | Bienstock et al., Quorus | USENIX Security 2026; ePrint 2025/1163 | MPC-friendly variant, t<n/2, 16/29 rounds, 150 KB per round | Targeted |
| 9 | Dufka et al., Trilithium (+ SplitKey writeup v0.1) | ePrint 2025/675 | 3 keygen / 14 signing rounds, CRP, UC | Targeted; writeup partly (first 200 lines) |
| 10 | Kao and Chang, TALUS | arXiv 2603.22109 (v5) | BCC, ~2^30 lower bound, cap ~2^14 | Targeted (abstract + key passages) |
| 11 | TALUS preview writeup v0.22 (2026-08-11) | NIST MPTC | Cap, TEE not proposed, response to Niot | **Full** |
| 12 | Kao, Shamir Nonce DKG | arXiv 2601.20917 | P2 needs abs(S minus C) >= 2, disclosed; claims N-1 unforgeability | Targeted |
| 13 | Niot, Key-recovery attacks on TALUS | ePrint 2026/1386 | Two attacks, sample table | **Full** |
| 14 | del Pino et al., Threshold Raccoon | EUROCRYPT 2024; ePrint 2024/184 | Non-ML-DSA threshold lattice sig | Abstract (PDF downloaded) |
| 15 | del Pino et al., lattice TS with identifiable aborts | ePrint 2025/871 (withdrawn) | Short-share DKG | Abstract |
| 16 | Gur, Katz, Silde | PQCrypto 2024 (full version ePrint 2023/1318) | Threshold-HE approach | Abstract (PDF downloaded; venue confirmed) |
| 17 | Bootle et al., LWE without modular reduction | ASIACRYPT 2018 | ILWE; easy if sigma_e not superpolynomially larger than sigma_a | Targeted |
| 18 | Zhou et al., Rejected signatures' challenges | TCHES 2025; ePrint 2025/214 | ILP on rejection leakage | Abstract (PDF downloaded) |
| 19 | Damm et al., Concealed ILWE | ASIACRYPT 2025; ePrint 2025/1629 | Huber/Cauchy regression | Abstract |
| 20 | Yates et al., ILWE with rejection sampling | arXiv 2512.08172 | Least squares on real signatures | Abstract (PDF downloaded) |
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
