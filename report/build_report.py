"""Builds report/Phase1_Report.docx. Run: python build_report.py"""
import re
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.section import WD_SECTION

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)  # A4
sec.left_margin = sec.right_margin = Inches(0.75)
sec.top_margin = sec.bottom_margin = Inches(0.8)

st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(10)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.space_after = Pt(4)
st.paragraph_format.space_before = Pt(0)
st.paragraph_format.line_spacing = 1.0


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


ROMAN = ["I", "II", "III", "IV", "V", "VI"]
_cnt = {"sec": 0, "sub": 0}


def heading(text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    text = re.sub(r"^\d+(\.\d+)?[a-z]? ", "", text)
    if level == 1 and text in ("Abstract", "References"):
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(3)
        run(p, text.upper(), bold=True).font.size = Pt(9)
    elif level == 1:
        _cnt["sec"] += 1
        _cnt["sub"] = 0
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        run(p, f"{ROMAN[_cnt['sec'] - 1]}. {text.upper()}")
    else:
        _cnt["sub"] += 1
        p.paragraph_format.space_before = Pt(5)
        p.paragraph_format.space_after = Pt(2)
        run(p, f"{chr(64 + _cnt['sub'])}. {text}", italic=True)


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
    k = 3.4 / sum(widths)
    widths = [w * k for w in widths]
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
            r.font.size = Pt(8)
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
run(p, "Project Phase 1 Report – Cryptography, BITS Pilani, Dubai Campus")
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "Ashmit Dhown (f20230205) · Srivathsa H Honyal (f20230198)", italic=True)

# ---------------- Abstract ----------------
para("**Abstract\u2014**ML-DSA (FIPS 204) is the NIST-standardised lattice-based digital signature, but it was designed for a single signer. "
     "Splitting the signing key among several parties, so that no single device holds the key, is hard because ML-DSA's "
     "rejection sampling and rounding steps do not combine well with secret sharing. In 2026 NIST opened a First Call for "
     "multi-party threshold schemes (IR 8214C), and four proposals aim to produce signatures that verify under an unmodified "
     "ML-DSA verifier: Mithril, Quorus, SplitForge/Trilithium and TALUS. This report surveys twenty-four papers and "
     "specifications covering these schemes, their predecessors, and the cryptanalytic tools (integer learning with errors, "
     "integer linear programming, regression) used to attack lattice signatures through leakage. The survey shows that "
     "earlier versions of TALUS fall to two practical key-recovery attacks, while no public attack on the other three exists, "
     "largely because they have not been systematically tested. We formulate four concrete open problems and propose a "
     "reusable leakage-testing harness that simulates each scheme's public transcripts, including aborted attempts, and runs "
     "a battery of statistical key-recovery tests against them.")

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
run(p, "Index Terms\u2014", bold=True, italic=True)
run(p, "ML-DSA, FIPS 204, threshold signatures, lattice cryptography, cryptanalysis, integer LWE, rejection sampling.", italic=True)
new = doc.add_section(WD_SECTION.CONTINUOUS)
cols = new._sectPr.xpath("./w:cols")
c = cols[0] if cols else OxmlElement("w:cols")
c.set(qn("w:num"), "2")
c.set(qn("w:space"), "360")
if not cols:
    new._sectPr.append(c)

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
     "that rejection sampling relies on; rounding is non-linear; and, as Section II-C shows, the lattice analogue of Feldman "
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
     "equation in the secret with small coefficients; this observation underlies the sample-count estimates in Section II-C. "
     "A pair of nonce and response is safe only because rejection sampling makes z's distribution independent of s1: "
     "z is accepted only when it lies in a box, and inside the box its distribution is uniform whichever s1 was used. Any "
     "threshold design that changes what is accepted, what is rejected, or what else is published must therefore re-establish "
     "this independence, and this is the property we test.")
para("**Survey methodology.** Sources were collected in three passes. First, the submissions page of the NIST First Call "
     "gave the four proposals and their preview writeups. Second, each proposal's ePrint or arXiv entry and its listed "
     "predecessors were followed, which produced the Mithril, Quorus, Trilithium, TALUS and Kao papers and the withdrawn "
     "preliminary versions. Third, searches for “Dilithium rejected signatures ILP”, “ILWE”, and “threshold "
     "lattice signatures” on ePrint, TCHES and proceedings of EUROCRYPT and ASIACRYPT surfaced the cryptanalytic literature. "
     "Inclusion required that a source either define a threshold ML-DSA construction, attack one, or supply a technique used by "
     "such an attack. Metadata of 22 of the 24 references were verified online by 1 October 2026; the two classical references "
     "(Shamir [21], Feldman [22]) are cited from memory and flagged for re-verification. The selection is deliberately weighted toward 2024–2026 "
     "because the area did not exist as a field before 2024.")
para("**Scope and honesty note.** This is a literature-and-specification assessment. Mithril, Quorus and Trilithium were "
     "studied through their abstracts, preview writeups and the descriptions in later papers; no scheme implementation code was run. "
     "The only experiment so far is a small simulation of the ILWE least-squares estimator on synthetic TALUS-style data (Section 3.5); "
     "it was not run against any scheme's reference code. Hypotheses below are labelled as such.")

