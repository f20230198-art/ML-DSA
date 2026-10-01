"""Builds report/Phase1_Report.docx. Run: python build_report.py"""
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)  # A4
sec.left_margin = sec.right_margin = Inches(1.0)
sec.top_margin = sec.bottom_margin = Inches(1.0)

st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(10)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.space_after = Pt(4)
st.paragraph_format.space_before = Pt(0)
st.paragraph_format.line_spacing = 1.15


def run(p, text, bold=False, italic=False):
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(10)
    r.bold, r.italic = bold, italic
    return r


def para(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    for i, part in enumerate(text.split("**")):
        if part:
            run(p, part, bold=(i % 2 == 1))
    return p


def heading(text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8 if level == 1 else 5)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run(p, text, bold=True, italic=(level == 2))


def bullet(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.first_line_indent = Inches(-0.18)
    p.paragraph_format.space_after = Pt(2)
    for i, part in enumerate(("• " + text).split("**")):
        if part:
            run(p, part, bold=(i % 2 == 1))


def shade(cell, color="D9D9D9"):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def table(rows, widths):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, txt in enumerate(row):
            c = t.cell(i, j)
            c.width = Inches(widths[j])
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = run(p, txt, bold=(i == 0))
            r.font.size = Pt(9)
            if i == 0:
                shade(c)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ---------------- Title ----------------
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "Cryptanalysis of Threshold ML-DSA Proposals in the NIST MPTC First Call: "
       "A Literature Survey and Problem Formulation", bold=True).font.size = Pt(14)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "Project Phase 1 Report – Cryptography course, BITS Pilani, Dubai Campus")
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "Srivathsa H Honyal (f20230198)", italic=True)

# ---------------- Abstract ----------------
heading("Abstract")
para("ML-DSA (FIPS 204) is the NIST-standardised lattice-based digital signature, but it was designed for a single signer. "
     "Splitting the signing key among several parties, so that no single device holds the key, is hard because ML-DSA's "
     "rejection sampling and rounding steps do not combine well with secret sharing. In 2026 NIST opened a First Call for "
     "multi-party threshold schemes (IR 8214C), and four proposals aim to produce signatures that verify under an unmodified "
     "ML-DSA verifier: Mithril, Quorus, SplitForge/Trilithium and TALUS. This report surveys twenty-three papers and "
     "specifications covering these schemes, their predecessors, and the cryptanalytic tools (integer learning with errors, "
     "integer linear programming, regression) used to attack lattice signatures through leakage. The survey shows that "
     "earlier versions of TALUS fall to two practical key-recovery attacks, while no public attack on the other three exists, "
     "largely because they have not been systematically tested. We formulate four concrete open problems and propose a "
     "reusable leakage-testing harness that simulates each scheme's public transcripts, including aborted attempts, and runs "
     "a battery of statistical key-recovery tests against them.")

# ---------------- Introduction ----------------
heading("1. Introduction")
para("**Digital signatures and the quantum threat.** A digital signature lets a signer prove that a message came from them "
     "and was not altered. Today's signatures (RSA, ECDSA) would be broken by a large quantum computer, so NIST has "
     "standardised post-quantum replacements. ML-DSA, specified in FIPS 204 [1] and derived from CRYSTALS-Dilithium [2], is the "
     "primary general-purpose choice. Its security rests on lattice problems, namely Module-LWE (learning with errors) and "
     "Module-SIS.")
para("**How ML-DSA signs.** Let A be a public matrix over the ring R_q = Z_q[X]/(X^256+1) with q = 8380417, and let the secret "
     "key be short vectors (s1, s2) with public key t = A·s1 + s2 (low bits dropped). To sign a message, the signer samples a "
     "random short nonce y, computes w = A·y and its high bits w1 = HighBits(w), derives a sparse challenge "
     "c = H(msg, w1), and outputs z = y + c·s1 together with a hint h. Two rejection checks are applied: "
     "‖z‖∞ < γ1 − β, which hides s1, and ‖LowBits(w − c·s2)‖∞ < γ2 − β, which hides s2 and keeps the "
     "hint small. If either fails, the signer restarts with a fresh nonce. This Fiat–Shamir-with-aborts structure is what makes "
     "signatures statistically independent of the key.")
para("**Why thresholding is hard.** In a (T, N) threshold scheme, any T of N parties can sign and fewer than T learn nothing. "
     "For ML-DSA three obstacles arise: s1, s2 and y must all be shared; HighBits is not additive, so parties cannot simply "
     "round their own pieces of w; and the s2 rejection check needs the full secret. Each proposal resolves this differently: "
     "replicated short shares with local rejection (Mithril), generic multiparty computation (Quorus, Trilithium), or "
     "pre-filtering nonces so the check always passes (TALUS).")
para("**Why cryptanalysis now.** NIST's First Call (IR 8214C) [3] invites threshold schemes, with preliminary packages expected "
     "from late 2026 and a package deadline not before March 2027. Early public scrutiny is most valuable before schemes are "
     "frozen. Two facts make ML-DSA-based designs fragile and drive most attacks in this report. First, A is tall (k ≥ ℓ in "
     "every parameter set), so for any short x, publishing A·x reveals x by Gaussian elimination; no lattice problem is "
     "involved. Second, z = y + c·s1 holds over the integers, so any leak of the nonce y gives s1 = c⁻¹(z − y). "
     "**Contributions of this report:** (i) a structured survey of the threshold ML-DSA landscape and the attack toolbox; "
     "(ii) a gap analysis; (iii) four formal open problems; and (iv) a proposed experimental methodology.")
