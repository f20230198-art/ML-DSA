"""Paper plan item 7: Kao P2 broadcast leak on real ML-DSA parameter sets.

Run: python -m experiments.kao_p2_real_demo --params ML-DSA-44 --keys 3
For each key: build a (N, T) Profile-P2 session, produce a signature that passes the unmodified FIPS 204
Verify of this repository, then run the outsider attack on (pk, message, signature, all broadcast W_i).
Controls: (a) the same attack with one W_i withheld must fail; (b) a signature from plain ML-DSA is
not attacked (no W_i exists), covered by the existing mldsa_controls. Reports exact-match against the
dealer's s1 and the public consistency check.
"""
import argparse
import json
import time

from harness.mldsa import dsa
from harness.mldsa.params import ALL
from harness.schemes import kao_p2_real as kp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default="ML-DSA-44", choices=sorted(ALL))
    ap.add_argument("--keys", type=int, default=3)
    ap.add_argument("--cfg", default="5,3;3,2;5,5", help="semicolon list of N,T pairs")
    ap.add_argument("--seed", type=int, default=2051)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    p = ALL[args.params]
    cfgs = [tuple(int(v) for v in c.split(",")) for c in args.cfg.split(";")]
    rows = []
    for (n, T) in cfgs:
        for k in range(args.keys):
            t0 = time.time()
            sch = kp.KaoP2(p, n, T, [args.seed, n, T, k])
            msg = f"kao p2 demo {n},{T},{k}".encode()
            S = list(range(1, T + 1))
            tr = sch.sign(msg, S)
            verifies = dsa.verify(tr.pk, msg, tr.signature, p)
            s1 = kp.attack_from_broadcast(p, tr, list(tr.broadcast.values()))
            exact = s1 is not None and bool((s1 == sch.secret["s1"]).all())
            pk_ok, short = (kp.consistent_with_pk(p, tr.pk, s1) if s1 is not None else (False, False))
            partial = list(tr.broadcast.values())[:-1]
            s1_ctl = kp.attack_from_broadcast(p, tr, partial)
            ctl_exact = s1_ctl is not None and bool((s1_ctl == sch.secret["s1"]).all())
            ctl_short = s1_ctl is not None and bool(abs(s1_ctl).max() <= p.eta)
            row = dict(params=p.name, N=n, T=T, key=k, attempts=tr.attempts, verifies=bool(verifies),
                       recovered_exact=exact, pk_consistent=bool(pk_ok), short=bool(short),
                       control_missing_Wi_exact=ctl_exact, control_missing_Wi_short=ctl_short,
                       seconds=round(time.time() - t0, 1))
            rows.append(row)
            print(json.dumps(row), flush=True)
    ok = sum(r["recovered_exact"] for r in rows)
    print(f"\n{p.name}: s1 recovered exactly from ONE signature + broadcast in {ok}/{len(rows)} keys; "
          f"all signatures verify: {all(r['verifies'] for r in rows)}; "
          f"control (one W_i withheld) exact: {sum(r['control_missing_Wi_exact'] for r in rows)}/{len(rows)}")
    if args.out:
        json.dump(rows, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