# ---------------- Literature survey ----------------
heading("2. Literature Survey")
heading("2.1 Background: lattice signatures and threshold lattice signatures", 2)
para("Dilithium [2] introduced the signing structure above, and FIPS 204 [1] standardised it as ML-DSA with parameter sets "
     "ML-DSA-44/65/87 at NIST security categories 2/3/5. Threshold signatures for lattices were first built with heavy tools "
     "such as threshold homomorphic encryption: Gür, Katz and Silde [16] give a two-round scheme from threshold HE. Threshold "
     "Raccoon [14] (Eurocrypt 2024) takes a lighter route using only symmetric primitives and simple lattice operations, with "
     "one-time additive masks that stop partial signing keys leaking through partial signatures; however its signatures are "
     "not ML-DSA signatures. Del Pino and Niot [24] give a compact Raccoon-based threshold signature that is limited to 2^64 signatures and about 8 parties. Del Pino, Espitau, Niot and Prest [15] extend short-share distributed key generation with "
     "identifiable aborts and a detector for adversarial short-vector correlations (this preliminary version has since been "
     "withdrawn in favour of a later paper). The decisive shift is toward schemes whose output verifies under the unmodified "
     "FIPS 204 verifier, because deployed certificates, hardware and pinned keys cannot change.")

para("**Rounding functions that matter for the attacks.** ML-DSA compresses the public key by splitting each coefficient of "
     "t = A·s1 + s2 into high and low parts with Power2Round, t = t1·2^d + t0 with d = 13, and publishes only t1. During "
     "signing, Decompose splits w = A·y into w1 (high bits, hashed into the challenge) and a low part with bound γ2. A hint "
     "vector h lets the verifier recompute w1 from A·z − c·t1·2^d, which equals w − c·s2 + c·t0. The second check "
     "exists because if c·s2 pushed a coefficient of w across a rounding boundary, the verifier would recover the wrong w1. "
     "Two consequences are used repeatedly below. First, the quantity v = A·z − c·t1·2^d that every verifier computes "
     "equals w − c·(s2 − t0), so v is public and carries the term c·(s2 − t0). Second, when the second rejection "
     "check is enforced, the low part of w stays at distance at least β from the boundary, which is what makes the leaked "
     "noise uninformative; when it is removed or altered, that protection disappears.")

heading("2.2 The four First-Call ML-DSA proposals", 2)
para("**Mithril** [4,5,6,7] (PQShield, Brave, Bristol) is the first practical ML-DSA-compatible threshold scheme. It uses "
     "replicated secret sharing with short shares, so shares stay small enough for ML-DSA's norm bounds, and performs "
     "rejection sampling locally per party with hyperball sampling, avoiding a global abort MPC. Communication is about 1 MB per "
     "participant for up to six parties, with Go implementations; the security argument is a game-based reduction in the random "
     "oracle model to MLWE and ML-DSA unforgeability under static corruption of up to T−1 parties. There are no identifiable "
     "aborts, and its parameters target a per-attempt success probability of 1/2 rather than ML-DSA's roughly 1/4, so the accepted-"
     "response distribution differs from FIPS 204. Each party publishes a full MLWE-sample commitment (so the Gaussian-elimination attack on bare A\u00b7x does not apply) and responses are rejection-sampled over hyperballs. Its proof uses R\u00e9nyi divergence and therefore covers only Q_s = 2^50 signing queries, with K parallel repetitions per attempt to amplify the success probability. The earlier version [5] was superseded by [4], which appears at USENIX Security 2026; the preview writeup [7] notes that up to 8 parties remains practical, that no synchronised broadcast channel is needed, and that the Go implementation uses floating point for hyperball sampling.")
para("**Quorus** [8] (J.P. Morgan) modifies ML-DSA signing to be MPC-friendly while keeping FIPS 204 verification and "
     "signature sizes, and provides MPC protocols for honest-majority settings with about 150 KB online communication per party "
     "per rejection-sampling round (0.31–0.59 MB per successful signature, 16 or 29 online rounds depending on the variant) and appears at USENIX Security 2026. It tolerates fewer than n/2 corruptions, supports up to 63 parties in its benchmarks and is proven secure in the "
     "universal composability framework. Its MPC-friendly variant draws the nonce uniformly, adds a small noise term e_w to w, removes the signing loop and always outputs w1 even when (z, h) is rejected; this is exactly what lets the Fiat–Shamir hash be computed in the clear and what the proof of simulatability of rejected partial signatures relies on.")
para("**SplitForge / Trilithium** [9] (Cybernetica) targets two parties, a server and a phone, plus a correlated randomness "
     "provider (CRP). It proves security against a malicious server or phone in the UC model, uses an actively secure "
     "comparison protocol and a new rounding protocol, and has a Rust implementation. Key generation takes 3 rounds and each signing attempt 14; the protocol is given both for unmodified ML-DSA and for the Quorus-style variant with a CRP-supplied noise term e_w. It is part of Cybernetica's SplitKey submission [9], is secure against one malicious party among server, phone and CRP, and the writeup concedes that a malicious CRP can mount selective-disclosure attacks that the authors consider harmless for the intended use. It "
     "publishes the high bits w_H even for rejected attempts, and its security argument for this rests on an MLWR-type assumption that the "
     "paper itself calls non-standard for ML-DSA parameters (Quorus [8] describes the same point as a heuristic that a rejected partial "
     "signature can be simulated as uniform).")
