#!/bin/sh
# Paper plan item 8: TALUS ILP statistics, 20 trials per point, fresh seed 2041, one GPU job at a time.
# Run from the repo root: sh experiments/run_item8.sh
set -e
R=experiments/results/item8
mkdir -p $R
python -m experiments.ilp_n256 --params ML-DSA-44 --N 50000 55000 60000 65000 70000 80000 \
  --trials 20 --seed 2041 --time-limit 120 --out $R/ilp_ML-DSA-44.json > $R/ilp_ML-DSA-44.log 2>&1
python -m experiments.ilp_n256 --params ML-DSA-65 --N 130000 143000 160000 179000 215000 \
  --trials 20 --seed 2041 --time-limit 120 --out $R/ilp_ML-DSA-65.json > $R/ilp_ML-DSA-65.log 2>&1
python -m experiments.ilp_n256 --params ML-DSA-87 --N 120000 135000 148000 165000 184000 \
  --trials 20 --seed 2041 --time-limit 120 --out $R/ilp_ML-DSA-87.json > $R/ilp_ML-DSA-87.log 2>&1
echo done
