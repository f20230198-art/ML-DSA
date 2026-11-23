"""Merge WP-T full-secret shard files into one results file and print the combined summary.

When ML-DSA-65/-87 are split across machines (Colab + this PC), each shard writes its own
JSON (e.g. full_secret_real_ML-DSA-65_k0-15.json, ..._k15-30.json). This gathers them into
one file keyed by (key, N), de-duplicates, and reports the full-secret rate over all keys.

  python -m experiments.merge_full_secret --params ML-DSA-65 \
      experiments/results/full_secret_real_ML-DSA-65_k*.json

With no shard paths given it globs the default pattern for --params.
"""
import argparse
import glob
import json

from harness.mldsa.params import ALL
from experiments.full_secret_real import print_summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True, choices=sorted(ALL))
    ap.add_argument("shards", nargs="*",
                    help="shard JSON files; default globs full_secret_real_<params>_k*.json")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    base = f"experiments/results/full_secret_real_{args.params}"
    shards = args.shards or sorted(glob.glob(base + "_k*.json")) + \
        ([base + ".json"] if glob.glob(base + ".json") else [])
    if not shards:
        raise SystemExit(f"no shard files found for {args.params}")

    merged, seeds = {}, set()
    for path in shards:
        d = json.load(open(path))
        seeds.add(d.get("args", {}).get("seed"))
        for r in d.get("rows", []):
            merged[(r["key"], r["N"])] = r   # later file wins on an exact (key, N) repeat
    if len(seeds) > 1:
        raise SystemExit(f"refusing to merge shards from different seeds: {seeds}")
    rows = sorted(merged.values(), key=lambda r: (r["key"], r["N"]))
    print(f"merged {len(shards)} shard(s) -> {len(rows)} (key, N) rows, "
          f"{len({r['key'] for r in rows})} keys, seed {seeds.pop()}")

    out = args.out or base + "_merged.json"
    json.dump(dict(params=args.params, rows=rows), open(out, "w"), indent=1)
    print(f"written: {out}")
    print_summary(rows, ALL[args.params])


if __name__ == "__main__":
    main()