para("**Secret sharing and threshold signatures.** Shamir secret sharing [21] hides a secret as the constant term of a random "
     "degree-(T−1) polynomial and gives each of N parties one evaluation; any T shares reconstruct the secret by Lagrange "
     "interpolation, while T−1 shares reveal nothing. Feldman's verifiable secret sharing [22] adds public commitments g^{a_i} "
     "to the polynomial coefficients so each party can check its share; this works because discrete-log commitments are hiding. "
     "Threshold Schnorr signatures such as FROST [23] exploit the linearity of Schnorr signing: partial signatures simply add. "
     "ML-DSA breaks every one of these conveniences. Shares of a short secret are not short, which violates the norm bounds "
     "that rejection sampling relies on; rounding is non-linear; and, as Section 2.3 shows, the lattice analogue of Feldman "
     "commitments (publishing A·x) is not hiding at all, because A·x is invertible. The design space is therefore "
     "genuinely different from the discrete-log setting.")
para("**Parameters.** All three ML-DSA parameter sets share q = 8380417, n = 256 and d = 13 dropped bits of t. They differ as "
     "follows, where τ is the number of ±1 entries in the challenge and β = τ·η bounds the size of c·s.")
table([
    ["Set", "NIST category", "(k, ℓ)", "η", "τ", "γ1", "γ2"],
    ["ML-DSA-44", "2", "(4, 4)", "2", "39", "2^17", "(q−1)/88"],
    ["ML-DSA-65", "3", "(6, 5)", "4", "49", "2^19", "(q−1)/32"],
    ["ML-DSA-87", "5", "(8, 7)", "2", "60", "2^19", "(q−1)/32"],
], [1.1, 1.0, 0.8, 0.5, 0.5, 0.7, 1.1])
para("The challenge c has only τ nonzero coefficients, which is why each signature gives the attacker one noisy linear "
     "equation in the secret with small coefficients; this observation underlies the sample-count estimates in Section 2.3. "
     "A pair of nonce and response is safe only because rejection sampling makes z's distribution independent of s1: "
     "z is accepted only when it lies in a box, and inside the box its distribution is uniform whichever s1 was used. Any "
     "threshold design that changes what is accepted, what is rejected, or what else is published must therefore re-establish "
     "this independence, and this is the property we test.")
para("**Scope and honesty note.** This is a literature-and-specification assessment. Mithril, Quorus and Trilithium were "
     "studied through their abstracts, preview writeups and the descriptions in later papers; no implementation code was run and "
     "no experiments have been performed yet. Hypotheses below are labelled as such.")

# ---------------- Literature survey ----------------
heading("2. Literature Survey")
heading("2.1 Background: lattice signatures and threshold lattice signatures", 2)
para("Dilithium [2] introduced the signing structure above, and FIPS 204 [1] standardised it as ML-DSA with parameter sets "
     "ML-DSA-44/65/87 at NIST security categories 2/3/5. Threshold signatures for lattices were first built with heavy tools "
     "such as threshold homomorphic encryption: Gür, Katz and Silde [16] give a two-round scheme from threshold HE. Threshold "
     "Raccoon [14] (Eurocrypt 2024) takes a lighter route using only symmetric primitives and simple lattice operations, with "
     "one-time additive masks that stop partial signing keys leaking through partial signatures; however its signatures are "
     "not ML-DSA signatures. Del Pino, Espitau, Niot and Prest [15] extend short-share distributed key generation with "
     "identifiable aborts and a detector for adversarial short-vector correlations (this preliminary version has since been "
     "withdrawn in favour of a later paper). The decisive shift is toward schemes whose output verifies under the unmodified "
     "FIPS 204 verifier, because deployed certificates, hardware and pinned keys cannot change.")

heading("2.2 The four First-Call ML-DSA proposals", 2)
para("**Mithril** [4,5,6,7] (PQShield, Brave, Bristol) is the first practical ML-DSA-compatible threshold scheme. It uses "
     "replicated secret sharing with short shares, so shares stay small enough for ML-DSA's norm bounds, and performs "
     "rejection sampling locally per party with hyperball sampling, avoiding a global abort MPC. Communication is about 1 MB per "
     "participant for up to six parties, with Go implementations; the security argument is a game-based reduction in the random "
     "oracle model to MLWE and ML-DSA unforgeability under static corruption of up to T−1 parties. There are no identifiable "
     "aborts, and its parameters target a per-attempt success probability of 1/2 rather than ML-DSA's roughly 1/4, so the accepted-"
     "response distribution differs from FIPS 204. The earlier version [5] was superseded by [4].")
para("**Quorus** [8] (J.P. Morgan) modifies ML-DSA signing to be MPC-friendly while keeping FIPS 204 verification and "
     "signature sizes, and provides MPC protocols for honest-majority settings with about 100 KB online communication per party "
     "per rejection-sampling round. It supports many parties (up to 64 in the preview writeup) and is proven secure in the "
     "universal composability framework. A distinguishing choice is that rejected attempts release (w1, c, ⊥) and the proof "
     "claims this is simulatable.")
para("**SplitForge / Trilithium** [9] (Cybernetica) targets two parties, a server and a phone, plus a correlated randomness "
     "provider (CRP). It proves security against a malicious server or phone in the UC model, uses an actively secure "
     "comparison protocol and a new rounding protocol, and has a Rust implementation. It needs about 14 rounds per attempt and "
     "relies on a heuristic that a rejected partial signature can be simulated as uniform.")
para("**TALUS** [10,11] (Codebat) introduces the Boundary Clearance Condition (BCC): for a constant fraction of nonces "
     "(31.7% at ML-DSA-65) the vector s2 provably cannot push w across a rounding boundary, so rejection checks can be enforced "
     "offline on preprocessed nonces. This yields a TEE-assisted one-round profile and a distributed MPC profile with two online "
     "rounds. The same paper proves a lower bound: any FIPS-exact scheme revealing a summed (Irwin–Hall) nonce admits key "
     "recovery after about 2^30 signatures. TALUS builds on Kao's Shamir nonce DKG [12], where the signing nonce is itself a "
     "Shamir secret sharing, with pairwise-cancelling PRF masks and claimed nonce-share min-entropy above 5× the key entropy "
     "for signing sets up to 17.")
