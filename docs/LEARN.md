# LEARN: the project explained from zero

Written for someone new to cryptography. Part 1 teaches the basics, Part 2 explains the project in plain words, Part 3 is a running log of everything we do, how, and why. New entries go at the bottom of Part 3.

---

# Part 1: Basics

## 1.1 What cryptography is for

Cryptography is the math that lets people do three things over an untrusted network:

- **Keep secrets** (encryption): only the intended reader can read a message.
- **Check who sent something** (authentication / signatures).
- **Detect tampering** (integrity).

This project is about the second and third: **digital signatures**.

## 1.2 Keys

Most modern cryptography uses a **key**: a secret number or object. In **public-key** cryptography you get a pair:

- a **secret key** (sk) that only you hold,
- a **public key** (pk) that everyone can see.

Knowing pk must not let anyone work out sk. That one-way-ness is what every scheme is built on.

## 1.3 Hash functions

A **hash function** turns any input into a fixed-size "fingerprint". Properties we need: the same input always gives the same fingerprint, a tiny change gives a totally different one, and you cannot go backwards from fingerprint to input. Examples: SHA-256, SHAKE. In signatures, we sign the hash of the message, not the message itself.

## 1.4 Digital signatures

A signature scheme has three algorithms:

1. **KeyGen**: produce (pk, sk).
2. **Sign(sk, message)**: produce a signature.
3. **Verify(pk, message, signature)**: say yes or no.

Security goal ("unforgeability"): without sk, nobody can produce a signature that verifies, even after seeing many valid signatures on messages of their choice. Real-world uses: software updates, HTTPS certificates, passports, cryptocurrency transactions.

## 1.5 Why the old schemes are in trouble: quantum computers

RSA and elliptic-curve signatures rely on problems (factoring, discrete logarithm) that a big enough **quantum computer** would solve quickly. No such machine exists today, but data and keys last decades, so NIST ran a competition and standardised **post-quantum** schemes whose hard problems are believed to resist quantum attacks.

## 1.5b Modular arithmetic in one minute

"Mod q" means keep only the remainder after dividing by q, like a clock. A clock mod 12: 10 + 5 = 3. Our q is 8380417 (a prime). Everything in ML-DSA happens mod q, which is why numbers "wrap around". Remember this: when an equation has **no** wrap-around (it holds over ordinary integers) it is much easier to attack. That fact will matter later.

## 1.6 Lattices and "learning with errors" (LWE)

A **lattice** is a regular grid of points in many dimensions. Some problems on lattices are very hard, even for quantum computers. The workhorse is **LWE (Learning With Errors)**:

> You are given a public matrix A and the vector t = A·s + e (mod q), where s is a short secret and e is a small random "error". Find s.

Without the error e it is easy (it is just solving linear equations). With the error it is believed to be hard. **Module-LWE** is the same idea using a bit of algebraic structure so everything is faster. A related problem is **Module-SIS** (find a short vector that A maps to zero).

Key vocabulary:

- **Short** vector: all entries are small numbers.
- **Norm** (written ‖v‖∞): the largest absolute entry of v. "Short" means small norm.

## 1.7 ML-DSA (the signature scheme this project is about)

ML-DSA is the NIST standard **FIPS 204**. It comes from a scheme called **CRYSTALS-Dilithium**. It has three security levels: ML-DSA-44, ML-DSA-65, ML-DSA-87.

**Keys.** The secret key is two short vectors s1 and s2. The public key is (A, t) where t = A·s1 + s2. This is an LWE instance: finding s1 from t is hard.

**Signing (the key idea).** To sign message m:

1. Pick a fresh random short vector **y** (the "nonce", one-time randomness).
2. Compute w = A·y and take its "high bits" w1 (throw away the low-order digits).
3. Compute a **challenge** c = Hash(m, w1). c is a very sparse polynomial with only a few ±1 entries.
4. Compute **z = y + c·s1**. This hides s1 behind the random y.
5. **Rejection sampling** (see next section): if z or a related quantity is too big, throw everything away and restart from step 1.
6. Output the signature (c, z, hint).

**Verifying.** Anyone can recompute w1 from (A, z, c, t) and check that hashing it gives c, and that z is short.

