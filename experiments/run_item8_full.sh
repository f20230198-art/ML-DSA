#!/bin/sh
# Paper plan item 8 (real full-secret run): ML-DSA-44, k = 4 elements per secret, 20 full secrets = 80 element trials per N.
# Fresh seed 2081, one GPU job at a time. Run from repo root: sh experiments/run_item8_full.sh
set -e
R=experiments/results/item8_full
mkdir -p $R
for N in 62000 66000 70000; do
  python -m experiments.ilp_n256 --params ML-DSA-44 --N $N --trials 80 --seed 2081 --time-limit 120 \
    --out $R/ilp_ML-DSA-44_$N.json > $R/ilp_ML-DSA-44_$N.log 2>&1
done
