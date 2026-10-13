"""Builds report/Phase1_Report.docx. Run: python build_report.py

Revised 13 Oct 2026: instructor feedback applied and Phase 2 results added.
Numbers in Sections IV-V come from docs/ROADMAP.md, docs/LEARN.md and experiments/results/*.
"""
import json
import re
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.section import WD_SECTION

RES = Path(__file__).resolve().parent.parent / "experiments" / "results"

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


ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
_cnt = {"sec": 0, "sub": 0, "tab": 0, "fig": 0}


def heading(text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    text = re.sub(r"^\d+(\.\d+)?\.? ", "", text)
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


def caption(kind, text):
    """IEEE-style caption: 'TABLE I' above tables, 'Fig. 1.' below figures (8 pt)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    if kind == "tab":
        _cnt["tab"] += 1
        p.paragraph_format.keep_with_next = True
        run(p, f"TABLE {ROMAN[_cnt['tab'] - 1]}. ", bold=False).font.size = Pt(8)
        run(p, text).font.size = Pt(8)
    else:
        _cnt["fig"] += 1
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(5)
        run(p, f"Fig. {_cnt['fig']}. ").font.size = Pt(8)
        run(p, text).font.size = Pt(8)


def table(rows, widths, cap=None):
    if cap:
        caption("tab", cap)
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


def figure(path, width, cap):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Inches(width))
    caption("fig", cap)


# Least-squares experiment numbers are read from the result file, never typed in.
LS = json.load(open(RES / "ls_error_vs_N.json"))
_ratios = [r["rms_mean"] / (95232 / (3 * 39 * r["N"]) ** 0.5) for r in LS["rows"]]
LS_DEV = max(abs(x - 1) for x in _ratios) * 100

# ---------------- Title ----------------
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "Breaking the Threshold: A Systematic Cryptanalysis of Threshold ML-DSA "
       "Submissions to the NIST Multi-Party Threshold Call", bold=True).font.size = Pt(14)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "Phase 1 Report (revised, with Phase 2 results) – Cryptography, BITS Pilani, Dubai Campus")
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "Ashmit Dhown (f20230205) · Srivathsa H Honyal (f20230198)", italic=True)

# ---------------- Abstract ----------------
para("**Abstract—**ML-DSA (FIPS 204) is the NIST-standardised lattice-based digital signature, designed for a single "
     "signer. Splitting its key among several parties is hard because rejection sampling and rounding do not combine well "
     "with secret sharing. NIST's 2026 First Call for multi-party threshold schemes (IR 8214C) has four proposals whose "
     "signatures verify under an unmodified ML-DSA verifier: Mithril, Quorus, SplitForge/Trilithium and TALUS. We survey "
     "twenty-four sources on these schemes and on leakage attacks against lattice signatures, and make the TALUS per-key "
     "signing cap our core problem. A leakage-testing harness built in Phase 2 (ML-DSA passing 81 NIST ACVP vectors, scheme "
     "views, least-squares, bounded-noise and integer-programming estimators) recovers the TALUS s2 channel secret of one "
     "ML-DSA-44 ring element from about 7×10^4 signatures (2^16.1), which is 3.1 bits above the cap and 0.9 bits above the "
     "authors' uniqueness wall in our channel model: a thinner margin, not a break. Controls give 9/9 recoveries on a leaky "
     "variant and 0/18 false keys on genuine ML-DSA. Along the way we reproduce both published attacks on an early TALUS "
     "version and find a parameter-proof gap in Mithril and a one-signature key exposure in a predecessor design; the "
     "latter two await coordinated disclosure.")

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
run(p, "Index Terms—", bold=True, italic=True)
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
     "and was not altered. RSA and ECDSA would be broken by a large quantum computer, so NIST standardised post-quantum "
     "replacements. ML-DSA, specified in FIPS 204 [1] and derived from CRYSTALS-Dilithium [2], is the primary choice; its "
     "security rests on the lattice problems Module-LWE (learning with errors) and Module-SIS.")
para("**How ML-DSA signs.** Intuitively, the signer hides its secret inside a random-looking answer and throws the answer "
     "away whenever it might give the secret away. Formally, all arithmetic is in the ring R_q = Z_q[X]/(X^n+1): polynomials "
     "of degree below n = 256 with coefficients modulo the prime q = 8380417. A is a public k×ℓ matrix of such polynomials. "
     "The secret key is a pair of short vectors (s1, s2) whose coefficients lie in [−η, η], and the public key is "
     "t = A·s1 + s2, of which only the high part t1 is published (t = t1·2^d + t0 with d = 13 dropped bits t0). To sign, "
     "the signer samples a random nonce y with coefficients below γ1, computes w = A·y and its high bits w1 = HighBits(w), "
     "derives a challenge c = H(msg, w1), a polynomial with exactly τ coefficients equal to ±1 and the rest 0, and outputs "
     "z = y + c·s1 with a short hint h. Here ‖x‖∞ denotes the largest absolute coefficient of x, and β = τ·η bounds "
     "‖c·s‖∞ for any secret s. Two rejection checks are applied: ‖z‖∞ < γ1 − β, which hides s1, and "
     "‖LowBits(w − c·s2)‖∞ < γ2 − β, which hides s2 (γ2 is the rounding range of LowBits). If either fails the "
     "signer restarts with a fresh y. This “Fiat–Shamir with aborts” structure makes accepted signatures statistically "
     "independent of the key. Table I lists the parameter values.")
table([
    ["Set", "NIST cat.", "(k, ℓ)", "η", "τ", "γ1", "γ2"],
    ["ML-DSA-44", "2", "(4, 4)", "2", "39", "2^17", "(q−1)/88"],
    ["ML-DSA-65", "3", "(6, 5)", "4", "49", "2^19", "(q−1)/32"],
    ["ML-DSA-87", "5", "(8, 7)", "2", "60", "2^19", "(q−1)/32"],
], [1.5, 0.7, 0.8, 0.4, 0.4, 0.6, 1.0], "ML-DSA parameter sets [1]")
para("**Why rejection makes signatures safe.** Picture z as a point in a box. Because y is uniform on a box of half-width "
     "γ1 and c·s1 is a small shift of at most β, every point inside the smaller box of half-width γ1 − β is equally likely "
     "whichever s1 was used; accepting only those points therefore hides s1 completely. Because c has only τ nonzero "
     "entries, anything that does leak gives the attacker one noisy linear equation with small coefficients per signature, "
     "which underlies all the sample counts below. Any threshold design that changes what is accepted, what is rejected or "
     "what else is published must re-establish this independence, and this is the property we test.")
para("**Why thresholding is hard.** In a (T, N) threshold scheme any T of N parties can sign and fewer than T learn nothing. "
     "Shamir secret sharing [21] hides a secret as the constant term of a random degree-(T−1) polynomial; Feldman [22] adds "
     "commitments g^{a_i} to its coefficients; threshold Schnorr schemes such as FROST [23] simply add partial signatures. "
     "ML-DSA breaks all three conveniences: shares of a short secret are not short; HighBits is not additive, so parties cannot "
     "round their own pieces of w; the s2 check needs the full secret; and the lattice analogue of a Feldman commitment, A·x, "
     "is not hiding (Section II-C). Two facts drive most attacks below. A is tall (k ≥ ℓ), so publishing A·x reveals x by "
     "Gaussian elimination. And z = y + c·s1 holds over the integers, so any leak of the nonce y gives s1 = c⁻¹(z − y).")
para("**Why now, and what this report contributes.** NIST's First Call (IR 8214C) [3] expects preliminary packages from late "
     "2026 and full packages not before March 2027, so scrutiny is most useful now. Following the Phase 1 review, the core "
     "problem is the TALUS signing cap (P1); the Mithril, rejected-attempt and Kao questions (P2–P4) are stretch goals. We "
     "give (i) a survey of the four proposals and the attack toolbox, (ii) the problem formulation, (iii) a working "
     "leakage-testing harness (Fig. 1) and (iv) its Phase 2 results with trial counts and seeds.")
para("**Survey method.** Sources came from the First Call submissions page, the proposals' ePrint/arXiv entries and their "
     "predecessors, and searches of ePrint, TCHES, EUROCRYPT and ASIACRYPT (“Dilithium rejected signatures ILP”, “ILWE”, "
     "“threshold lattice signatures”). A source was kept if it defines, attacks or supplies a technique against a threshold "
     "ML-DSA design. Metadata of all references were verified online (Shamir [21] and Feldman [22] against Crossref).")
para("**Scope and honesty note.** Quorus [8] and Trilithium [9] were read in full; Mithril [4] in full except Appendices D, E "
     "and most of G; Kao [12] main text and Appendices B–O. Our own harness code was run (Section IV); the schemes' reference "
     "code was not, except the Mithril authors' parameter script. Every TALUS number relies on our channel model, because "
     "the v0.22 writeup does not list the values released per signature. Results are labelled as measured, derived or hypothesis.")

# ---------------- Literature survey ----------------
heading("2. Literature Survey")
heading("2.1 Background", 2)
para("Dilithium [2] introduced the signing structure above and FIPS 204 [1] standardised it. Early lattice threshold "
     "signatures used threshold homomorphic encryption (Gür, Katz and Silde [16]); Threshold Raccoon [14] uses only "
     "symmetric primitives and one-time additive masks but does not output ML-DSA signatures; del Pino and Niot [24] give a "
     "compact Raccoon-based scheme limited to 2^64 signatures and about 8 parties. An earlier preprint on identifiable "
     "aborts [15] is withdrawn and listed for history only. The decisive shift is toward output that verifies under the "
     "unmodified FIPS 204 verifier, because deployed certificates and pinned keys cannot change.")
para("**Rounding and the public value v.** A hint lets the verifier recompute w1 from v = A·z − c·t1·2^d. Substituting "
     "z = y + c·s1 shows v = w − c·(s2 − t0), so v is public and carries the term c·s′ with s′ = s2 − t0. The second "
     "rejection check keeps LowBits(w) at least β away from a rounding boundary, so v reveals nothing; once the check is "
     "removed or altered, that protection disappears.")

heading("2.2 The four First-Call ML-DSA proposals", 2)
para("**Mithril** [4,6,7] (PQShield, Brave, Bristol; USENIX Security 2026) uses replicated secret sharing with short shares "
     "and local rejection with hyperball (Euclidean-ball) sampling, about 1 MB per participant for up to six parties, with "
     "a Go implementation. Security is a game-based reduction to MLWE and ML-DSA unforgeability under static corruption of "
     "up to T−1 parties, without identifiable aborts. Each attempt succeeds with probability about 1/2 (ML-DSA: about 1/4), "
     "with K parallel repetitions, and each party publishes a full MLWE-sample commitment, so the bare-A·x attack does not "
     "apply. The proof uses Rényi divergence and covers Q_s = 2^50 signing queries. The superseded version [5] is not relied on. "
     "The preview writeup [7] adds that up to 8 parties remain practical, that no synchronised broadcast channel is needed, "
     "and that the Go code uses floating point for hyperball sampling.")
para("**Why local rejection is delicate.** Single-signer ML-DSA accepts a nonce only if both checks pass, about 1/4 of the "
     "time. With N parties each holding a short additive share, the sum of their responses must land in the same box, but "
     "no party knows the sum. Mithril lets each party sample its nonce share from a hyperball, so the aggregate has a "
     "predictable norm, and decides acceptance locally. The accepted responses are then close to, but not exactly, the "
     "FIPS 204 distribution; how close is a quantitative question (problem P2), not a bug.")
para("**Quorus** [8] (J.P. Morgan; USENIX Security 2026) modifies signing to be MPC-friendly while keeping FIPS 204 "
     "verification: the nonce is uniform, a small noise term e_w is added to w, and w1 is output even when (z, h) is "
     "rejected. It tolerates fewer than n/2 corruptions, is proven in the universal composability (UC) framework, and costs "
     "about 150 KB per party per attempt (0.31–0.59 MB per signature, 16 or 29 rounds), benchmarked up to 63 parties. "
     "Always releasing w1 lets the Fiat–Shamir hash be computed in the clear; the proof that rejected partial signatures "
     "can be simulated relies on the noise e_w.")
para("**SplitForge / Trilithium** [9] (Cybernetica) targets a server and a phone plus a correlated randomness provider (CRP). "
     "It is UC-secure against one malicious party among the three, takes 14 rounds per signing attempt, and publishes the "
     "high bits w_H even for rejected attempts, justified by an MLWR-type assumption that the paper itself calls "
     "non-standard for ML-DSA parameters. It uses an actively secure comparison protocol and a new rounding protocol, has a "
     "Rust implementation, is given both for unmodified ML-DSA and for a Quorus-style variant with CRP-supplied noise e_w, "
     "and is part of Cybernetica's SplitKey submission. The writeup concedes that a malicious CRP can mount "
     "selective-disclosure attacks that the authors consider harmless for the intended use.")
para("**TALUS** [10,11] (Codebat) introduces the Boundary Clearance Condition (BCC): for a constant fraction of nonces (43.2%, "
     "31.7% and 39.1% at ML-DSA-44/65/87) s2 provably cannot push w across a rounding boundary, so rejection can be done "
     "offline on preprocessed nonces, giving a two-round distributed MPC profile. The paper states that its cap-based shield "
     "for the s2 channel is model-supported rather than proven, and proves that any FIPS-exact scheme revealing a summed "
     "(Irwin–Hall) nonce admits key recovery after about 2^30 signatures. A TEE-assisted one-round variant appears in v0.22 "
     "only as a contrasting example. TALUS builds on Kao's Shamir nonce DKG [12], where the signing nonce is itself "
     "Shamir-shared with pairwise-cancelling PRF masks and claimed nonce-share min-entropy above 5× the key entropy for "
     "signing sets up to 17.")
table([
    ["Scheme", "Design", "Trust / corruption", "Rounds", "Public attacks"],
    ["Mithril [4]", "Replicated short shares, local rejection", "Dishonest majority (T−1), static; N ≤ 6", "~3 per attempt", "None found"],
    ["Quorus [8]", "MPC-friendly ML-DSA variant", "Honest majority, UC, n ≤ 64", "16–29", "None found"],
    ["Trilithium [9]", "2-party MPC + CRP", "CRP honest; one party malicious", "14 per attempt", "None; MLWR-type assumption"],
    ["TALUS [10,11]", "BCC nonce filtering, Shamir nonce DKG", "Honest majority N ≥ 2T−1", "2 (v0.22)", "Earlier versions broken [13]"],
], [1.0, 1.9, 1.7, 0.9, 1.3], "The four ML-DSA-compatible First-Call proposals")

heading("2.3 Published attacks on TALUS", 2)
para("Niot [13] (ePrint 2026/1386) gives two practical attacks on earlier TALUS versions. **Attack 1** exploits non-hiding "
     "commitments: TALUS-MPC broadcast A·s1,i at key generation and A·ŷ in the blame phase. A is left-invertible except with "
     "probability at most 2^-15 (ML-DSA-44) or 2^-38 (-65/-87), so x = A⁺(A·x) reveals every key share and the nonce, and "
     "s1 = c⁻¹(z − y) follows from one signature. **Attack 2** targets the removed s2 check. Intuitively, every signature "
     "reveals a very noisy linear equation in the secret, and enough of them average the noise away. Precisely, with "
     "HighBits(w) known from the hint, the observable is b = −c·s′ + e with e = LowBits(w) roughly uniform on [−γ2, γ2]. "
     "This is integer LWE (ILWE, LWE without reduction mod q), which least squares solves [17]: the per-coefficient error "
     "is about σ_e/√(Nτ) with σ_e² ≈ γ2²/3, and rounding succeeds once this is below 1/2, so")
para("N ≈ 4γ2²/(3τ)  signatures,                                                  (1)", align=WD_ALIGN_PARAGRAPH.CENTER)
para("about 2^28–2^31 (Table III). Niot stresses that (1) is unoptimised, and that reinstating the check is not enough "
     "because a corrupted party can bias its nonce share (e.g. y_i = 0) so the check always passes.")
table([
    ["Set", "γ2", "τ", "4γ2²/(3τ)", "log2"],
    ["ML-DSA-44", "95,232", "39", "3.1 x 10^8", "28.2"],
    ["ML-DSA-65", "261,888", "49", "1.9 x 10^9", "30.8"],
    ["ML-DSA-87", "261,888", "60", "1.5 x 10^9", "30.5"],
], [1.1, 0.9, 0.5, 1.2, 0.6], "Least-squares sample estimate (1) per parameter set")
para("The authors' response (v0.22 [11]) replaces commitments by zero-knowledge well-formedness proofs and handles the s2 "
     "channel with a mandatory per-key signing cap of about 2^13/2^14/2^14 (ML-DSA-44/65/87), enforced by key rotation, "
     "against a claimed integer-uniqueness wall near 2^15.2/2^16.4/2^16.2 below which the observations cannot determine s2 "
     "by themselves. Each preprocessed nonce is bound to one quorum and erased after use. The cap is the entire defence of "
     "the s2 channel, which makes it the natural core target; it also hurts deployability, because certificates and pinned "
     "keys cannot rotate every few thousand signatures.")
para("**Worked illustration of Attack 1.** Working in the NTT domain, A splits into 256 independent k×ℓ matrices over Z_q, "
     "one per slot. Each is left-invertible unless an event of probability about 1/q occurs, which is the origin of the "
     "2^-15 and 2^-38 bounds, so any observer solves the system slot by slot and obtains s1,i exactly; shortness is "
     "irrelevant because no lattice problem arises. With k = ℓ = 1 the commitment is just a·s mod q, and dividing by a "
     "recovers s. The reasoning “discrete-log commitments hide, so lattice ones should” fails because g^x hides x only "
     "since discrete logarithms are hard, whereas A·x is a linear map and linear maps are easy to undo.")
para("**Worked illustration of Attack 2.** Consider one coefficient of s′. A single sample b = −c·s′ + e constrains a sum "
     "of τ secret coefficients to a window about 2γ2 wide, far wider than the secret's range, so it says almost nothing. "
     "Averaging over independent challenges shrinks the uncertainty like 1/√(Nτ), and once it falls below 1/2 each "
     "coefficient can be rounded. The factor γ2²/τ in (1) shows why ML-DSA-44, with the small γ2 = (q−1)/88, is the most "
     "exposed per signature. Two points matter for P1: (1) treats the noise as Gaussian, wasting the information in its "
     "sharp edges, and it recovers s′ one coefficient at a time, whereas ILP and lattice reduction use all constraints jointly.")

heading("2.4 Leakage-based cryptanalysis of lattice signatures", 2)
para("Bootle et al. [17] introduced the ILWE view of linear leakage in BLISS. Zhou et al. [18] show that the challenges of "
     "rejected Dilithium signatures bound c·s from both sides and recover keys by integer linear programming (ILP). Damm et "
     "al. [19] define Concealed ILWE, where only a fraction of samples leak, and break masked Dilithium with Huber and Cauchy "
     "regression. Yates et al. [20] find least-squares attacks on captured signatures insufficient at the parameters they "
     "studied. Hence any threshold design that releases values correlated with c·s1 or c·s2 must be tested with estimators "
     "stronger than least squares: bounded-noise estimators, ILP, robust regression and lattice reduction.")
para("**Why a summed nonce leaks.** If each of T parties adds a uniform nonce share, the aggregate follows a bell-shaped "
     "Irwin–Hall law, and z = y + c·s1 is that bell shifted by c·s1, so each signature carries a little Fisher information "
     "about s1. Kao [12] bounds the per-signature loss below 0.013 bits, but [10] proves an attack after about 2^30 signatures "
     "at ML-DSA-65; a design must make the revealed nonce exactly uniform (the claim of Quorus and Trilithium) or cap the "
     "number of signatures (TALUS).")
para("**Corruption models.** Static corruption fixes the corrupted set before the protocol starts; adaptive corruption "
     "chooses it during execution. Dishonest-majority security (Mithril) allows T−1 corrupted signers; honest-majority "
     "security (Quorus, TALUS-MPC) requires N ≥ 2T−1. Without identifiable aborts, as in Mithril, a corrupted party can "
     "abort after seeing honest contributions and retry, so aborted transcripts join the adversary's view. The harness "
     "therefore treats the corruption model as an input, not a constant.")
para("**Countermeasures.** Masking splits secrets into shares so that no intermediate value correlates with the key, but [19] "
     "shows masking alone fails when a fraction of samples leak with low noise. Against rejection leakage the defence is to "
     "hide which check failed and to release nothing derived from a rejected response, which is why Quorus's release of "
     "(w1, c, ⊥) needs its careful simulation argument. Costs differ: masking costs time, a signing cap costs key rotation, "
     "and hiding rejected transcripts costs interaction.")

heading("2.5 Related and superseded work", 2)
para("The Mithril line began as a poster [6] and a withdrawn preliminary ePrint [5]; all Mithril claims here come from [4] "
     "and [7]. Kao's design [12] is not a Call submission, but TALUS builds on it and it shows the same patterns. Its fully "
     "distributed profile P2 broadcasts masked commitments, and the paper's own remarks show that an exposed λ_h·A·y_h "
     "yields y_h and then the key; the masks hide these only when |S∖C| ≥ 2, that is, when at least two signers are honest. "
     "The paper concedes that at T = N with N−1 corruptions mask hiding fails in P2, yet its Table 1 still claims "
     "dishonest-majority unforgeability with UC proofs against static adversaries. Its Irwin–Hall analysis bounds the loss "
     "by 0.013 bits per signing query, stated as non-vacuous for q_s < 16,000.")

heading("2.6 Gap analysis and comparison", 2)
bullet("**No systematic public testing** of Mithril, Quorus or Trilithium transcripts, only design-level arguments.")
bullet("**TALUS's cap** sits about 2 bits below the authors' wall and 14–17 bits below Niot's unoptimised estimate (1); an "
       "optimised bounded-noise or ILP estimator could close this gap.")
bullet("**Rejected-attempt transcripts** (Quorus, Trilithium) and **Mithril's accepted distribution and hint loss** "
       "(7–12 bits reported; proof for Q_s = 2^50 only) lack independent re-derivation.")
bullet("**Corruption-model gaps**: static-only proofs, honest-majority boundaries and side conditions such as |S∖C| ≥ 2.")
para("Mithril alone tolerates a dishonest majority but is limited to N ≤ 6; Quorus scales but needs an honest majority and "
     "many rounds; Trilithium covers phone-and-server with a trusted helper; TALUS minimises rounds but its s2 protection is a "
     "usage cap rather than a structural argument. Independent testing therefore adds most value where a proof contains a "
     "margin (TALUS), a heuristic (Trilithium) or a changed distribution (Mithril). Evidence quality differs as well: "
     "Mithril and Quorus have reductions in the (quantum) random oracle model, Trilithium a UC proof resting on an "
     "MLWR-type assumption, and TALUS an information-theoretic argument with a numerical margin. A margin is the one kind "
     "of evidence that can be checked directly by experiment, which is a further reason to make the TALUS cap the core problem.")

heading("2.7 A reusable attack checklist", 2)
para("Generalising the observed attacks, Table IV lists ten questions that can be asked of any threshold ML-DSA design; "
     "they structure both the survey and the harness of Section IV.")
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
], [0.4, 3.2, 2.9], "Attack checklist distilled from the survey")

heading("2.8 Literature matrix", 2)
para("Table V rates each surveyed source for relevance (H central, M supporting, L background) and marks its themes: TS "
     "threshold signatures, MD ML-DSA compatible, AT attack or leakage, SS secret sharing or MPC, RS rejection sampling, ST "
     "standard. Ref. [25], added in Phase 2 for the Mithril finding, is not part of the survey matrix.")
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
], [1.5, 0.4, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3], "Literature matrix of the 24 surveyed sources")
para("Of the 24 sources, 13 are central, 6 supporting and 5 background; sixteen appeared in 2025 or 2026, and 22 of 24 in "
     "2018 or later. The sources marked AT are the evidence base for the estimators in Section IV.")
para("**Design rules that follow from the survey.** Do not publish any linear image of a secret or nonce under A, however it "
     "is masked, unless the mask stays hiding under the worst-case corruption allowed (checklist items 1 and 8). Treat the "
     "nonce as secret as the key, including in blame and abort procedures (item 2). Keep every single-signer rejection check "
     "or prove that the replacement leaks no more (item 3). And bound the signatures per key only with a margin that an "
     "optimised estimator, not just least squares, cannot close (item 4). The First-Call history shows these rules are easy "
     "to violate when importing discrete-log patterns.")

heading("2.9 Attack surface: Phase 1 hypotheses and verdicts after full reading", 2)
para("Each Phase 1 hypothesis is listed with its verdict after reading the papers and running the harness (details in "
     "Section V). “Confirmed” means the paper text supports it; it does not mean an attack.")
para("**Mithril.** (i) Accepted-response loss beyond 2^50: confirmed as a proof gap; the published parameters give "
     "Q_s = 2^26–2^37 under the paper's own theorem (Section V-B). (ii) Hint loss of 7–12 bits: revised; our lattice-estimator "
     "rerun gives up to 23.9 bits for ML-DSA-65. (iii) Adaptive corruption and (iv) selective aborts: not examined further. "
     "(v) Floating-point sampler: not tested (Go code not run).")
para("**Quorus.** (i) Reveal-on-reject is proven simulatable: confirmed, but the proof is computational (MLWE), not "
     "statistical. We also correct our own wording: A·y + e_w is uniform per coefficient, not as a whole vector, so only "
     "low-order statistical tests are ruled out. (ii) Only ⊥ is revealed: confirmed; the batched-OR step has 40-bit "
     "soundness. (iii) Building blocks: two text errors found (Section V-D), not attacks. (iv) Honest-majority boundary: narrowed; "
     "the paper treats only n = 2t+1.")
para("**Trilithium.** (i) Revised: after rejection the released value is the commitment w_H, not a partial signature, "
     "under an explicit MLWR-type assumption. (ii) The declassified bit is one bit per attempt, as in ML-DSA retries: "
     "confirmed. (iii) A malicious server tampering with the rejection check: confirmed as a simulation gap visible in the "
     "paper's own proof text, worth at most about log2(attempts) bits once. (iv) CRP: trusted; CRP+server collusion is fatal "
     "by design.")
para("**TALUS v0.22.** The cap is the whole s2 argument and the noise has sharp edges: measured in Section V-A. **Kao P2:** "
     "hypothesis strengthened to a key exposure (Section V-C).")

# ---------------- Problem formulation ----------------
heading("3. Problem Formulation")
heading("3.1 Threat model and notation", 2)
para("A (T, N) threshold scheme Π has a transcript distribution Tr_Π(sk, m): everything an adversary sees while m is "
     "signed, including broadcasts, corrupted parties' state and aborted attempts. The adversary statically corrupts as many "
     "parties as the scheme allows, observes q_s signing sessions and wins by recovering the secret (s1 suffices, since s2 "
     "then follows from t). We study key recovery, which is stronger evidence than a distinguishing bias. Table VI adds the "
     "notation not defined in Section I.")
table([
    ["Symbol", "Meaning"],
    ["s′, t0", "s′ = s2 − t0, where t0 holds the d = 13 dropped low bits of t"],
    ["e, b", "e = LowBits(w) rounding residue; b = −c·s′ + e one observation"],
    ["(T, N), S, C", "Threshold, parties; signing set S, corrupted set C"],
    ["q_s, N, N*", "Sessions observed; signatures used; N* = N giving 99% success"],
    ["cap, wall", "TALUS per-key signature limit; authors' uniqueness wall q_uniq"],
], [1.1, 5.4], "Notation added for Sections III–V")
para("What each scheme publishes beyond the signature (c, z, h) decides which checklist items apply. Table VII gives it as "
     "confirmed by the full readings of Phase 2.")
table([
    ["Scheme", "Published beyond (c, z, h)", "Aborted attempts"],
    ["Mithril", "Per-party MLWE-sample commitments w_i; round messages", "Commitments still released; no identifiable aborts"],
    ["Quorus", "MPC messages; w1 of every attempt", "Releases (w1, c, ⊥); one pass/fail bit only"],
    ["Trilithium", "Two-party MPC messages; CRP values", "Releases w_H and one declassified bit"],
    ["TALUS v0.22", "ZK well-formedness proofs; blame data", "None online: nonces pre-filtered, bound to quorum"],
], [0.9, 2.5, 2.1], "What each scheme releases (after full reading)")

heading("3.2 Core problem P1: the TALUS signing cap", 2)
para("**Intuition.** TALUS removes the s2 check, so each signature leaks one noisy equation in s′, and the defence is to stop "
     "before enough equations accumulate. Because BCC confines the noise e to (−γ2+β, γ2−β), the noise has hard edges: a "
     "single sample near an edge excludes many candidate secrets, so a bounded-noise estimator can need far fewer samples "
     "than least squares, whose error falls only like 1/√N. **Statement.** Given observations b_j = −c_j·s′ + e_j with e_j "
     "confined to the BCC interval, find the number of signatures N* at which s′ is recovered (and checked against the "
     "public key) with probability 0.99, for each parameter set, and compare log2 N* with the cap and the wall. A value "
     "below the cap is a break; above it, log2 N* minus log2 cap is the margin in bits. **Success criterion:** N* with stated "
     "trials and seeds, a positive control (estimator recovers a leaky variant) and a negative control (no false keys on "
     "genuine ML-DSA).")
para("**Why the cap needs measuring.** Because the public key already determines s2, protection below the wall is "
     "computational. The authors model a syndrome meet-in-the-middle at cost 2^{H/2} with residual entropy H ≥ 502 "
     "(about 2^160), but the only proven floor is about 2^58 at ML-DSA-65 and 2^49 at -87 (below 128 bits), and ML-DSA-44 has "
     "no public cokernel (k = ℓ). Above the wall the observations alone determine s′, so an efficient estimator that "
     "succeeds there recovers the key with no lattice work; between cap and wall, safety rests on that unproven model. "
     "Hence P1 measures N* directly. "
     "**Hypothesis (stated in Phase 1):** bounded-noise and ILP estimators beat the least-squares estimate (1) by a wide margin.")
heading("3.3 Stretch goals P2–P4", 2)
para("**P2 (Mithril).** Check the Q_s = 2^50 accounting and the a posteriori key-sharing hint loss for the exact share "
     "subset of T−1 corrupted parties. **P3 (rejected attempts).** Test whether rejected-attempt transcripts of Quorus and "
     "Trilithium depend on s1 or s2. **P4 (Kao P2).** Decide whether the masked commitments hide y when |S∖C| = 1, as the "
     "paper's Table 1 implies. Phase 1 hypotheses were: P2, a wall above 2^64 (a null result) with the hint loss "
     "re-derived; P3, Quorus simulatable thanks to e_w while Trilithium's assumption holds only approximately; P4, failure "
     "at |S∖C| = 1. Success criteria were a numerical bound with derivation (P2), a statistical test with stated "
     "false-positive rate and sample budget (P3), and an explicit recovery on a toy instance or a reason why the masks hide (P4).")

# ---------------- Harness ----------------
heading("4. The Leakage-Testing Harness")
figure(RES / "harness_architecture.png", 2.6,
       "Harness architecture. Our ML-DSA core produces every signing attempt with its secret internals; a scheme view "
       "keeps only what that scheme releases (secrets stop there); an adapter turns the observations into pairs (c, b); "
       "the estimators never see the secret, and the experiments score them against ground truth.")
para("**Design (Fig. 1).** (1) **ML-DSA core** (harness/mldsa): NTT, SHAKE sampling, hints and sign/verify that keeps every "
     "attempt; it matches the dilithium-py implementation byte for byte and passes 81 official NIST ACVP vectors (key "
     "generation, signing, verification) for all three parameter sets. (2) **Scheme views**: plain ML-DSA (negative "
     "control), a y-leaking variant (positive control), TALUS-BCC, TALUS v0.1 and Mithril, plus stand-alone Quorus, "
     "Trilithium and Kao simulators. (3) **Estimators**: least squares; a bounded-noise “edge” estimator, posed as a "
     "Chebyshev linear program (minimise the largest residual |b + c·s′|) and solved on CPU or GPU; an ILP finishing step "
     "that searches for an integer s′ consistent with every bound; and theory curves (Fisher information and Cramér–Rao "
     "bounds). Every recovery is checked against ground truth, and every run is seeded and logged.")
para("**Estimators, with intuition.** Least squares averages: stacking N samples (c, b) gives an overdetermined integer "
     "system whose solution has per-coefficient error variance about σ_e²/(Nτ), so error falls like 1/√N. Bounded noise "
     "uses the edges: if every |e| is at most a known bound, each sample is a pair of linear inequalities |b + c·s′| ≤ bound, "
     "and the feasible region (a polytope) shrinks roughly like 1/N rather than 1/√N; the Chebyshev LP finds its centre "
     "and rounding gives s′. ILP finishing replaces that rounding by an integer search inside the polytope, in the manner "
     "of [18], which helps when a few coefficients sit near a rounding boundary. Fisher information I per signature sets "
     "the Cramér–Rao bound on any unbiased estimator's variance; key recovery then needs on the order of 4/(I·τ) "
     "signatures [10]. Robust regression (Huber, Cauchy [19]) and lattice-estimator hint accounting are kept for "
     "schemes where only a fraction of samples leak or where corrupted parties hold partial information.")
para("**A view in action (TALUS).** For each signing attempt the core records y, w, c, z and which check failed. The TALUS "
     "view (1) keeps only attempts whose nonce satisfies BCC, as the offline filter would; (2) drops the secret fields; "
     "(3) emits what an observer can compute, v = A·z − c·t1·2^d and the hint, together with c; the adapter then forms "
     "b = −c·s′ + e. A corrupted-coalition variant would add the corrupted parties' shares, and for schemes with aborts "
     "the view emits exactly the fields the specification says are revealed for a rejected attempt, no more. Because the "
     "estimator receives only the view's output, any key it recovers was recoverable from public data.")
para("**Implementation.** Python with numpy and scipy; the linear programs use the HiGHS solver; the ring products inside "
     "the edge estimator, about 90% of its run time, run on an NVIDIA GPU with PyTorch in double precision, about 3× faster "
     "than the CPU version and checked against it. Least squares is solved exactly in one pass: after an FFT the equations "
     "for each frequency are independent, so each frequency is a single division (agreeing with an iterative solver to "
     "10^-13). Transcripts for several trials are built in parallel processes while the GPU solves.")
para("**Evaluation and validity.** Every experiment reports signatures used, recovered fraction, cost and parameter set. "
     "N* is the smallest N with success ≥ 0.99 over the stated trials (interpolated between grid points). Recovery is "
     "verified against ground truth, so partial correlations are never counted as breaks. Internal threats (primitive bugs, "
     "estimator over-fitting) are addressed by the ACVP vectors and by many random keys; external threats (our simulator "
     "differing from the real protocol, parameters changing before the packages) remain and are why every TALUS number is "
     "labelled as model-based; a negative result is phrased only as a bound on what was tried.")
para("**End-to-end check (gate B).** Real ML-DSA-44 attempts passed through the TALUS view and the unchanged estimator "
     "recovered s′ for 2/2 keys at N = 2×10^5 and 4×10^5 accepted signatures and 0/2 at 10^5 (seed 2029), consistent with "
     "N* in Table IX.")
para("**Least-squares calibration (Fig. 2).** To validate the simulator and the error law behind (1) we measured the "
     f"least-squares error on ML-DSA-44, n = 256 (one ring element), plain LowBits noise, N ∈ {{10^3, 3·10^3, 10^4, 3·10^4, "
     f"10^5, 3·10^5}}, {LS['trials']} trials per N, seed {LS['seed']} (generator default_rng([{LS['seed']}, N, trial])). The "
     f"mean RMS error stays within {LS_DEV:.0f}% of γ2/√(3τN) at every N. Real TALUS v0.1 signatures (keys from seeds "
     "101–103) fall on the same curve. Extrapolating, rounding every coefficient needs on the order of 10^9 signatures, "
     "so least squares alone is far from the cap; the bounded-noise estimator is what matters for P1.")
figure(RES / "ls_error_vs_N.png", 3.2,
       f"Least-squares RMS error per coefficient against signatures N (ML-DSA-44, n = 256). Blue: synthetic channel, mean "
       f"and min–max over {LS['trials']} trials (seed {LS['seed']}); orange: real TALUS v0.1 signatures (seeds 101–103); "
       "dashed: theory γ2/√(3τN).")
table([["N", "Measured RMS (min–max)", "Theory", "Ratio"]] + [
    [f"{r['N']:,}", f"{r['rms_mean']:.1f} ({r['rms_min']:.1f}–{r['rms_max']:.1f})", f"{r['theory']:.1f}",
     f"{r['rms_mean'] / r['theory']:.3f}"] for r in LS["rows"]
], [0.9, 2.0, 0.8, 0.7], f"Least-squares error, ML-DSA-44, {LS['trials']} trials per N, seed {LS['seed']}")
para("**Reading Fig. 2.** The slope −1/2 on the log–log plot is the 1/√N law; the ratio column shows no drift with N, so "
     "the Gaussian approximation of uniform LowBits noise is accurate here. An RMS error of 16 at 3×10^5 signatures is still "
     "32 times the 1/2 needed for rounding, which is why least squares never recovered a key in any of our TALUS runs.")

# ---------------- Results ----------------
heading("5. Phase 2 Results")
heading("5.1 P1: margin of the TALUS cap (core result)", 2)
para("**Model assumption.** We model the TALUS s2 channel as b = −c·s′ + e with e uniform on the BCC interval; the v0.22 "
     "writeup does not list per-signature released values, so this is our reading, not the specification. N* is measured "
     "per ring element (one of k) unless stated. Table IX summarises the margins.")
table([
    ["Set", "Cap", "Wall", "Measured N*", "log2", "Above cap / wall"],
    ["-44 edge", "2^13", "2^15.2", "1.45e5 (20 tr.)", "17.1", "4.1 / 1.9"],
    ["-44 edge+ILP", "2^13", "2^15.2", "7e4 (8/8)", "16.1", "3.1 / 0.9"],
    ["-65 edge", "2^14", "2^16.4", "3.58e5 (20 tr.)", "18.4", "4.4 / 2.0"],
    ["-87 edge", "2^14", "2^16.2", "3.69e5 (20 tr.)", "18.5", "4.5 / 2.3"],
], [1.5, 0.6, 0.7, 1.4, 0.5, 1.0], "TALUS cap margins, ML-DSA-44/65/87, n = 256 (per ring element)")
para("For ML-DSA-44 the full secret (all k = 4 elements) was recovered in 20/20 trials at 1.46×10^5. With the ILP finishing "
     "step (seed 2032, 8 trials per point) success was 1/8 at 5×10^4, 5/8 at 6×10^4, 8/8 at 7×10^4 and 32/32 from 8×10^4 to "
     "1.45×10^5, where plain rounding gave 0/8 at 8×10^4. For -65 and -87 (seed 2026 for the dense runs) the full secret was "
     "checked with 300 trials (seed 2028): 299/300 elements at 2^18.47 and 300/300 at 2^18.53, so by a union bound the "
     "full-secret success is at least about 91% and 92% (95% confidence). With ILP (4 trials per point, seed 2032) -65 "
     "needs about 2^17.45 (4/4; 3.45 bits above the cap, 1.05 above the wall) and -87 at most 2^17.18 (4/4 at the lowest N tried; 3.18 and 0.98). **Controls.** On real ML-DSA-44 signing without the r0 check the estimator recovered the key "
     "in 9/9 runs (3 keys × N = 2, 4, 8×10^5); on genuine ML-DSA it returned the key for 0/18 keys (15 of them from seed 2027), only "
     "the public-equivalent −t0, so the false-positive rate is below about 15% at 95% confidence. **Verdict:** no break; "
     "the margin above the cap is 3–4.5 bits and above the authors' wall only about 1–2 bits, thinner than the 12–15 bits "
     "suggested by (1).")
para("**From toy rings to full size.** We first ran the edge estimator on reduced rings (n = 8 to 128, 10–20 trials per "
     "point, ML-DSA-44 numbers). Per-element N* flattened around 1–2×10^5 (n = 64: 2.8×10^5; n = 128: 1.9×10^5) instead of "
     "falling toward the cap, which is why the full-size runs above were then made denser. At n = 64 the harder target "
     "s2 − t0 needed the same N* as s2, and plain LowBits noise behaved like BCC noise. Relative to plain least squares "
     "(about 3.6×10^9 in our model) the edge estimator is worth about four orders of magnitude, yet it stops 3–4.5 bits "
     "short of the cap. The theory module explains the shape: for one coefficient alone the uniform-noise error falls like "
     "1/N exactly (checked by Monte Carlo), and when all 256 coefficients are solved jointly a fitted coupling constant "
     "(about 0.76·τ^0.42) accounts for the real N* sitting 1.5–2 bits above the single-coefficient formula. ILP finishing "
     "lowers the 50% point by 1.0×, 1.1×, 1.1× and 1.5× at n = 8, 16, 32 and 64, consistent with the roughly 2× at n = 256.")
para("**Limits of the P1 result.** (i) The channel model (independent uniform noise on the BCC interval, no wrap-around, "
     "no use of the hint) is our reading of TALUS, not quoted from the specification. (ii) The ILP figure is per ring "
     "element with 8 trials per point. (iii) Lattice reduction and better use of hints were not tried, so N* is an upper "
     "bound on what an attacker needs. (iv) Our wall and cap figures are the authors'; we did not re-derive the wall.")
heading("5.2 TALUS v0.1 and Mithril", 2)
para("**TALUS v0.1 (Niot's attacks reproduced).** On our implementation of the arXiv v2 design [10] (ML-DSA-44, |S| = 3, keys "
     "from seeds 101–103; DKG simplified to Shamir sharing), attack 1 recovered s1 exactly from the key-generation broadcast "
     "(3/3 keys) and from one MPC signature (60/60). Attack 2 by least squares follows the theory curve up to N = 10^5 "
     "(Fig. 2) and would need about 1.2×10^9 signatures. A separate sanity run on real no-check ML-DSA-44 transcripts gave "
     "0.97× Niot's error formula (12 runs), and on the same transcripts the edge estimator needed about 1,500× fewer "
     "signatures than his least-squares N. Simplifications: plain ML-DSA key generation followed by Shamir sharing of s1 "
     "instead of the paper's DKG, the MPC computation of w1 replaced by its correct output, and |S| = T = 3 throughout. "
     "The exercise shows why TALUS changed its design, and that our views reproduce a published break exactly.")
para("**Mithril proof-parameter gap (P2).** Theorem 3.2 of [4] bounds the number of safe queries through a hyperball-"
     "intersection lemma taken from the ePrint full version of Devevey et al. [25] (App. A.6). That bound uses exponent "
     "n−1 where a correct cylinder argument gives (n−1)/2; for ML-DSA-44 it gives 2^-50.1 where the exact value is "
     "2^-33.5 (reproduced with the authors' own Sage parameter script). With the published parameters the theorem then "
     "covers Q_s = 2^26–2^37 rather than 2^50. Under the typical norm distribution (heuristic, not a proof) most sets "
     "still reach 2^50, some fall up to about 3 bits short; corrected parameters need 1.3× to 8.5× more parallel "
     "repetitions K. The faulty bound is ePrint-only (the ASIACRYPT version states only the exact formula), and among 13 "
     "citing works we checked only Mithril uses it; HAETAE, the other main hyperball scheme, evaluates the exact "
     "incomplete-Beta value numerically and is unaffected. Seen from the other side, reaching 2^50 with the published radii "
     "would require the norm bound B in the proof to sit only 0–7 standard deviations above the mean norm of c·s, whereas "
     "the proof needs an overwhelming bound (the paper's footnote says about 13). This is a proof gap, not an attack: "
     "exceeding the bound slightly enlarges a Rényi-divergence budget and does not obviously reveal s. **Hint loss.** With the exact share "
     "subset of T−1 parties, the lattice estimator gives losses of 4.9–7.7 (ML-DSA-44), 17.7–23.9 (-65) and 8.6–14.4 bits "
     "(-87), against the reported 7–12 (Table X).")
table([
    ["Set", "Reported loss", "Our estimate (Python)", "Lattice estimator"],
    ["ML-DSA-44", "7–12 bits", "4–7 bits", "4.9–7.7 bits"],
    ["ML-DSA-65", "7–12 bits", "14.6–20.7 bits", "17.7–23.9 bits"],
    ["ML-DSA-87", "7–12 bits", "7.6–12.8 bits", "8.6–14.4 bits"],
], [1.0, 1.0, 1.3, 1.3], "Mithril a posteriori key-sharing hint loss, exact T−1 share subset")
para("**Beyond 2^50.** Signature schemes are usually assumed to face up to 2^64 queries. For Mithril the accepted response "
     "is uniform on an intersection of balls, so the Rényi divergence has the closed form 1/(1−δ) at any order and no "
     "Fisher-information leak arises from shape alone; but at 2^64 queries every published set falls short of the "
     "proof's requirement (27–38 bits by the theorem, 3–17 bits under the typical-case heuristic), and parameters corrected "
     "for 2^64 need K larger by 1.7× to 23×. Correcting only the faulty lemma at 2^50 lowers the radius ratio φ from 7–9 to "
     "5.3–7.7 and raises K by 1.3× to 8.5× (worst case ML-DSA-65 with (T, N) = (5, 6): from 1,200 to 10,234); "
     "communication grows with K. These figures are computed from the paper's formulas, not simulated.")
para("The Python core-SVP substitute reproduces the paper's 12 bits for ML-DSA-44 when given the paper's constant 0.74; "
     "the lattice-estimator run (Sage 10.4, rough mode) is the one we quote. Only ML-DSA-65 clearly exceeds the claimed "
     "range. Both Mithril items are accounting and proof issues: none gives an attack on the scheme.")
heading("5.3 Kao's P2 profile (P4)", 2)
para("The paper's own text (Fig. 1b, Remark 11, App. M.1) has every party broadcast W_i, and its pairwise masks cancel "
     "(Lemma 1), so Σ W_i = A·y is public; Gaussian elimination gives y and then s1 = c⁻¹(z − y) from a single P2 "
     "signature, for any |S∖C|. The proof of Corollary 5 itself calls this value the public broadcast, and no later appendix "
     "changes it. Confirmed by algebra and a toy implementation; the author's code is not public. The toy (ring size 8, "
     "real q) also checks the narrower Phase 1 hypothesis: with all but one signer corrupted, the honest party's mask can "
     "be stripped and λ_h·A·y_h inverted, while with two honest signers this route fails, as the paper says; the sum "
     "route above, however, works whatever the number of honest parties. Two further points: Corollary 6 claims the full "
     "threshold-signature functionality without the |H| ≥ 2 condition that its Simulator 17 needs, and the key-generation "
     "commitment t(i) = A·s1(i) + s2(i) carries the noise s2(i), so the bare A·s1,i pattern broken in TALUS does not recur there.")
heading("5.4 Quorus and Trilithium (P3)", 2)
para("Our Quorus implementation produced 0 of 272,664 signatures failing FIPS 204 verification. No statistical leak is "
     "possible by construction at the level of single coefficients; a lattice-level distinguisher was not run. For "
     "Trilithium, exact enumeration at n = 4 and Monte Carlo at n = 8 (2×10^8 samples × 3 trials) show the gap between "
     "rejected w_H and the simulator shrinking with γ1 and n (branch 2: 3×10^-5 to 7×10^-7 at n = 8). Paper errata, not "
     "attacks: Quorus Functionality 6 uses the bound γ2−β−η where every other place uses γ2−β (PDF p. 32), and Lemma 8 "
     "has a wrong normalising constant; Trilithium's simulation of unsuccessful signing (p. 24) leaves the gap noted in Section II-I.")
para("**Trilithium in more detail.** The released mixture after a rejection comes from two branches: branch 3 (the z check "
     "failed) and branch 2 (z passed but the LowBits check failed). Exact enumeration at n = 4 showed a real but small "
     "gap between rejected w_H and the simulator, shrinking with γ1 (branch 3 roughly as γ1^-2.7). A branch-2 floor near "
     "10^-4 persisted for γ1 ≥ γ2 at q = 257, 513 and 1025, so it is not a small-q artefact; it comes from the wrap-around "
     "rounding cell, and masking that cell removes it (30–65× smaller). Exact convolution for n = 2 to 6 at q = 17 shows "
     "both gaps falling with n (branch 3 by 2–3 orders of magnitude from n = 4 to 6). At n = 8 the branch-3 gap is below the "
     "Monte Carlo floor of about 10^-7. Toy sizes cannot prove anything about n = 256, but every trend points toward the "
     "assumption holding statistically; a lattice-level distinguisher remains untested. On H-F3, a server that tampers with "
     "the rejection check is detected and stopped, so the leak is bounded by the stopping time, about log2(attempts) bits, "
     "once; the issue is that the paper's simulation does not reproduce how that stopping probability depends on the real z.")
para("**Quorus in more detail.** Besides the two text errors, the batched-OR protocol has statistical soundness 2^-39 "
     "(κ = 40), so about one rejected attempt in 2^39 is wrongly declared a pass and its failing, key-dependent z is opened; "
     "at roughly 10^11 signatures this is not practical, but 40-bit statistical security is lower than usual. A rough "
     "reduction (ours, not run) suggests the MLWE instance behind Theorem 2 is about as hard as ML-DSA key recovery itself.")
heading("5.5 Disclosure status", 2)
para("The Kao P2 and Mithril findings have not yet been reported to the authors; coordinated disclosure is pending, and "
     "both are stated here neutrally as our reading of public documents. Quorus and Trilithium items are errata.")

# ---------------- Phase 3 and conclusion ----------------
heading("6. Phase 3 Prototype and Conclusion")
para("**What the Phase 3 prototype will demonstrate.** An end-to-end TALUS-cap margin tool: given transcripts produced by "
     "the TALUS reference code (packages expected from March 2027) through a scheme view, it runs the bounded-noise "
     "estimator with ILP finishing, reports N* and the margin in bits against the cap and the wall, and runs the positive "
     "and negative controls automatically, so a reported margin is never quoted without them. Concretely it will (i) "
     "replace our channel model by the released values of the real code, (ii) extend ILP finishing to the full secret and "
     "to ML-DSA-65/87, and (iii) rerun the Mithril parameter check on the submitted parameters. Success means reproducing "
     "Table IX on real transcripts, or explaining any difference, with each margin reported together with its controls. "
     "Until packages appear, the prototype runs on our TALUS view, so the demonstration does not depend on the release date. "
     "The demonstration will be a single command that takes a transcript file and a parameter set and prints the margin "
     "table with its controls, trial counts and seeds; the stretch goals continue alongside it (a lattice-level "
     "distinguisher for rejected transcripts, the Go signing code of Mithril, and disclosure to the Kao and Mithril authors).")
table([
    ["Stage", "Phase 2 item (Phase 1 plan)", "Status (13 Oct 2026)"],
    ["1", "ML-DSA primitives, interface, ILWE sanity check", "Done: 81 ACVP vectors; 0.97× Niot's formula"],
    ["2", "TALUS cap, bounded-noise and ILP (P1)", "Done for per-element N*; ILP only -44"],
    ["3", "Mithril accepted z, hint accounting (P2)", "Done: proof gap; hint table"],
    ["4", "Quorus, Trilithium rejected attempts (P3)", "Done at statistical level; lattice test not run"],
    ["5", "Kao P2 and DKG claims (P4)", "Done: key exposure confirmed in text"],
    ["6", "Rerun on reference code (from Mar. 2027)", "Phase 3; only Mithril script run so far"],
], [0.5, 3.0, 3.0], "Phase 2 plan against outcome, and the hand-over to Phase 3")
para("Table XI sets the Phase 1 plan against what Phase 2 delivered.")
para("**Research questions, answered.** (RQ1) Which threshold ML-DSA designs exist? Four First-Call proposals, differing in "
     "corruption model, party count and rounds (Table II). (RQ2) Which are broken? Earlier TALUS versions, by two attacks "
     "that we reproduced; Kao's P2 profile exposes the key from one signature by the paper's own text. (RQ3) Which "
     "techniques work? Linear inversion of published A·x, nonce-leak recovery, and for the TALUS channel a bounded-noise "
     "estimator with ILP finishing, about four orders of magnitude better than least squares. (RQ4) Where is the evidence "
     "thinnest? The TALUS cap margin (now measured at 3–4.5 bits above the cap), Mithril's parameter-proof accounting, and "
     "the untested lattice-level question for rejected transcripts in Quorus and Trilithium.")
para("**Lessons from Phase 2.** Three methodological points carry over to Phase 3. First, controls change conclusions: "
     "without the negative control the estimator's output −t0 on genuine ML-DSA could have been mistaken for leakage. "
     "Second, reduced-size runs can mislead in either direction (the ML-DSA-87 shortcut at n = 64 overstated the margin, "
     "and ILP gains grow with n), so only full-size numbers are quoted. Third, reading the papers in full revised two of "
     "our own Phase 1 statements (Trilithium releases w_H, not a partial signature; uniformity holds per coefficient only), "
     "which is why every hypothesis in Section II-I now carries a verdict.")
para("**Positioning.** Earlier cryptanalysis of lattice signatures [17]–[20] targets a single signer leaking through a "
     "physical side channel. Here the leakage is logical: it is part of the protocol transcript, visible to any observer or "
     "corrupted party, and its noise distribution is known exactly from the specification. Results therefore transfer "
     "across implementations, and schemes analysed only by proof gain an independent empirical check.")
para("**Ethics.** We study only public, standardisation-stage specifications, as NIST invites. Findings about a scheme are "
     "shared with its authors before any public posting, and we distinguish confirmed key recovery, measured margins, proof "
     "gaps and errata, labelling results that rely on our simulators rather than the authors' code.")
para("**Conclusion.** The survey of twenty-four sources showed that threshold ML-DSA designs fail when patterns from "
     "discrete-log protocols are imported, and that three of the four proposals had not been tested. Phase 2 built and "
     "validated a harness and measured the core quantity: the TALUS cap holds in our model, but by 3–4.5 bits above the "
     "cap and only about 1–2 bits above the authors' wall, much less than least squares suggests. Secondary findings are a "
     "proof-parameter gap in Mithril, a key exposure in Kao's P2 profile, and errata in Quorus and Trilithium, with "
     "disclosure to the authors to follow before any public posting.")

# ---------------- References ----------------
heading("References")
refs = [
    ("NIST", "FIPS 204: Module-Lattice-Based Digital Signature Standard", "Aug. 2024."),
    ("L. Ducas, E. Kiltz, T. Lepoint, V. Lyubashevsky, P. Schwabe, G. Seiler, and D. Stehlé", "CRYSTALS-Dilithium: A lattice-based digital signature scheme", "IACR Trans. Cryptogr. Hardw. Embed. Syst., vol. 2018, no. 1, pp. 238–268, 2018."),
    ("NIST", "Multi-Party Threshold Schemes: First Call for Submissions", "NIST IR 8214C, 2026."),
    ("S. Celi, R. del Pino, T. Espitau, G. Niot, and T. Prest", "Efficient threshold ML-DSA", "in Proc. USENIX Security Symp., 2026 (full version: IACR ePrint 2026/013)."),
    ("G. Borin, S. Celi, R. del Pino, T. Espitau, G. Niot, and T. Prest", "Threshold signatures reloaded: ML-DSA and enhanced Raccoon with identifiable aborts", "IACR ePrint 2025/1166, 2025 (withdrawn May 2026)."),
    ("S. Celi et al.", "Poster: Efficient threshold ML-DSA up to 6 parties", "in Proc. ACM CCS, 2025, doi:10.1145/3719027.3760739."),
    ("S. Celi, G. Delerue, R. del Pino, T. Espitau, G. Niot, and T. Prest", "Mithril: Efficient threshold ML-DSA from secret sharing with short shares", "NIST MPTC First Call preview writeup v1.0, Jan. 2026."),
    ("A. Bienstock, L. de Castro, D. Escudero, A. Polychroniadou, and A. Takahashi", "Quorus: Efficient, scalable threshold ML-DSA signatures from MPC", "in Proc. USENIX Security Symp., 2026 (full version: IACR ePrint 2025/1163)."),
    ("A. Dufka, S. Kravtšenko, P. Laud, and N. Snetkov", "Trilithium: Efficient and universally composable distributed ML-DSA signing", "IACR ePrint 2025/675, 2025; see also SplitForge, SplitKey preview writeup v0.1, NIST MPTC, Jan. 2026."),
    ("L. Kao and R. Chang", "TALUS: FIPS-204-exact threshold ML-DSA via boundary clearance", "arXiv:2603.22109, 2026."),
    ("L. Kao and R. Chang", "TALUS: FIPS-204-exact threshold ML-DSA via boundary clearance (preview writeup v0.22)", "NIST MPTC First Call, Aug. 2026."),
    ("L. Kao", "FIPS 204-compatible threshold ML-DSA via Shamir nonce DKG", "arXiv:2601.20917, 2026."),
    ("G. Niot", "Key-recovery attacks on TALUS: A cryptanalytic note", "IACR ePrint 2026/1386, Jul. 2026."),
    ("R. del Pino, S. Katsumata, M. Maller, F. Mouhartem, T. Prest, and M.-J. Saarinen", "Threshold Raccoon: Practical threshold signatures from standard lattice assumptions", "in Proc. EUROCRYPT 2024, LNCS 14652, 2024."),
    ("R. del Pino, T. Espitau, G. Niot, and T. Prest", "Simple and efficient lattice threshold signatures with identifiable aborts", "IACR ePrint 2025/871, 2025 (withdrawn May 2026)."),
    ("K. D. Gür, J. Katz, and T. Silde", "Two-round threshold lattice-based signatures from threshold homomorphic encryption", "in Proc. PQCrypto 2024, LNCS 14772, 2024."),
    ("J. Bootle, C. Delaplace, T. Espitau, P.-A. Fouque, and M. Tibouchi", "LWE without modular reduction and improved side-channel attacks against BLISS", "in Proc. ASIACRYPT 2018, LNCS 11272, pp. 494–524, 2018."),
    ("Y. Zhou, W. Wang, Y. Sun, and Y. Yu", "Rejected signatures’ challenges pose new challenges: Key recovery of CRYSTALS-Dilithium via side-channel attacks", "IACR Trans. Cryptogr. Hardw. Embed. Syst., 2025 (ePrint 2025/214)."),
    ("S. Damm et al.", "Solving concealed ILWE and its application for breaking masked Dilithium", "in Proc. ASIACRYPT 2025 (ePrint 2025/1629)."),
    ("K. Yates, A. Pierrottet, A. Al Mamun, R. Cartor, M. Chowdhury, and S. Gao", "Security analysis of integer learning with errors with rejection sampling", "arXiv:2512.08172, Dec. 2025."),
    ("A. Shamir", "How to share a secret", "Commun. ACM, vol. 22, no. 11, pp. 612–613, 1979."),
    ("P. Feldman", "A practical scheme for non-interactive verifiable secret sharing", "in Proc. IEEE FOCS, 1987, pp. 427–438."),
    ("C. Komlo and I. Goldberg", "FROST: Flexible round-optimized Schnorr threshold signatures", "in Proc. SAC 2020, LNCS 12804, 2021, pp. 34–65."),
    ("R. del Pino and G. Niot", "Finally! A compact lattice-based threshold signature", "in Proc. PKC 2025, Part III, LNCS 15676, 2025, pp. 169–199."),
    ("T. Devevey, O. Fawzi, A. Passelègue, and D. Stehlé", "On rejection sampling in Lyubashevsky’s signature scheme", "in Proc. ASIACRYPT 2022, LNCS 13794, pp. 34–64, 2022 (full version: IACR ePrint 2022/1249)."),
]
for i, (au, ti, ve) in enumerate(refs, 1):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.3)
    p.paragraph_format.space_after = Pt(1)
    for txt, it in ((f"[{i}] {au}, “{ti},” ", False), (ve, True)):
        run(p, txt, italic=it).font.size = Pt(8)

doc.save("Phase1_Report.docx")
print("saved")
