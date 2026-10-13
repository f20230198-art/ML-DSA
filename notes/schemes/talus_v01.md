# TALUS v0.1 (the version Niot attacked)

## Sources (checked online 2026-10-13)

- L. Kao, R. Chang, "TALUS: Threshold ML-DSA with One-Round Online Signing via Boundary Clearance
  and Carry Elimination", arXiv:2603.22109. Versions: v1 2026-03-23 (Kao only), v2 2026-03-24
  (Kao and Chang), v3 2026-07-08, v4 2026-07-23, v5 2026-08-09 (current title "TALUS: FIPS-204-Exact
  Threshold ML-DSA via Boundary Clearance"). Downloaded v1 and v2 PDFs (94 pp.) to
  `papers/talus_v01_dl/`.
- G. Niot, "Key-Recovery Attacks on TALUS: A Cryptanalytic Note", IACR ePrint 2026/1386
  (received 2026-07-07). Abstract page re-checked; the PDF could not be downloaded in this
  session (the server returned an HTML page), so the earlier full reading (DOSSIER) is relied on.
- Niot's abstract names only "TALUS ... available on arXiv", no version. Since the note was
  received 2026-07-07 and v3 appeared 2026-07-08, the attacked text is v1/v2. **"v0.1" in this
  project = arXiv 2603.22109v2** (our label, not the authors'). v1 and v2 differ in author list and
  wording; the protocols I compared (TEE/MPC signing, Feldman broadcasts) read the same.

## What was read (v2, text extracted with pypdf)

Read: Sec. 4.3-4.5 (BCC Safety Theorem, Remarks 5-6, Corollaries 2-5), Sec. 6 (TALUS-TEE:
Protocols 5-10), Sec. 7.2 (Protocol 11 KeyGen, Remark 20), Round 1 of TALUS-MPC preprocessing
(Feldman Phi_{h,k} broadcast), Protocol 16 (MPC Sign). Not read: the CarryCompare / CSCP MPC
details, security proofs, appendices (incl. B.6), experiments.

Key facts from the text:
- No r0-check at all: "In TALUS, we never perform the FIPS 204 r0-check" (Remark 5). A nonce is
  filtered by BCC on LowBits(w) only, before the challenge exists.
- Released per signature: sigma = (c_tilde, z, h), and the coordinator broadcasts w1.
- TALUS-MPC KeyGen Round 2 broadcasts A s1_i (and s2_i); every preprocessing Round 1 broadcasts
  Phi_{h,0} = A y_h. (In v2 this is every signing, not only in blame.)
- Nonce: y = sum of |S| pieces, each uniform on [-gamma1/|S|+1, gamma1/|S|].

## What was implemented

`harness/schemes/talus_v01.py`: `TalusV01` signer (real FIPS 204 hashing, SampleInBall, hint from
public data, z-bound and hint-weight checks, no r0-check), `TalusAttempt` (dsa.Attempt + y_parts,
phi0, LowBits(w)), views `TalusV01SigView` (any observer) and `TalusV01MPCView` (+ Phi_{h,0}),
Niot attack 1 (`invert_A` by Gaussian elimination mod q per NTT slot; `attack1_keygen`,
`attack1_nonce`), attack 2 observable `s2_channel`: b = A z - c t1 2^d - 2 gamma2 w1 = r0 - c(s2 - t0),
r0 uniform in (-(gamma2-beta), gamma2-beta). Signatures verify with the unmodified verifier.
Experiment: `experiments/talus_v01_niot.py`, logs `experiments/results/talus_v01_niot_*.log`.

## Assumptions / simplifications

- KeyGen: plain ML-DSA keygen + Shamir sharing of s1 mod q (instead of the Pedersen DKG).
- Nonce pieces from numpy RNG; MPC w1 computed directly (CarryCompare not implemented; its
  correct output is assumed), Theorem 14's 2% correction failure not modelled.
- |S| = T = 3 in all runs.

## Results (ML-DSA-44) -- see the report in the task hand-off and the logs

Keys = seeds 101 (N up to 1e5), 102, 103 (N up to 3e4); |S| = 3; 0.425 signatures per attempt.

- Attack 1: exact s1 from the KeyGen broadcast 3/3 keys; from ONE MPC signature 60/60 (20 per key).
- Attack 2 (least squares, all 4 rows x 256 coeffs, target s2 - t0), rms error (seed 101 / 102 / 103)
  vs theory sigma_e/sqrt(N tau):
  N=1e3: 281 / 276 / 278 (278); N=3e3: 165 / 158 / 162 (161); N=1e4: 92 / 87 / 90 (88);
  N=3e4: 52 / 52 / 52 (51); N=1e5: 28 (28). Exactly correct coefficients: at most 14/1024.
- Extrapolating the curve, rms 0.25 needs about 1.2e9 signatures (Niot's table: ~3.1e8 with his
  criterion). Not recovered within the runs; the experiment confirms the channel is real on actual
  v0.1 transcripts and that least squares behaves exactly as the Gaussian theory predicts.