para("To see why Mithril's local rejection is delicate, recall that single-signer ML-DSA accepts a nonce only if both ‖z‖∞ "
     "and the low-bits check pass, which happens with probability about 1/4 at the standard parameters. With N parties each "
     "holding a short additive share, the sum of their responses must still lie in the same box, but no party knows the sum. "
     "Mithril lets each party sample its nonce share from a hyperball (a Euclidean ball rather than a box), so that the "
     "aggregate has predictable norm, and decides acceptance locally from the party's own contribution. Because the aggregate "
     "distribution is then a sum of ball-distributed terms rather than uniform on a box, the accepted-response distribution is "
     "close to, but not exactly, the FIPS 204 one; the size of this gap, and whether it can be measured with a feasible number of "
     "signatures, is the subject of problem P2 below. This difference is intrinsic to the design and is not a bug, which is why "
     "the question is quantitative rather than binary.")
table([
    ["Scheme", "Design", "Trust / corruption model", "Rounds", "Public attacks"],
    ["Mithril [4]", "Replicated short shares, local rejection", "Dishonest majority (T−1), static; N ≤ 6", "~3 per attempt", "None found"],
    ["Quorus [8]", "MPC-friendly ML-DSA variant", "Honest majority, UC, n ≤ 64", "16–29 broadcast", "None found"],
    ["Trilithium [9]", "2-party MPC + CRP", "CRP honest; one party malicious", "14 per attempt", "None; heuristic assumption"],
    ["TALUS [10,11]", "BCC nonce filtering, Shamir nonce DKG", "Honest majority N ≥ 2T−1", "2 (v0.22)", "Broken (earlier versions) [13]"],
], [1.0, 1.9, 1.7, 0.9, 1.3])

heading("2.3 Published attacks on TALUS", 2)
para("Niot [13] (ePrint 2026/1386) gives two independent practical attacks on earlier TALUS versions. "
     "**Attack 1** exploits non-hiding commitments. TALUS-MPC used Feldman-style commitments A·x copied from discrete-log "
     "protocols. Since A is left-invertible with failure probability at most 2^-15 for ML-DSA-44 and 2^-38 for -65/-87 (a "
     "union bound over the 256 NTT slots), x = A⁺(A·x). The key-generation broadcast A·s1,i therefore reveals every key "
     "share, and the blame phase's A·ŷ_h reveals the aggregate nonce, giving s1 = c⁻¹(z − y) from a single signature. "
     "**Attack 2** targets the removed s2 rejection check in both TALUS-TEE and TALUS-MPC. Each signature releases "
     "v = Az − c·t1·2^d = w − c(s2 − t0); with HighBits(w) known from the hint, the observable is b = −c·s′ + e where "
     "e = LowBits(w) is roughly uniform. This is ILWE (LWE without modular reduction), which Bootle et al. [17] showed is "
     "solvable by least squares when error variance is not superpolynomially larger than sample variance. The estimated "
     "requirement is N ≳ 4γ2²/(3τ) signatures, which the note's table lists as roughly 3.1×10^8 (ML-DSA-44), "
     "1.9×10^9 (-65) and 1.5×10^9 (-87), while the abstract says “a few hundred million”. Niot stresses these figures are "
     "unoptimised and expects lattice reduction to cut them substantially. Reinstating the check is not sufficient, because a "
     "corrupted party can bias its nonce share (for instance y_i = 0) so the check always passes.")
para("The authors' response [11] (preview writeup v0.22) replaces commitments by zero-knowledge well-formedness proofs and "
     "handles the s2 channel by a mandatory per-key signing cap of about 2^13/2^14/2^14 signatures (ML-DSA-44/65/87), enforced "
     "by key rotation, against a claimed integer-uniqueness wall near 2^15.2/2^16.4/2^16.2. Each preprocessed nonce is bound to "
     "one quorum and erased after use. Whether the cap's margin to the true attack cost is real is exactly the kind of question "
     "this project targets, and the cap also hurts deployability because certificates and pinned keys cannot rotate every few "
     "thousand signatures.")

para("**Worked illustration of Attack 1.** Suppose party i broadcasts the commitment C_i = A·s1,i, where s1,i is a short vector "
     "with ℓ polynomial entries and A has k ≥ ℓ rows. Working in the NTT domain, A splits into 256 independent k×ℓ matrices over "
     "Z_q, one per slot. Each is left-invertible unless a union of events of probability about 1/q each occurs, which is the origin "
     "of the 2^-15 and 2^-38 failure bounds. Any observer therefore solves the linear system slot by slot and obtains s1,i exactly; "
     "the shortness of the secret is irrelevant because no lattice problem arises. For a toy case with k = ℓ = 1 the "
     "commitment is just the product a·s mod q, and dividing by a recovers s. This is why the reasoning “the discrete-log "
     "commitment is hiding, so the lattice one should be” fails.")
para("**Worked illustration of Attack 2.** Consider one coefficient of s′. Each signature yields b = −c·s′ + e with c "
     "a fixed sparse ±1 vector and e a bounded error. A single sample constrains a sum of τ secret coefficients to an interval "
     "of width about 2γ2, far wider than the secret's range, so one sample says almost nothing. Averaging many samples "
     "against independent challenges shrinks the uncertainty in proportion to 1/√(Nτ), and once it falls below half the "
     "spacing between plausible values each coefficient can be rounded. The quantity γ2²/τ in the sample estimate shows "
     "directly why ML-DSA-44, with its small γ2 = (q−1)/88, is more exposed per signature than -65 and -87.")