## 1.8 Rejection sampling: the part that makes this hard

z = y + c·s1 would leak s1 slowly if we always output it: the distribution of z would be centred on c·s1, so many signatures reveal the centre. Fix: only output z when it lands in a safe box, so that within the box z looks uniform no matter what s1 is. Otherwise throw it away and retry. Two checks:

- **Check 1**: ‖z‖∞ < γ1 − β. Hides s1.
- **Check 2**: ‖LowBits(w − c·s2)‖∞ < γ2 − β. Hides s2 and keeps verification correct.

Typically ML-DSA needs about 4 tries per signature. Rejected tries are never published in the normal single-signer scheme. Remember: **whatever is published must look independent of the secret.** Every attack in this project is about something being published that is not independent of the secret.

## 1.9 Secret sharing and "threshold" signatures

What if one device holding sk is a single point of failure? Idea: split sk among N parties so that any **T** of them can sign together but fewer than T can do nothing. This is a **(T, N) threshold scheme**, built on **secret sharing**:

- **Shamir secret sharing**: hide the secret as the constant term of a random polynomial of degree T−1. Give each party one point on the curve. Any T points determine the polynomial (and the secret); T−1 points reveal nothing.
- **Commitments**: a way to publish a "locked" version of a value that proves you committed to it without revealing it. In older schemes (discrete log) you publish g^x, which is safe. TALUS tried the lattice analogue, publishing A·x. **That is not safe** (see 1.10).

Why thresholding ML-DSA is hard:

1. The secret and the nonce must be shared, but shares of a short vector are not short, which breaks the norm checks.
2. "High bits" is not additive: high bits of a sum is not the sum of high bits.
3. The rejection checks need the full secret, which nobody holds.

Different schemes pick different tricks (see Part 2).

## 1.10 Cryptanalysis: attacking schemes on purpose

**Cryptanalysis** is the study of breaking cryptography. Cryptographers do this to schemes they did not design, before attackers do. This project is cryptanalysis of *proposed* threshold schemes, with the goal of reporting findings to the designers.

Two facts that power most attacks here:

1. **A is a tall matrix** (more rows than columns). So if someone publishes A·x for a short x, you recover x by **Gaussian elimination**: ordinary school linear algebra, no lattice hardness. Over the integers (no wrap-around) this is easy. So publishing A·x is *not* hiding.
2. **z = y + c·s1 holds with no wrap-around.** So if anyone learns the nonce y, then s1 = (z − y) / c. One leaked nonce = broken key.

Another tool: **ILWE** (Integer LWE). It is LWE without the mod q. Data of the form b = −c·s′ + e (small noise e) can be solved by **least squares** (the same maths as fitting a line to noisy data) given enough samples. With more cleverness you use **integer linear programming (ILP)** or **robust regression** to need fewer samples. That is how a leaked "noisy equation per signature" turns into key recovery after enough signatures.

**Fisher information** measures how much a single observation tells you about a hidden parameter. If every signature leaks a tiny bit of Fisher information about s1, after enough signatures (roughly 4 / (information × τ)) you can estimate s1. This is the "wall" you will see in the docs.

## 1.11 NIST and the Call

NIST (US standards body) runs the process that standardises cryptography. In 2026 it opened a **First Call for Multi-Party Threshold Schemes** (**IR 8214C**, the "MPTC" project). Teams submitted threshold designs; the public can analyse them. Our job is to analyse the four that threshold ML-DSA.

## 1.12 Glossary

| Term | Meaning |
|------|---------|
| ML-DSA | NIST post-quantum signature standard (FIPS 204) |
| Dilithium | The scheme ML-DSA is based on |
| Lattice | Multi-dimensional grid; source of hard problems |
| LWE / MLWE | Learning With Errors / Module version; the hard problem |
| Nonce (y) | One-time random value used when signing |
| Challenge (c) | Hash-derived sparse polynomial used in signing |
| Rejection sampling | Throw away outputs that would leak the key |
| Threshold (T, N) | Any T of N parties can sign |
| MPC | Multi-party computation: computing on shared secrets without revealing them |
| DKG | Distributed key generation: parties build a shared key with no dealer |
| UC | Universal composability: a strong style of security proof |
| TEE | Trusted execution environment (secure hardware enclave) |
| ILWE | LWE without modulus; solvable by regression |
| ILP | Integer linear programming |
| Cryptanalysis | Analysing and trying to break crypto |
| ePrint | IACR's open preprint server for crypto papers |

