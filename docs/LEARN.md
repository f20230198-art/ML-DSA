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

**When Fisher information breaks down.** For noise with hard edges (uniform on an interval) the Fisher information is infinite, so the usual 1/sqrt(N) error formula does not apply. Instead the smallest and largest observed values pin the answer, and the error shrinks like 1/N. That is why the edge estimator beats least squares by a huge factor.

**Integer programming (ILP).** A linear program allows any real numbers; an integer program forces whole numbers. The secret coefficients are small whole numbers, so after the linear program gives an approximate answer, an integer program can search the few nearby whole-number candidates and pick the one that fits every observation.

**Sharp edges and the 1/N idea.** If noise is bell-shaped, averaging N samples shrinks the error like 1/sqrt(N): 100 times more data buys 10 times more accuracy. If noise is uniform with hard edges (everything between -a and +a, nothing outside), the biggest and smallest values you see trap the hidden number between two walls, and the error shrinks like 1/N: 100 times more data buys 100 times more accuracy. Much less data is needed. TALUS's noise has hard edges, so this is the main thing we want to test.

**Positive and negative controls.** A test that never fires proves nothing. A *positive control* feeds the test a case that is known to leak, and it must find the leak. A *negative control* feeds it a case known not to leak, and it must stay quiet. Only with both does "we found nothing" mean something.

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
| NTT | Number-theoretic transform: a fast way to multiply polynomials mod q (like FFT, but exact) |
| Known-answer test (KAT) | Run the code on fixed inputs and compare with the correct output from a trusted implementation |
| ACVP vectors | NIST's official known-answer tests (from its Automated Cryptographic Validation Protocol server); passing them means our code computes exactly what the standard says |
| Renyi divergence | A number that says how different two probability distributions are, in the "worst case" sense: if it is M, any event is at most M times likelier under one than the other. Proofs multiply it over all signatures, so a tiny excess per signature limits how many signatures the proof covers |
| Hyperball | All points within a fixed straight-line (Euclidean) distance of a centre, in many dimensions. Mithril draws its random masks from a hyperball and accepts a signature share only if it lands inside a slightly smaller ball |
| Proof gap | The security proof's conditions are not met by the actual parameters. It is not an attack; it means the proof says less than claimed |
| Oracle (testing) | A trusted independent implementation we compare our code against |

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

### 2026-10-04: Plain-language rewrite of the LaTeX report
- **What:** Rewrote the body of `report/latex/phase1_report.tex` in shorter, plainer sentences (fewer semicolons and dashes, jargon explained). Facts, maths, tables and citations unchanged. Old version kept as `phase1_report_before_rewrite.tex`.
- **Also fixed:** the contribution table pointed to wrong section/table numbers; it now uses automatic LaTeX references.
- **Why:** the user found the old wording hard to read.

### 2026-10-06: Plan for the next phase (`docs/PLAN.md`)
- **What:** Wrote a staged plan (A to G) saying what code to write, what to run, how to use each result, and how to present it. Added matching items to `docs/ROADMAP.md` and two basics to Part 1 (sharp edges, controls).
- **How:** Read the dossier, roadmap, harness and the scaling experiment, then ordered work by value over cost and attached a written go/no-go gate to each stage.
- **Why:** The gap that matters is that plain least squares needs about 3.6e9 TALUS signatures while the scheme caps a key at 2^13 to 2^14. The plan tests whether an estimator that uses the hard edges of the noise (guess: error shrinks like 1/N) closes that gap. Either outcome is a result: a break or a measured margin.
- **Honest status:** the 1/N idea is a hypothesis from a one-dimensional analogy, not yet tested. Nothing was run for this entry. Deadlines for later phases are unknown and listed as open questions.

### 2026-10-06: Edge-aware estimator prepared (not yet run)
- **What:** Wrote the code for the TALUS bounded-noise experiment: reduced-ring arithmetic (`harness/mldsa/ringn.py`), the hard-edged noise channel (`harness/schemes/talus_bcc.py`), the edge estimator and a memory-light version of it (`harness/estimators/edge.py`), 12 new tests, the experiment script (`experiments/talus_edge_scaling.py`) and the run steps (`docs/RUNBOOK.md`).
- **Earlier same day:** a rough first test (not saved) on small rings suggested the edge estimator beats least squares by about 100 times at 100,000 signatures, and that its error falls like 1/N. A bigger run used about 6 GB of memory and was stopped, which is why the new solver stores only a few hundred constraints at a time.
- **How it works, in simple words:** each observation says "the secret times a known challenge is within B of this number". Intersecting thousands of such bands pins the secret down. The solver keeps a small set of the tightest bands, solves for the secret, checks which unused bands it violates, adds those, and repeats.
- **Honest status:** the files pass a syntax check only. Nothing, including the new tests, has been executed, by request. The 1/N law, the estimate of about 2^18 signatures and any comparison with the TALUS cap remain hypotheses until the runbook is followed.
- **Vocabulary:** *LP (linear program)* = finding numbers that satisfy many linear inequalities while minimising something. *Feasible* = consistent with every observation.

### 2026-10-06: First run of the edge estimator (small rings) and TALUS C0 re-read
- **What:** Ran the 30 tests (all pass) and the small ladder (ring sizes n = 8, 16, 32; 20 trials per point; ML-DSA-44 numbers, BCC noise, target s2). Also re-read the TALUS v0.22 preview writeup (main text, 9 pages) for the C0 step. Notes in `notes/schemes/talus.md`; raw results in `experiments/results/`.
- **Result, in simple words:** the edge estimator recovers the whole ring element exactly at about 1.8e5 to 4e5 signatures (2^17.5 to 2^18.7). Least squares did not recover anything at any size tried (its error stayed near 100 when it needs to be under 0.5). Plain least squares needs about 3.6e9 at full size, so the edge idea is worth roughly four orders of magnitude here. That supports H1 in spirit.
- **What it does NOT show:** the TALUS cap is 2^13 to 2^14 (8k to 16k), so these numbers are still 10 to 30 times above the cap. Also the sizes are tiny (n = 8 to 32, not 256), the exact 1/N law is not confirmed (the error hits 0 once recovery succeeds, which wrecks the slope fit; the printed slopes of -12 are an artifact, and `K_hat` is not constant), and the needed N went DOWN as n grew (tau = 1, 2, 5 nonzeros per challenge at n = 8, 16, 32). Whether that keeps going toward n = 256 (tau = 39) is exactly what the n = 64/128/256 points must show. Full secret recovery also needs all k = 4 ring elements, so the real N is a bit higher than the per-element numbers.
- **C0 finding:** the writeup itself says a passive attack recovers the key after about 2^30 signatures and that the cap is the defence, so the s2 channel is still open at v0.22. It does not say what is released per signature or how t0 enters, so our noise model is an assumption.
- **A mistake of mine:** I first thought the run was hung and killed it. It was only slow (about 40 s per point). The script saves after every point, so nothing was lost.
- **Vocabulary:** *artifact* (in a fit) = a number that comes from how we computed it, not from the real behaviour.

### 2026-10-06: Medium ladder (n = 64, 128) for the edge estimator
- **What:** Ran n = 64 and n = 128 (10 trials per point, same model as above). Results in `experiments/results/talus_edge_ML-DSA-44_bcc_s2.json`, log in `ladder_medium.log`.
- **Result:** per-element signatures needed for exact recovery (50% / 99% success): n = 32: 1.8e5 / 2.6e5; n = 64: 1.7e5 / 2.8e5; n = 128: 1.4e5 / 1.9e5. So the number is flattening around 1e5 to 2e5, about 2^17 to 2^18, instead of dropping toward the cap.
- **Provisional reading against gate C1:** about 2^17 is roughly 3 to 4 bits above the cap (2^13 to 2^14) and about 1 to 2 bits above the authors' uniqueness wall (2^15.2 to 2^16.4). If n = 256 behaves the same, the cap holds against this attacker with a measured margin of a few bits, and the authors' wall is consistent with it. This is NOT a break.
- **Why it is only provisional:** n = 256 not run; only 10 trials per point (coarse success rates); the noise model is our assumption (independent uniform noise, no wrap-around, no hint side information, see C0 note); per-element numbers, and all k = 4 elements must succeed, which raises N a little; the 1/N law still not cleanly fitted.
- **Next:** run n = 256 near N = 1e5 to 2e5, then ML-DSA-65/-87, `--target s2-t0` and `--noise plain`.