para("**TALUS** [10,11] (Codebat) introduces the Boundary Clearance Condition (BCC): for a constant fraction of nonces "
     "(31.7% at ML-DSA-65, 43.2% at -44, 39.1% at -87) the vector s2 provably cannot push w across a rounding boundary, so rejection checks can be enforced "
     "offline on preprocessed nonces. This yields a TEE-assisted one-round variant (described in v0.22 only as a contrasting example, not proposed for the threshold setting) and a distributed MPC profile, the proposed system, with two online "
     "rounds. The paper states that its cap-based shield for the s2 channel is model-supported rather than proven. The same paper proves a lower bound: any FIPS-exact scheme revealing a summed (Irwin–Hall) nonce admits key "
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

para("**Numerical check of the sample estimate.** The estimate N ≈ 4γ2²/(3τ) can be evaluated directly from the "
     "parameters and reproduces the figures in [13]. Table I lists the values, which also show why ML-DSA-65 and -87 need about "
     "six and five times as many signatures as -44 even though their τ is larger.")
table([
    ["Set", "γ2", "τ", "4γ2²/(3τ)", "log2"],
    ["ML-DSA-44", "95,232", "39", "3.1 x 10^8", "28.2"],
    ["ML-DSA-65", "261,888", "49", "1.9 x 10^9", "30.8"],
    ["ML-DSA-87", "261,888", "60", "1.5 x 10^9", "30.5"],
], [1.1, 0.9, 0.5, 1.2, 0.6])
para("These are about 2^28 to 2^31 signatures, which is 2^12 to 2^15 times larger than TALUS's cap of 2^13 to 2^14 per key. "
     "The gap of 12 to 15 bits is the margin the unoptimised estimate leaves; whether an optimised estimator can close it is "
     "problem P1 in Section III. Two points deserve emphasis. The estimate treats the noise as Gaussian with the variance of a "
     "uniform distribution, which wastes the information in its sharp edges. And it recovers s′ one coefficient at a time, "
     "whereas lattice reduction can exploit the fact that s′ is short in every coordinate simultaneously.")

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

para("**Countermeasures studied in the literature.** The same papers discuss defences that inform design choices. For "
     "side-channel leakage, masking splits secrets into shares so that no single intermediate value correlates with the key, "
     "and shuffling randomises the order of coefficient operations; Damm et al. [19] show masking alone is insufficient when "
     "even a fraction of samples leak with low noise. For rejection-sampling leakage, the straightforward defence is to hide "
     "which check failed and to avoid releasing any value derived from a rejected response, which is why Quorus's choice to "
     "release (w1, c, ⊥) needs the careful simulation argument it provides. At protocol level, the TALUS authors' response "
     "limits the number of signatures per key, while Niot's remark [13] shows that merely restoring a removed check is not enough "
     "if a corrupted party can bias its nonce share. These defences have different costs: masking costs time, a signing cap "
     "costs key rotation, and hiding rejected transcripts costs interaction. Comparing them quantitatively is outside the "
     "scope of Phase 1, but the harness will produce the leakage measurements such a comparison needs.")

heading("2.5 Related and superseded work", 2)
para("The Mithril line began as a poster [6] and a preliminary ePrint [5] covering both ML-DSA and an enhanced Raccoon with "
     "identifiable aborts (up to 64 parties); the latter was later split into two papers, one of which is [4]. Kao's "
     "predecessor [12] is not itself a Call submission but shows the same patterns: its fully distributed profile P2 broadcasts "
     "masked commitments, and the paper's own remarks show an exposed λ_h·A·y_h yields y_h and then the key; masks hide "
     "these only when |S∖C| ≥ 2. The paper discloses this: at T = N with N−1 corruptions, mask hiding does not hold in P2, yet its Table 1 still claims dishonest-majority unforgeability (tolerating N−1 corruptions) with complete UC proofs against static adversaries. Whether the loss of mask hiding can be turned into key recovery, which would contradict that claim, is the open question we formulate as P4. "
     "Its Irwin–Hall analysis bounds the security loss by 0.013 bits per signing query, with the proved bound stated as non-vacuous "
     "for q_s < 16,000, whereas [10] later proves a passive attack near 2^30 signatures for any scheme revealing such a summed nonce.")

heading("2.6 Gap analysis", 2)
bullet("**No systematic public testing** of Mithril, Quorus or Trilithium transcripts, only design-level arguments.")
bullet("**TALUS's cap** rests on an information-theoretic argument, with a gap of about 2 bits to the authors' wall and about "
       "14–17 bits to Niot's unoptimised estimate, which an optimised bounded-noise or ILP estimator could close.")
bullet("**Rejected-attempt transcripts** (Quorus reveal-on-reject, Trilithium's uniform-rejected-partial heuristic) have no "
       "empirical leakage analysis in the literature we found.")
bullet("**Mithril's accepted-response distribution** (success probability 1/2) and its a posteriori key-sharing hint loss "
       "(7–12 bits reported) lack independent re-derivation; the proof covers only Q_s = 2^50 signing queries, below the 2^64 usually assumed for signatures.")
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
heading("2.8 Attack surface of each scheme (working hypotheses)", 2)
para("The following subsections record where we expect to look first. They are hypotheses derived from the specifications and "
     "later papers, not results.")
para("**Mithril.** (i) The accepted-response distribution: with success probability 1/2 per attempt instead of about 1/4, the "
     "nonce distribution and rejection region differ from FIPS 204, so the Renyi or Fisher-information loss must "
     "be computed concretely beyond the proven Q_s = 2^50 up to the 2^64 queries NIST typically assumes for signatures. (ii) A posteriori key sharing: the adversary obtains a noisy hint on the existing ML-DSA secret, "
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
para("**SplitForge / Trilithium.** The paper publishes w_H even in rejected runs and states openly that this needs an MLWR-type "
     "assumption, noting that related work either adds a noise term (as Quorus does), introduces a rejected-decisional assumption, "
     "or treats the question as open. This is the most attackable claim. Because the nonce y is fresh in every attempt, each "
     "published w_H is an LWR-style sample under a new secret, so any accumulation of information about s1 or s2 must come "
     "through the rejection events. The rejection-check result is declassified to both parties, so the bits revealed about c\u00b7s2 "
     "per attempt should be bounded. The correlated randomness provider is a trusted third party that, per the writeup, can mount "
     "selective-disclosure attacks the authors consider harmless, and the scheme is two-party only (2-of-2).")
para("**TALUS v0.22.** The signing cap is the whole security argument for the s2 channel. Under BCC the noise "
     "e = LowBits(w) is restricted to (−γ2+β, γ2−β), so it has sharp edges, which carry more information per sample than "
     "variance alone. Other surfaces are the zero-knowledge share well-formedness proofs, the blame procedure, quorum binding "
     "(a nonce-reuse observation was reported by S. Jo on an earlier version) and malicious nonce bias.")

heading("2.9 A reusable attack checklist", 2)
para("Generalising the observed attacks, we distilled ten questions that can be asked of any threshold ML-DSA design. They "
     "structure both the survey and the harness described in Section III.")
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

heading("2.10 Literature matrix", 2)
para("Table II rates every cited source for relevance (H = central, M = supporting, L = background) and marks the themes it "
     "covers: TS = threshold signatures, MD = ML-DSA compatible, AT = attack or leakage analysis, SS = secret sharing or MPC "
     "building block, RS = rejection sampling, ST = standard or specification.")
table([
    ["Ref", "Year", "Rel.", "TS", "MD", "AT", "SS", "RS", "ST"],
    ['[1] FIPS 204', '2024', 'H', '', 'x', '', 'x', '', 'x'],
    ['[2] Dilithium', '2018', 'M', '', 'x', '', 'x', '', ''],
    ['[3] IR 8214C', '2026', 'H', 'x', 'x', '', '', '', 'x'],
    ['[4] Mithril ePrint', '2026', 'H', 'x', 'x', '', 'x', 'x', ''],
    ['[5] Reloaded', '2025', 'M', 'x', 'x', '', '', 'x', ''],
    ['[6] Mithril poster', '2025', 'L', 'x', 'x', '', '', '', ''],
    ['[7] Mithril PW01', '2026', 'H', 'x', 'x', '', 'x', 'x', 'x'],
    ['[8] Quorus', '2025', 'H', 'x', 'x', '', 'x', 'x', ''],
    ['[9] Trilithium', '2025', 'H', 'x', 'x', '', 'x', 'x', ''],
    ['[10] TALUS', '2026', 'H', 'x', 'x', 'x', 'x', 'x', ''],
    ['[11] TALUS PW v0.22', '2026', 'H', 'x', 'x', 'x', 'x', 'x', 'x'],
    ['[12] Shamir nonce DKG', '2026', 'H', 'x', 'x', 'x', 'x', '', ''],
    ['[13] Niot attack', '2026', 'H', 'x', 'x', 'x', '', 'x', ''],
    ['[14] Threshold Raccoon', '2024', 'M', 'x', '', '', 'x', '', ''],
    ['[15] Lattice TS + IA', '2025', 'L', 'x', '', '', 'x', '', ''],
    ['[16] Gur et al.', '2024', 'L', 'x', '', '', 'x', '', ''],
    ['[17] ILWE / BLISS', '2018', 'H', '', '', 'x', '', '', ''],
    ['[18] Rejected sigs', '2025', 'H', '', 'x', 'x', '', 'x', ''],
    ['[19] Concealed ILWE', '2025', 'H', '', 'x', 'x', '', 'x', ''],
    ['[20] ILWE + rej. samp.', '2025', 'M', '', 'x', 'x', '', 'x', ''],
    ['[21] Shamir', '1979', 'L', '', '', '', 'x', '', ''],
    ['[22] Feldman', '1987', 'M', '', '', '', 'x', '', ''],
    ['[23] FROST', '2020', 'L', 'x', '', '', 'x', '', ''],
    ['[24] Finally!', '2025', 'M', 'x', '', '', 'x', '', ''],
], [1.5, 0.4, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3])
para("Of the 24 sources, 13 are rated central (H), 6 supporting (M) and 5 background (L). Sixteen were published in 2025 or 2026, "
     "and 22 of 24 are from 2018 or later. The sources marked AT are the evidence base for the estimators in Section III.")

para("**Recommendations that follow from the survey.** Four design rules emerge from the failures recorded in the literature. "
     "Do not publish any linear image of a secret or nonce under the public matrix, however it is masked, unless the mask "
     "remains hiding under the worst-case corruption allowed (checklist items 1 and 8). Treat the response nonce as a secret "
     "with the same status as the key, including in blame and abort procedures (item 2). Keep every rejection check that the "
     "single-signer scheme has, or prove that the replacement leaks no more (item 3). And bound the number of signatures per "
     "key only with a margin that an optimised estimator, not just least squares, cannot close (item 4). These rules are "
     "not new individually, but the First-Call submissions show they are easy to violate when importing patterns from "
     "discrete-log threshold schemes.")

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
para("The transcript is where the schemes differ most, so we summarise what each is claimed to publish beyond the final "
     "signature. These entries are taken from the sources as we read them and are to be checked against the full papers.")
table([
    ["Scheme", "Published beyond (c, z, h)", "Aborted attempts"],
    ["Mithril", "Round messages of the signing set; per-party commitments to w", "Visible to corrupted parties; no identifiable aborts"],
    ["Quorus", "MPC protocol messages; honest-majority broadcasts", "Releases (w1, c, ⊥)"],
    ["Trilithium", "Two-party messages; CRP-correlated values", "Declassified rejection bit; partial responses"],
    ["TALUS v0.22", "ZK well-formedness proofs; blame data on dispute", "Nonces pre-filtered offline; bound to quorum"],
], [0.9, 2.5, 2.1])
para("Two readings of this table guide the experiments. First, the right column determines whether rejected-attempt tests "
     "(P3) are meaningful for a scheme at all: TALUS filters offline, so its online transcripts have no rejected attempts and "
     "the relevant leakage is in the accepted values and the cap. Second, the middle column determines which items of the "
     "checklist apply, for instance item 1 (published A·x) is relevant wherever commitments to w or shares are broadcast, "
     "and is the first thing the harness tests on any new transcript format.")
heading("3.2 Open problems", 2)
para("**P1 (TALUS signing cap).** The authors [10] already price the s2 channel: below an integer-uniqueness wall q_uniq \u2248 2^15.2/2^16.4/2^16.2 the noisy observations O = r0 + c(t0 \u2212 s2) cannot by themselves determine s2, and the cap of 2^13\u20132^14 sits about two bits below it. Because the public key already determines s2, protection is computational: they model a syndrome meet-in-the-middle at cost 2^{H/2} with residual entropy H \u2265 502 (about 2^160), but the only proven floor is about 2^58/2^49 at ML-DSA-65/87 (below 128 bits), and ML-DSA-44 has no public cokernel (k = \u2113). Problem P1 is therefore to measure the true cost of recovering s\u2032 given at most 2^14 sharp-edged observations, with bounded-noise estimators, ILP and hint-integrating lattice estimators, and to compare it with the modelled and proven figures. A cost well below 2^128 at the cap would break the design; a cost near the model would give independent support for it.")
para("**P2 (Mithril accepted-response leakage).** Compute the Fisher information I about s1 carried by one accepted response z "
     "under Mithril's hyperball sampling and 1/2 acceptance, derive the attack wall ≈ 4/(I·τ), and compare it with the proven Q_s = 2^50 and the 2^64 usually assumed. "
     "Also re-derive the hardness loss of the a posteriori key-sharing hint using the exact share subset held by T−1 corrupted "
     "parties, with the lattice estimator.")
para("**P3 (Rejected-attempt leakage in Quorus, Trilithium and Mithril).** Quorus and Trilithium release the high bits w_H and the challenge c "
     "for rejected attempts, and Mithril releases each party's full commitment w_i = [A|I]\u00b7r_i (a complete MLWE sample, not a bare A\u00b7x) even when its partial response is rejected. Quorus adds a noise term e_w to w so that this is provably simulatable, while Trilithium keeps unmodified "
     "ML-DSA and relies on an MLWR-type assumption. Test whether the rejected-attempt transcripts, together with the accept or "
     "reject bit, carry any dependence on s1 or s2, using regression and ILP-style tests, and quantify the hardness of the "
     "underlying rounding instances with the lattice estimator. A positive result in Trilithium would show the assumption fails at "
     "ML-DSA parameters; a null result bounds it. The rejection bit declassified in Trilithium should also be quantified in bits per attempt about c\u00b7s2.")
para("**P4 (Kao's P2 profile).** The paper [12] states that in profile P2 the broadcast commitments are hidden only when |S\u2216C| \u2265 2, and its own Remark 15 argues that an exposed \u03bb_h\u00b7A\u00b7y_h gives y_h by linear algebra and then s_{1,h} = c\u207b\u00b9(z_h \u2212 y_h). With |S| = T and T\u22121 corrupted parties inside S we have |S\u2216C| = 1, so by the paper's own argument the key would fall, yet Table 1 credits P2 with dishonest-majority unforgeability. Decide whether P2 is secure only for |S| \u2265 T+1, and whether the Feldman-style DKG commitments show the A\u00b7s1,i pattern broken in [13] (the paper itself uses a trusted dealer for key generation).")
para("**Hypotheses and success criteria.** For each problem we state what would count as a result. For P1 we hypothesise that a "
     "hint-aware estimators beat the least-squares sample estimate by a wide margin, and the criterion is a "
     "measured work cost for recovering s\u2032 at 2^14 observations, checked by recovering the key against the public key at reduced parameters. For P2 we hypothesise that the Fisher "
     "information per signature is small enough that the wall exceeds 2^64 (well above the proven 2^50), so a null result is the expected outcome and the "
     "criterion is a numerical bound with its derivation. For P3 we hypothesise that Quorus's reveal-on-reject is simulatable "
     "as claimed because of the added noise, while Trilithium's MLWR-type assumption may only hold approximately, and the criterion is a statistical "
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
     "whose ordinary least-squares solution has per-coefficient error variance about σ_e²/(N·τ), because the denominator "
     "concentrates at N·τ and the numerator has variance N·τ·σ_e². For uniform noise on [−γ2, γ2] with σ_e² ≈ γ2²/3, nearest-integer "
     "rounding recovers a coefficient once the standard deviation σ_e/√(N·τ) drops below 1/2; this gives "
     "N ≈ 4γ2²/(3τ) as derived in [13]. Our first experiment checks this "
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
     "rather than relying on a Gaussian approximation, and report the resulting wall in bits to compare with the proven 2^50 and the assumed 2^64.")
para("**Hint accounting.** For schemes where the adversary holds partial information about the secret (Mithril's share subsets), "
     "we model the information as additional linear equations or a modified distribution on the secret and feed it to a lattice "
     "estimator to measure the loss in bits of security, as opposed to treating the instance as fresh MLWE.")

para("**Simulator walkthrough (TALUS-style, accepted attempt).** To make the interface concrete, the simulator for a TALUS-like "
     "scheme performs the following steps per signature. (1) Sample the aggregate nonce y from the scheme's distribution, "
     "keeping only nonces that satisfy the boundary clearance condition. (2) Compute w = A·y and w1 = HighBits(w). (3) Derive "
     "c from a random message and w1. (4) Compute z = y + c·s1 and apply the first rejection check. (5) Emit the public "
     "record (c, z, h), plus whatever the scheme additionally broadcasts, together with a ground-truth tag. The estimator "
     "receives only the public record. A corrupted-coalition variant additionally emits the internal shares of the "
     "corrupted parties. For schemes with aborted attempts, step (4) emits a record flagged as rejected together with exactly "
     "the fields the specification says are revealed, no more.")
para("**Evaluation metrics.** We report (i) the minimum sample count at which the full secret is recovered with probability "
     "at least 0.9 over repeated runs; (ii) the fraction of coefficients recovered as a function of sample count; (iii) for "
     "statistical tests, the p-value or test statistic against the null of independence from the secret, with the number of "
     "samples; and (iv) cost, measured as CPU time and memory. Recovery is verified against the public key, so a claimed "
     "recovery can be checked by anyone: given a candidate s1, compute t and compare. This avoids the common problem of "
     "reporting partial correlations as breaks.")
para("**Threats to validity.** Internal threats include bugs in the primitives (mitigated by known-answer tests) and "
     "estimator tuning that overfits to synthetic keys (mitigated by testing on many random keys). External threats include "
     "differences between the simulated protocol and the real one, and parameter changes between preview writeups and final "
     "packages. Construct threats include treating least-squares success as the only measure of leakage, since a scheme "
     "can leak information that a particular estimator misses; for this reason several estimators are run on every "
     "transcript type, and negative results are phrased as bounds on what was tried.")

heading("3.5 Experimental design and validation", 2)
para("Every experiment reports four quantities: the number of signatures consumed, the recovered key fraction, wall-clock cost, "
     "and the parameter set. Validation proceeds in three stages. (a) Primitives are checked against FIPS 204 known-answer tests, "
     "so that a harness that cannot sign like ML-DSA cannot be mistaken for evidence about it. (b) Each simulator is checked by "
     "recovering a key from a deliberately leaky variant (for example publishing A·y), to confirm the estimators have power. "
     "(c) Null results are reported with the sample budget and an explicit statement of which attack classes were tried. We "
     "start at reduced dimensions to validate scaling laws, then move to full parameter sets, with the largest runs "
     "vectorised or written in a compiled language. The schedule follows the order in the roadmap: harness and sanity check, "
     "TALUS cap, Mithril, Quorus and Trilithium, Kao's claims, and finally reruns on reference code when packages are published.")
para("**Preliminary result.** A first harness (18 unit tests) simulates b = −c·s + e, e = LowBits(w), for ML-DSA-44 and recovers s by "
     "least squares. Measured error matches γ2/√(3τN) within 3% (N = 5,000 to 160,000). Extrapolating, rounding all 1,024 coefficients "
     "of s2 needs about 3.6×10^9 signatures (50% success), roughly 12 times the 4γ2²/(3τ) formula. This model ignores t0, bounded noise "
     "and lattice reduction and does not reproduce Niot's derivation [13]; read the formula as an order of magnitude.")
para("**Expected outcomes and risks.** Positive results are attacks or concrete margins; negative results are bounded "
     "statements of the form “no leakage detected with q samples”, which are still useful evidence. Risks: billion-sample "
     "experiments need vectorised or compiled inner loops; simulators may deviate from the true protocols if our reading of "
     "unread papers is wrong; and Mithril, whose team includes the author of [13], is likely already hardened against these "
     "patterns. Any finding should be shared with the scheme teams before publication, and posted to ePrint following standard "
     "responsible-disclosure practice.")

para("**Expected contributions.** If the project succeeds, it yields three kinds of artefact. A reusable open-source harness "
     "with validated ML-DSA primitives and a scheme-simulator interface, so that new threshold designs can be screened "
     "in hours rather than weeks. A set of measured margins and bounds for the four proposals, expressed in bits of "
     "security and in signatures, so that NIST and the teams can compare designs on the same scale. And a verified or "
     "refuted statement about Kao's P2 profile [12], which matters because TALUS builds on it. Even when no attack is found, "
     "the checklist and the measurements give the community a concrete way to assess how much testing each scheme has "
     "received, which is currently missing for three of the four proposals.")

heading("3.6 Limitations of this survey and Phase 2 plan", 2)
para("The survey has three limitations that bear on how its conclusions should be read. First, the full Mithril, Quorus and "
     "Trilithium papers were not read end to end; for Quorus and Trilithium in particular, claims about reveal-on-reject and "
     "the rejected-partial heuristic come from abstracts and from how other papers describe them, so every statement in "
     "Section II-H is a hypothesis to verify against the primary text. Second, several sources are preview writeups or "
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
para("A secondary outcome is educational and methodological: the checklist in Section II-I and the harness together "
     "provide a quick screening procedure that a designer can run on a new threshold ML-DSA variant before submitting it. "
     "Because several of the observed failures came from importing patterns from discrete-log protocols, a screening tool "
     "that encodes the lattice-specific pitfalls (invertible commitments, nonce leakage, removed rejection checks) has value "
     "beyond the four schemes studied here.")

# ---------------- Conclusion ----------------
heading("4. Conclusion")
para("Threshold ML-DSA is moving from research to standardisation, and the single published break of an early TALUS version "
     "shows how easily thresholding can leak a key through commitments or removed rejection checks. The survey of twenty-four "
     "sources identifies three schemes without public attacks only because they are untested, one scheme whose security now rests "
     "on a signing cap with an uncertain margin, and a toolbox (ILWE, ILP, robust regression) mature enough to test them. We "
     "formalised four open problems and proposed a leakage-testing harness as a reusable contribution. Phase 2 will implement the "
     "harness, reproduce the TALUS attack, and run the estimators on the remaining schemes.")

# ---------------- References ----------------
para("**Why the open problems are tractable in a course-scale project.** Each of P1–P4 reduces to a bounded computation. "
     "P1 needs a simulator that emits (c, v) pairs and an estimator, both of which are linear-algebra code that runs on a laptop "
     "at reduced dimension and on a workstation at full dimension. P2 is a numerical integral over the acceptance region of "
     "the hyperball sampler followed by a lattice-estimator call. P3 is a two-sample test on transcript statistics. P4 is algebra "
     "on a published protocol and a small toy implementation. None requires access to proprietary code or hardware, "
     "and none depends on solving a hard lattice problem at full security parameters, because the attacks of interest "
     "exploit leakage rather than breaking MLWE. The main resource is therefore careful engineering and sample budget, "
     "not new mathematics, which keeps the project feasible while still addressing questions that the designers' own "
     "papers leave open.")
para("**Positioning against existing work.** Prior cryptanalysis of lattice signatures [17]–[20] targets a single signer "
     "whose implementation leaks through a physical side channel. Here the leakage is logical: it is part of the protocol "
     "transcript, visible to any observer or corrupted party, and independent of hardware. This changes both the threat model, "
     "where the adversary is a protocol participant, and the estimators, where the noise distribution is known exactly "
     "from the specification rather than measured. It also means results transfer across implementations, which is why a "
     "specification-level harness is more valuable than any single code audit. Conversely, schemes that were analysed only "
     "by proof, such as Quorus and Trilithium, gain an independent empirical check that proofs alone cannot provide.")
para("**Summary of findings by research question.** The survey was guided by four questions. (RQ1) Which threshold ML-DSA "
     "designs exist and how do they differ? Four First-Call proposals, distinguished by corruption model, party count and round "
     "complexity (Table of Section II-B). (RQ2) Which are known to be broken? Earlier TALUS versions, by two independent "
     "attacks [13]; none of the others in public. (RQ3) Which techniques can break a scheme of this kind? Linear inversion "
     "of published A·x, nonce-leak recovery, ILWE by least squares, ILP on rejection bounds and robust regression "
     "([13], [17]–[19]). (RQ4) Where is the evidence thinnest? In heuristics (Trilithium), margins (TALUS cap), and "
     "distributional deviations (Mithril). These answers directly produce the four open problems of Section III and the "
     "ordering of the Phase 2 plan.")
para("**Phase 2 milestones and acceptance tests.** Phase 2 is organised so that each milestone has a pass/fail test. "
     "M1: the primitives reproduce FIPS 204 known-answer vectors for all three parameter sets. M2: a deliberately leaky "
     "scheme (publishing A·s1) is broken in one signature by the Gaussian-elimination estimator. M3: the TALUS-without-check "
     "simulator is broken by least squares at a sample count that matches the measured error law γ₂/√(3τN); a preliminary run shows that rounding every coefficient of s2 needs about 12 times the Table I formula for ML-DSA-44, so M3 must explain this gap, at reduced "
     "parameters. M4: the bounded-noise estimator beats least squares by the stated margin or the report explains why not. "
     "M5 and M6: simulators for Mithril, Quorus and Trilithium produce transcripts that follow the specifications, as "
     "checked by an independent reading of each paper. M7: the written results state, for each scheme, either an attack or a "
     "bound. Failing M1 or M2 stops the project until fixed, because later results would be untrustworthy; failing "
     "M4 is itself an informative outcome. This staging also gives an early signal if the schedule slips.")
heading("References")
refs = [
    ("NIST", "FIPS 204: Module-Lattice-Based Digital Signature Standard", "Aug. 2024."),
    ("L. Ducas, E. Kiltz, T. Lepoint, V. Lyubashevsky, P. Schwabe, G. Seiler, and D. Stehl\u00e9", "CRYSTALS-Dilithium: A lattice-based digital signature scheme", "IACR Trans. Cryptogr. Hardw. Embed. Syst., vol. 2018, no. 1, pp. 238\u2013268, 2018."),
    ("NIST", "Multi-Party Threshold Schemes: First Call for Submissions", "NIST IR 8214C, 2026."),
    ("S. Celi, R. del Pino, T. Espitau, G. Niot, and T. Prest", "Efficient threshold ML-DSA", "in Proc. USENIX Security Symp., 2026 (full version: IACR ePrint 2026/013)."),
    ("G. Borin, S. Celi, R. del Pino, T. Espitau, G. Niot, and T. Prest", "Threshold signatures reloaded: ML-DSA and enhanced Raccoon with identifiable aborts", "IACR ePrint 2025/1166, 2025 (withdrawn May 2026)."),
    ("S. Celi et al.", "Poster: Efficient threshold ML-DSA up to 6 parties", "in Proc. ACM CCS, 2025, doi:10.1145/3719027.3760739."),
    ("S. Celi, G. Delerue, R. del Pino, T. Espitau, G. Niot, and T. Prest", "Mithril: Efficient threshold ML-DSA from secret sharing with short shares", "NIST MPTC First Call preview writeup v1.0, Jan. 2026."),
    ("A. Bienstock, L. de Castro, D. Escudero, A. Polychroniadou, and A. Takahashi", "Quorus: Efficient, scalable threshold ML-DSA signatures from MPC", "in Proc. USENIX Security Symp., 2026 (full version: IACR ePrint 2025/1163)."),
    ("A. Dufka, S. Kravt\u0161enko, P. Laud, and N. Snetkov", "Trilithium: Efficient and universally composable distributed ML-DSA signing", "IACR ePrint 2025/675, 2025; see also SplitForge, SplitKey preview writeup v0.1, NIST MPTC, Jan. 2026."),
    ("L. Kao and R. Chang", "TALUS: FIPS-204-exact threshold ML-DSA via boundary clearance", "arXiv:2603.22109, 2026."),
    ("L. Kao and R. Chang", "TALUS: FIPS-204-exact threshold ML-DSA via boundary clearance (preview writeup v0.22)", "NIST MPTC First Call, Aug. 2026."),
    ("L. Kao", "FIPS 204-compatible threshold ML-DSA via Shamir nonce DKG", "arXiv:2601.20917, 2026."),
    ("G. Niot", "Key-recovery attacks on TALUS: A cryptanalytic note", "IACR ePrint 2026/1386, Jul. 2026."),
    ("R. del Pino, S. Katsumata, M. Maller, F. Mouhartem, T. Prest, and M.-J. Saarinen", "Threshold Raccoon: Practical threshold signatures from standard lattice assumptions", "in Proc. EUROCRYPT 2024, LNCS 14652, 2024."),
    ("R. del Pino, T. Espitau, G. Niot, and T. Prest", "Simple and efficient lattice threshold signatures with identifiable aborts", "IACR ePrint 2025/871, 2025 (withdrawn May 2026)."),
    ("K. D. G\u00fcr, J. Katz, and T. Silde", "Two-round threshold lattice-based signatures from threshold homomorphic encryption", "in Proc. PQCrypto 2024, LNCS 14772, 2024."),
    ("J. Bootle, C. Delaplace, T. Espitau, P.-A. Fouque, and M. Tibouchi", "LWE without modular reduction and improved side-channel attacks against BLISS", "in Proc. ASIACRYPT 2018, LNCS 11272, pp. 494\u2013524, 2018."),
    ("Y. Zhou, W. Wang, Y. Sun, and Y. Yu", "Rejected signatures\u2019 challenges pose new challenges: Key recovery of CRYSTALS-Dilithium via side-channel attacks", "IACR Trans. Cryptogr. Hardw. Embed. Syst., 2025 (ePrint 2025/214)."),
    ("S. Damm et al.", "Solving concealed ILWE and its application for breaking masked Dilithium", "in Proc. ASIACRYPT 2025 (ePrint 2025/1629)."),
    ("K. Yates, A. Pierrottet, A. Al Mamun, R. Cartor, M. Chowdhury, and S. Gao", "Security analysis of integer learning with errors with rejection sampling", "arXiv:2512.08172, Dec. 2025."),
    ("A. Shamir", "How to share a secret", "Commun. ACM, vol. 22, no. 11, pp. 612\u2013613, 1979."),
    ("P. Feldman", "A practical scheme for non-interactive verifiable secret sharing", "in Proc. IEEE FOCS, 1987, pp. 427\u2013438."),
    ("C. Komlo and I. Goldberg", "FROST: Flexible round-optimized Schnorr threshold signatures", "in Proc. SAC 2020, LNCS 12804, 2021, pp. 34\u201365."),
    ("R. del Pino and G. Niot", "Finally! A compact lattice-based threshold signature", "in Proc. PKC 2025, Part III, LNCS 15676, 2025, pp. 169\u2013199."),
]
for i, (au, ti, ve) in enumerate(refs, 1):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.3)
    p.paragraph_format.space_after = Pt(1)
    for txt, it in ((f"[{i}] {au}, \u201c{ti},\u201d ", False), (ve, True)):
        run(p, txt, italic=it).font.size = Pt(8)

doc.save("Phase1_Report.docx")
print("saved")