---

# Part 2: The project in simple words

## 2.1 What are we doing?

Four teams proposed ways to let several parties jointly produce a standard ML-DSA signature. We want to **check whether those schemes leak the secret key**, by building a test harness (a program) that simulates what an attacker would see and tries a set of known key-recovery techniques.

Why it matters: if a design leaks, finding it now (before NIST standardises) protects everyone later.

## 2.2 The four schemes in one line each

- **Mithril** (PQShield, Brave, Bristol): shares of a short key, each party decides locally whether to accept. Up to 6 parties.
- **Quorus** (J.P. Morgan): uses MPC to run a tweaked ML-DSA signing. Many parties, but needs an honest majority.
- **SplitForge / Trilithium** (Cybernetica): two parties (say a phone and a server) plus a helper that hands out correlated randomness.
- **TALUS** (Codebat): pre-filters nonces so a check always passes, which saves rounds.

## 2.3 What is already known

A researcher (Guilhem Niot) published practical **key-recovery attacks on earlier versions of TALUS**:

1. TALUS published A·x style commitments; by Gaussian elimination you get the key shares. (Fact 1 above.)
2. TALUS removed the s2 rejection check; each signature then leaks a noisy equation, and after some hundreds of millions of signatures (maybe far fewer with better maths) the key falls out. (ILWE.)

TALUS's authors replied by limiting each key to a few thousand signatures. Whether that margin is really safe is an open question.

No public attack exists on the other three. That could mean they are safe, or merely that nobody has tested them.

## 2.4 What we plan to build

A **leakage-testing harness**:

1. Code for ML-DSA basics (NTT, rounding, sampling).
2. Simulators that produce the public transcript of each scheme, **including rejected attempts**.
3. Estimators (least squares, bounded-noise, ILP, Fisher information) that try to recover the key from those transcripts.

Results are either "key recovered after N signatures" or "nothing found up to N signatures", both useful.

## 2.5 The coursework deliverable (Phase 1)

A 10-page report (Times New Roman 10 pt) covering: abstract, introduction, literature survey of recent papers (we cite 23), problem formulation with a proposed solution, conclusion, references. It lives in `report/`. Turnitin is run by you, not us.

## 2.6 How the repo is organised

See [README.md](../README.md). Short version: `docs/` for explanations and plans, `notes/` for reading notes, `harness/` for the code (empty so far), `report/` for the Phase 1 report.

---

# Part 3: Changelog (what we did, how, why)

Newest entries at the bottom. Format: **date, what, how, why.**

### 2026-10-01: Repo created
- **What:** Set up a git repo linked to https://github.com/f20230198-art/ML-DSA.git with first docs.
- **How:** `git init`, added the remote, wrote README, docs, folders, committed locally.
- **Why:** A clean home for the project. Rules agreed: commits authored only by you, never any co-author line, and **nothing is ever pushed by us**; you push yourself.

### 2026-10-01: Restructured around the dossier
- **What:** Moved `threshold-mldsa-dossier.md` to `docs/DOSSIER.md`; created `docs/ROADMAP.md`, `docs/CHECKLIST.md`, `docs/DESIGN.md`, notes per scheme, and empty `harness/` folders.
- **How:** Read the dossier and mapped its "ranked plan" to roadmap items and its 10-point checklist to a doc.
- **Why:** The dossier is the research direction; the repo should mirror it.

