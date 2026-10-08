"""Extract a small subset of the official NIST ACVP ML-DSA vectors into acvp_mldsa.json.

Source: github.com/usnistgov/ACVP-Server, gen-val/json-files/ML-DSA-{keyGen,sigGen,sigVer}-FIPS204/
internalProjection.json (downloaded 8 Oct 2026). Only groups our code supports are kept: pure
signing (external interface with context, or internal interface on a raw message). PreHash and
external-mu groups are skipped.

Usage: python harness/tests/vectors/extract_acvp.py <dir with the three ACVP folders> [per_group]
"""
import json
import os
import sys

src = sys.argv[1]
per = int(sys.argv[2]) if len(sys.argv) > 2 else 3


def load(name):
    with open(os.path.join(src, name, "internalProjection.json")) as f:
        return json.load(f)["testGroups"]


def keep(g):
    return g.get("preHash", "pure") in ("pure", "none") and not g.get("externalMu", False)


out = {"keyGen": [], "sigGen": [], "sigVer": []}
for g in load("ML-DSA-keyGen-FIPS204"):
    for t in g["tests"][:per]:
        out["keyGen"].append(dict(param=g["parameterSet"], seed=t["seed"], pk=t["pk"], sk=t["sk"]))
for g in load("ML-DSA-sigGen-FIPS204"):
    if not keep(g):
        continue
    for t in g["tests"][:per]:
        out["sigGen"].append(dict(param=g["parameterSet"], interface=g["signatureInterface"],
                                  sk=t["sk"], message=t["message"], context=t.get("context", ""),
                                  rnd=t.get("rnd", "00" * 32), signature=t["signature"]))
for g in load("ML-DSA-sigVer-FIPS204"):
    if not keep(g):
        continue
    for t in g["tests"][:2 * per]:
        out["sigVer"].append(dict(param=g["parameterSet"], interface=g["signatureInterface"],
                                  pk=t["pk"], message=t["message"], context=t.get("context", ""),
                                  signature=t["signature"], passed=t["testPassed"], reason=t["reason"]))

dst = os.path.join(os.path.dirname(__file__), "acvp_mldsa.json")
with open(dst, "w") as f:
    json.dump(out, f)
print({k: len(v) for k, v in out.items()}, "->", dst)