para("**Why a summed nonce leaks (the Irwin–Hall bound).** In many designs each of T parties contributes a nonce share y_i "
     "drawn uniformly from a box, and the aggregate nonce is their sum. The sum of uniform variables is not uniform: it "
     "follows an Irwin–Hall distribution, which is bell-shaped. The accepted response z = y + c·s1 is then a shifted copy "
     "of this bell, and the shift is c·s1. Each signature therefore contributes a small amount of Fisher information about "
     "s1, much as repeated noisy measurements of a position reveal it. The information per signature is tiny, which is why the "
     "Irwin–Hall loss for a single signature is below 0.013 bits in [12], but it accumulates, and [10] proves that after "
     "roughly 2^30 signatures at ML-DSA-65 an efficient attack succeeds. A design can avoid this only by making the revealed "
     "aggregate nonce exactly uniform, which is the claim made for Quorus and Trilithium, or by limiting the number of "
     "signatures, which is what the TALUS cap does. The existence of this lower bound is what makes checklist item 4 central.")
para("**Corruption models and why they matter.** The proofs behind the schemes assume different adversaries. Static corruption "
     "means the adversary picks the corrupted set before the protocol starts; adaptive corruption lets it choose during "
     "execution. Dishonest-majority security (Mithril) allows up to T−1 corrupted signers, while honest-majority security "
     "(Quorus, TALUS-MPC) requires N ≥ 2T−1 and guarantees nothing beyond that. Identifiable aborts let honest parties "
     "name a misbehaving party; without them, as in Mithril, a corrupted party can abort after seeing honest contributions and "
     "retry, so aborted transcripts become part of the adversary's view. Each of these choices changes which transcripts "
     "an attack harness must simulate, which is why the harness treats the corruption model as an input rather than a constant.")

heading("2.4 Leakage-based cryptanalysis of lattice signatures", 2)
para("The tools behind these attacks come from a line of work on ILWE and rejection-sampling leakage. Bootle et al. [17] "
     "introduced the ILWE view of linear leakage in BLISS. Zhou, Wang, Sun and Yu [18] (TCHES 2025) show that the challenges of "
     "rejected Dilithium signatures leak: rejected responses impose upper and lower bounds on the product c·s, which they "
     "turn into an integer linear programming (ILP) problem and recover full keys in seconds to minutes on all three levels, "
     "validated on an ARM Cortex-M4. Damm et al. [19] (ASIACRYPT 2025) define Concealed ILWE, where only a fraction of samples is "
     "zero-knowledge, show ordinary least squares fails, and use Huber and Cauchy regression to break a masked Dilithium in under "
     "two minutes. Yates et al. [20] test least-squares attacks on ILWE instances built directly from captured signatures and "
     "find that, at the studied parameters, the experiments reinforce the schemes' proclaimed security. Together these show "
     "that any threshold design which releases values correlated with c·s1 or c·s2 must be examined with estimators "
     "stronger than plain least squares: bounded-noise estimators, ILP, robust regression and lattice reduction.")

heading("2.5 Related and superseded work", 2)
para("The Mithril line began as a poster [6] and a preliminary ePrint [5] covering both ML-DSA and an enhanced Raccoon with "
     "identifiable aborts (up to 64 parties); the latter was later split into two papers, one of which is [4]. Kao's "
     "predecessor [12] is not itself a Call submission but shows the same patterns: its fully distributed profile P2 broadcasts "
     "masked commitments, and the paper's own remarks show an exposed λ_h·A·y_h yields y_h and then the key; masks hide "
     "these only when |S∖C| ≥ 2, and with |S| = T and T−1 corrupted parties inside S, |S∖C| = 1. This is a hypothesis from "
     "our reading and needs confirmation. Its Irwin–Hall nonce-loss bound is also only non-vacuous for q_s < 16,000, "
     "whereas [10] later proves an attack near 2^30.")

heading("2.6 Gap analysis", 2)
bullet("**No systematic public testing** of Mithril, Quorus or Trilithium transcripts, only design-level arguments.")
bullet("**TALUS's cap** rests on an information-theoretic argument, with a gap of about 2 bits to the authors' wall and about "
       "14–17 bits to Niot's unoptimised estimate, which an optimised bounded-noise or ILP estimator could close.")
bullet("**Rejected-attempt transcripts** (Quorus reveal-on-reject, Trilithium's uniform-rejected-partial heuristic) have no "
       "empirical leakage analysis in the literature we found.")
bullet("**Mithril's accepted-response distribution** (success probability 1/2) and its a posteriori key-sharing hint loss "
       "(7–12 bits reported) lack independent re-derivation at q_s = 2^64.")
bullet("**Corruption-model gaps**: static-only proofs, honest-majority boundaries (N = 2T−1), and conditions buried in "
       "footnotes (|S∖C| ≥ 2).")

heading("2.7 Comparative discussion", 2)
para("The proposals sit at different points of a four-way trade-off between corruption tolerance, number of parties, "
     "interaction, and the strength of the evidence for security. Mithril is the only one that tolerates a dishonest majority "
     "(T−1 corrupt), but it is limited to N ≤ 6 and gives no identifiable aborts. Quorus scales to many parties with "
     "UC-style proofs, but only with an honest majority and with many broadcast rounds, which matters on wide-area networks. "
     "Trilithium covers the narrow but commercially important phone-and-server case and needs an extra trusted randomness provider. "
     "TALUS minimises online rounds and, with a TEE, reaches one round, but its security is the least settled: the s2 channel is "
     "closed by a usage cap rather than a structural argument. Evidence quality differs as well. Mithril and Quorus have "
     "reductions in the random oracle or quantum random oracle model; Trilithium has a UC proof that uses a heuristic; TALUS "
     "has an information-theoretic argument with a numerical margin. For a standardisation process these differences suggest "
     "that independent empirical testing adds most value where the proof contains a heuristic or a margin, namely Trilithium "
     "and TALUS, and where the parameters change the accepted distribution, namely Mithril.")