### 2026-10-01: Phase 1 report written
- **What:** Built a 10-page report (`report/Phase1_Report.docx`, generated by `report/build_report.py`) and `notes/papers.md` listing 23 sources.
- **How:** Verified abstracts of the key papers online (ePrint, arXiv, TCHES, ASIACRYPT pages), then wrote the survey from the dossier plus those papers. No LaTeX is installed, so the report is built as a Word file with python-docx and converted to PDF through Word to count pages.
- **Why:** Phase 1 coursework requires a literature survey and problem formulation with more than 15 papers. Note: the stated deadline (25.09.2026) has already passed, so check with the instructor.
- **Caveats:** Papers 2, 16, 21-23 are cited from memory; the full Mithril, Quorus and Trilithium papers are not yet read. The report says so openly.
- **Created this file** to keep explaining the project as it evolves.

### 2026-10-01: Report converted to IEEE format, literature matrix, CLAUDE.md
- **What:** Reformatted the report to IEEE style (two columns, Roman-numeral section headings, A/B/C subsections, italic Index Terms, numbered references with quoted titles). Added a literature matrix (Table II) rating each of the 23 papers H/M/L for relevance and ticking which themes it covers. Still exactly 10 pages. Created `CLAUDE.md` with the standing rules and updated memory.
- **How:** Patched `report/build_report.py` (two-column section, IEEE heading function, reference tuples), rebuilt, converted to PDF through Word and counted pages.
- **Why:** The course asked for IEEE form, and a matrix shows at a glance how related each paper is. CLAUDE.md makes sure the rules (no co-author, never push, update this file) persist across sessions.
- **Relevance summary:** 13 central, 5 supporting, 5 background; 15 of 23 are from 2025-2026.

### 2026-10-01: Downloaded the papers and checked the report against them
- **What:** Downloaded the full PDFs of 19 papers (the two withdrawn ones have no PDF) and checked the report's claims against the real text. Fixed several mistakes and added a 24th reference (Finally!, PKC 2025).
- **How:** Downloaded with curl, extracted text with pypdf, read the Niot note and the TALUS and Mithril writeups in full, and searched the long papers for the exact passages each claim depends on.
- **Why:** The first draft was written from abstracts and the dossier, so some details could have been wrong.
- **What changed:** Quorus communication is 150 KB not 100 KB; TALUS's TEE variant is not actually proposed; the least-squares variance formula was wrong; Kao's paper openly states the |S minus C| >= 2 limitation, so problem P4 is now phrased as "does that limitation give key recovery despite the paper's N-1 claim?"; Mithril and Quorus are USENIX Security 2026.
- **Honest status:** I read three documents completely and checked specific passages in about ten more. I did NOT read every paper end to end (see `notes/papers.md`, column "Depth").

**Beginner note, what is a "preview writeup"?** NIST asked each team to submit a short public document describing their plan before the full package is due. These are the "preview writeups"; they can still change.

### 2026-10-01: Second reading pass, sharper problems P2 and P3
- **What:** Read the security proof of Mithril and the rejection-check argument of Trilithium. Rewrote problems P2 and P3 in the report.
- **Findings:** Mithril's proof only covers 2^50 signing queries (NIST usually assumes 2^64), so there is a gap between what is proven and what is needed; the real question is how many signatures an attacker needs. Trilithium publishes the high bits of w even for rejected attempts and depends on an extra assumption (MLWR, "learning with rounding") that its own authors call non-standard; Quorus avoids this by adding a bit of noise.
- **Simple idea behind this:** a signer throws away "bad" attempts. If a threshold scheme still shows some data from the thrown-away attempts, an attacker may learn something from them. That is why rejected attempts matter.
- **Why:** these two points are the most concrete places to look for weaknesses, and they were wrong or vague in the first draft.

### 2026-10-01: Full reading of the main papers, report corrected again
- **What:** Read the main bodies of Quorus, Trilithium, TALUS, Mithril (security part) and Kao, plus the two writeups for Niot, TALUS, Mithril, Quorus. Corrected the report again (still 10 pages).
- **What changed in plain words:**
  - TALUS's own authors already worked out how the leak through the second secret (s2) behaves and say their safety margin is "model-supported, not proven". So problem P1 is now "how much work does it really take to recover s2 from at most about 16,000 signatures", not just "how many signatures".
  - Kao's paper itself says one of its modes (P2) hides data only if at least 2 honest signers take part; by the paper's own argument the key would leak if only T signers sign while T-1 are corrupted. So P4 is now a sharper question.
  - Mithril publishes a "noisy" commitment (a full MLWE sample) even for rejected attempts, like Quorus, so P3 now covers Mithril too.
  - Trilithium also offers the Quorus noise fix as an option.
