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