para("Deployment realities amplify this. A threshold signature that verifies under standard FIPS 204 can be dropped into "
     "existing PKI, code-signing and TLS stacks unchanged, which is the main appeal of all four designs. But a key that must "
     "be rotated every 2^13 signatures (TALUS) or a signer that is limited to six parties (Mithril) restricts the settings in "
     "which these are practical, and tests that expose a larger margin would materially change which designs are viable.")

heading("2.8 Attack surface of each scheme (working hypotheses)", 2)
para("The following subsections record where we expect to look first. They are hypotheses derived from the specifications and "
     "later papers, not results.")
para("**Mithril.** (i) The accepted-response distribution: with success probability 1/2 per attempt instead of about 1/4, the "
     "nonce distribution and rejection region differ from FIPS 204, so the Renyi or Fisher-information loss at q_s = 2^64 must "
     "be computed concretely. (ii) A posteriori key sharing: the adversary obtains a noisy hint on the existing ML-DSA secret, "
     "which the authors quantify as a 7–12 bit loss; this should be re-derived for the exact share subset held by T−1 corrupted "
     "parties. (iii) Adaptive corruption is argued heuristically with a loss of at most 5 bits for N ≤ 6, a proof gap rather "
     "than an attack. (iv) Selective aborts: with no identifiable aborts, corrupted parties can abort after seeing honest "
     "contributions, so aborted-attempt transcripts must be checked. (v) Implementation: the Go proof of concept uses floating "
     "point for hyperball sampling, so sampler bias and timing leakage are plausible, and a fixed-point C reference is planned.")
para("**Quorus.** (i) Reveal-on-reject: rejected attempts release (w1, c, ⊥) and the paper proves this simulatable; we "
     "can test it empirically by feeding rejected-attempt transcripts to least-squares and ILP tests against c·s1 and c·s2. "
     "(ii) Which check failed: related work [18] shows that if the identity of the failing check leaks, keys can be recovered, so "
     "implementations must reveal only ⊥. (iii) The MPC building blocks (the rejection-sampling functionality, batched OR, and "
     "offline preprocessing) are where implementation mistakes would hide. (iv) Honest majority is a hard assumption, so "
     "behaviour at N = 2T−1 boundaries deserves a check.")
para("**SplitForge / Trilithium.** The statement that a rejected partial signature can be simulated as uniform is heuristic and "
     "is the most attackable claim: the distribution of rejected partial responses may depend on s1 or s2. The rejection-check "
     "result is declassified to both parties, so the number of bits about c·s2 revealed per attempt should be bounded. The "
     "correlated randomness provider is a trusted third party, so what it can learn from its own correlated values matters, and "
     "the scheme is two-party only (2-of-2).")
para("**TALUS v0.22.** The signing cap is the whole security argument for the s2 channel. Under BCC the noise "
     "e = LowBits(w) is restricted to (−γ2+β, γ2−β), so it has sharp edges, which carry more information per sample than "
     "variance alone. Other surfaces are the zero-knowledge share well-formedness proofs, the blame procedure, quorum binding "
     "(a nonce-reuse observation was reported by S. Jo on an earlier version) and malicious nonce bias.")

heading("2.9 A reusable attack checklist", 2)
para("Generalising the observed attacks, we distilled ten questions that can be asked of any threshold ML-DSA design. They "
     "structure both the survey and the harness described in Section 3.")
table([
    ["#", "Question", "Typical consequence"],
    ["1", "Is A·x published for a secret or nonce x?", "x = A⁺(A·x) by Gaussian elimination"],
    ["2", "Does any nonce leak to an observer?", "s1 = c⁻¹(z − y)"],
    ["3", "Are rejection checks removed, moved or altered?", "ILWE: regress released values on c·s1, c·s2"],
    ["4", "Is the accepted-z distribution non-uniform?", "Fisher information; wall ≈ 4/(I·τ) signatures"],
    ["5", "What do rejected-attempt transcripts reveal?", "ILP on rejection bounds [18]"],
    ["6", "Can a corrupted party bias its nonce share?", "Checks always pass; statistical attack revived"],
    ["7", "Are quorum and session bindings enforced?", "Nonce reuse across quorums or sessions"],
    ["8", "Are there corruption-model gaps?", "Static-only proofs; conditions such as |S∖C| ≥ 2"],
    ["9", "How much do a posteriori hints reduce hardness?", "Lattice-estimator bit loss"],
    ["10", "Do implementations match the specification?", "Float samplers, timing, test vectors"],
], [0.4, 3.2, 2.9])

# ---------------- Problem formulation ----------------
heading("3. Problem Formulation and Possible Solution")
heading("3.1 Threat model and notation", 2)
para("Fix an ML-DSA parameter set with parameters (q, k, ℓ, τ, γ1, γ2, β). A (T, N) threshold scheme Π has a "
     "transcript distribution Tr_Π(sk, m) over everything an adversary observes while the scheme signs message m: the final "
     "signature, broadcasts, coordinator messages and, for corrupted parties, their internal state, and (crucially) the data of "
     "aborted attempts. The adversary statically corrupts up to the number of parties the scheme allows, sees q_s signing "
     "sessions on chosen messages, and wins if it recovers s1 (equivalently the secret key, since s2 follows from t) or forges. "
     "We study key recovery, which is strictly stronger evidence of breakage than a distinguishing bias.")
