"""Builds report/Phase1_Report.docx. Run: python build_report.py

Revised 13 Oct 2026: instructor feedback applied and Phase 2 results added. Updated 29 Oct 2026 with the 14-16 Oct results,
then given a plain-language pass (short sentences, few dashes and colons in prose).
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


ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI"]
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
run(p, "Phase 2 Report – Cryptography, BITS Pilani, Dubai Campus")
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "Ashmit Dhown 2023A7PS0205U · Srivathsa H Honyal 2023A7PS0198U", italic=True)

# ---------------- Abstract ----------------
para("**Abstract—**ML-DSA (FIPS 204) is the lattice based digital signature that NIST standardised. It was designed for a "
     "single signer. Splitting its key among several parties is hard, because rejection sampling and rounding do not fit "
     "well with secret sharing. NIST's 2026 First Call for multi party threshold schemes (IR 8214C) has four proposals whose "
     "signatures pass an unchanged ML-DSA verifier. They are Mithril, Quorus, SplitForge/Trilithium and TALUS. We survey 33 "
     "sources on these schemes and on leakage attacks against lattice signatures. Our core problem is the TALUS signing cap, "
     "the limit on how many signatures one key may produce. In Phase 2 we built a leakage testing harness. It has an ML-DSA "
     "implementation that passes 81 NIST ACVP test vectors, a view of what each scheme releases, and estimators based on "
     "least squares, bounded noise and integer programming. In our model of the TALUS s2 channel it recovers the whole "
     "secret of ML-DSA-44 in 18 of 20 trials at 7×10^4 signatures (2^16.1). For 95% success it needs about 3.1 bits more "
     "than the cap allows for ML-DSA-44 and 3.5 bits more for ML-DSA-65 and ML-DSA-87. That is about 1 bit above the "
     "authors' uniqueness wall. The margin is thin, but it is not a break. As controls, the estimator recovers the secret in "
     "9 of 9 runs on a leaky variant and returns no false key for 18 genuine ML-DSA keys. Along the way we reproduce both "
     "published attacks on an early TALUS version. We find a gap between Mithril's parameters and its proof, although its "
     "real Go transcripts show no s2 leak. We also show that a predecessor design gives away the key from one signature at "
     "full ML-DSA size. These last two findings await coordinated disclosure.")

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
     "and was not changed. A large quantum computer would break RSA and ECDSA, so NIST standardised post quantum "
     "replacements. The main one is ML-DSA, specified in FIPS 204 [1] and derived from CRYSTALS-Dilithium [2]. Its security "
     "rests on two lattice problems, Module-LWE (learning with errors) and Module-SIS.")
para("**How ML-DSA signs.** In simple terms, the signer hides its secret inside a random looking answer, and throws the "
     "answer away whenever it might give the secret away. In more detail, all arithmetic is in the ring "
     "R_q = Z_q[X]/(X^n+1). Its elements are polynomials of degree below n = 256 with coefficients modulo the prime "
     "q = 8380417. A is a public k×ℓ matrix of such polynomials. The secret key is a pair of short vectors (s1, s2) whose "
     "coefficients lie in [−η, η]. The public key is t = A·s1 + s2, and only its high part t1 is published. We write "
     "t = t1·2^d + t0, where t0 holds the d = 13 dropped low bits. To sign, the signer picks a random nonce y with "
     "coefficients below γ1. It computes w = A·y and the high bits w1 = HighBits(w). It then derives a challenge "
     "c = H(msg, w1). This is a polynomial with exactly τ coefficients equal to ±1 and the rest zero. The output is "
     "z = y + c·s1 together with a short hint h. We write ‖x‖∞ for the largest absolute coefficient of x. The number "
     "β = τ·η bounds ‖c·s‖∞ for any secret s. Two rejection checks follow. The first, ‖z‖∞ < γ1 − β, hides s1. The "
     "second, ‖LowBits(w − c·s2)‖∞ < γ2 − β, hides s2. Here γ2 is the rounding range of LowBits. If either check fails, "
     "the signer starts again with a fresh y. This design is called Fiat–Shamir with aborts. It makes accepted signatures "
     "statistically independent of the key. Table I lists the parameter values.")
table([
    ["Set", "NIST cat.", "(k, ℓ)", "η", "τ", "γ1", "γ2"],
    ["ML-DSA-44", "2", "(4, 4)", "2", "39", "2^17", "(q−1)/88"],
    ["ML-DSA-65", "3", "(6, 5)", "4", "49", "2^19", "(q−1)/32"],
    ["ML-DSA-87", "5", "(8, 7)", "2", "60", "2^19", "(q−1)/32"],
], [1.5, 0.7, 0.8, 0.4, 0.4, 0.6, 1.0], "ML-DSA parameter sets [1]")
para("**Why rejection keeps signatures safe.** Think of z as a point in a box. The nonce y is uniform on a box of half width "
     "γ1, and c·s1 moves it by at most β. So every point inside the smaller box of half width γ1 − β is equally likely, "
     "whatever s1 was used. Accepting only those points therefore hides s1 completely. The challenge c has only τ nonzero "
     "entries. So if anything does leak, the attacker gets one noisy linear equation with small coefficients per "
     "signature. All the sample counts in this report come from this fact. Any threshold design that changes what is "
     "accepted, what is rejected or what else is published must bring back this independence. This is the property we test.")
para("**Why a threshold version is hard.** In a (T, N) threshold scheme, any T of the N parties can sign together, and "
     "fewer than T learn nothing. Shamir secret sharing [21] hides a secret as the constant term of a random polynomial of "
     "degree T−1. Feldman [22] adds commitments g^{a_i} to its coefficients. Threshold Schnorr schemes such as FROST [23] "
     "simply add up partial signatures. ML-DSA loses all three of these conveniences. Shares of a short secret are not "
     "short. HighBits is not additive, so parties cannot round their own pieces of w. The s2 check needs the full secret. "
     "And the lattice version of a Feldman commitment, A·x, does not hide x (Section II-C). Two facts drive most attacks "
     "below. First, A is tall (k ≥ ℓ), so anyone who sees A·x can recover x by Gaussian elimination. Second, "
     "z = y + c·s1 holds over the integers, so any leak of the nonce y gives s1 = c⁻¹(z − y).")
para("**Why now, and what this report adds.** NIST's First Call (IR 8214C) [3] expects early packages from late 2026 and "
     "full packages from March 2027, so outside checking is most useful now. This year has already shown why. In July 2026 "
     "Niot [13] recovered keys from earlier TALUS versions. TALUS v0.22 [11] answered with a limit on the number of "
     "signatures per key, and nobody had measured its safety margin independently. After the Phase 1 review, that signing "
     "cap is our core problem (P1). The Mithril, rejected attempt and Kao questions (P2 to P4) are stretch goals. The "
     "report gives four things. First, a survey of the four proposals, the attack toolbox and recent work. Second, the "
     "problem statement. Third, our proposed solution, a leakage testing harness (Fig. 1). Its main estimator uses the hard "
     "edges of the TALUS noise and finishes with integer programming. Fourth, simulation results with trial counts and "
     "seeds. They show that our method needs about 5×10^4 times fewer signatures than the least squares baseline, yet "
     "still stays about 3 bits above the cap.")
para("**How we found the sources.** We started from the First Call submissions page, the proposals' ePrint and arXiv "
     "entries and the papers they build on. We then searched ePrint, TCHES, EUROCRYPT and ASIACRYPT with queries such as "
     "“Dilithium rejected signatures ILP”, “ILWE” and “threshold lattice signatures”. We kept a source if it defines or "
     "attacks a threshold ML-DSA design, or supplies a technique against one. We checked the details of every reference "
     "online, and checked Shamir [21] and Feldman [22] against Crossref. For Phase 2 we repeated the search in October "
     "2026 over ePrint 2024 to 2026 and the preview writeups of the NIST call. This added nine sources, [26] to [34] "
     "(Section II-F).")
para("**What we read and ran.** We read Quorus [8], Trilithium [9] and Mithril [4] in full. For Mithril this includes "
     "Appendices D, E and G at the level of the proof steps. For Kao [12] we read the main text and Appendices B to O. We "
     "ran our own harness code (Section IV). Of the schemes' own code we ran only Mithril's parameter script and its Go "
     "signing code. Every TALUS number depends on our model of the channel, because the v0.22 writeup does not list the "
     "values released with each signature. We label every result as measured, derived or hypothesis.")

# ---------------- Literature survey ----------------
heading("2. Literature Survey")
heading("2.1 Background", 2)
para("Dilithium [2] introduced the signing method above, and FIPS 204 [1] standardised it. Early lattice threshold "
     "signatures used threshold homomorphic encryption (Gür, Katz and Silde [16]). Threshold Raccoon [14] uses only "
     "symmetric tools and one time additive masks, but its signatures are not ML-DSA signatures. Del Pino and Niot [24] "
     "give a compact scheme based on Raccoon, limited to 2^64 signatures and about 8 parties. An earlier preprint on "
     "identifiable aborts [15] has been withdrawn and is listed for history only. The big shift in recent work is toward "
     "signatures that pass the unchanged FIPS 204 verifier, because deployed certificates and pinned keys cannot change.")
para("**Rounding and the public value v.** The hint lets the verifier recompute w1 from v = A·z − c·t1·2^d. Putting in "
     "z = y + c·s1 gives v = w − c·(s2 − t0). So v is public and contains the term c·s′, with s′ = s2 − t0. The second "
     "rejection check keeps LowBits(w) at least β away from a rounding boundary, and so v reveals nothing. If the check is "
     "removed or changed, this protection is lost.")

heading("2.2 The four First Call ML-DSA proposals", 2)
para("**Mithril** [4,6,7] comes from PQShield, Brave and Bristol and appears at USENIX Security 2026. It uses replicated "
     "secret sharing with short shares, and each party does its own rejection using hyperball sampling (sampling from a "
     "Euclidean ball). It costs about 1 MB per participant for up to six parties and has a Go implementation. Its security "
     "proof reduces to MLWE and to the unforgeability of ML-DSA. It allows up to T−1 corrupted parties chosen in advance, "
     "without identifiable aborts. Each attempt succeeds with probability about 1/2 (ML-DSA alone has about 1/4), with K "
     "parallel repetitions. Each party publishes a full MLWE sample as its commitment, so the bare A·x attack does not "
     "apply. The proof uses Rényi divergence and covers Q_s = 2^50 signing queries. We do not rely on the older version "
     "[5]. The preview writeup [7] adds three points. Up to 8 parties remain practical, no synchronised broadcast channel "
     "is needed, and the Go code uses floating point for hyperball sampling.")
para("**Why rejection by each party is delicate.** A single ML-DSA signer accepts a nonce only if both checks pass, about "
     "one time in four. With N parties that each hold a short additive share, the sum of their answers must land in the "
     "same box, but no party knows the sum. Mithril lets each party draw its nonce share from a hyperball, so that the sum "
     "has a predictable size, and each party decides acceptance on its own. The accepted answers are then close to the "
     "FIPS 204 distribution, but not exactly equal to it. How close they are is a question of numbers (problem P2), not a bug.")
para("**Quorus** [8] comes from J.P. Morgan and also appears at USENIX Security 2026. It changes signing so that it suits "
     "MPC (secure multi party computation), while keeping FIPS 204 verification. The nonce is uniform, a small noise term "
     "e_w is added to w, and w1 is output even when (z, h) is rejected. It tolerates fewer than n/2 corrupted parties and "
     "is proven secure in the universal composability (UC) framework. It costs about 150 KB per party per attempt, which "
     "is 0.31 to 0.59 MB per signature over 16 or 29 rounds, and was tested with up to 63 parties. Because w1 is always "
     "released, the Fiat–Shamir hash can be computed in the open. The proof that rejected partial signatures can be "
     "simulated relies on the noise e_w.")
para("**SplitForge/Trilithium** [9] comes from Cybernetica. It targets a server and a phone, helped by a correlated "
     "randomness provider (CRP). It is UC secure against one malicious party out of the three and takes 14 rounds per "
     "signing attempt. It publishes the high bits w_H even for rejected attempts. This is justified by an MLWR type "
     "assumption (Module Learning With Rounding, which is like MLWE but replaces random noise with fixed rounding). The "
     "paper itself calls this assumption non standard for ML-DSA parameters. Trilithium uses an actively secure comparison "
     "protocol and a new rounding protocol, and has a Rust implementation. It is given both for unchanged ML-DSA and for a "
     "Quorus style variant in which the CRP supplies the noise e_w. It is part of Cybernetica's SplitKey submission. The "
     "writeup admits that a malicious CRP can mount selective disclosure attacks, which the authors consider harmless for "
     "the intended use.")
para("**TALUS** [10,11] comes from Codebat. It introduces the Boundary Clearance Condition (BCC). For a fixed share of "
     "nonces (43.2%, 31.7% and 39.1% for ML-DSA-44, 65 and 87), s2 provably cannot push w across a rounding boundary. So "
     "rejection can be done offline on prepared nonces, which gives a distributed MPC version with two rounds. The paper "
     "says its cap based protection of the s2 channel is supported by a model rather than proven. It also proves that any "
     "FIPS exact scheme that reveals a summed (Irwin–Hall) nonce allows key recovery after about 2^30 signatures. A one "
     "round variant helped by a TEE (trusted execution environment, a hardware enclave trusted to keep secrets) appears in "
     "v0.22 only as a contrasting example. TALUS builds on Kao's Shamir nonce DKG [12]. There the signing nonce is itself "
     "Shamir shared, with pairwise cancelling PRF masks, and the paper claims the nonce shares keep more than five times "
     "the key's entropy for signing sets of up to 17.")
table([
    ["Scheme", "Design", "Trust / corruption", "Rounds", "Public attacks"],
    ["Mithril [4]", "Replicated short shares, local rejection", "Dishonest majority (T−1), static; N ≤ 6", "~3 per attempt", "None found"],
    ["Quorus [8]", "MPC-friendly ML-DSA variant", "Honest majority, UC, n ≤ 64", "16–29", "None found"],
    ["Trilithium [9]", "2-party MPC + CRP", "CRP honest; one party malicious", "14 per attempt", "None; MLWR-type assumption"],
    ["TALUS [10,11]", "BCC nonce filtering, Shamir nonce DKG", "Honest majority N ≥ 2T−1", "2 (v0.22)", "Earlier versions broken [13]"],
], [1.0, 1.9, 1.7, 0.9, 1.3], "The four ML-DSA compatible First Call proposals")

heading("2.3 Published attacks on TALUS", 2)
para("Niot [13] (ePrint 2026/1386) gives two practical attacks on earlier TALUS versions. **Attack 1** uses commitments that "
     "do not hide. TALUS-MPC broadcast A·s1,i during key generation and A·ŷ in the blame phase. A can be inverted from the "
     "left except with probability at most 2^-15 for ML-DSA-44 or 2^-38 for ML-DSA-65 and 87. So x = A⁺(A·x) reveals every "
     "key share and the nonce, and s1 = c⁻¹(z − y) follows from one signature. **Attack 2** targets the removed s2 check. "
     "In simple terms, every signature reveals a very noisy linear equation in the secret, and enough of them average the "
     "noise away. More precisely, HighBits(w) is known from the hint, so the attacker sees b = −c·s′ + e, where "
     "e = LowBits(w) is roughly uniform on [−γ2, γ2]. This is integer LWE (ILWE), which is LWE without reduction modulo q, "
     "and least squares solves it [17]. The error per coefficient is about σ_e/√(Nτ), with σ_e² ≈ γ2²/3. Rounding works "
     "once this error is below 1/2, so the attack needs about")
para("N ≈ 4γ2²/(3τ)  signatures,                                                  (1)", align=WD_ALIGN_PARAGRAPH.CENTER)
para("which is 2^28 to 2^31 (Table III). Niot stresses that (1) is not optimised. He also notes that putting the check back "
     "is not enough, because a corrupted party can bias its nonce share (for example y_i = 0) so that the check always passes.")
table([
    ["Set", "γ2", "τ", "4γ2²/(3τ)", "log2"],
    ["ML-DSA-44", "95,232", "39", "3.1 x 10^8", "28.2"],
    ["ML-DSA-65", "261,888", "49", "1.9 x 10^9", "30.8"],
    ["ML-DSA-87", "261,888", "60", "1.5 x 10^9", "30.5"],
], [1.1, 0.9, 0.5, 1.2, 0.6], "Least-squares sample estimate (1) per parameter set")
para("The authors' response, v0.22 [11], replaces the commitments with zero knowledge proofs that the values are well "
     "formed. It handles the s2 channel with a mandatory limit of about 2^13, 2^14 and 2^14 signatures per key (ML-DSA-44, "
     "65 and 87), enforced by changing the key. The authors compare this cap with an integer uniqueness wall near 2^15.2, "
     "2^16.4 and 2^16.2. Below the wall, they claim, the observations alone cannot pin down s2. Each prepared nonce is tied "
     "to one quorum and erased after use. The cap is the only defence of the s2 channel, so it is the natural core target. "
     "It also hurts practical use, because certificates and pinned keys cannot be replaced every few thousand signatures.")
para("**Attack 1 in detail.** The number theoretic transform (NTT) is the modular version of the FFT. It turns a product of "
     "polynomials in R_q into 256 separate products of numbers modulo q, one per slot. In the NTT domain, A splits into 256 "
     "separate k×ℓ matrices over Z_q, one per slot. Each one can be inverted from the left unless an event of probability "
     "about 1/q happens, and this is where the 2^-15 and 2^-38 bounds come from. So any observer solves the system slot by "
     "slot and gets s1,i exactly. Shortness plays no role, because no lattice problem is involved. With k = ℓ = 1 the "
     "commitment is just a·s mod q, and dividing by a gives back s. The tempting reasoning is that discrete log commitments "
     "hide, so lattice ones should too. It fails because g^x hides x only because discrete logarithms are hard, while A·x "
     "is a linear map, and linear maps are easy to undo.")
para("**Attack 2 in detail.** Look at one coefficient of s′. A single sample b = −c·s′ + e places a sum of τ secret "
     "coefficients in a window about 2γ2 wide. This is far wider than the range of the secret, so one sample says almost "
     "nothing. Averaging over many independent challenges shrinks the uncertainty like 1/√(Nτ). Once it falls below 1/2, "
     "each coefficient can be rounded. The factor γ2²/τ in (1) shows why ML-DSA-44, with its small γ2 = (q−1)/88, leaks "
     "the most per signature. Two points matter for P1. Formula (1) treats the noise as Gaussian and so wastes the "
     "information in its sharp edges. It also recovers s′ one coefficient at a time, while integer programming and lattice "
     "reduction use all the constraints together.")

heading("2.4 Leakage attacks on lattice signatures", 2)
para("Bootle et al. [17] introduced the ILWE view of linear leakage in BLISS. Zhou et al. [18] show that the challenges of "
     "rejected Dilithium signatures bound c·s from both sides, and they recover keys by integer linear programming (ILP). "
     "Damm et al. [19] define Concealed ILWE, where only some samples leak, and break masked Dilithium with Huber and "
     "Cauchy regression. Yates et al. [20] find that least squares attacks on captured signatures are not enough at the "
     "parameters they studied. So any threshold design that releases values linked to c·s1 or c·s2 must be tested with "
     "estimators stronger than least squares. These include bounded noise estimators, ILP, robust regression and lattice "
     "reduction.")
para("**Why a summed nonce leaks.** Suppose each of T parties adds a uniform nonce share. The total then follows a bell "
     "shaped Irwin–Hall distribution, and z = y + c·s1 is that bell moved by c·s1. So each signature carries a little "
     "Fisher information about s1. Kao [12] bounds the loss below 0.013 bits per signature, but [10] proves an attack after "
     "about 2^30 signatures at ML-DSA-65. A design must therefore either make the revealed nonce exactly uniform, as Quorus "
     "and Trilithium claim, or limit the number of signatures, as TALUS does.")
para("**Corruption models.** With static corruption the attacker picks the corrupted parties before the protocol starts. "
     "With adaptive corruption it can pick them while the protocol runs. Dishonest majority security, as in Mithril, "
     "allows T−1 corrupted signers. Honest majority security, as in Quorus and TALUS-MPC, needs N ≥ 2T−1. Without "
     "identifiable aborts, as in Mithril, a corrupted party can abort after seeing the honest parties' messages and try "
     "again. The aborted transcripts then become part of what the attacker sees. For this reason the harness treats the "
     "corruption model as an input, not a fixed setting.")
para("**Countermeasures.** Masking splits secrets into shares so that no value in between is linked to the key. But [19] "
     "shows that masking alone fails when some samples leak with little noise. Against leakage from rejection, the defence "
     "is to hide which check failed and to release nothing computed from a rejected answer. This is why Quorus needs a "
     "careful simulation argument for releasing (w1, c, ⊥). Each defence has a cost. Masking costs time, a signing cap "
     "costs key changes, and hiding rejected transcripts costs extra interaction.")

heading("2.5 Related and older work", 2)
para("The Mithril line began as a poster [6] and an early ePrint that has since been withdrawn [5]. All Mithril claims here "
     "come from [4] and [7]. Kao's design [12] is not a Call submission, but TALUS builds on it and it shows the same "
     "patterns. Its fully distributed profile P2 broadcasts masked commitments. The paper's own remarks show that an "
     "exposed value λ_h·A·y_h gives y_h and then the key. The masks hide these values only when |S∖C| ≥ 2, that is, when "
     "at least two signers are honest. The paper admits that mask hiding fails in P2 at T = N with N−1 corrupted parties. "
     "Yet its Table 1 still claims unforgeability with a dishonest majority, with UC proofs against static attackers. Its "
     "Irwin–Hall analysis bounds the loss by 0.013 bits per signing query and calls this meaningful for q_s < 16,000.")

heading("2.6 Recent work from 2024 to 2026 (added in Phase 2)", 2)
para("**Lattice threshold designs that give up ML-DSA compatibility.** Espitau, Katsumata and Takemure [27] give a two "
     "round lattice threshold signature under a new assumption, algebraic one more MLWE. Its signatures are about 11 KB "
     "even for 1024 signers. Ringtail [26] reaches two rounds from standard LWE. Its first round does not depend on the "
     "message, its signatures are 13.4 KB, it needs 10.5 KB of online communication at 1024 parties, and it was run across "
     "8 countries. These authors have joined forces in Tanuki [28], a two round scheme based on Raccoon that was announced "
     "for the same NIST call. Its signatures are not ML-DSA signatures, so it falls outside our four targets. Together "
     "these schemes show the price of FIPS 204 compatibility. Giving it up buys fewer rounds and thousands of parties. "
     "TOPCOAT [29], from the Cybernetica group behind Trilithium, is an earlier two party Dilithium protocol with public "
     "key compression and fewer rounds, based on MLWE and MSIS.")
para("**Follow ups to the ML-DSA proposals.** Rambaud, Roth and Urban [30] turn Mithril into a “threshold signatures as a "
     "service” variant called ML-DSaaS. It merges the first two rounds into one round that does not depend on the message, "
     "and reports an online phase two to three times faster. A preprint by Meng [31], posted on 20 October 2026 after our "
     "experiments, studies nonce repetition caused by faults. If a party's device is forced to reuse its nonce across "
     "sessions, the responses it reveals expose its share. The preprint reports exact key recovery on Mithril. It rates "
     "Quorus as immune, because responses of single parties are never revealed. It rates TALUS as exposed only if the one "
     "time preparation is skipped, and Trilithium as fragile under faults. This is a physical fault model, outside our "
     "model in which the attacker sees only transcripts. We read only its abstract page and have not reproduced it.")
para("**Better leakage estimators for ML-DSA.** Two 2026 preprints improve the toolbox of Section II-D for a single ML-DSA "
     "signer when one bit of the nonce leaks with each signature. Schubert et al. [32] replace linear regression with "
     "constraint solving and hill climbing. They need 37 to 68 times fewer relations, between 5,000 and 35,000. Paskarbeit "
     "et al. [33] estimate the bit error rate of noisy leakage and cut the relations needed by 20 to 44%. Both agree with "
     "the lesson of our P1 result. Estimators that use the exact structure of the leakage beat plain least squares by "
     "orders of magnitude. Finally, HAETAE [34] is the main other Fiat–Shamir with aborts signature built on hyperball "
     "sampling. Section V-B uses it to check Mithril's intersection bound.")

heading("2.7 Gaps and comparison", 2)
bullet("**No systematic public testing** of Mithril, Quorus or Trilithium transcripts. There are only arguments at the "
       "design level.")
bullet("**The TALUS cap** sits about 2 bits below the authors' wall and 14 to 17 bits below Niot's unoptimised estimate "
       "(1). A better bounded noise or ILP estimator could close this gap.")
bullet("**Rejected attempt transcripts** (Quorus, Trilithium) and **Mithril's accepted distribution and hint loss** (7 to "
       "12 bits reported, proof for Q_s = 2^50 only) have not been checked independently.")
bullet("**Gaps in the corruption model.** Some proofs cover static corruption only, some need an honest majority, and some "
       "have side conditions such as |S∖C| ≥ 2.")
para("Only Mithril tolerates a dishonest majority, but it is limited to N ≤ 6. Quorus scales, but needs an honest majority "
     "and many rounds. Trilithium covers a phone and a server with a trusted helper. TALUS uses the fewest rounds, but its "
     "s2 protection is a usage limit rather than a structural argument. Independent testing therefore helps most where a "
     "proof contains a margin (TALUS), a heuristic (Trilithium) or a changed distribution (Mithril). The quality of the "
     "evidence also differs. Mithril and Quorus have reductions in the (quantum) random oracle model. Trilithium has a UC "
     "proof that rests on an MLWR type assumption. TALUS has an information theoretic argument with a numerical margin. A "
     "margin is the one kind of evidence that an experiment can check directly. This is one more reason to make the TALUS "
     "cap the core problem.")

heading("2.8 A reusable attack checklist", 2)
para("From the attacks above, Table IV lists ten questions that can be asked of any threshold ML-DSA design. They shape "
     "both the survey and the harness of Section IV.")
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
], [0.4, 3.2, 2.9], "Attack checklist drawn from the survey")
heading("2.9 Literature matrix", 2)
para("Table V rates each source for relevance (H central, M supporting, L background) and marks its themes. The themes are "
     "TS threshold signatures, MD ML-DSA compatible, AT attack or leakage, SS secret sharing or MPC, RS rejection sampling, "
     "and ST standard. Rows [26] to [34] were added in Phase 2 (Section II-F). Ref. [25] was added in Phase 2 for the "
     "Mithril finding and is not part of the survey matrix.")
table([
    ["Ref", "Year", "Rel.", "TS", "MD", "AT", "SS", "RS", "ST"],
    ['[1] FIPS 204', '2024', 'H', '', 'x', '', 'x', '', 'x'],
    ['[2] Dilithium', '2018', 'M', '', 'x', '', 'x', '', ''],
    ['[3] IR 8214C', '2026', 'H', 'x', 'x', '', '', '', 'x'],
    ['[4] Mithril ePrint', '2026', 'H', 'x', 'x', '', 'x', 'x', ''],
    ['[5] Reloaded', '2025', 'L', 'x', 'x', '', '', 'x', ''],
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
    ['[26] Ringtail', '2025', 'M', 'x', '', '', 'x', '', ''],
    ['[27] AOM-MLWE TS', '2024', 'M', 'x', '', '', 'x', '', ''],
    ['[28] Tanuki PW', '2026', 'M', 'x', '', '', 'x', '', 'x'],
    ['[29] TOPCOAT', '2024', 'M', 'x', 'x', '', 'x', 'x', ''],
    ['[30] ML-DSaaS', '2026', 'H', 'x', 'x', '', 'x', 'x', ''],
    ['[31] Fault nonce rep.', '2026', 'H', 'x', 'x', 'x', '', '', ''],
    ['[32] Descent', '2026', 'M', '', 'x', 'x', '', 'x', ''],
    ['[33] Noisy leakage', '2026', 'M', '', 'x', 'x', '', 'x', ''],
    ['[34] HAETAE', '2024', 'L', '', '', '', '', 'x', ''],
], [1.5, 0.4, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3], "Literature matrix of the 33 surveyed sources")
para("Of the 33 sources, 15 are central, 11 supporting and 7 background. The two withdrawn ePrints [5] and [15] are "
     "background only, and no claim rests on them. Twenty two sources appeared in 2025 or 2026, and 31 of the 33 in 2018 "
     "or later. The sources marked AT are the evidence base for the estimators in Section IV.")
para("**Design rules that follow from the survey.** Do not publish any linear image of a secret or nonce under A, however "
     "it is masked, unless the mask still hides it under the worst corruption allowed (checklist items 1 and 8). Keep the "
     "nonce as secret as the key, also in blame and abort steps (item 2). Keep every single signer rejection check, or "
     "prove that the replacement leaks no more (item 3). Limit the signatures per key only with a margin that a good "
     "estimator, not just least squares, cannot close (item 4). The history of the First Call shows that these rules are "
     "easy to break when patterns from discrete log protocols are copied over.")

heading("2.10 Attack surface, Phase 1 hypotheses and verdicts after full reading", 2)
para("Below, each Phase 1 hypothesis is listed with its verdict after we read the papers and ran the harness. Details are "
     "in Section V. “Confirmed” means the paper text supports the hypothesis. It does not mean an attack.")
para("**Mithril.** (i) Loss through accepted answers beyond 2^50 queries. Confirmed as a proof gap. Under the paper's own "
     "theorem the published parameters give Q_s = 2^26 to 2^37 (Section V-B). (ii) Hint loss of 7 to 12 bits. Revised. "
     "Our rerun of the lattice estimator gives up to 23.9 bits for ML-DSA-65. (iii) Adaptive corruption and (iv) selective "
     "aborts. Not examined further. (v) Floating point sampler. We ran the Go code, and its transcripts show no s2 leak "
     "(Section V-B). We did not audit the sampler itself.")
para("**Quorus.** (i) Revealing values on rejection is proven to be simulatable. Confirmed, but the proof is computational "
     "(based on MLWE), not statistical. We also correct our own earlier wording. A·y + e_w is uniform for each coefficient "
     "on its own, not as a whole vector, so only simple statistical tests are ruled out. (ii) Only ⊥ is revealed. "
     "Confirmed. The batched OR step has 40 bit soundness. (iii) Building blocks. We found two text errors (Section V-D), "
     "not attacks. (iv) Honest majority boundary. Narrowed, since the paper treats only n = 2t+1.")
para("**Trilithium.** (i) Revised. After a rejection the released value is the commitment w_H, not a partial signature, "
     "under an explicit MLWR type assumption. (ii) One declassified bit per attempt, as in ML-DSA retries. Confirmed. "
     "(iii) A malicious server that tampers with the rejection check. Confirmed as a simulation gap that is visible in the "
     "paper's own proof. It is worth at most about log2(attempts) bits, once. (iv) The CRP is trusted, and a CRP that "
     "colludes with the server is fatal by design.")
para("**TALUS v0.22.** The cap is the whole s2 argument and the noise has sharp edges. We measure this in Section V-A. "
     "**Kao P2.** The hypothesis is strengthened to a key exposure, shown at full ML-DSA size (Section V-C).")

# ---------------- Problem formulation ----------------
heading("3. Problem Formulation")
heading("3.1 Threat model and notation", 2)
para("A (T, N) threshold scheme Π has a transcript distribution Tr_Π(sk, m). This is everything an attacker sees while m is "
     "signed, including broadcasts, the state of corrupted parties and aborted attempts. The attacker corrupts, in "
     "advance, as many parties as the scheme allows. It watches q_s signing sessions, and it wins if it recovers the "
     "secret. Recovering s1 is enough, since s2 then follows from t. We study key recovery because it is stronger evidence "
     "than a small statistical bias. Table VI adds the notation not defined in Section I.")
table([
    ["Symbol", "Meaning"],
    ["s′, t0", "s′ = s2 − t0, where t0 holds the d = 13 dropped low bits of t"],
    ["e, b", "e = LowBits(w) rounding residue; b = −c·s′ + e one observation"],
    ["(T, N), S, C", "Threshold, parties; signing set S, corrupted set C"],
    ["q_s, N, N*", "Sessions observed; signatures used; N* = N giving 95% success"],
    ["cap, wall", "TALUS per-key signature limit; authors' uniqueness wall q_uniq"],
], [1.1, 5.4], "Notation added for Sections III to V")
para("What each scheme publishes on top of the signature (c, z, h) decides which checklist items apply. Table VII lists "
     "it as confirmed by our full readings in Phase 2.")
table([
    ["Scheme", "Published beyond (c, z, h)", "Aborted attempts"],
    ["Mithril", "Per-party MLWE-sample commitments w_i; round messages", "Commitments still released; no identifiable aborts"],
    ["Quorus", "MPC messages; w1 of every attempt", "Releases (w1, c, ⊥); one pass/fail bit only"],
    ["Trilithium", "Two-party MPC messages; CRP values", "Releases w_H and one declassified bit"],
    ["TALUS v0.22", "ZK well-formedness proofs; blame data", "None online: nonces pre-filtered, bound to quorum"],
], [0.9, 2.5, 2.1], "What each scheme releases (after full reading)")

heading("3.2 Core problem P1, the TALUS signing cap", 2)
para("**The idea.** TALUS removes the s2 check, so each signature leaks one noisy equation in s′. The defence is to stop "
     "before enough equations pile up. BCC keeps the noise e inside (−γ2+β, γ2−β), so the noise has hard edges. A single "
     "sample near an edge rules out many candidate secrets. So a bounded noise estimator may need far fewer samples than "
     "least squares, whose error falls only like 1/√N. **Statement.** We are given observations b_j = −c_j·s′ + e_j, with "
     "each e_j inside the BCC interval. For each parameter set, find the number of signatures N* at which s′ is recovered, "
     "and checked against the public key, with probability 0.95. Then compare log2 N* with the cap and the wall. A value "
     "below the cap is a break. A value above it gives a margin of log2 N* minus log2 cap bits. **Success criterion.** N* "
     "with stated trials and seeds, a positive control (the estimator recovers a leaky variant) and a negative control "
     "(no false keys on genuine ML-DSA).")
para("**Why the cap needs measuring.** The public key already determines s2, so below the wall the protection is "
     "computational. The authors model a meet in the middle attack on the syndrome, with cost 2^{H/2} and leftover entropy "
     "H ≥ 502 (about 2^160). But the only proven floor is about 2^58 at ML-DSA-65 and 2^49 at ML-DSA-87, which is below "
     "128 bits. ML-DSA-44 has no public cokernel at all, since k = ℓ. Above the wall the observations alone determine s′. "
     "So an efficient estimator that works there recovers the key without any lattice work. Between the cap and the wall, "
     "safety rests on that unproven model. This is why P1 measures N* directly. **Hypothesis (stated in Phase 1).** "
     "Bounded noise and ILP estimators beat the least squares estimate (1) by a wide margin.")
heading("3.3 Stretch goals P2 to P4", 2)
para("**P2 (Mithril).** Check the Q_s = 2^50 accounting, and the hint loss from key sharing for the exact set of shares "
     "held by T−1 corrupted parties. **P3 (rejected attempts).** Test whether the transcripts of rejected attempts in Quorus "
     "and Trilithium depend on s1 or s2. **P4 (Kao P2).** Decide whether the masked commitments hide y when |S∖C| = 1, as "
     "the paper's Table 1 implies. Our Phase 1 hypotheses were as follows. For P2, a wall above 2^64 (no attack) with the "
     "hint loss worked out again. For P3, Quorus can be simulated thanks to e_w, while Trilithium's assumption holds only "
     "roughly. For P4, the masks fail at |S∖C| = 1. The success criteria were a numerical bound with its derivation (P2), a "
     "statistical test with a stated false positive rate and sample budget (P3), and an explicit key recovery on a toy "
     "instance or a reason why the masks hide (P4).")

# ---------------- Harness ----------------
heading("4. Proposed Solution, a Leakage Testing Harness")
figure(RES / "harness_architecture.png", 2.6,
       "Harness architecture. Our ML-DSA core produces every signing attempt with its secret internals. A scheme view "
       "keeps only what that scheme releases, so secrets stop there. An adapter turns the observations into pairs (c, b). "
       "The estimators never see the secret, and the experiments score them against the true key.")
para("**Design (Fig. 1).** The harness has three parts. (1) **ML-DSA core** (harness/mldsa). It covers the NTT, SHAKE "
     "sampling, hints, and signing and verification, and it keeps every attempt. It matches the dilithium-py "
     "implementation byte for byte and passes 81 official NIST ACVP vectors for key generation, signing and verification, "
     "for all three parameter sets. (2) **Scheme views.** Plain ML-DSA (negative control), a variant that leaks y "
     "(positive control), TALUS-BCC, TALUS v0.1 and Mithril, plus separate simulators for Quorus, Trilithium and Kao. "
     "(3) **Estimators.** Least squares. A bounded noise “edge” estimator, written as a Chebyshev linear program that makes "
     "the largest residual |b + c·s′| as small as possible, and solved on CPU or GPU. An ILP finishing step that searches "
     "for an integer s′ that fits every bound. And theory curves from Fisher information and Cramér–Rao bounds. Every "
     "recovery is checked against the true key, and every run is seeded and logged.")
para("**How the estimators work.** Least squares averages. Stacking N samples (c, b) gives an integer system with more "
     "equations than unknowns. Its solution has an error variance of about σ_e²/(Nτ) per coefficient, so the error falls "
     "like 1/√N. The bounded noise estimator uses the edges instead. If every |e| is at most a known bound, each sample "
     "gives a pair of linear inequalities, |b + c·s′| ≤ bound. The region that satisfies all of them is a polytope, and it "
     "shrinks roughly like 1/N rather than 1/√N. The Chebyshev linear program finds its centre, and rounding gives s′. ILP "
     "finishing replaces that rounding with an integer search inside the polytope, in the style of [18]. This helps when "
     "a few coefficients sit near a rounding boundary. The Fisher information I per signature sets the Cramér–Rao bound on "
     "the variance of any unbiased estimator. Key recovery then needs on the order of 4/(I·τ) signatures [10]. We keep "
     "robust regression (Huber, Cauchy [19]) and hint accounting with the lattice estimator for schemes where only some "
     "samples leak, or where corrupted parties hold partial information.")
para("**A view in action (TALUS).** For each signing attempt the core records y, w, c, z and which check failed. The TALUS "
     "view does three things. (1) It keeps only attempts whose nonce satisfies BCC, as the offline filter would. (2) It "
     "drops the secret fields. (3) It outputs what an observer can compute, v = A·z − c·t1·2^d and the hint, together "
     "with c. The adapter then forms b = −c·s′ + e. A version with a corrupted group of parties would add their shares. "
     "For schemes with aborts, the view outputs exactly the fields that the specification says a rejected attempt "
     "reveals, and nothing more. The estimator receives only the view's output, so any key it recovers could be recovered "
     "from public data.")
para("**Implementation.** The code is Python with numpy and scipy. The linear programs use the HiGHS solver. The ring "
     "products inside the edge estimator take about 90% of its run time. They run on an NVIDIA GPU with PyTorch in double "
     "precision, about three times faster than the CPU version, and we checked them against it. Least squares is solved "
     "exactly in one pass. After an FFT the equations for each frequency are independent, so each frequency needs a single "
     "division. This agrees with an iterative solver to 10^-13. Transcripts for several trials are built in parallel "
     "processes while the GPU solves.")
para("**Evaluation and validity.** Every experiment reports the signatures used, the fraction recovered, the cost and the "
     "parameter set. N* is the point where a logistic fit to the success counts reaches 0.95. We use 20 trials per N and "
     "Clopper–Pearson intervals. Recovery is checked against the true key, so a partial match is never counted as a "
     "break. Two kinds of risk remain. Internal risks, such as bugs in the primitives or an estimator that overfits, are "
     "handled by the ACVP vectors and by many random keys. External risks, such as our simulator differing from the real "
     "protocol or parameters changing before the packages appear, remain. This is why every TALUS number is labelled as "
     "based on our model. A negative result is stated only as a bound on what we tried.")
para("**End to end check (gate B).** We passed real ML-DSA-44 attempts through the TALUS view and the unchanged estimator. "
     "It recovered s′ for 2 of 2 keys at N = 2×10^5 and 4×10^5 accepted signatures, and for 0 of 2 at 10^5 (seed 2029). "
     "This agrees with N* in Table IX.")
para("**Least squares calibration (Fig. 2).** To check the simulator and the error law behind (1), we measured the least "
     f"squares error on ML-DSA-44 with n = 256 (one ring element) and plain LowBits noise. We used N ∈ {{10^3, 3·10^3, "
     f"10^4, 3·10^4, 10^5, 3·10^5}}, {LS['trials']} trials per N and seed {LS['seed']} (generator "
     f"default_rng([{LS['seed']}, N, trial])). The mean RMS error stays within {LS_DEV:.0f}% of γ2/√(3τN) at every N. Real "
     "TALUS v0.1 signatures (keys from seeds 101 to 103) fall on the same curve. Extending the curve, rounding every "
     "coefficient correctly needs on the order of 10^9 signatures. So least squares alone is far from the cap, and the "
     "bounded noise estimator is what matters for P1.")
figure(RES / "ls_error_vs_N.png", 3.2,
       f"Least squares RMS error per coefficient against the number of signatures N (ML-DSA-44, n = 256). Blue shows the "
       f"synthetic channel, with the mean and the range over {LS['trials']} trials (seed {LS['seed']}). Orange shows real "
       "TALUS v0.1 signatures (seeds 101 to 103). The dashed line is the theory curve γ2/√(3τN).")
table([["N", "Measured RMS (min–max)", "Theory", "Ratio"]] + [
    [f"{r['N']:,}", f"{r['rms_mean']:.1f} ({r['rms_min']:.1f}–{r['rms_max']:.1f})", f"{r['theory']:.1f}",
     f"{r['rms_mean'] / r['theory']:.3f}"] for r in LS["rows"]
], [0.9, 2.0, 0.8, 0.7], f"Least-squares error, ML-DSA-44, {LS['trials']} trials per N, seed {LS['seed']}")
para("**Reading Fig. 2.** The slope of −1/2 on the log scale plot is the 1/√N law. The ratio column shows no drift with "
     "N, so treating the uniform LowBits noise as Gaussian is accurate here. At 3×10^5 signatures the RMS error is still "
     "16, which is 32 times the 1/2 needed for rounding. This is why least squares never recovered a key in any of our "
     "TALUS runs.")

# ---------------- Results ----------------
heading("5. Phase 2 Results")
heading("5.1 P1, margin of the TALUS cap (core result)", 2)
para("**Model assumption.** We model the TALUS s2 channel as b = −c·s′ + e, with e uniform on the BCC interval. The v0.22 "
     "writeup does not list the values released with each signature, so this is our reading, not the specification. "
     "Unless we say otherwise, N* is measured for one ring element out of k. Table IX sums up the margins.")
table([
    ["Set", "Cap", "Wall", "Element 95%", "Whole s2 95%", "Above cap / wall"],
    ["ML-DSA-44", "2^13", "2^15.2", "2^16.01", "2^16.09 (run)", "3.1 / 0.9"],
    ["ML-DSA-65", "2^14", "2^16.4", "2^17.40", "2^17.51 (extr.)", "3.5 / 1.1"],
    ["ML-DSA-87", "2^14", "2^16.2", "2^17.30", "2^17.51 (extr.)", "3.5 / 1.3"],
], [1.0, 0.5, 0.6, 0.9, 1.2, 1.0], "TALUS cap margins, n = 256, edge estimator with ILP finishing (whole-secret 95% point)")
figure(RES / "talus_success_vs_N.png", 3.2,
       "Key recovery success against the number of signatures N on the TALUS s2 channel, ML-DSA-44, n = 256, 20 trials "
       "per point. Grey is least squares (seed 2026), 0 of 20 everywhere. Blue is the edge estimator with rounding (seed "
       "2026). Orange is the edge estimator with ILP finishing (seed 2041). Green is the whole secret, all k = 4 elements, "
       "edge with ILP (seed 2081). The dashed lines are the authors' cap and uniqueness wall.")
para("**Why our method is better than the baseline (Fig. 3).** Least squares is the estimator behind Niot's attack (1). On "
     "the same transcripts it recovers nothing up to 2^17.8 signatures, and in our model it needs about 2^31.7. The edge "
     "estimator reaches 100% at 2^17.2. ILP finishing moves the curve about 1.1 bits further left, to 95% at 2^16.0 for one "
     "element. That is a gain of about 2^15.7 over the baseline, or roughly 5×10^4 times fewer signatures. The gain comes "
     "from using the known hard edges of the noise instead of averaging them away. The whole secret curve sits only about "
     "0.1 bit to the right of the one element curve.")
para("**Statistics.** Each point uses 20 independent trials (seed 2041, ILP time limit 120 s), with a logistic fit to the "
     "success counts. For one ring element of ML-DSA-44 we see 0 of 20 at 2^15.61, 11 of 20 at 2^15.87, 19 of 20 at "
     "2^15.99, and 20 of 20 from 2^16.10. ML-DSA-65 gives 16 of 20 at 2^17.29 and 20 of 20 at 2^17.71. ML-DSA-87 gives 18 "
     "of 20 at 2^17.18 and 20 of 20 at 2^17.49. **Whole secret.** An attacker needs all k elements from the same "
     "signatures. If the elements are independent, 95% success for the whole secret needs p_elem^k = 0.95, where p_elem is "
     "the success rate for one element. For ML-DSA-44 we ran it (seed 2081, 20 whole secrets per N). We got 3 of 20 at "
     "2^15.92, 15 of 20 at 2^16.01 and 18 of 20 at 2^16.10. These lie inside the intervals of the predicted 0.26, 0.77 and "
     "0.90, so the extrapolations for ML-DSA-65 and 87 can be trusted. Without ILP, with plain rounding, the points sit "
     "about 1 bit higher (for ML-DSA-44, N*99 = 1.45×10^5). **Controls.** We ran real ML-DSA-44 signing without the r0 "
     "check, which is the second rejection check of Section I on r0 = LowBits(w − c·s2). The estimator recovered the "
     "secret element s2 − t0 (one ring element) in 9 of 9 runs (3 keys, each at N = 2, 4 and 8×10^5). On genuine ML-DSA it "
     "returned the secret for 0 of 18 keys (15 of them from seed 2027). It only ever returned −t0, which is already "
     "equivalent to public data. So the false positive rate is below about 15% at 95% confidence (Table X). **Verdict.** "
     "No break. The margin above the cap is about 3 to 3.5 bits, and above the authors' wall only about 1 bit. This is much "
     "thinner than the 12 to 15 bits that (1) suggests.")
table([
    ["Run (ML-DSA-44, one element)", "Seed", "Keys × N", "Edge: secret", "Edge: −t0", "LS: secret", "Time"],
    ["Positive: no r0 check", "2026", "3 × {2,4,8}e5", "9/9", "0/9", "0/9", "49–74 s"],
    ["Negative: genuine ML-DSA", "2026", "3 × {2,4,8}e5", "0/9", "9/9", "0/9", "41–58 s"],
    ["Negative: genuine ML-DSA", "2027", "15 × 2e5", "0/15", "15/15", "0/15", "40–61 s"],
    ["Gate B: real signing, TALUS view", "2029", "2 × {1,2,4}e5", "0/2, 2/2, 2/2", "–", "–", "46–67 s"],
], [1.7, 0.45, 0.95, 0.85, 0.65, 0.65, 0.65],
   "Controls and end-to-end check: same estimator settings in every run; time is the GPU estimator per run")
para("**Other ways to attack the cap, all closed.** (a) Changing the key is a fresh key generation (v0.22 Sec. 2.3), not a "
     "refresh of the shares, so leakage does not carry over. (b) Rejected attempts stay offline. The rare online failures "
     "add at most about 0.03 bits. (c) A corrupt insider can subtract its own nonce shares, but in the MPC version at "
     "least T honest shares remain. The insider wall is 2^24.8 to 2^29.7, which is 12 to 16 bits above the cap (Table XI). "
     "A simulation with two honest shares (n = 8) shows that maximum likelihood needs 1.5 to 2 times what the formula "
     "says, so the formula favours the attacker. Only the TEE variant, which is not proposed, falls below the cap, from "
     "T = 7, 11 and 9 for ML-DSA-44, 65 and 87, as the authors admit. (d) A corrupt coordinator sees a value outside the "
     "box once every 2^33.1, 2^35.5 and 2^37.3 sessions by our exact convolution. This is within one bit of the authors' "
     "figures. (e) Below the wall the estimate is only a soft hint, with 43% of coefficients right at the cap. Used in a "
     "lattice attack, it lowers the cost of recovering the ML-DSA-44 key from 2^123.8 to 2^120.6. So a lattice attack "
     "cannot finish the job under the cap.")
table([
    ["Set (cap)", "MPC insider, T = 2..6", "Margin over cap", "TEE coalition, T = 2", "TEE below cap from"],
    ["ML-DSA-44 (2^13)", "2^24.8–2^26.1", "+11.8 to +13.1", "2^14.6", "T = 7"],
    ["ML-DSA-65 (2^14)", "2^28.5–2^29.7", "+14.5 to +15.7", "2^16.4", "T = 11"],
    ["ML-DSA-87 (2^14)", "2^28.2–2^29.4", "+14.2 to +15.4", "2^16.1", "T = 9"],
], [1.25, 1.25, 1.1, 1.15, 1.0],
   "TALUS insider walls (signatures a corrupt insider needs), rough Fisher formula; m = 2 case checked exactly")
para("**From toy rings to full size.** We first ran the edge estimator on smaller rings, n = 8 to 128, with 10 to 20 "
     "trials per point and ML-DSA-44 numbers (Fig. 4). N* per element levelled off around 1 to 2×10^5 (2.8×10^5 at n = 64 "
     "and 1.9×10^5 at n = 128) instead of falling toward the cap. This is why we then made the full size runs above "
     "denser. At n = 64 the harder target s2 − t0 needed the same N* as s2, and plain LowBits noise behaved like BCC "
     "noise. Compared with plain least squares (about 3.6×10^9 in our model), the edge estimator gains about four orders "
     "of magnitude. Without ILP, however, it stays 4 to 4.5 bits above the cap. The least squares figure is about 12 times "
     "estimate (1), which is 3.1×10^8, for a simple reason. Formula (1) only asks that the typical error per coefficient "
     "fall to 1/2. Rounding all 256 coefficients correctly at once needs the error to be about 3.5 standard deviations "
     "inside 1/2. Since the error shrinks like 1/√N, this costs a factor of about 3.5² ≈ 12 in N. The theory module "
     "explains the shape. For one coefficient alone, the error under uniform noise falls exactly like 1/N, which we "
     "checked by Monte Carlo. When all 256 coefficients are solved together, a fitted coupling constant of about "
     "0.76·τ^0.42 explains why the real N* sits 1.5 to 2 bits above the single coefficient formula. ILP finishing lowers "
     "the 50% point by a factor of 1.0, 1.1, 1.1 and 1.5 at n = 8, 16, 32 and 64. This fits the factor of about 2 at n = 256.")
figure(RES / "talus_ladder.png", 3.2,
       "Success of the edge estimator (rounding, no ILP) for one ring element against N, ML-DSA-44 BCC channel, ring size "
       "n = 8 to 256 (20 or 10 trials per point as labelled, script default seed 2026). Larger rings need fewer signatures "
       "per element. So the full size n = 256 is the one that matters, and toy sizes make the attacker look weaker than it is.")
para("**Limits of the P1 result.** (i) The channel model is our reading of TALUS, not a quote from the specification. It "
     "assumes independent uniform noise on the BCC interval, no wrap around, and no use of the hint. (ii) We ran the whole "
     "secret experiment for ML-DSA-44 only. ML-DSA-65 and 87 are extrapolated. (iii) We did not use the hint h separately, "
     "and the lattice estimate is a Python core-SVP model. Core-SVP counts only the cost of the single shortest vector "
     "search inside lattice reduction, which is the usual cautious way to price lattice attacks. So N* is an upper bound "
     "on what an attacker needs. (iv) The wall and cap figures are the authors'. We did not work out the wall again ourselves.")
heading("5.2 TALUS v0.1 and Mithril", 2)
para("**TALUS v0.1 (Niot's attacks reproduced).** We implemented the arXiv v2 design [10] with ML-DSA-44, |S| = 3, keys "
     "from seeds 101 to 103, and a DKG simplified to Shamir sharing. Attack 1 recovered s1 exactly from the key generation "
     "broadcast (3 of 3 keys) and from one MPC signature (60 of 60). Attack 2 by least squares follows the theory curve up "
     "to N = 10^5 (Fig. 2) and would need about 1.2×10^9 signatures. A separate check on real ML-DSA-44 transcripts "
     "without the check gave 0.97 times Niot's error formula (12 runs). On the same transcripts the edge estimator needed "
     "about 1,500 times fewer signatures than his least squares N. Our simplifications were plain ML-DSA key generation "
     "followed by Shamir sharing of s1 instead of the paper's DKG, the MPC computation of w1 replaced by its correct "
     "output, and |S| = T = 3 throughout. The exercise shows why TALUS changed its design. It also shows that our views "
     "reproduce a published break exactly.")
para("**Mithril proof parameter gap (P2).** Theorem 3.2 of [4] bounds the number of safe queries using a lemma on the "
     "intersection of hyperballs. The lemma is taken from the ePrint full version of Devevey et al. [25] (App. A.6). That "
     "bound uses the exponent n−1, where a correct cylinder argument gives (n−1)/2. For ML-DSA-44 it gives 2^-50.1, while "
     "the exact value is 2^-33.5. We reproduced this with the authors' own Sage parameter script. With the published "
     "parameters the theorem then covers Q_s = 2^26 to 2^37 queries rather than 2^50. Under the typical norm distribution, "
     "which is a heuristic and not a proof, most sets still reach 2^50, and some fall up to about 3 bits short. Corrected "
     "parameters need 1.3 to 8.5 times more parallel repetitions K (Table XII). The faulty bound appears only in the ePrint "
     "version, since the ASIACRYPT version states only the exact formula. Of 13 citing works we checked, only Mithril uses "
     "it. HAETAE [34], the other main hyperball scheme, computes the exact incomplete Beta value numerically and is not "
     "affected. Seen the other way, reaching 2^50 with the published radii would need the norm bound B in the proof to sit "
     "only 0 to 7 standard deviations above the mean norm of c·s. The proof, however, needs an overwhelming bound, and the "
     "paper's footnote says about 13. This is a proof gap, not an attack. Going slightly over the bound enlarges a Rényi "
     "divergence budget a little and does not obviously reveal s. We wrote a corrected bound with a proof. It uses the "
     "exponent (n−1)/2 and is within 0.04 bits of the exact value at Mithril sizes. It held at all 320 test points, while "
     "the printed bound failed at 149. **Real transcripts.** We ran the authors' Go signing code (ML-DSA-44, "
     "(T, N) = (2, 3), 110,000 slots, of which 39,461 had no party rejecting). Regressing the leftover of A·z − c·t − w on "
     "−c·s2 gives a slope of 0.004 ± 0.10, where 1 would mean an s2 leak. So accepted answers do not depend on s2. Only "
     "c·t0 remains, which is equivalent to public data, and we corrected our Mithril view to match. **Hint loss.** For the "
     "exact set of shares held by T−1 parties, the lattice estimator gives losses of 4.9 to 7.7 bits (ML-DSA-44), 17.7 to "
     "23.9 bits (ML-DSA-65) and 8.6 to 14.4 bits (ML-DSA-87), compared with the reported 7 to 12 bits (Table XIII).")
table([
    ["Set (15 (T,N) each)", "Thm 3.2, paper's B", "Typical case", "Below 2^50", "Corrected φ", "K factor, 2^50 / 2^64"],
    ["ML-DSA-44", "2^27.4–2^33.0", "2^46.7–2^53.5", "3", "5.27–5.64", "1.50–3.73 / 2.00–7.16"],
    ["ML-DSA-65", "2^26.0–2^34.9", "2^47.4–2^56.5", "4", "5.92–6.55", "1.60–8.53 / 2.00–23.2"],
    ["ML-DSA-87", "2^30.7–2^37.3", "2^53.7–2^60.6", "0", "7.09–7.66", "1.33–3.77 / 1.67–8.35"],
], [1.05, 1.1, 1.05, 0.65, 0.8, 1.35],
   "Mithril: signing queries Q_s covered, over all 45 published parameter sets (claimed 2^50); typical case is a "
   "heuristic from the empirical norm distribution; K factor is the extra parallel repetitions after correcting the lemma")
table([
    ["Set", "Reported loss", "Our estimate (Python)", "Lattice estimator"],
    ["ML-DSA-44", "7–12 bits", "4–7 bits", "4.9–7.7 bits"],
    ["ML-DSA-65", "7–12 bits", "14.6–20.7 bits", "17.7–23.9 bits"],
    ["ML-DSA-87", "7–12 bits", "7.6–12.8 bits", "8.6–14.4 bits"],
], [1.0, 1.0, 1.3, 1.3], "Mithril a posteriori key-sharing hint loss, exact T−1 share subset")
para("**Beyond 2^50 queries.** Signature schemes are usually assumed to face up to 2^64 queries. In Mithril the accepted "
     "answer is uniform on an intersection of balls. So the Rényi divergence has the closed form 1/(1−δ) at any order, and "
     "the shape alone causes no Fisher information leak. But at 2^64 queries every published set falls short of what the "
     "proof needs, by 27 to 38 bits under the theorem and by 3 to 17 bits under the typical case heuristic. Parameters "
     "corrected for 2^64 need K to be 1.7 to 23 times larger. Correcting only the faulty lemma at 2^50 lowers the radius "
     "ratio φ from 7 to 9 down to 5.3 to 7.7, and raises K by 1.3 to 8.5 times. The worst case is ML-DSA-65 with "
     "(T, N) = (5, 6), where K goes from 1,200 to 10,234. Communication grows with K. These figures are computed from the "
     "paper's formulas, not simulated.")
para("The Python core-SVP substitute reproduces the paper's 12 bits for ML-DSA-44 when given the paper's constant 0.74. The "
     "figure we quote is from the lattice estimator run (Sage 10.4, rough mode). Only ML-DSA-65 clearly goes beyond the "
     "claimed range. Both Mithril items are accounting and proof issues, and neither gives an attack on the scheme.")
heading("5.3 Kao's P2 profile (P4)", 2)
para("In the paper's own text (Fig. 1b, Remark 11, App. M.1), every party broadcasts W_i, and the pairwise masks cancel "
     "(Lemma 1). So Σ W_i = A·y is public. Gaussian elimination gives y, and then s1 = c⁻¹(z − y) from a single P2 "
     "signature, whatever |S∖C| is. The proof of Corollary 5 itself calls this value the public broadcast, and no later "
     "appendix changes it. **Shown at full size.** We re-implemented the scheme at the real ML-DSA-44, 65 and 87 sizes. The "
     "combined signatures pass the standard verifier, and we recovered s1 exactly from one signature for 15 of 15 keys "
     "per set (Table XIV). We used (N, T) = (3, 2), (5, 3) and (5, 5), five keys each, seed 2051, and each attack took "
     "under 0.2 s. Holding back a single W_i drops this to 0 of 15, so the attack really uses the sum. The author's code "
     "is not public, and our rejection checks run in the open rather than inside the paper's MPC. Our earlier toy version "
     "(ring size 8, real q) also checks the narrower Phase 1 hypothesis. With all signers but one corrupted, the honest "
     "party's mask can be removed and λ_h·A·y_h inverted. With two honest signers this route fails, as the paper says. The "
     "sum route above, however, works whatever the number of honest parties. Two more points. Corollary 6 claims the full "
     "threshold signature functionality without the condition |H| ≥ 2 that its Simulator 17 needs. And the key generation "
     "commitment t(i) = A·s1(i) + s2(i) carries the noise s2(i), so the bare A·s1,i pattern broken in TALUS does not "
     "appear there.")
table([
    ["Step", "Key recovery from one P2 signature (public data only)"],
    ["Input", "pk = (ρ, t1); message; signature (c̃, z, h); broadcast values W_i of the accepted attempt"],
    ["1", "w ← Σ_i W_i mod q (pairwise masks cancel, so w = A·y)"],
    ["2", "A ← ExpandA(ρ); move A and w to the NTT domain"],
    ["3", "For each of the 256 slots solve the k×ℓ system Â_j·ŷ_j = ŵ_j (A tall, invertible w.h.p.); y ← NTT⁻¹(ŷ)"],
    ["4", "c ← SampleInBall(c̃); s1 ← c⁻¹·(z − y) in R_q"],
    ["Check", "s1 short (‖s1‖∞ ≤ η) and consistent with t1; result 15/15 per set, 0/15 with one W_i withheld"],
], [0.55, 5.95], "Kao P2 attack as run at real ML-DSA-44/65/87 size")
heading("5.4 Quorus and Trilithium (P3)", 2)
para("Our Quorus implementation produced 272,664 signatures, and none failed FIPS 204 verification. By construction no "
     "statistical leak is possible at the level of single coefficients. We did not run a distinguisher at the lattice "
     "level. For Trilithium we used exact enumeration at n = 4 and Monte Carlo at n = 8 (2×10^8 samples, 3 trials). Both "
     "show the gap between the rejected w_H and the simulator shrinking as γ1 and n grow. For branch 2 at n = 8 it goes "
     "from 3×10^-5 to 7×10^-7. We also found errors in the papers, which are not attacks. Quorus Functionality 6 uses the "
     "bound γ2−β−η where every other place uses γ2−β (PDF p. 32). Quorus Lemma 8 prints the denominator 2(β+1)δ+1 instead "
     "of (2β+1)δ+1. An exhaustive check shows that the printed probabilities sum to only 0.84 to 0.95. Trilithium's "
     "simulation of unsuccessful signing (p. 24) leaves the gap noted in Section II-J.")
para("**Trilithium in more detail.** After a rejection, the released values come from two branches. In branch 3 the z "
     "check failed. In branch 2 the z check passed but the LowBits check failed. Exact enumeration at n = 4 showed a real "
     "but small gap between the rejected w_H and the simulator. It shrinks as γ1 grows, roughly like γ1^-2.7 for branch 3. "
     "A branch 2 floor near 10^-4 remained for γ1 ≥ γ2 at q = 257, 513 and 1025, so it is not caused by a small q. It "
     "comes from the rounding cell that wraps around, and masking that cell removes it (30 to 65 times smaller). Exact "
     "convolution for n = 2 to 6 at q = 17 shows both gaps falling as n grows. Branch 3 falls by 2 to 3 orders of "
     "magnitude from n = 4 to 6 (Fig. 5). The figure also shows that the trend is not steady from n = 3 to 4. At n = 8 the "
     "branch 3 gap is below the Monte Carlo floor of about 3×10^-7. Toy sizes cannot prove anything about n = 256, but "
     "every trend points toward the assumption holding statistically. A distinguisher at the lattice level remains "
     "untested. On the server tampering issue (H-F3), a server that tampers with the rejection check is detected and "
     "stopped. So the leak is bounded by the stopping time, about log2(attempts) bits, once. The problem is that the "
     "paper's simulation does not reproduce how that stopping probability depends on the real z.")
figure(RES / "trilithium_gap.png", 3.2,
       "Trilithium toy model (q = 17, γ2 = 4, τ = 1). The plot shows the squared Hellinger distance H² between the "
       "rejected w_H distribution and the paper's simulator, for each rejection branch. Telling them apart needs about "
       "1/H² rejected attempts. For n = 2 to 6 the values are exact (mean of 5 keys, seed 2026 + n). For n = 8 they come "
       "from Monte Carlo (2×10^8 samples, 3 keys, seed 2026, bias corrected). An open marker means below the sampling floor.")
para("**Quorus in more detail.** Apart from the two text errors, the batched OR protocol has statistical soundness 2^-39 "
     "(κ = 40). So about one rejected attempt in 2^39 is wrongly declared a pass, and its failing z, which depends on the "
     "key, is opened. At roughly 10^11 signatures this is not practical, but 40 bit statistical security is lower than "
     "usual. A rough reduction, which is ours and was not run, suggests that the MLWE instance behind Theorem 2 is about as "
     "hard as recovering the ML-DSA key itself.")
heading("5.5 Disclosure status", 2)
para("We have not yet reported the Kao P2 and Mithril findings to the authors. Coordinated disclosure is pending, and both "
     "are stated here neutrally as our reading of public documents. The Quorus and Trilithium items are errata.")

# ---------------- Phase 3 and conclusion ----------------
heading("6. Phase 3 Prototype and Conclusion")
para("**What the Phase 3 prototype will show.** It will be a complete tool for measuring the TALUS cap margin. It takes "
     "transcripts produced by the TALUS reference code (packages expected from March 2027) and passes them through a "
     "scheme view. It then runs the bounded noise estimator with ILP finishing and reports N* and the margin in bits "
     "against the cap and the wall. It also runs the positive and negative controls automatically, so a margin is never "
     "reported without them. In concrete terms it will (i) replace our channel model with the values the real code "
     "releases, (ii) run the whole secret ILP for ML-DSA-65 and 87 instead of extrapolating, and (iii) rerun the Mithril "
     "parameter check on the submitted parameters. Success means reproducing Table IX on real transcripts, or explaining "
     "any difference, with each margin reported together with its controls. Until the packages appear, the prototype runs "
     "on our TALUS view, so the demonstration does not depend on the release date. The demonstration will be a single "
     "command. It takes a transcript file and a parameter set and prints the margin table with its controls, trial counts "
     "and seeds. The stretch goals continue alongside it. These are a lattice level distinguisher for rejected "
     "transcripts, and disclosure to the Kao and Mithril authors.")
table([
    ["Stage", "Phase 2 item (Phase 1 plan)", "Status (29 Oct 2026)"],
    ["1", "ML-DSA primitives, interface, ILWE sanity check", "Done: 81 ACVP vectors; 0.97× Niot's formula"],
    ["2", "TALUS cap, bounded-noise and ILP (P1)", "Done: 20 trials/point; whole secret run for -44"],
    ["3", "Mithril accepted z, hint accounting (P2)", "Done: proof gap, corrected bound; Go transcripts"],
    ["4", "Quorus, Trilithium rejected attempts (P3)", "Done at statistical level; lattice test not run"],
    ["5", "Kao P2 and DKG claims (P4)", "Done: key from one signature at full size"],
    ["6", "Rerun on reference code (from Mar. 2027)", "Phase 3; Mithril script and Go code run so far"],
], [0.5, 3.0, 3.0], "Phase 2 plan against outcome, and the hand-over to Phase 3")
para("Table XV compares the Phase 1 plan with what Phase 2 delivered.")
para("**Research questions, answered.** (RQ1) Which threshold ML-DSA designs exist? There are four First Call proposals. "
     "They differ in corruption model, number of parties and rounds (Table II). (RQ2) Which are broken? Earlier TALUS "
     "versions, by two attacks that we reproduced. Kao's P2 profile also exposes the key from one signature, going by the "
     "paper's own text. (RQ3) Which techniques work? Linear inversion of a published A·x, recovery from a leaked nonce, "
     "and for the TALUS channel a bounded noise estimator with ILP finishing. The last is about four orders of magnitude "
     "better than least squares. (RQ4) Where is the evidence thinnest? The TALUS cap margin, now measured at about 3 to "
     "3.5 bits above the cap. Mithril's accounting between parameters and proof. And the untested question at the "
     "lattice level for rejected transcripts in Quorus and Trilithium.")
para("**Lessons from Phase 2.** Three points about method carry over to Phase 3. First, controls change conclusions. "
     "Without the negative control, the estimator's output −t0 on genuine ML-DSA could have been mistaken for leakage. "
     "Second, runs at reduced size can mislead in either direction. The ML-DSA-87 shortcut at n = 64 overstated the "
     "margin, and the ILP gains grow with n. So we quote only full size numbers. Third, reading the papers in full "
     "corrected two of our own Phase 1 statements. Trilithium releases w_H, not a partial signature, and uniformity holds "
     "only for each coefficient on its own. This is why every hypothesis in Section II-J now has a verdict.")
para("**How this work differs from earlier work.** Earlier cryptanalysis of lattice signatures [17] to [20] targets a "
     "single signer that leaks through a physical side channel. Here the leakage is logical. It is part of the protocol "
     "transcript, any observer or corrupted party can see it, and its noise distribution is known exactly from the "
     "specification. So our results carry over across implementations, and schemes that were analysed only by proof gain "
     "an independent check by experiment.")
para("**Ethics.** We study only public specifications at the standardisation stage, as NIST invites. We share findings "
     "about a scheme with its authors before any public posting. We keep confirmed key recovery, measured margins, proof "
     "gaps and errata apart, and we label results that rely on our simulators rather than on the authors' code.")
para("**Conclusion.** The survey of 33 sources showed that threshold ML-DSA designs fail when patterns from discrete log "
     "protocols are copied over, and that three of the four proposals had not been tested. In Phase 2 we built and checked "
     "a harness and measured the core quantity. The TALUS cap holds in our model, but only by about 3 to 3.5 bits for the "
     "whole secret and about 1 bit above the authors' wall. This is much less than least squares suggests. Insider, "
     "coordinator, key change and lattice finishing routes do not lower it. Our other findings are a gap between "
     "Mithril's parameters and its proof, a key exposure in Kao's P2 profile, and errata in Quorus and Trilithium. We will "
     "disclose these to the authors before any public posting.")

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
    ("C. Boschini, D. Kaviani, R. W. F. Lai, G. Malavolta, A. Takahashi, and M. Tibouchi", "Ringtail: Practical two-round threshold signatures from learning with errors", "in Proc. IEEE Symp. Security and Privacy, 2025, doi:10.1109/SP61157.2025.00070 (IACR ePrint 2024/1113)."),
    ("T. Espitau, S. Katsumata, and K. Takemure", "Two-round threshold signature from algebraic one-more learning with errors", "in Proc. CRYPTO 2024, Part VII, pp. 387–424; J. Cryptol., vol. 38, no. 4, 2025 (IACR ePrint 2024/496)."),
    ("C. Boschini, T. Espitau, A. Kaiser, S. Katsumata, D. Kaviani, R. W. F. Lai, G. Malavolta, T. Prest, P. Schwabe, A. Takahashi, K. Takemure, and M. Tibouchi", "Tanuki: Two-round threshold signatures from lattices", "NIST MPTC First Call preview writeup v0.1, Jan. 2026."),
    ("N. Snetkov, J. Vakarjuk, and P. Laud", "TOPCOAT: towards practical two-party Crystals-Dilithium", "Discover Computing, vol. 27, no. 1, art. 18, 2024, doi:10.1007/s10791-024-09449-2."),
    ("M. Rambaud, S. Roth, and A. Urban", "Threshold signatures as-a-service: Achieving threshold ML-DSA in one online round", "IACR ePrint 2026/814, Apr. 2026."),
    ("Y. Meng", "Fault-induced nonce repetition in threshold lattice signatures: A reveal-structure criterion, cross-scheme analysis, and detection boundaries", "IACR ePrint 2026/2566, Oct. 2026."),
    ("C. Schubert, N. J. Müller, J.-P. Seifert, and M. Margraf", "Descent into broken trust: Uncovering ML-DSA subkeys with scarce leakage and local optimization", "IACR ePrint 2026/472, Mar. 2026."),
    ("N. Paskarbeit, C. Schubert, M. Margraf, and J.-P. Seifert", "Statistical inference from noisy randomness leakage for ML-DSA attacks", "IACR ePrint 2026/1712, Aug. 2026."),
    ("J. H. Cheon, H. Choe, J. Devevey, T. Güneysu, D. Hong, M. Krausz, G. Land, M. Möller, D. Stehlé, and M. Yi", "HAETAE: Shorter lattice-based Fiat–Shamir signatures", "IACR Trans. Cryptogr. Hardw. Embed. Syst., vol. 2024, no. 3, pp. 25–75, 2024."),
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