- **Honest status:** I read the main text of the five core papers but NOT their appendix proofs, and only the abstracts of the background papers (Raccoon, Gur-Katz-Silde, Dilithium, FROST). `notes/papers.md` lists exactly what was and was not read.
- **Vocabulary:** an *appendix proof* is the long technical proof placed at the end of a paper; the main body states the result, the appendix proves it.

### 2026-10-01: Legal / permission check for publishing an attack
- **What:** Checked what NIST's call says about public analysis, after a team chat worried about "US agency" and permissions.
- **Findings:** NIST's call (IR 8214C) is built around public analysis: the stated goal is a body of reference material that the community analyses openly. Submitters hand in specs and open-source code. So analysing the submissions is intended. I did NOT find (and did not read the full text for) any rule requiring submitters' permission to publish cryptanalysis. Still unverified: the exact rules in the final call, and each submission's licence.
- **Plain words:** in cryptography, breaking a published scheme on paper or on your own machine is normal research (that is what conferences are for). Trouble only starts if you attack live systems you do not own. We only test our own copies of the code.
- **Real risk (the one Ashmit raised):** we may find nothing. Fix: make the report/paper valuable either way (a tested harness plus clear "we tried X, the margin is Y" results is a valid result).
- **Courtesy step:** tell the scheme authors before making any finding public (already in CLAUDE.md).

### 2026-10-01: First harness code, first experiment, report re-checked
- **What:** Wrote the first real code in `harness/` (ML-DSA parameters, rounding functions, polynomial multiplication, challenge sampler, a least-squares "ILWE" estimator) with 18 tests that all pass (`python -m pytest harness/tests`). Ran `experiments/ilwe_scaling.py` (output saved next to it).
- **What the experiment does, in simple words:** TALUS (an early version) leaked, with every signature, a value equal to "secret x known challenge + noise". Given many such pairs, you can average the noise away and read the secret. We simulated this for ML-DSA-44 and checked that the leftover error shrinks exactly as the maths predicts (error = noise size / sqrt(3 x tau x number of signatures)). It did (within 3%).
- **Finding to be careful about:** the formula N = 4*gamma2^2/(3*tau) in Niot's note gives error std 0.5, which is not enough to round all 1,024 secret coefficients correctly. In our simple model about 12 times more signatures (3.6e9) are needed. This does NOT contradict Niot (we did not read his derivation; his version may count differently or use better tricks). It only says the formula is an order of magnitude. Both numbers are far above TALUS's signing cap (2^13 to 2^14), which is the more important fact.
- **Report:** updated the scope note (one small experiment now exists), added a "Preliminary result" paragraph, changed milestone M3, removed the "Future directions" paragraph to stay at exactly 10 pages, and verified online the from-memory citations 2 (Dilithium), 16 (Gur-Katz-Silde), 23 (FROST) and 24 (del Pino-Niot). Shamir [21] and Feldman [22] are still from memory.
- **Vocabulary:** *unit test* = a small automatic check that a piece of code does what it should. *Matched filter / least squares* = two ways of averaging many noisy equations to estimate a hidden value.

### 2026-10-04: LaTeX version of the Phase 1 report
- **What:** Wrote `report/latex/phase1_report.tex` (IEEEtran, 10 pt, Times via newtx), with sections arranged to match the marking scheme: Abstract, Introduction, Literature Survey, Problem Formulation, Possible Solution, Conclusion, References.
- **How:** Took the content of `report/build_report.py`, moved stray paragraphs (feasibility, milestones) into the right sections, trimmed repetition, and used real equations and tables.
- **Why:** The submission rubric marks those exact sections, and the user wanted a LaTeX source to compile themselves. Not compiled here (no LaTeX installed), so the page count still has to be checked to be 10.
- **Update same day:** user asked for exactly 10 pages again, so the trimmed parts (worked attack examples, per-scheme attack surface, transcript table, metrics, risks, milestones, limitations) were added back into the LaTeX.