table([
    ["Symbol", "Meaning"],
    ["A, t", "Public matrix over R_q (k×ℓ) and public key t = A·s1 + s2"],
    ["s1, s2", "Short secret vectors; s′ = s2 − t0 where t0 holds the dropped low bits of t"],
    ["y, z, c", "Nonce, response z = y + c·s1, and sparse challenge with τ entries of ±1"],
    ["w, w1", "w = A·y and its high-bits part w1 = HighBits(w); e = LowBits(w) is the rounding residue"],
    ["γ1, γ2, β", "Response bound, rounding bound, and bound on |c·s| (β = τ·η)"],
    ["(T, N)", "Threshold and number of parties; S is the signing set and C the corrupted set"],
    ["q_s", "Number of signing sessions the adversary observes"],
], [1.1, 5.4])
heading("3.2 Open problems", 2)
para("**P1 (TALUS signing cap).** Given the post-BCC noise e = LowBits(w) restricted to (−γ2+β, γ2−β), find the minimum "
     "number of signatures q* at which an optimised estimator recovers s′ = s2 − t0, and compare q* with the cap "
     "(2^13–2^14) and the uniqueness wall (2^15–2^16). Sharp noise edges carry more information per sample than variance "
     "alone, so bounded-noise estimators, ILP and lattice reduction should beat least squares. Either outcome is informative: "
     "q* below the cap breaks the design; q* above it gives a concrete security margin.")
para("**P2 (Mithril accepted-response leakage).** Compute the Fisher information I about s1 carried by one accepted response z "
     "under Mithril's hyperball sampling and 1/2 acceptance, derive the attack wall ≈ 4/(I·τ), and check it exceeds 2^64. "
     "Also re-derive the hardness loss of the a posteriori key-sharing hint using the exact share subset held by T−1 corrupted "
     "parties, with the lattice estimator.")
para("**P3 (Rejected-attempt leakage in Quorus and Trilithium).** Test whether the distribution of rejected-attempt "
     "transcripts, (w1, c, ⊥) in Quorus and rejected partial responses in Trilithium, depends on s1 or s2. A positive result "
     "would invalidate the simulatability claim or heuristic; the declassified rejection-check bit in Trilithium should be "
     "quantified in bits per attempt about c·s2.")
para("**P4 (Confirm or refute Kao's P2 claim).** Decide whether the masked-commitment argument fails at |S∖C| = 1, which "
     "would be a one-signature key recovery for any |S| = T with T−1 corruptions, and whether the Feldman-style DKG "
     "commitments show the A·s1,i pattern broken in [13].")
para("**Hypotheses and success criteria.** For each problem we state what would count as a result. For P1 we hypothesise that a "
     "bounded-noise estimator needs at least an order of magnitude fewer signatures than least squares, and the criterion is "
     "a recovered key (checked against the public key) at a sample count below 2^16. For P2 we hypothesise that the Fisher "
     "information per signature is small enough that the wall exceeds 2^64, so a null result is the expected outcome and the "
     "criterion is a numerical bound with its derivation. For P3 we hypothesise that Quorus's reveal-on-reject is simulatable "
     "as claimed while Trilithium's rejected-partial heuristic may only hold approximately, and the criterion is a statistical "
     "test with a stated false-positive rate and sample budget. For P4 we hypothesise, from the algebra in [12], that the P2 "
     "profile fails at |S∖C| = 1, and the criterion is either an explicit recovery procedure on a toy instance or a precise "
     "reason why the masks still hide the commitments. Stating these in advance keeps the project from drifting into whatever "
     "happens to be easy to measure.")
heading("3.3 Proposed solution: a leakage-testing harness", 2)
para("We propose a reusable software harness with three layers. (1) **ML-DSA primitives**: parameters, NTT over R_q, "
     "Power2Round, Decompose, MakeHint/UseHint and the FIPS 204 samplers, validated against known-answer tests. (2) **Scheme "
     "simulators**: each emits the public transcript on synthetic keys, covering accepted and aborted attempts and the view of "
     "a corrupted coalition. (3) **Estimators** keyed to a ten-point checklist distilled from the survey: Gaussian elimination "
     "for published A·x; direct nonce-leak recovery; least squares and ILWE regression; bounded-noise and ILP "
     "estimators; robust (Huber/Cauchy) regression [19]; Fisher-information computation; and lattice-estimator accounting "
     "for hints. Checklist items beyond statistics (quorum/session binding, corruption-model gaps, floating-point samplers and "
     "timing) are handled by reading specifications and reference code.")
para("**Method.** Step 1 is a sanity check: reproduce Niot's ILWE attack [13] on TALUS-style transcripts at reduced "
     "parameters and confirm the sample-count formula N ≈ 4γ2²/(3τ). Step 2 addresses P1 by swapping the estimator for "
     "bounded-noise/ILP variants and plotting recovery probability against sample count. Steps 3–4 address P2 and P3 by running "
     "the same estimators on Mithril, Quorus and Trilithium simulators, with the null result being “no detectable dependence "
     "up to a stated sample budget”. Step 5 addresses P4 by direct algebra on the published protocol. When full packages appear "
     "(from March 2027) the harness is rerun on the actual reference code.")
para("**Implementation considerations.** The harness is research software, so correctness and reproducibility outrank speed. "
     "Polynomial arithmetic uses the NTT with q = 8380417 and a primitive 512th root of unity, as in FIPS 204; the samplers "
     "(ExpandA, ExpandS, ExpandMask, SampleInBall) are built on SHAKE128 and SHAKE256. Prototypes are written in a high-level "
     "language with vectorised numerics, and only the inner loops that must run over 10^8 to 10^9 signatures are moved to "
     "compiled code. Every experiment is seeded and logged so that a reported recovery can be replayed, and keys are generated "
     "synthetically so that ground truth is always available for scoring. Estimators are written against a small interface that "
     "takes a stream of transcript records and returns a candidate secret and a confidence score, so that a new scheme "
     "requires only a new simulator and no change to the analysis code. This separation, between what a scheme publishes and "
     "how an attacker uses it, is what makes the checklist reusable across proposals.")
