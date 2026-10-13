# Disclosure drafts (NOT SENT)

Drafts only. The user decides whether and when to send, after asking the course instructor (ROADMAP item). Nothing here has been published. Fill in names and the sender line before sending. Attach only what is listed.

---

## 1. Kao, Profile P2: sum of broadcast W_i reveals A·y

**To:** Leo Kao (address from arXiv 2601.20917)
**Subject:** Possible key-recovery issue in Profile P2 of "FIPS 204-Compatible Threshold ML-DSA via Shamir Nonce DKG"

Dear Dr. Kao,

I am a student studying threshold ML-DSA proposals for a cryptography course, and I believe I have found an issue in Profile P2 of your paper (arXiv 2601.20917v6). I am writing to you privately before mentioning it anywhere else.

In P2, each party broadcasts W_i = λ_i A y_i + m_i^(w) to all parties (Fig. 1(b), Remark 11, App. M.1). By Lemma 1 the pairwise masks cancel, so any party, or anyone who sees the broadcast, can compute Σ W_i = A y = w exactly, not only w1 = HighBits(w). Together with the public signature (c̃, z) this gives A z − w = c A s1, hence A s1 = c⁻¹(A z − w). The left-inverse argument of Remark 11 then recovers s1. This works from a single P2 signature, whatever the number of honest parties. Lemma 2 hides each individual W_i, but not their sum. Your own proof of Corollary 5 (p. 65-66) also treats (c̃, w) as the public broadcast in P2, and the 5-round combiner of App. O handles only the r0-check shares, so it does not seem to change this.

We checked the algebra on a small toy model (tiny ring degree, real q, no rejection sampling or MPC). Your code was not available, so we could not check whether an implementation computes w inside the MPC instead. If it does, P2 would not be affected, and we would be glad to hear it.

We also noticed that in Simulator 17 the simulated honest W̃_i sum to A ỹ, which does not match the real signature. That may be where the proof misses the issue. Corollary 6 states that P2 realizes F_ThreshSig with no |H| >= 2 condition, while Simulator 17 assumes |H| >= 2.

We have not shared this with anyone outside our course team. Please let us know how you would like to proceed, and whether you would object to us describing it in our (non-public) course report.

Kind regards,
[name, institution]

---

## 2. Mithril authors: Lemma 2.5 bound and Q_s; a posteriori sharing hint loss

**To:** the corresponding author of "Efficient Threshold ML-DSA" (ePrint 2026/013); cc the other authors if appropriate
**Subject:** Question on Lemma 2.5 and the resulting Q_s in "Efficient Threshold ML-DSA"

Dear authors,

I am a student working on a course project about threshold ML-DSA, and I would like to ask about two points in your full version (ePrint 2026/013). They concern proof accounting, not an attack.

1. **Lemma 2.5.** The bound I_{1−1/φ²}((n+1)/2, 1/2) < (1−1/φ²)^{n−1} · n · (1−1/φ) is smaller than the exact value at your dimensions. In your script params/hyperball.sage (commit 66e269e), boundI is 2^−50.1 for ML-DSA-44 (φ = 7, dim 2048), while the exact incomplete beta is 2^−33.5 (we computed it with mpmath at 60 digits, inside Sage). The same exponent appears in Devevey, Fawzi, Passelègue and Stehlé (ASIACRYPT 2022, ePrint 2022/1249, App. A.6). Carrying out their cylinder argument gives exponent (n−1)/2 instead. With the exact value, Theorem 3.2 at the published parameters covers about 2^26 to 2^37 signing queries rather than 2^50. Keeping 2^50 would need φ ≈ 5.3–7.7 and a K that is 1.3 to 8.5 times larger. A typical-case average still gives about 2^50 for most sets.

2. **A posteriori sharing (Sec. 3.3).** For σ_share = √2, we computed the exact per-coefficient posterior of the secret given the shares of T−1 parties. Running the lattice estimator (commit 53da598, rough mode) on it, ML-DSA-65 (η = 4) loses about 18 to 24 bits rather than 7 to 12. ML-DSA-44 loses 5 to 8 bits. We may be misreading which σ convention you used, so we would value your view.

Our scripts and numbers are available if they would be useful. We have not made this public.

Kind regards,
[name, institution]

---

## 3. Devevey, Fawzi, Passelègue, Stehlé (optional, only after hearing from the Mithril authors)

**Subject:** Exponent in the upper bound of App. A.6, "On Rejection Sampling in Lyubashevsky's Signature Scheme"

Short note: the cylinder upper bound I_{1−1/η²}((n+1)/2, 1/2) < (1−1/η²)^{n−1} · n · (1−1/η) falls below the exact value from about n = 100 onward (for example n = 2048, η = 7: exact 2^−33.5, bound 2^−50.1). The cylinder argument gives 2 V_{n−1}/V_n · (1−1/η²)^{(n−1)/2} · (1−1/η). The consequence 1/η² < 1 − (ε/n)^{1/(n−1)} inherits the same exponent. We checked the ePrint version only.
