"""Quorus' MPC-friendly ML-DSA signing (Algorithm 1 of ePrint 2025/1163), single attempt, Stage F.

Differences from FIPS 204 signing (as in the paper):
- w := A y + e_w with e_w uniform in [-eta, eta]^(k n) (added before Decompose);
- one attempt only; on rejection the transcript (w1, c, None) is released;
- second check on w0 - c e (e = s2), computed as LowBits(w) - c s2 without re-decomposing;
- hint from MakeHint(-c t0, A z - c t + c t0) (the "skip e_w" optimization), check ||c t0|| and weight.
`attempt` returns everything (including the signature if any) so the correctness of the released
signature can be checked with the standard FIPS 204 verifier. Experiments only, not constant time.
"""
from dataclasses import dataclass

import numpy as np

from ..mldsa import dsa
from ..mldsa import sampling as smp
from ..mldsa.hints import make_hint
from ..mldsa.ntt import intt, ntt
from ..mldsa.params import D, N, Q, Params
from ..mldsa.rounding import decompose, mod_pm


@dataclass
class QuorusAttempt:
    w1: np.ndarray
    c_tilde: bytes
    failed: str          # "" (signature), "z_norm", "w0_norm" (line 3), "ct0_norm", "hint_weight" (line 6)
    sig: bytes = None
    verifies: bool = None


class QuorusSigner:
    def __init__(self, p: Params, xi: bytes, add_ew=True):
        self.p, self.add_ew = p, add_ew
        self.pk, self.sk, sec = dsa.keygen_internal(xi, p)
        self.rho, self.tr = sec["rho"], sec["tr"]
        self.s1h, self.s2h, self.t0h = ntt(sec["s1"]), ntt(sec["s2"]), ntt(sec["t0"])
        self.t = sec["t"]
        self.a_hat = smp.expand_a(self.rho, p.k, p.l)

    def attempt(self, message: bytes, rng, ctx=b""):
        p = self.p
        m_prime = bytes([0, len(ctx)]) + ctx + message
        mu = dsa.H(self.tr + m_prime, 64)
        y = rng.integers(-p.gamma1 + 1, p.gamma1 + 1, size=(p.l, N))
        e_w = rng.integers(-p.eta, p.eta + 1, size=(p.k, N)) if self.add_ew else np.zeros((p.k, N), int)
        w = (intt(dsa.mat_vec_hat(self.a_hat, ntt(y % Q))) + e_w) % Q
        w1, w0 = decompose(w, p.gamma2)
        c_tilde = dsa.H(mu + dsa.w1_encode(w1, p), dsa.c_tilde_len(p))
        c = smp.sample_in_ball(c_tilde, p.tau)
        ch = ntt(c)
        cs1 = mod_pm(intt((ch[None, :] * self.s1h) % Q), Q)
        cs2 = mod_pm(intt((ch[None, :] * self.s2h) % Q), Q)
        z = y + cs1
        w0bar = w0 - cs2
        if np.abs(z).max() >= p.gamma1 - p.beta:
            return QuorusAttempt(w1, c_tilde, "z_norm")
        if np.abs(w0bar).max() >= p.gamma2 - p.beta:
            return QuorusAttempt(w1, c_tilde, "w0_norm")
        ct0 = intt((ch[None, :] * self.t0h) % Q)
        az = intt(dsa.mat_vec_hat(self.a_hat, ntt(z % Q)))
        ct = intt((ch[None, :] * ntt(self.t)) % Q)
        h = make_hint((-ct0) % Q, (az - ct + ct0) % Q, p.gamma2)
        if dsa.inf_norm(ct0) >= p.gamma2:
            return QuorusAttempt(w1, c_tilde, "ct0_norm")
        if int(h.sum()) > p.omega:
            return QuorusAttempt(w1, c_tilde, "hint_weight")
        sig = dsa.sig_encode(c_tilde, z, h, p)
        return QuorusAttempt(w1, c_tilde, "", sig, dsa.verify_internal(self.pk, m_prime, sig, p))


def main():
    import argparse
    import collections
    import time
    from ..mldsa.params import ALL
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", nargs="+", default=list(ALL))
    ap.add_argument("--attempts", type=int, default=20000)
    ap.add_argument("--keys", type=int, default=4)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--no-ew", action="store_true", help="control: e_w = 0 (plain ML-DSA single attempt)")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    for name in args.params:
        p = ALL[name]
        cnt = collections.Counter()
        bad = 0
        t0 = time.time()
        per_key = args.attempts // args.keys
        for kidx in range(args.keys):
            signer = QuorusSigner(p, rng.bytes(32), add_ew=not args.no_ew)
            for i in range(per_key):
                a = signer.attempt(rng.bytes(16), rng)
                cnt[a.failed] += 1
                if a.failed == "" and not a.verifies:
                    bad += 1
        n = per_key * args.keys
        line3 = cnt["z_norm"] + cnt["w0_norm"]
        passed3 = n - line3
        print(f"{name} e_w={'off' if args.no_ew else 'on'} attempts={n} keys={args.keys} ({time.time() - t0:.0f}s)")
        print(f"  z_norm {cnt['z_norm'] / n:.4f}  w0_norm {cnt['w0_norm'] / n:.4f}  -> M_rep = {n / max(passed3, 1):.2f}")
        print(f"  line 6 failures given line 3 passed: ct0 {cnt['ct0_norm'] / max(passed3, 1):.4f}  "
              f"hint {cnt['hint_weight'] / max(passed3, 1):.4f}")
        print(f"  signatures {cnt['']}, failing FIPS 204 verification: {bad} "
              f"({bad / max(cnt[''], 1):.2e})")


if __name__ == "__main__":
    main()