### 2026-10-06: Stage A (our own ML-DSA) and Stage B (scheme views)
- **What:** Wrote a full ML-DSA in the harness: `ntt.py` (fast polynomial multiplication), SHAKE-based samplers appended to `sampling.py`, `hints.py`, and `dsa.py` (key generation, signing, verifying, byte encodings). Signing can return **every attempt**, accepted or rejected, with the reason for rejection and the secret internals (y, w1, c, z). Then `schemes/base.py`: a `SchemeView` says what an adversary sees of each attempt. Two controls: `YLeakView` (a toy that also leaks the nonce y, so the key must be recoverable) and `PlainMLDSAView` (real ML-DSA, rejected attempts hidden, nothing should leak).
- **How I checked it:** installed `dilithium-py` (a separate pure-Python FIPS 204 implementation) as an oracle. For ML-DSA-44, -65 and -87 our public key, secret key and signature are byte-for-byte identical to the oracle's, including signatures that needed several attempts, and each verifies the other's. 12 new tests (42 in total) all pass.
- **Honest limits:** the oracle's own match with the official NIST test vectors is taken from its documentation, not re-checked by us; I did not download or run the official KAT files. Our code is not constant-time and is for experiments only. The views are controls only; no scheme-specific view (TALUS, Mithril, Quorus, Trilithium) exists yet, because those need their papers read first. Gate B (express TALUS and Mithril without changing estimators) is therefore not passed yet.
- **Why it matters:** every later result depends on the rejection behaviour being exactly right, and now rejected attempts can be studied with real values instead of synthetic ones.

### 2026-10-06: Stage D, Kao P2 check on a toy
- **What:** Downloaded Kao's paper (arXiv 2601.20917, version 6, 3 March 2026) and read the parts about profile P2 (Remarks 11 and 15, Lemma 2, the signing algorithm, Appendix B.1). Wrote `harness/schemes/kao_p2.py`, a tiny model (ring size 8, real modulus q) of how P2 hides each party's commitment: every pair of parties shares a secret seed, each party adds a mask made from those seeds to its commitment W_i, and the masks cancel when everything is added up. 5 new tests in `harness/tests/test_kao_p2.py`; the whole suite (47 tests) passes.
- **Result in simple words:** if you corrupt all signers except one, you know every seed that touches the honest party, so you can compute its mask and strip it off. That reveals lambda_h * A * y_h, which gives the honest party's secret nonce share y_h (solving linear equations, because A has more rows than columns). Subtract it from the public signature and divide by the challenge c, and you get the honest party's key share. Add your own shares and you have the full key from ONE signature. The toy does this exactly. With two honest parties the same attack fails (a control), because the seed between the two honest parties is unknown to you.
- **Is it new?** No. The paper itself says this in Remarks 11 and 15 and in its Table 1 footnote, and says P2 needs at least two honest signers for privacy. What looks inconsistent is that the paper still claims P2 is unforgeable against N-1 corruptions; since key recovery implies forgery, that claim only seems to hold if restated as "at least two honest signers in the signing set". Second observation, also from the toy: because the masks cancel in the sum, adding up all broadcast W_i gives A*y exactly, so if P2 really broadcasts every W_i then even an outsider recovers y and the key, whatever the number of honest parties. I could not confirm from the text whether P2 broadcasts them like that (its MPC part is described only for the r0-check), so this stays a question for the authors.
- **Honest limits:** I did not read every appendix line by line; the authors' code is not public; the toy has no rejection sampling, r0-check, hints or MPC, and uses a random matrix A. Nothing was published; contact the author first.
- **New basic idea:** a *pairwise mask* is a random value two parties both can compute (from a shared seed), added by one and subtracted by the other so it vanishes in the total. It hides a single value only from someone who does not know that seed.

### 2026-10-06: Speeding up the experiments (exact least squares, GPU) and results so far
- **What:** (1) Profiled one n = 256 trial: about 90% of the edge estimator's time is ring products (FFTs) in the "which observations does this guess violate?" check, only about 10% is the linear program. (2) Found that least squares can be solved exactly in one pass: after an FFT the equations for each frequency are independent, so each frequency is a single division (`least_squares_fft` in `edge.py`). It agrees with the old iterative solver to 1e-13 and takes 2.6 s instead of 40 s at n = 256, N = 120,000. (3) Added `harness/estimators/edge_gpu.py`: the same cutting-plane algorithm with the FFT work on the NVIDIA GPU (PyTorch, float64). It gives the same answer as the CPU code (difference 2.5e-8) and takes 8.8 s instead of 25.9 s. The experiment script has a new `--device gpu` option. Two new tests (14 in `test_edge.py`).
- **Why not faster:** the linear program (HiGHS) cannot use the GPU, so the speed-up is about 3 times for the edge estimator, about 30 times for least squares.
- **Results so far (per ring element, exact recovery, ML-DSA-44, BCC noise):** n = 256: 50% at 8.7e4, 99% at 1.9e5 signatures (2^16.4, 2^17.5), 5 trials per point. ML-DSA-65 at n = 64: exact recovery from about 5e5. ML-DSA-87, `s2-t0` and plain-noise runs at n = 64 are still running; ML-DSA-65 at n = 256 is running on the GPU. The numbers stay above the cap (2^13 to 2^14) and above the uniqueness wall (2^15.2 to 2^16.4), so no break is indicated. Final table to follow when the runs end.
- **Sub-task by a helper agent (Stage D):** see the Kao P2 entry above and `notes/schemes/kao-p2.md`. I checked that its files exist and the full suite passes (49 tests).
- **Vocabulary:** *profiling* = measuring which part of a program uses the time. *GPU* = graphics chip that does many identical small calculations at once, good for FFTs.

### 2026-10-06: Margin table for the TALUS cap (first full set of runs)
- **What:** Finished all planned runs: ML-DSA-44 and -65 at the full ring size n = 256, ML-DSA-87 at n = 64, plus two checks at n = 64 for ML-DSA-44 (target s2-t0, and "plain" noise without the BCC shrink). Raw numbers: `experiments/results/*.json`, logs `*.log`.
- **Result (per ring element, exact recovery with 99% chance, edge-aware estimator; interpolated between grid points, so rough):**

| Parameter set | n | signatures N* | log2 N* | cap | bits above cap | wall | bits above wall |
|---|---|---|---|---|---|---|---|
| ML-DSA-44 | 256 | 1.9e5 | 17.5 | 2^13 | 4.5 | 2^15.2 | 2.3 |
| ML-DSA-65 | 256 | 5.2e5 | 19.0 | 2^14 | 5.0 | 2^16.4 | 2.6 |
| ML-DSA-87 | 64 only | 5.2e5 | 19.0 | 2^14 | 5.0 | 2^16.2 | 2.8 |

- **Other checks:** target s2-t0 (the harder target that includes t0) needs the same N* at n = 64 (about 2.8e5 at 99%) as plain s2; plain noise instead of BCC changes almost nothing (1.6e5 / 2.8e5). Least squares recovered nothing in any run.
- **Gate C1 reading:** the edge-aware estimator is about 4 to 5 bits above the cap and 2 to 3 bits above the authors' uniqueness wall in this model, so no break is indicated; the cap holds against this attacker with a measured margin. That also means the authors' wall is roughly consistent with what we measure. Compared with plain least squares (about 3.6e9) the edge idea is worth about 4 orders of magnitude, but it does not reach the cap.
- **Why this is not final:** (1) 5 trials per point at n = 256 and 10 at n = 64, so success rates are coarse and the 99% numbers are interpolations; (2) ML-DSA-87 only at n = 64, using the observation that -65 gives the same N* at n = 64 and n = 256; (3) recovering the whole secret needs all k = 4, 6 or 8 ring elements to succeed, so the real N* is somewhat above these per-element values; (4) the noise model is our reading of TALUS, not a quoted spec (no hint information, no wrap-around, independent uniform noise); (5) the 1/N law was never cleanly fitted; (6) a stronger attacker (lattice reduction, ILP on the leftover ambiguity, better use of the hints) is not tested.
- **Next:** more trials around the transition, a full-secret (k ring elements) check, then Stage E (Mithril).

