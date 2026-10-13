while read P k t; do
python -m experiments.ilp_n256 --params $P --N ${k}000 --trials 1 --first $t --time-limit 300 --out experiments/results/ilp_n256_${P}_${k}k_t$t.json > experiments/results/ilp_n256_${P}_${k}k_t$t.txt 2>&1
done < todo.txt
echo DONE > serial_done.flag
