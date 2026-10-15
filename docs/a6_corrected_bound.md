# Corrected upper bound for Devevey-Fawzi-Passelegue-Stehle, App. A.6 (paper plan item 9)

Written 14 Oct 2026. Numerical check: `experiments/a6_corrected_bound.py`, output `experiments/results/a6_corrected_bound.txt`. The source and the error are described in `notes/schemes/mithril.md` ("Lemma 2.5 traced to its source").

## The printed statement and why it fails

Source: ePrint 2022/1249, App. A.6 (not in the ASIACRYPT 2022 proceedings, which give only the exact identity). Copied as Lemma 2.5 into Mithril (ePrint 2026/013). With $x = 1 - 1/\varphi^2$, it states

$$I_x\!\left(\tfrac{n+1}{2}, \tfrac12\right) < x^{\,n-1}\cdot n\cdot(1 - 1/\varphi),$$

"by placing the hyperspherical cap into a cylinder of height $1 - 1/\varphi$". The bound is smaller than the exact value at 149 of 320 grid points ($2 \le n \le 8192$, $1.05 \le \varphi \le 50$), including every Mithril parameter set. For example, at $n = 2048$, $\varphi = 7$: exact $2^{-33.53}$, printed $2^{-50.12}$. The cylinder's base is an $(n-1)$-ball of radius $\sqrt{x}$, so its volume carries $x^{(n-1)/2}$, not $x^{n-1}$.

## Proposition

Let $n \ge 2$, $\varphi > 1$, $h = 1/\varphi$, $x = 1 - h^2$. Then

**(a)** $\displaystyle I_x\!\left(\tfrac{n+1}{2}, \tfrac12\right) \;\le\; \frac{2V_{n-1}}{V_n}\, x^{(n-1)/2}(1-h) \;<\; \sqrt{\frac{2(n+2)}{\pi}}\; x^{(n-1)/2}(1-h),$

**(b)** $\displaystyle I_x\!\left(\tfrac{n+1}{2}, \tfrac12\right) \;\le\; \frac{2V_{n-1}}{V_n}\, \frac{x^{(n+1)/2}}{(n-1)\,h} \;<\; \sqrt{\frac{2(n+2)}{\pi}}\; \frac{\varphi\, x^{(n+1)/2}}{n-1}.$

Here $V_d = \pi^{d/2}/\Gamma(d/2+1)$ is the volume of the unit $d$-ball. Part (a) is the A.6 cylinder argument done correctly. Part (b) is sharper: within 0.04 bits of the exact value at the Mithril dimensions.

## Proof

*Cap identity.* Let $C = \{u \in B_n : u_1 \ge h\}$ be the cap of the unit $n$-ball at height $h$. The standard identity, which is DFPS22 Lemma 6 in the proceedings, is $\mathrm{vol}(C)/V_n = \tfrac12 I_{1-h^2}\!\left(\tfrac{n+1}{2}, \tfrac12\right)$. So $I_x = 2\,\mathrm{vol}(C)/V_n$. Slicing at $u_1 = t$ gives an $(n-1)$-ball of radius $\sqrt{1-t^2}$:

$$\mathrm{vol}(C) = V_{n-1}\int_h^1 (1-t^2)^{(n-1)/2}\,dt.$$

*(a)* For $t \in [h, 1]$, $1 - t^2 \le 1 - h^2 = x$. So the integral is at most $x^{(n-1)/2}(1-h)$. This is the cylinder of height $1-h$ over the base of radius $\sqrt{x}$.

*(b)* For $t \ge h$, $t^2 - h^2 = (t-h)(t+h) \ge 2h(t-h)$. So
$1 - t^2 = x - (t^2-h^2) \le x\left(1 - \tfrac{2h(t-h)}{x}\right) \le x\,e^{-2h(t-h)/x}$, using $1 - u \le e^{-u}$. Raising to the power $(n-1)/2 > 0$ and extending the integral to $\infty$:

$$\int_h^1 (1-t^2)^{(n-1)/2}dt \le x^{(n-1)/2}\int_0^\infty e^{-(n-1)hs/x}\,ds = \frac{x^{(n+1)/2}}{(n-1)h}.$$

*Volume ratio.* $\dfrac{2V_{n-1}}{V_n} = \dfrac{2}{\sqrt\pi}\,\dfrac{\Gamma(n/2+1)}{\Gamma(n/2+1/2)} < \dfrac{2}{\sqrt\pi}\sqrt{\tfrac n2 + 1} = \sqrt{\dfrac{2(n+2)}{\pi}}$. This uses Gautschi's inequality $\Gamma(y+1)/\Gamma(y+s) < (y+1)^{1-s}$ with $y = n/2$, $s = 1/2$. $\square$

## Numerical check (all 320 grid points)

| Statement | Below exact (invalid) | Largest slack over exact |
|---|---|---|
| Printed A.6 / Mithril Lemma 2.5 | 149 points | (not a bound) |
| (a) cylinder, exact ratio | 0 | |
| (a) closed form | 0 | 11.96 bits |
| (b) closed form | 0 | 6.35 bits (small $\varphi$); 0.04 bits at Mithril sizes |

| dim $n = 256(k+l)$ | $\varphi$ | exact | printed | (a) | (b) |
|---|---|---|---|---|---|
| 2048 (ML-DSA-44) | 7 | -33.53 | -50.12 | -25.49 | -33.49 |
| 2816 (ML-DSA-65) | 8 | -35.09 | -52.69 | -26.77 | -35.06 |
| 3840 (ML-DSA-87) | 9 | -37.56 | -57.07 | -28.94 | -37.53 |

(log2 values; exact computed with mpmath at 50 digits.)

## Corrected parameter condition

A.6 also derives a sufficient condition on $\varphi$ from the faulty bound, $1/\varphi^2 < 1 - (\varepsilon/n)^{1/(n-1)}$, and that condition inherits the error. A valid replacement for $I_x \le 2\varepsilon$, from (b):

$$\sqrt{\tfrac{2(n+2)}{\pi}}\;\frac{\varphi}{n-1}\left(1 - \tfrac{1}{\varphi^2}\right)^{(n+1)/2} \le 2\varepsilon.$$

Because (b) is within 0.04 bits of the exact value at the Mithril sizes, using it gives essentially the same $Q_s$ as the exact incomplete Beta value: about $2^{26}$ to $2^{37}$ at the published parameters, as already reported. Using the closed form of (a) would cost about 8 bits.

## Status and caveats

- The proof is elementary. It was checked numerically on the grid above, but no one else has reviewed it.
- "Exact" relies on the cap identity above (standard; DFPS22 Lemma 6) and on mpmath's regularised incomplete Beta function.
- Disclosure: per `docs/disclosure_drafts.md`, contact the Mithril authors first, then optionally DFPS. Nothing is public.