### 2026-10-08: Official NIST test vectors, firmer TALUS numbers, first Mithril finding
- **NIST test vectors (what):** downloaded NIST's official ML-DSA test vectors (ACVP, from github.com/usnistgov/ACVP-Server) and kept a small subset in `harness/tests/vectors/acvp_mldsa.json` (script `extract_acvp.py` rebuilds it). New test `harness/tests/test_acvp.py`: 9 key generations, 36 signatures (deterministic and randomised, with and without context) and 36 verifications (valid and deliberately corrupted signatures). **All 81 pass.** Not covered: "pre-hash" signing and "external mu", which our code does not implement. **Why:** until now our ML-DSA had only been compared with another library; now it matches the standard itself.
- **TALUS, denser run (what):** ML-DSA-44 at full size n = 256 with 20 trials per point (before: 5) at 7 values of N between 6e4 and 2.3e5. Success per ring element: 0, 0, 15%, 75%, 100%, 100%, 100%. So the 50% point is 1.07e5 and the 99% point 1.45e5 (2^17.1). Because all k = 4 ring elements must be recovered, I also checked the full secret: at N = 1.46e5 every one of the 20 trials worked, so full-secret recovery is reached by about 1.46e5 (but 20 trials can only show "at least about 86% success" with 95% confidence, so treat 99% as approximate). **Margin:** 2^17.1 is about 4 bits above the TALUS cap (2^13) and about 1.9 bits above the authors' wall (2^15.2). Still no break; the margin is about 0.4 bits thinner than the 5-trial estimate.
- **ML-DSA-87 at n = 256 (what):** 5 trials per point: 0% at 1.96e5, 100% at 3.49e5. So N* (99%) lies between 2^17.6 and 2^18.4: at least 3.6 bits above the cap (2^14) and at least 1.4 bits above the wall (2^16.2). Lower than the n = 64 value (5.2e5), so the earlier n = 64 shortcut overstated the margin; the full-size number is the one to quote.
- **A solver crash and fix:** one hard case made the linear-program solver (HiGHS) return "status unknown". `harness/estimators/edge.py` now has `solve_lp`, which retries with HiGHS's interior-point and then dual-simplex methods before giving up; both CPU and GPU estimators use it.
- **Mithril (Stage E, what):** read the full version of the paper (ePrint 2026/013; main text, parameter appendix, the Renyi part of the proof). Its Theorem 3.2 says how many signing queries Q_s the proof covers, as a formula in the published radii r, r', the repetitions K and a bound B on the size of c times the secret share. Wrote `harness/schemes/mithril_params.py` to evaluate that formula for all 45 published parameter sets, and to sample the real size of c times the secret share.
- **Mithril result (in simple words):** the paper says B is a very safe bound, 13 standard deviations above normal, and claims Q_s = 2^50. Our code reproduces their B (11 to 17 standard deviations). But plugging that B into their own theorem with their own published radii gives only Q_s = 2^26 to 2^37. Turned around, the radii only give 2^50 if B is barely above the typical size (0 to 2 standard deviations for ML-DSA-44; for some settings, like 5-of-6, even below it, so more than half of signing sessions fall outside the proof's assumption). So either the parameters were computed with a different B than the paper states, or the proof as written covers far fewer signatures than claimed. **This is a proof gap, not an attack**: going slightly over B makes each signature leak a little more than the proof budgets, not reveal the key.
- **Honest limits:** we did not run the authors' Go code or see their parameter script; they may compute B differently; the NIST preview writeup v1.0 parameters were not compared; the rest of the proof appendix was skimmed. Under our disclosure rule, the authors should be asked first before this goes anywhere public. Details: `notes/schemes/mithril.md`, raw output `experiments/results/mithril_params.txt`.
- **Tests:** 133 pass (49 old, 81 NIST vectors, 3 Mithril checks).
- **Next:** for Mithril, compute the actual leakage per signature when B is exceeded (honest Q_s under the real norm distribution); check the writeup v1.0 parameters; draft a note to the authors. For TALUS: more trials for ML-DSA-87; Stage F (Quorus, Trilithium; papers now in `papers/`).

### 2026-10-08 (later): Mithril, how many signatures are safe in the typical case
- **What:** extended `harness/schemes/mithril_params.py`. In each signing session the secret-dependent part (c times the secret share) has a slightly different size. The paper's lemma tells us how much each session can leak (a small number eps) for that size. I computed eps for the real spread of sizes and averaged it, giving the number of signatures that keep total leakage within budget. Two new tests (135 total, all pass).
- **Result in simple words:** with this "typical case" view, the published parameters give about 2^50 signatures or more for most settings, matching the paper's claim. Some settings fall short by up to about 3 bits: ML-DSA-44 with 4-of-6 and 5-of-6 (2^48.6, 2^47.0) and ML-DSA-65 with 4-of-5, 4-of-6, 5-of-6, 6-of-6 (2^47.6 to 2^49.4). So the big 13 to 24 bit gap from this morning comes from applying the theorem strictly with its worst-case bound; the parameters seem to have been chosen for the typical case.
- **What this means for us:** the finding is smaller than it first looked, but cleaner: "the formal theorem does not cover the published parameters; a typical-case estimate does, except for a few settings that are up to about 3 bits short". It is a statement about the proof, not an attack.
- **Why only a heuristic:** the typical-case view assumes each session's challenge is random. A proof must cover every session, and an attacker picks the messages. The attacker cannot see the secret, so it is hard to choose bad challenges, but that has not been proven.
- **Next:** write a short private note to the Mithril authors asking how B was computed; check the NIST writeup v1.0 parameters; then the stronger TALUS attacker or Stage F.

### 2026-10-08 (evening): why Mithril's numbers do not add up (root cause)
- **What:** the Mithril authors' code is public (GitHub `GuilhemN/threshold-ml-dsa`). I downloaded it to a temporary folder and read their parameter script `params/hyperball.sage` (did not run it). It uses exactly the paper's bound B, so B was not the problem. It fixes a tuning number phi = 7 (for ML-DSA-44), 8 and 9, and estimates security with the formula of the paper's Lemma 2.5. That formula gives 2^-50 for ML-DSA-44, which is where "2^50 signatures" comes from.
- **The problem:** Lemma 2.5 is supposed to be an *upper bound* on a quantity (an incomplete beta function, a standard function that here measures the leftover leakage). I computed the exact quantity with two independent libraries (scipy, and mpmath at 60 digits): it is 2^-33.5, about 17 bits *larger* than the "upper bound". An upper bound that is smaller than the real value is wrong. With the exponent halved, (dim-1)/2 instead of dim-1, the bound becomes correct, so it looks like a copying mistake from the source paper (Devevey et al., CRYPTO 2023), which I could not download yet.
- **What it means:** with the correct value, the published Mithril parameters are covered by the paper's theorem only for about 2^26 to 2^37 signatures, not 2^50. It is still **not an attack**: the typical-case estimate from this afternoon (about 2^50 for most settings) still stands, and the scheme is likely fine in practice. But the formal guarantee is weaker than stated, and fixing it needs slightly different parameters (more communication).
- **Why this matters for our paper:** it is now a concrete, checkable, reproducible finding: a misstated lemma, used in the public parameter script, makes the claimed proof bound 13 to 24 bits too optimistic. A test (`test_lemma25_bound_is_not_an_upper_bound_at_mithril_dims`) shows it. 136 tests pass.
- **New idea in simple words:** an *upper bound* is a number proven to be at least as big as the true value, so it can safely be used in its place. If an "upper bound" is below the true value, every conclusion drawn from it is too optimistic.
- **Next:** check the original lemma in Devevey et al.; compute what corrected parameters would cost.

### 2026-10-08 (afternoon): Stage F started: Quorus checked, Trilithium read
- **What (reading):** read the core of Quorus (its modified signing, Algorithm 1; its security theorems; how the parties decide "reject" without revealing which number failed) and the zero-knowledge section of Trilithium. Notes in `notes/schemes/quorus.md` and `notes/schemes/trilithium.md`. Checked online that the attack paper Quorus cites (Zhou, Wang, Sun, Yu, ePrint 2025/214: a side-channel key recovery that uses rejected signatures' challenges) exists.
- **What (code):** `harness/schemes/quorus.py` signs exactly as Quorus' Algorithm 1: one attempt, a small extra noise e_w added to the commitment, and a shortcut where e_w is left out of the hint. Every signature it outputs is checked with our standard ML-DSA verifier. 7 new tests.
- **Result:** 1.2 million attempts in total (with and without e_w). The rejection rates match the paper's Table 2 (4.30 vs 4.25, 5.12 vs 5.09, 3.85 vs 3.85). The hint failure rate is 0.4 to 1.3% (paper: "around 2%"). **Not one of 272,664 signatures failed verification.** That fits a short argument: the extra noise is at most eta, the safety margin in the check is beta = tau times eta, which is much bigger, so the shortcut can never change the result. The paper only says this holds "empirically"; we can give the reason.
- **What we did not find:** any leak. A simple statistical test on rejected transcripts cannot see anything, because the commitment is uniformly spread modulo q; finding a leak would need a lattice attack, which is what Quorus' theorem rules out. We say "no leak detectable by statistics", not "no leak".
- **Trilithium (reading only):** in its unmodified version it reveals the high bits of A y even for rejected attempts, and relies on an assumption (MLWR) the authors themselves call non-standard for ML-DSA's parameters. Testing that needs a lattice experiment at small sizes; not started.
- **New idea in simple words:** a *batched OR* is a trick to learn only "did anything fail?" from many secret yes/no checks, without learning which one failed.

### 2026-10-10: Mithril, what fixing the proof would cost
- **What:** added `corrected_params` to `harness/schemes/mithril_params.py` (run with `--corrected`; output `experiments/results/mithril_corrected.txt`). For each of the 45 published settings it keeps the paper's r and B, picks the tuning number phi from the *exact* formula so that the theorem really covers 2^50 signatures, works out the new outer radius r', and then increases K (the number of parallel attempts per session) until a signing session succeeds at least as often as with the published numbers. 1 new test, 144 pass.
- **Result in simple words:** phi has to drop (7 to about 5.5 for ML-DSA-44, 8 to about 6.3 for -65, 9 to about 7.4 for -87). The radius r' only grows by a tiny amount (12 to 89 out of about 250,000 to 660,000), but each party's chance of accepting falls, and with T parties that adds up. To keep sessions succeeding as often as before, K must grow 1.3 to 2 times for small groups and up to 8.5 times for the largest (ML-DSA-65 5-of-6: 1200 to 10,234). Communication grows roughly in step with K.
- **Why:** this turns "the proof has a mistake" into "here is the price of the fix", which is what scheme authors and NIST need in order to judge it.
- **Honest limits:** uses the paper's own approximation that each party accepts with probability 1/M; we did not rerun the authors' script; a different fix (e.g. changing r) could be cheaper.
- **Also started:** ML-DSA-87 TALUS run at full size with 20 trials per point (before: 5).
- **New idea in simple words:** *parallel repetitions (K)*: instead of retrying a failed signing session, the parties run K attempts at once and keep one that works. More K means fewer retries but more data sent.

### 2026-10-10 (later): Firmer TALUS numbers for ML-DSA-65 and -87
- **What:** reran the edge estimator at full size n = 256 with 20 trials per point (before: 5) at 7 values of N around the transition, for ML-DSA-87 and ML-DSA-65. Raw data: `experiments/results/talus_edge_ML-DSA-{87,65}_bcc_s2_n256_dense.json`, logs `dense_256_{87,65}.log`. Command: `python -m experiments.talus_edge_scaling --params ML-DSA-87 --n 256 --trials 20 --steps 7 --lo 0.25 --hi 0.55 --device gpu` (-65: `--lo 0.22 --hi 0.67`), seed 2026.
- **Interruption:** the NVIDIA driver crashed at 15:20 while both runs used the GPU at once, and Windows later restarted. The script saves after every point, so both resumed from point 4; afterwards they ran one at a time.
- **Result (per ring element):**

| Parameter set | 50% at | 99% at | log2 N*99 | cap | bits above cap | wall | bits above wall |
|---|---|---|---|---|---|---|---|
| ML-DSA-44 (8 Oct) | 1.07e5 | 1.45e5 | 17.1 | 2^13 | 4.1 | 2^15.2 | 1.9 |
| ML-DSA-65 | 2.61e5 | 3.58e5 | 18.4 | 2^14 | 4.4 | 2^16.4 | 2.0 |
| ML-DSA-87 | 2.32e5 | 3.69e5 | 18.5 | 2^14 | 4.5 | 2^16.2 | 2.3 |

- **In simple words:** for all three security levels, our attacker needs about 16 to 22 times more signatures than TALUS allows. The cap holds in our model.
- **Honest limits:** 20 trials per point give coarse percentages (-87 shows 90% then 80%, which is noise); 99% is interpolated; recovering all k = 6 or 8 ring elements needs slightly more than these per-element values (not separately checked for -65/-87); same model assumptions as before (our reading of TALUS, no stronger lattice attacker).

### 2026-10-10 (evening): Trilithium, do thrown-away attempts give clues? (tiny exact test)
- **What:** Trilithium shows w_H = HighBits(A y) for every signing attempt, also the ones it throws away. The authors argue a thrown-away w_H looks like the output of a simple simulator, using an assumption they call non-standard. I built a tiny version (`harness/schemes/trilithium_toy.py`): polynomials with 4 coefficients instead of 256, one polynomial instead of 4 to 7, q = 257. Because it is tiny, the program lists every possible y and computes the exact probability of every w_H, so there is no sampling noise. Command: `python -m experiments.trilithium_toy --gamma1 4 8 12 16 24 32 48`, 5 random keys per size, seed 2026. Results: `experiments/results/trilithium_toy.txt`, notes: `notes/schemes/trilithium.md`.
- **Bug caught on the way:** the first run showed 100% rejection at two sizes, which is impossible. c times s1 was computed after reducing c mod q, so -1 became 256. Fixed; a test now checks c s1 is small.
- **Result in simple words:** at this tiny size the thrown-away w_H does differ from the simulator's output and does depend on the secret key. But the difference shrinks quickly as the random range gamma1 grows: an attacker would need about 200 thrown-away attempts at gamma1 = 4 and about 100,000 at gamma1 = 48, for the "y left the box" case. For the other rejection case (the r0 check), the difference shrinks fast at first, then stops shrinking between gamma1 = 32 and 48; I could not yet explain why.
- **What it means:** the weak spot we suspected is real in principle, but it gets weaker as the scheme grows, which supports the authors. It says nothing direct about the real sizes (256 coefficients, gamma1 = 131072 or 524288). Not an attack.
- **New ideas in simple words:** *exact enumeration* = trying every possible input instead of a random sample. *Hellinger distance* = a number saying how different two probability lists are; roughly 1 divided by its square is how many samples you need to tell them apart.

### 2026-10-10 (night): Controls for the TALUS attack tool, from real ML-DSA signing
- **Why:** a leak detector is only trustworthy if it finds a leak where one exists (positive control) and stays quiet where none exists (negative control). Until now our TALUS numbers had neither.
- **Idea in simple words:** from any normal ML-DSA signature and the public key, anyone can compute a value b = w' - 2 gamma2 w1. Because ML-DSA throws away attempts that fail the "r0 check", b only contains t0 (a value ML-DSA's security analysis already treats as public) plus noise; s2 cancels out. If a scheme skipped the r0 check, the same b would contain s2 - t0, and from that A s1, i.e. the whole key. So one pipeline gives both controls: skip the check (positive), keep it (negative).
- **What:** `harness/schemes/mldsa_controls.py` signs in batches with a genuine ML-DSA-44 key (FIPS 204 steps; y and c from numpy's random generator instead of SHAKE, which is the same distribution in the usual model). Two tests check the algebra exactly: in genuine ML-DSA the leftover noise equals r0 and stays below gamma2 - beta. `experiments/mldsa_controls.py` runs the edge estimator, with the same settings for both cases, on ring element 0. 3 keys (seed 2026), N = 200k, 400k, 800k accepted signatures. Raw: `experiments/results/mldsa_controls_ML-DSA-44.json`, log `mldsa_controls.log`.
- **Result:** positive control: the key part s2 - t0 recovered in **9 of 9** runs (already at 200k). Negative control: key recovered in **0 of 9** runs; in all 9 the estimator returns -t0 instead, which is harmless. So the tool finds the key when it is there and does not "find" it when it is not.
- **Limits:** 3 keys only (so the false-positive rate is "0 of 9", not a precise number); one ring element; the positive control is a broken ML-DSA variant, not the historical TALUS v0.1.
- **New idea in simple words:** *positive / negative control* = a test where you already know the right answer (leak / no leak), used to check the measuring tool itself.

## 2026-10-11: Sanity check of Niot's attack 2 on real signatures

- **Idea in simple words:** Niot's attack uses plain least squares (fitting the hidden key to noisy equations). His note says the error shrinks like gamma2 / sqrt(3 tau N). We checked that this formula holds on signatures from real ML-DSA-44 signing (the no-r0-check variant from the controls), not only on our idealised random data.
- **What / how:** `experiments/niot_sanity.py`, 3 keys (seed 1386), N = 5k, 20k, 80k, 200k accepted signatures, ring element 0, least squares via `edge.least_squares_fft`. Log: `experiments/results/niot_sanity.log`, raw: `niot_sanity_ML-DSA-44.json`.
- **Result:** measured error / formula = **0.97 on average (sd 0.04, 12 runs)**, so the formula is right on real transcripts. At 200k signatures the least-squares error is about 19, far from the 0.5 needed to round correctly (only 0-3% of coefficients right). Same signatures, our edge (bounded-noise) estimator already recovers the key (controls entry above). So the smarter estimator needs about **1,500 times fewer** signatures than Niot's own formula (3.1e8) and roughly 10,000 times fewer than full least-squares recovery (about 3.6e9, from our earlier extrapolation), which is the improvement Niot predicted ("bounded noise could cut it substantially").
- **Why it matters:** confirms both pieces of our pipeline (data and least-squares baseline) against a published number, so our TALUS margin numbers rest on a checked tool.
- **Limits:** ML-DSA-44 only; one ring element; least squares was not run to full recovery (too many signatures), only checked against the error law.

## 2026-10-11: Trilithium toy test, why the branch-2 gap stops shrinking

- **Idea in simple words:** Trilithium reveals a rounded commitment even for failed signing attempts, and argues these look like random data. On a tiny 4-coefficient version we compute the exact distributions. One kind of failure (branch 2, the "r0 check" fails) stopped getting closer to random as we grew gamma1. We asked: is that because of the small modulus q, or because of the ratio gamma1/gamma2?
- **What / how:** reran the exact enumeration at q = 513 and q = 1025 so each ratio appears at two or three sizes of q. Results in `notes/schemes/trilithium.md` and `experiments/results/trilithium_toy_q1025.*`, `trilithium_toy_q513_g64.*`.
- **Result:** neither explanation fits cleanly. Once gamma1 >= gamma2 the gap stays at about 1e-4 for every q we tried. So it is a real, stable feature of that failure type at this toy size, not a small-q accident. The other failure type (branch 3) keeps shrinking as expected. Why the floor exists is still an open guess.
- **Limits:** n = 4 only; nothing here says anything about real ML-DSA size (n = 256). No attack.

## 2026-10-11: Mithril, how much leaks per accepted signature, and what 2^64 signatures would need

- **Idea in simple words:** in Mithril each party's answer z is a random point in a ball, nudged by a secret-dependent shift v, and kept only if it lands inside a fixed smaller ball. Ideally the kept points are spread perfectly evenly in the small ball whatever v is. Because the big ball is only slightly bigger, a thin sliver of the small ball (on the side away from v) can never be reached. That sliver is the leak: tiny per signature, but it adds up over many signatures.
- **What / how:** wrote down the exact formula (the leak per signature is the sliver's share of the ball, so the "Rényi divergence", a measure of how different two distributions are, is 1/(1 - sliver)). Then reused our earlier numbers to see whether the published parameters would hold for 2^64 signatures (the figure used by other schemes), and added a `--target` option to `harness/schemes/mithril_params.py` to compute the parameters that would.
- **Result:** Mithril claims 2^50 signatures, and at 2^64 every published set falls short (by 3 to 17 bits even in the optimistic typical case). Fixing it for 2^64 means running 1.7 to 23 times more parallel attempts K (worst ML-DSA-65 (5,6): 1200 to 27,806), so much more communication.
- **Limits:** formula and parameter arithmetic only; no simulation (the sizes are far too big to compute exactly). The leak would be expensive to exploit, roughly as expensive as the proof says; no attack found.
- **New word:** *Rényi divergence* = a number saying how distinguishable two distributions are; security proofs multiply it once per signature.

## 2026-10-11: Trilithium toy, the branch-2 floor comes from the "wrap-around" cell

- **Idea in simple words:** ML-DSA's rounding (Decompose) puts the numbers just below q into the same bucket as the numbers around 0, so bucket 0 is a bit wider than the others. We guessed that this uneven bucket causes the gap that would not shrink.
- **What / how:** recomputed the gap after throwing away every result that touches bucket 0 (`experiments/trilithium_edge_cell.py`, 5 cases).
- **Result:** with gamma1 at least twice gamma2, the gap drops 30 to 65 times (to about 1e-6) and keeps shrinking. So the floor lives in bucket 0. When gamma1 = gamma2 a smaller gap remains.
- **Limits:** we removed the whole bucket 0, not just the wrapped numbers, so this shows *where* the effect is rather than proving exactly *why*. Toy size (n = 4) only, no attack.

## 2026-10-11: Mithril, how much the corrupted parties learn when an existing key is split

- **Idea in simple words:** Mithril lets you take an ML-DSA key you already have and split it into many small random pieces (shares) that add up to the key. If T-1 parties are dishonest, together they hold every piece except one. Because the pieces are small, the sum of what they hold is already "close" to the secret: this is a *hint*. A hint makes the lattice problem behind the key easier, so the key has fewer bits of security.
- **What / how:** `harness/schemes/mithril_hint.py` computes, for one coefficient, exactly what the dishonest parties know (the probability of each secret value given their pieces), turns it into an "effective size" of the remaining secret, and feeds that into a standard estimate of the cost of the best lattice attack (primal uSVP, core-SVP). Our cost for the normal key matches the official Dilithium numbers, so the calculator is checked.
- **Result:** the paper says the loss is 7 to 12 bits. For ML-DSA-44 we get 4 to 7 bits (the paper's 12 reproduces if we use its own, more cautious 0.74 number). For ML-DSA-65 the loss is 15 to 21 bits, more than claimed: its secret coefficients range up to 4 instead of 2, and shares of size about 1.4 hide a wide secret poorly. ML-DSA-87: 8 to 13 bits.
- **Limits:** a simple Python estimate, not the official lattice estimator (needs Sage); only one attack type; the paper itself calls its number a heuristic sanity check. No attack on normal Mithril key generation.
- **New words:** *hint* = extra noisy information about the secret; *core-SVP* = a standard way to price a lattice attack, 0.292 x (BKZ block size) bits; *posterior* = what you believe about the secret after seeing the hint.

## 2026-10-11: Wrong paper downloaded (our mistake), corrected

- **What:** we asked for ePrint 2023/245 to check Mithril's Lemma 2.5. Reading Mithril's bibliography showed its reference [27] is a different paper by partly the same authors: ePrint 2022/1249 (ASIACRYPT 2022). The 2023/245 PDF is kept in `papers/` but does not contain the lemma.
- **Why it matters:** a reminder to check a citation against the citing paper's own reference list, not from memory.

## 2026-10-11: The wrong bound comes from the original paper, not from Mithril

- **Idea in simple words:** Mithril uses a formula (a ceiling on the size of a "cap" cut off a ball) to prove its security. We had found that the ceiling is lower than the true value, so it cannot be a ceiling. Now we read the paper it was copied from (Devevey, Fawzi, Passelegue, Stehle 2022, Appendix A.6): the same wrong formula is there. Mithril copied it faithfully.
- **How:** the original says "put the cap inside a cylinder". We did that calculation ourselves: the cylinder's base is a smaller ball of radius sqrt(1 - 1/eta^2) in one dimension less, and its volume shrinks with exponent (n-1)/2. The paper wrote n-1, double the right exponent, which makes the ceiling far too small in high dimension. Our corrected ceiling is always above the true value (new test).
- **Why it matters:** the mistake is upstream, so other schemes that used this bound might also be affected (not checked). For Mithril our earlier numbers stand.
- **Limits:** we read the ePrint version only, not the published conference version.

## 2026-10-11: Trilithium, does a bigger dimension help, and what the one public bit reveals

- **Idea in simple words:** Trilithium publishes the rounded commitment w_H even for failed signing attempts. On tiny toys these failed w_H were slightly different from random and slightly dependent on the key. The open question: does this get better or worse as the dimension n grows (real ML-DSA has n = 256)?
- **How:** the old program tried every y, which explodes with n. New trick (`harness/schemes/trilithium_conv.py`): w = A y is a sum of independent pieces, one per coordinate of y, so its exact distribution can be built step by step by adding shifted copies (a "convolution"). Its cost depends on q^n instead, so with a small q (17) we reached n = 6. It gives exactly the same numbers as the old program where both run (new test).
- **Result:** from n = 4 to n = 6 the gap falls about 100 to 1000 times for one failure type and 15 to 70 times for the other; the dependence on the key also falls. So bigger dimension helps, as the authors argue. n = 8 is still too big to compute exactly.
- **Reading the protocol:** each attempt also opens one bit, "passed or failed" (not which check failed). That check is only protected against a cheating server in a weak way. Our reading: a cheating server can learn about one bit and is then caught by the phone; the paper's informal argument seems right, with this small caveat. The helper that hands out correlated randomness (CRP) must be honest; if it teams up with the server, privacy is gone, as the paper says.
- **New word:** *convolution* = the distribution of a sum of independent random values, computed by adding up shifted copies.
- **Limits:** toy sizes only (q = 17, n <= 6); protocol caveat is a paper-level reading, not run.

## 2026-10-11: Trilithium, what happens when the server cheats on the pass/fail bit

- **Idea in simple words:** the server can tamper with the pass/fail check. If its tampering makes a bad attempt look "passed", the phone checks the signature, sees it is invalid, and both stop forever. So the server can cheat only once and is caught.
- **What we found by reading Sec. 5, 7 and App. F:** the paper says exactly this and concludes the cheater learns at most one bit. A small subtlety: the moment of getting caught can depend on the secret (the server can choose a check that trips only on certain rejected values), so the time of the stop leaks a little, at most about log2(number of attempts) bits, once. The security proof's simulator does not seem to account for this. Tiny and not an attack, but a precise point to raise with the authors.
- **New word:** *selective failure* = making a protocol fail only for certain secret values, so the failure itself leaks information.

## 2026-10-11: Kao's fully distributed mode (P2) leaks the whole key, confirmed from the paper's own text

- **Idea in simple words:** in ML-DSA the commitment w = A y must stay hidden; only its rounded "high bits" are public. If someone learns the full w, then together with the public signature z = y + c s1 they can compute A s1 and then s1, the secret key. Kao's P2 mode hides each party's piece W_i with random masks that cancel when all pieces are added. The paper proves each single piece looks random. But P2 sends every piece to every party, so anyone can add them all up: the masks cancel and the full w appears.
- **What we did:** we had built this attack on a toy on 6 Oct, but did not know if P2 really broadcasts every piece. Today we downloaded the paper (arXiv allows it) and found three places that say so (Fig. 1b, Remark 11, Appendix M.1). The toy test still recovers the key.
- **Why it matters:** this would let any single participant, or anyone watching the broadcast, recover the whole key after one signature. It only affects P2, not the other two modes.
- **Limits:** toy only; the author's code is not public, and an implementation could compute w inside the secure computation instead. We must tell the author privately before saying anything publicly.
- **Side note:** the paper's own security bound only covers about 16,000 signatures (it loses 0.0066 bits per signature), which is much less than other schemes target.

## 2026-10-11: Mithril hint loss, checked with the official lattice estimator

- **What / how:** earlier today we priced the attack with our own small Python formula. Now we ran the community-standard tool (the "lattice estimator" by Albrecht et al., which needs the Sage maths system; we ran Sage inside Docker so nothing had to be installed). It tries two attack families and reports the cheaper one.
- **Result:** the same picture, slightly worse for the defender (1-3 bits more loss): ML-DSA-44 loses 5-8 bits, ML-DSA-65 18-24 bits (paper says 7-12), ML-DSA-87 9-14 bits. Using the paper's own 0.74 number, even ML-DSA-44 loses 14 bits, a bit above the paper's "at most 12".
- **New word:** *Docker* = a way to run a complete prepared software environment (here: Sage) in a box on your computer.

## 2026-10-11: Ran the Mithril authors' own script, and drafted (not sent) emails to authors

- **What:** with Sage now working in Docker, we ran the parameter script published by the Mithril authors. It produces exactly the numbers in their paper, and its security figure uses the wrong bound (2^-50 where the true value is 2^-33.5). So our finding no longer rests only on reading their code; we ran it.
- **Emails:** `docs/disclosure_drafts.md` holds polite private drafts to Kao (P2 key recovery), the Mithril authors (bound and hint loss) and optionally the authors of the original lemma. Nothing has been sent. Responsible practice is to tell authors privately first and give them time to answer; ask the instructor before sending.

## 2026-10-12: Trilithium at dimension n = 8, by random sampling

- **What:** the exact method (count every possible case) stops at n = 6 because the number of cases explodes. For n = 8 we instead drew 200 million random samples per setting (3 keys each) and measured the distance (squared Hellinger) between the real rejected values and what the paper's simulator would produce. Code: `harness/schemes/trilithium_mc.py`, `experiments/trilithium_mc.py`; results in `experiments/results/trilithium_mc.txt`.
- **How we trust it:** at n = 6 the sampled numbers match the exact ones. Random sampling always shows a small fake distance even when two distributions are identical (the "bias" column); a "null" run that compares the simulator with itself confirms that this floor is about 3e-7 at n = 8.
- **Result:** branch 3 (the main rejected value): the measured distance equals the noise floor, so any real gap is smaller than about 1e-7; we cannot see it. Branch 2 still shows a real gap: about 3e-5 at gamma1 = 4, about 7e-7 at gamma1 = 8 and 16. So both gaps keep falling as n grows, matching the n = 2..6 trend. At real sizes (n = 256) this trend suggests the gap is negligible, but that is an extrapolation, not a measurement.
- **Also:** `experiments/mldsa_controls.py` got a `--controls` option to run only the positive or negative control.

## 2026-10-12: Does the TALUS estimator ever "find" a key that is not there? (false-positive test)

- **What:** a good attack test must not cry wolf. We signed 200,000 messages with genuine ML-DSA-44 (which is safe against this estimator) for 15 fresh keys (seed 2027) and ran the same estimator each time. Log: `experiments/results/mldsa_controls_fp.log`, data: `mldsa_controls_fp_ML-DSA-44.json`.
- **Result:** the secret key came out 0 times out of 15; every time the estimator returned -t0 instead, a value an attacker can already get from the public key, so it is harmless. Adding the 3 earlier keys: 0 of 18 keys. With 0 hits in 18 independent tries, we can say with 95% confidence that the false-positive rate is below about 15% (1 - 0.05^(1/18)). This is a small sample: it shows the estimator is not obviously fooled, not that it can never be.
- **Why it matters:** together with the positive control (key found 9/9 when the protection is removed), this shows the estimator detects real leakage and does not invent it.

## 2026-10-13: TALUS, recovering the WHOLE secret (all ring elements) for ML-DSA-65 and -87

- **What:** earlier numbers were "per ring element". The secret has k pieces (k = 6 for -65, k = 8 for -87) and an attacker needs all of them. We took the first N where all 20 earlier trials worked and ran 300 fresh trials there (seed 2028). Results: `experiments/results/talus_full_ML-DSA-65.json`, `talus_full_ML-DSA-87.json`, log `talus_full.log`.
- **Result:** -65 at N = 362,887 (2^18.47): 299 of 300 elements recovered. -87 at N = 378,723 (2^18.53): 300 of 300.
- **From one piece to all pieces:** if one piece fails with probability p, all k pieces succeed with probability at least 1 - k*p (union bound; this does not even need the pieces to be independent). With 95% confidence p is at most 1.6% (-65, one failure in 300) and 1.0% (-87, none in 300), so full-secret success is at least about 91% (-65) and 92% (-87); the most likely values are about 98% and close to 100%.
- **Meaning:** the full-secret N sits at about 2^18.5 for both, still about 4.5 bits above the TALUS cap. Conclusion unchanged: no break in our model.
- **Speed-up:** `experiments/talus_edge_scaling.py` got `--workers`: transcripts are built in parallel processes while the GPU solves (results identical to the serial run; checked on a small case). 6 workers ran out of memory (15 GB machine), 3 work: about 20 s per trial at n = 256.

## 2026-10-13: Finished the open Phase 2 items

- **Scheme views (Stage B):** a "view" is the list of what an attacker actually sees from one signing attempt. We wrote views for TALUS and Mithril (`harness/schemes/views.py`) and a small translator that turns them into the input our estimators already use. Test of the whole chain: real ML-DSA-44 signing -> TALUS view -> unchanged estimator recovered the key piece for 2 of 2 keys with 200,000 and 400,000 accepted signatures, and for 0 of 2 with 100,000 (`experiments/gate_b_views.py`, seed 2029). This matches the earlier N*99 of about 145,000.
- **Estimators:** `fisher.py` gives the theory curves (see the two new basics in Part 1). For one coefficient alone the theory is exact and matches simulation; when all 256 are solved together, a fitted constant that grows with the challenge weight tau explains why real N* is 1.5-2 bits above the simple formula. `ilp.py` adds the integer finishing step; at n = 64 it cuts the needed signatures by about 1.4x, at n = 8 not at all (there, several wrong secrets fit the data equally well).
- **TALUS v0.1:** we built the early TALUS version (arXiv 2603.22109v2; calling it "v0.1" is our label) on top of real ML-DSA. Niot's first attack recovers the whole secret s1 exactly, from the key-setup messages (3/3 keys) and from a single signature (60/60), because that version broadcasts A*s1_i and A*y_h. His second attack (least squares) behaves exactly as theory says and would need about a billion signatures. This shows why TALUS changed design.
- **Mithril bound:** the published ASIACRYPT paper of Devevey et al. does not contain the faulty bound; only their ePrint full version does. Of 13 papers citing them, only Mithril uses it. HAETAE computes the exact value, so it is safe.
- **Kao appendices:** reading the rest did not rescue Kao's fully distributed mode P2; his own proof of Corollary 5 calls the full w "the public broadcast", which is exactly what our attack uses. Two sentences added to the (unsent) email draft.
- **Quorus and Trilithium full read:** our hypotheses hold. One correction to our own wording: "A*y + e is uniform" is true for each single number but not for the whole vector, so we can only say no simple statistical test sees a leak. We also found small errors in the papers (a bound written as gamma2-beta-eta in one Quorus functionality vs gamma2-beta everywhere else, checked on PDF p. 32; a wrong constant in Quorus Lemma 8; Trilithium's simulation-gap text on p. 24). None is an attack.
- **Why:** these were the remaining Phase 2 roadmap items. Not done: running the scheme authors' Go/other reference code (packages phase, March 2027; most code not public).

## 2026-10-13: The integer finishing step at full size lowers the TALUS margin by about 1 bit

- **What:** we ran the new ILP step (Part 1, "Integer programming") on the full-size ML-DSA-44 channel (n = 256), 8 trials per point, seed 2032. Script `experiments/ilp_n256.py`; results `experiments/results/ilp_n256*.json`. To save time the slow points ran as parallel processes with the same seeds, so results equal a serial run.
- **Result:** with the ILP step the key piece came out in 1/8 trials at 50,000 signatures, 5/8 at 60,000, 8/8 at 70,000 and 32/32 from 80,000 up. Plain rounding needed about 145,000 for 99%.
- **Meaning:** about 70,000 signatures (2^16.1) now suffice: about 3.1 bits above the TALUS cap (was 4.1) and only about 0.9 bits above the authors' uniqueness wall (was 1.9). Still not a break, but the safety margin is thinner than we first reported. Caveats: one ring element, 8 trials per point. **Update (same day):** ML-DSA-65 and -87 re-run with ILP (4 trials per point, run one at a time to spare the laptop): -65 needs about 2^17.45, -87 at most 2^17.18; both about 3.2-3.5 bits above the cap and about 1 bit above the wall. Same picture for all three: thinner margin, no break.

## 2026-10-13: Report revised with the instructor's feedback and the Phase 2 results

- **What:** `report/build_report.py` (Word) and `report/latex/phase1_report.tex` were rewritten together. The TALUS signing cap (P1) is now the main problem; Mithril, Quorus/Trilithium and Kao are stretch goals. New: Phase 2 results section with the margin table (including the ILP result), controls, TALUS v0.1, Mithril bound gap, Kao P2, Quorus/Trilithium errata; Fig. 1 harness architecture (`experiments/arch_diagram.py`); Fig. 2 least-squares error vs N with theory (`experiments/ls_error_plot.py`, 10 trials per N, seed 2033: measured within 2% of theory at every N); symbols defined at first use; a Phase 3 prototype section. Shamir and Feldman checked on Crossref; the two withdrawn ePrints are listed for history only.
- **How we kept 10 pages:** cut old plans (milestones, expected outcomes) that the results replace. The Word PDF is exactly 10 pages. The LaTeX was checked by script but not compiled (no LaTeX installed).
- **Why:** the instructor asked for these changes once Phase 2 was done. The Kao and Mithril findings are written neutrally because the authors have not been told yet.

## 2026-10-13: Plan for turning the project into a conference paper

- **What:** `docs/PAPER_PLAN.md`. Honest status: one real break (Kao P2, not an official submission), two proof gaps in Mithril (not key theft), a thinner but intact TALUS margin. Good enough for PQCrypto 2027 (due 24 Nov 2026); USENIX needs a break of an official scheme.
- **Most promising idea:** TALUS's defence is "change the key often". If its key change only reshuffles the managers' pieces of the same secret (a "refresh"), the crumbs from every round add up and the cap stops protecting anything. Checking this is just reading the spec, so it comes first next session.
- **Why:** cheap checks that could change the story go before long experiments.

## 2026-10-14: TALUS key rotation checked (paper plan item 1); GPU vs CPU timing

- **What:** re-downloaded the TALUS v0.22 preview writeup from NIST (`papers/talus_pw02/`) and read Sec. 2.2-2.3. Also timed one TALUS point on the GPU and on the CPU.
- **Result (item 1):** the writeup says it directly: share refresh "does not reset the accumulated signature leakage, so the per-key signing cap is discharged by key rotation (fresh key generation)". So rotation makes a brand-new key, and the crumbs from the old key are useless for the new one. Our hoped-for hole is not there. The cap still holds, and our attack stays about 3 bits above it.
- **Item 2, partly:** nonces that fail the BCC filter are thrown away offline, with w1 still hidden under a commitment, so they leak nothing (by the writeup). New open point: rare leftover rejections (z too big, too many hints) are only caught by the final Verify check, after each signer has already broadcast z_i. Whether those failed sessions count toward the cap, and how rare they are, needs the full Package spec.
- **GPU test:** ML-DSA-44, n = 256, N = 70,000, 1 trial: the GPU did the edge step in 4 s vs 12 s on the CPU, but used ~1.0 GB of normal RAM (the CUDA libraries) vs 0.23 GB. New rule: at most 1 GPU run + 2 CPU runs at once.
- **Why:** a quick reading check that could have meant a break went first; it came back negative, and saying so plainly matters.
- **Update, item 2 closed:** the full TALUS paper (arXiv v5, Sec. 6) measures how often an online signing attempt fails: about 2% at ML-DSA-44, 0.4% at -65, 0.8% at -87, and never because z was too big (the summed nonce stays well inside the limit). Even if those failed sessions were not counted toward the cap, they would give the attacker only ~2% more data, about 0.03 bits, against our ~3-bit gap. So rejected attempts do not rescue the attack either.
- **Item 6 done (Mithril ML-DSA-65, full lattice estimator):** last time we used the estimator's quick "rough" mode; now the full one (all attacks except the very slow Arora-GB; script `experiments/mithril_hint_estimator_full65.sage`, run in Docker). Plain ML-DSA-65 costs about 2^203.8 operations to break this way. With Mithril's sharing hint it drops to 2^189.0 / 2^184.3 / 2^182.5 (S = 2 / 6 / 20 signers): a loss of 15-21 bits, where the Mithril paper says 7-12. The full mode gives bigger absolute numbers than rough mode (it counts costs more completely), but the loss is about the same, so the earlier finding stands. Plain answer: measured against ML-DSA-65's own Category 3 baseline, the hint pushes it well below; it is still far above Category 1 (~2^143), so it is a gap in the paper's security claim, not a practical attack.

## 2026-10-14: TALUS statistics with 20 trials per point (paper plan item 8)

- **What:** re-ran the ILP attack on the TALUS s2 channel model at full size (n = 256, one ring element), 20 trials per signature count N, fresh seed 2041, for all three ML-DSA levels. Script `experiments/run_item8.sh`, analysis `experiments/item8_analysis.py`, results `experiments/results/item8/`. One GPU job at a time; the ILP solver was stopped after 120 s per trial (a stopped trial counts as a failure, so this can only make the attack look weaker).
- **How we read it:** for each N, a 95% confidence interval (Clopper-Pearson: the range the true success rate very likely lies in, given 20 tries). Then a logistic curve (an S-shaped "success vs log2 N" curve) fitted to all trials, which gives the N where success reaches 50% and 95%.
- **Result:** 95% success at about 2^16.0 (-44), 2^17.4 (-65), 2^17.3 (-87) signatures. That is about 3.0-3.4 bits above the TALUS cap and about 1 bit above the authors' uniqueness wall. Same picture as the earlier 4-8 trial runs, now with proper error bars. The jump from failure to success is sharp: about 0.2-0.4 bits in log2 N.
- **Why:** a paper needs statistics, not 4 trials per point. Caveat: still our channel model and one ring element, not the TALUS code or the whole key.

## 2026-10-14: corrected bound for the Devevey A.6 lemma (paper plan item 9)

- **What:** wrote a correct replacement for the faulty "cap ceiling" formula that Mithril copied from Devevey et al. (`docs/a6_corrected_bound.md`), with a short proof and a computer check (`experiments/a6_corrected_bound.py`).
- **Idea in simple words:** picture a ball and slice off a thin cap at the top. We need a guaranteed ceiling on how much of the ball's volume that cap holds. The old proof put the cap inside a short cylinder (a can) and used the can's volume. That idea is fine, but the formula squared one factor too many, so the "ceiling" came out lower than the real volume. Doing the can correctly gives a true ceiling (part a), but a loose one (about 8 bits too high). A sharper trick (part b) uses the fact that the cap's slices shrink quickly as you go up, almost like an exponential decay. That gives a ceiling within 0.04 bits of the true value at Mithril's sizes.
- **Check:** 320 combinations of dimension and parameter: the new bounds are never below the true value; the old formula was below it at 149.
- **Why it matters:** with the correct ceiling, Mithril's proof gives about 2^26-2^37 signing sessions rather than 2^50, as already found. Now the paper can offer the fix as well as the problem.
- **New basic (Part 1 material):** the *regularised incomplete Beta function* I_x(a, b) is the standard way to write "what fraction of a ball lies in a cap". Gautschi's inequality is a simple bound on a ratio of Gamma functions, used here to turn ball volumes into a plain square-root formula.

## 2026-10-15: Mithril on real transcripts (paper plan item 5)

- **What:** the Mithril authors' public repository (GuilhemN/threshold-ml-dsa) contains their Go signing code. We installed Go, added a small dumper that records real signing sessions (with the secret kept as the answer key), and ran our Mithril view on 110000 of them. Files: `harness/mithril_go/dump_test.go`, `harness/schemes/mithril_go.py`, `experiments/mithril_real_transcripts.py`, result `experiments/results/mithril_real_transcripts.txt`.
- **Question:** our model assumed the published data gives a noisy copy of c times the secret part s2. Is that true in the real code?
- **Idea in simple words:** Mithril throws away a signing try if the combined answer lands too far out (rejection sampling). The check covers both the public part z and a hidden part z2 = c s2 + noise. Rejection sampling is designed so that kept answers look the same whatever the secret is. If it works, the hidden part z2 carries no trace of s2, and the only secret-looking thing left is c t0 (t0 = low bits of the public key, which ML-DSA already assumes may leak).
- **How we tested:** a regression (fit a straight line through a cloud of points) of the leftover u on -c s2. Slope 1 would mean s2 leaks as modelled; slope 0 means it does not.
- **Result:** slope 0.004 +/- 0.10 from 39461 kept sessions. So 1 is ruled out (about 10 standard errors away). Our earlier model was too pessimistic; we corrected it. No attack on Mithril from this channel. Also confirmed: our ML-DSA code rebuilds Mithril's public key exactly.
- **Why it matters:** the paper can say the Mithril channel was tested on the authors' own code, not only on our model.
- **New basic:** *standard error* = how much an estimate would wobble if you repeated the experiment; "10 standard errors away" means essentially impossible by chance.

## 2026-10-15: TALUS with a corrupt insider (paper plan item 3, first pass)

- **What:** read the insider part of the latest TALUS paper (arXiv v5, App. D) and estimated how many signatures a corrupt party would need (`experiments/talus_insider_wall.py`).
- **Idea in simple words:** in TALUS the secret random number y used in each signature is the sum of several parties' random pieces. An outsider sees z = y + c s1 with y a sum of many pieces, which looks "smooth". A corrupt party knows its own pieces and subtracts them, so for it the leftover noise is a sum of fewer pieces: narrower and with sharper edges. Sharp edges leak the secret faster (the same reason the s2 channel leaks).
- **Result:** in the proposed version (MPC), at least T honest pieces always remain, because the committee has an honest majority. Our estimate says the insider still needs about 2^25-2^30 signatures, which is 12-16 bits more than the key-rotation cap allows. No hole found. In the TEE version (not proposed), a group of T-1 corrupt signers leaves only one honest piece: a flat noise with a sharp edge. There the attack fits under the cap from about T = 7, as the authors themselves admit.
- **Caveat:** rough formulas, no simulation yet; the corrupt-coordinator view is not checked.
- **New basic:** *Irwin-Hall distribution IH(m)* = the sum of m independent uniform random numbers. m = 1: flat box; m = 2: triangle; large m: close to a bell curve. Fewer summands = sharper edges = more leakage.

## 2026-10-16: check of the m = 2 insider number (paper plan item 3, follow-up)

- **What:** the earlier insider estimate for two honest pieces (a triangle-shaped noise) used a hand-cut formula. We replaced it with an exact count (`experiments/talus_m2_fisher.py`, result `experiments/results/talus_m2_fisher.txt`).
- **Idea in simple words:** how fast an attacker learns the secret from noisy samples depends on how steeply the noise's probability changes from one value to the next. For a triangle we can add up that steepness exactly instead of approximating it.
- **Result:** the exact sum agrees with the hand formula within 1% (ratio 0.991 to 0.996). The wall for T = 2 stays at 2^25.0 / 2^28.5 / 2^28.3, i.e. 12-14 bits above the cap. Still no hole. Still open: a full simulation of the attack and the corrupt-coordinator view.
- **New basic:** *Fisher information* = a number saying how much one noisy sample tells you about the hidden value; more information means fewer samples are needed.

## 2026-10-16: how much of the secret does the edge estimator get below the wall? (paper plan item 4, step 1)

- **What:** `experiments/partial_recovery.py`, result `experiments/results/partial_recovery.json`. ML-DSA-44, one ring element (256 coefficients of s2), TALUS bounded-noise channel, 2 trials each.
- **Idea in simple words:** full recovery needs about 2^16 signatures, but the cap is 2^13. Below full recovery the estimator still gets part of the answer right. If we knew a good part of s2 exactly, the public key t = A s1 + s2 would turn that into exact equations on s1 and leave a smaller lattice problem (a "lattice finish").
- **Result:** at N = 2^13 (the cap) about 43% of the coefficients round to the right value (random guessing: 20%); at 2^14 about 47%. Picking only the coefficients that sit close to an integer raises precision only to about 50-65%, with 15-30% kept. So at the cap we get a soft hint, not certain knowledge.
- **What this means:** a lattice finish needs hard (certain) coordinates or a proper per-coordinate probability. Neither is available yet, so no attack under the cap is shown. A real test needs the posterior for each coordinate (sampling inside the set of secrets consistent with all signatures) and an LWE-with-soft-hints estimate. Not done.
- **Caveats:** 2 trials per point; the LP picks a corner of the consistent set, which is a biased point guess. Joint solving across ring elements adds nothing by itself: the elements are independent given the challenges.

## 2026-10-16: paper outline and scorecard (paper plan item 10)

- **What:** `docs/PAPER_OUTLINE.md`: the claim of the paper, the threat model, a scorecard table with one row per tested channel, and the section plan.
- **Idea in simple words:** a paper needs one clear sentence about what is new. Ours: a first systematic check of how much each threshold ML-DSA proposal leaks, with a test kit that has known-leaky and known-safe controls. The scorecard puts every result next to its margin (how many bits of safety remain) and the file that proves it.
- **Honest state:** no break of an official submission. The strongest findings are the incorrect printed bound in Mithril's proof, the Kao P2 broadcast issue (not yet demonstrated on real ML-DSA-44), and the thin 3-bit margin for TALUS' outsider view.

## 2026-10-16: one-command reproduction (paper plan item 12)

- **What:** `experiments/reproduce.py`. `python -m experiments.reproduce` lists every table and figure with the command, cost and output file; `--fast` reruns the quick ones; `--run ID` runs one.
- **Why:** venues like USENIX require an artifact that lets a reviewer redo the results. A listed command per result also makes our own claims checkable.
- **Check:** the fast items (insider walls, m = 2 Fisher check, A.6 bound, TALUS success table, architecture figure) rerun in about 25 s and give output identical to the stored files (git shows no changes).
- **Not covered:** heavy items (the GPU ILP trials, Sage hint estimator, Mithril Go transcripts) are listed with their commands but not rerun by `--fast`.