heading("3.4 Estimators in more detail", 2)
para("**Least squares and the ILWE sample bound.** Each signature supplies a sample (c, b) with b = −c·s′ + e, where "
     "c has τ coefficients of ±1 and e is the noise. Stacking N samples gives an overdetermined integer linear system "
     "whose ordinary least-squares solution has per-coordinate error variance about Var(e)/(N·τ/n) in the "
     "normalised ring representation. For uniform noise on [−γ2, γ2] with Var(e) ≈ γ2²/3, rounding recovers an "
     "entry of s′ correctly with overwhelming probability once the standard deviation falls below a fraction of 1/2 times the "
     "bound on |s′|; this reproduces the order N ≈ 4γ2²/(3τ) quoted in [13]. Our first experiment checks this "
     "scaling on reduced parameters, where the signature counts are small enough to run end to end.")
para("**Bounded-noise estimation.** If e is not Gaussian but supported on a known interval (as under BCC), the posterior for "
     "each secret coefficient is much tighter than variance suggests, because every sample rules out all candidates for which "
     "|b + c·s′| exceeds the bound. Each sample is thus a pair of linear inequalities, and the feasible region is a "
     "polytope that shrinks with N faster than the least-squares confidence ellipsoid. We will implement this as an "
     "integer linear program in the manner of [18], and as a cheaper iterated-elimination heuristic, and measure the "
     "sample count at which the feasible integer point becomes unique.")
para("**Robust regression.** When only a fraction of samples are informative, as in Concealed ILWE [19], the Huber and Cauchy "
     "losses downweight outliers and succeed where least squares fails. Our simulators produce mixtures of accepted and "
     "rejected samples, so robust regression is the natural third estimator.")
para("**Fisher information and the attack wall.** For a scheme whose accepted responses have density f_s(z) depending on the "
     "secret s through a location shift c·s, the Fisher information I about s per signature determines the Cramér–Rao lower "
     "bound on any unbiased estimator’s variance. Following the argument in [10], key recovery requires on the order of "
     "4/(I·τ) signatures; we compute I numerically from the exact acceptance region and sampling distribution of each scheme "
     "rather than relying on a Gaussian approximation, and report the resulting wall in bits to compare with q_s = 2^64.")
para("**Hint accounting.** For schemes where the adversary holds partial information about the secret (Mithril's share subsets), "
     "we model the information as additional linear equations or a modified distribution on the secret and feed it to a lattice "
     "estimator to measure the loss in bits of security, as opposed to treating the instance as fresh MLWE.")

heading("3.5 Experimental design and validation", 2)
para("Every experiment reports four quantities: the number of signatures consumed, the recovered key fraction, wall-clock cost, "
     "and the parameter set. Validation proceeds in three stages. (a) Primitives are checked against FIPS 204 known-answer tests, "
     "so that a harness that cannot sign like ML-DSA cannot be mistaken for evidence about it. (b) Each simulator is checked by "
     "recovering a key from a deliberately leaky variant (for example publishing A·y), to confirm the estimators have power. "
     "(c) Null results are reported with the sample budget and an explicit statement of which attack classes were tried. We "
     "start at reduced dimensions to validate scaling laws, then move to full parameter sets, with the largest runs "
     "vectorised or written in a compiled language. The schedule follows the order in the roadmap: harness and sanity check, "
     "TALUS cap, Mithril, Quorus and Trilithium, Kao's claims, and finally reruns on reference code when packages are published.")
para("**Expected outcomes and risks.** Positive results are attacks or concrete margins; negative results are bounded "
     "statements of the form “no leakage detected with q samples”, which are still useful evidence. Risks: billion-sample "
     "experiments need vectorised or compiled inner loops; simulators may deviate from the true protocols if our reading of "
     "unread papers is wrong; and Mithril, whose team includes the author of [13], is likely already hardened against these "
     "patterns. Any finding should be shared with the scheme teams before publication, and posted to ePrint following standard "
     "responsible-disclosure practice.")

heading("3.6 Limitations of this survey and Phase 2 plan", 2)
para("The survey has three limitations that bear on how its conclusions should be read. First, the full Mithril, Quorus and "
     "Trilithium papers were not read end to end; for Quorus and Trilithium in particular, claims about reveal-on-reject and "
     "the rejected-partial heuristic come from abstracts and from how other papers describe them, so every statement in "
     "Section 2.8 is a hypothesis to verify against the primary text. Second, several sources are preview writeups or "
     "preliminary versions that may change before the package deadline, and two of the cited ePrints have been withdrawn "
     "and superseded. Third, the numerical figures quoted for TALUS differ slightly between the abstract and the table of the "
     "cryptanalytic note; we use the table. Phase 2 therefore begins by reading the unread papers in full, then proceeds in the "
     "order below.")
table([
    ["Stage", "Work item", "Output"],
    ["0", "Choose tooling; read the remaining primary papers; recheck NIST schedule", "Reading table, tooling decision"],
    ["1", "ML-DSA primitives, transcript interface, estimators; reproduce ILWE sanity check", "Harness v0.1, validated on KATs"],
    ["2", "TALUS cap: bounded-noise and ILP estimators vs cap and wall (P1)", "Sample count vs recovery curves"],
    ["3", "Mithril accepted-z and hint accounting (P2)", "Fisher-information bound, bit-loss table"],
    ["4", "Quorus and Trilithium rejected-attempt tests (P3)", "Statistical test results"],
    ["5", "Kao P2 and DKG claims (P4)", "Confirmed-or-refuted note"],
    ["6", "Rerun on reference code once packages appear", "Updated results"],
], [0.6, 3.9, 2.0])

heading("3.7 Relation to NIST evaluation and ethical considerations", 2)
para("The harness is aimed at public, standardisation-stage specifications, consistent with NIST's invitation for public "
     "scrutiny. The deliverables are intended as evidence for the scheme teams and the NIST MPTC forum: a reproducible "
     "script, the sample budget, and the parameter set. We will follow coordinated disclosure, contacting the authors before "
     "any public posting, and will distinguish clearly between confirmed breaks (key recovered), margins (key recovered above a "
     "stated cap), and null results. Results that rely on our simulators rather than on the authors' code will be labelled as "
     "such, since a simulator can differ from the real protocol.")
para("A secondary outcome is educational and methodological: the checklist in Section 2.9 and the harness together "
     "provide a quick screening procedure that a designer can run on a new threshold ML-DSA variant before submitting it. "
     "Because several of the observed failures came from importing patterns from discrete-log protocols, a screening tool "
     "that encodes the lattice-specific pitfalls (invertible commitments, nonce leakage, removed rejection checks) has value "
     "beyond the four schemes studied here.")

# ---------------- Conclusion ----------------
heading("4. Conclusion")
para("Threshold ML-DSA is moving from research to standardisation, and the single published break of an early TALUS version "
     "shows how easily thresholding can leak a key through commitments or removed rejection checks. The survey of twenty-three "
     "sources identifies three schemes without public attacks only because they are untested, one scheme whose security now rests "
     "on a signing cap with an uncertain margin, and a toolbox (ILWE, ILP, robust regression) mature enough to test them. We "
     "formalised four open problems and proposed a leakage-testing harness as a reusable contribution. Phase 2 will implement the "
     "harness, reproduce the TALUS attack, and run the estimators on the remaining schemes.")

# ---------------- References ----------------
heading("References")
refs = [
    "NIST, FIPS 204: Module-Lattice-Based Digital Signature Standard, August 2024.",
    "L. Ducas, E. Kiltz, T. Lepoint, V. Lyubashevsky, P. Schwabe, G. Seiler, D. Stehlé, CRYSTALS-Dilithium: A Lattice-Based Digital Signature Scheme, IACR TCHES 2018(1), 238–268.",
    "NIST, Multi-Party Threshold Schemes: First Call for Submissions, NIST IR 8214C, 2026.",
    "S. Celi, R. del Pino, T. Espitau, G. Niot, T. Prest, Efficient Threshold ML-DSA, IACR ePrint 2026/013.",
    "G. Borin, S. Celi, R. del Pino, T. Espitau, G. Niot, T. Prest, Threshold Signatures Reloaded: ML-DSA and Enhanced Raccoon with Identifiable Aborts, IACR ePrint 2025/1166 (withdrawn 2026, superseded by 2026/013 and 2026/419).",
    "S. Celi et al., Poster: Efficient Threshold ML-DSA up to 6 Parties, ACM CCS 2025 (poster), doi:10.1145/3719027.3760739.",
    "Mithril: Efficient Threshold ML-DSA from Secret Sharing with Short Shares, NIST MPTC First Call preview writeup PW01, 2026.",
    "A. Bienstock, L. de Castro, D. Escudero, A. Polychroniadou, A. Takahashi, Quorus: Efficient, Scalable Threshold ML-DSA Signatures from MPC, IACR ePrint 2025/1163.",
    "A. Dufka, S. Kravtšenko, P. Laud, N. Snetkov, Trilithium: Efficient and Universally Composable Distributed ML-DSA Signing, IACR ePrint 2025/675.",
    "L. Kao, R. Chang, TALUS: FIPS-204-Exact Threshold ML-DSA via Boundary Clearance, arXiv:2603.22109.",
    "TALUS, NIST MPTC First Call preview writeup v0.22, August 2026.",
    "L. Kao, FIPS 204-Compatible Threshold ML-DSA via Shamir Nonce DKG, arXiv:2601.20917.",
    "G. Niot, Key-Recovery Attacks on TALUS: A Cryptanalytic Note, IACR ePrint 2026/1386, July 2026.",
    "R. del Pino, S. Katsumata, M. Maller, F. Mouhartem, T. Prest, M.-J. Saarinen, Threshold Raccoon: Practical Threshold Signatures from Standard Lattice Assumptions, EUROCRYPT 2024, LNCS 14652.",
    "R. del Pino, T. Espitau, G. Niot, T. Prest, Simple and Efficient Lattice Threshold Signatures with Identifiable Aborts, IACR ePrint 2025/871 (withdrawn 2026, superseded by 2026/419).",
    "K. D. Gür, J. Katz, T. Silde, Two-Round Threshold Lattice-Based Signatures from Threshold Homomorphic Encryption, PQCrypto 2024, LNCS 14772.",
    "J. Bootle, C. Delaplace, T. Espitau, P.-A. Fouque, M. Tibouchi, LWE Without Modular Reduction and Improved Side-Channel Attacks Against BLISS, ASIACRYPT 2018, LNCS 11272, 494–524.",
    "Y. Zhou, W. Wang, Y. Sun, Y. Yu, Rejected Signatures' Challenges Pose New Challenges: Key Recovery of CRYSTALS-Dilithium via Side-Channel Attacks, IACR TCHES 2025 (ePrint 2025/214).",
    "S. Damm, A. Fischer, A. May, S. Marzougui, L. Schwarz, H. Seidler, J.-P. Seifert, J. Thietke, V. Q. Ulitzsch, Solving Concealed ILWE and its Application for Breaking Masked Dilithium, ASIACRYPT 2025 (ePrint 2025/1629).",
    "K. Yates, A. Pierrottet, A. Al Mamun, R. Cartor, M. Chowdhury, S. Gao, Security Analysis of Integer Learning with Errors with Rejection Sampling, arXiv:2512.08172, December 2025.",
    "A. Shamir, How to Share a Secret, Communications of the ACM 22(11), 612–613, 1979.",
    "P. Feldman, A Practical Scheme for Non-interactive Verifiable Secret Sharing, FOCS 1987, 427–438.",
    "C. Komlo, I. Goldberg, FROST: Flexible Round-Optimized Schnorr Threshold Signatures, SAC 2020, LNCS 12804.",
]
for i, r in enumerate(refs, 1):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.3)
    p.paragraph_format.space_after = Pt(1)
    run(p, f"[{i}] {r}").font.size = Pt(9)

doc.save("Phase1_Report.docx")
print("saved")
