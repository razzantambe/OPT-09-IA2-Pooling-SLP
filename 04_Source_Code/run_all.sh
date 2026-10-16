#!/bin/bash
# Full IA-2 experiment: all 11 af instances x 20 runs x 3 seeds, baseline (IA-1 code) vs proposed, + ablations (seed 12345)
# about 3.5 h on 2 cores. Results go to ../06_Results/<method>/seed<s>/
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
INST="af-1 af-2 af-3 af-4 af-5 af-5-fs af-6-f af-6-fs af-7 af-7b af-7b-fs"
R=../06_Results
mkdir -p $R/logs
q1() {
  for s in 12345 2024 7; do python run_experiments.py --method baseline --instances $INST --runs 20 --seed $s --outdir $R/baseline/seed$s; done
  python run_experiments.py --method abl_polish --instances $INST --runs 20 --seed 12345 --outdir $R/abl_polish/seed12345
}
q2() {
  for s in 12345 2024 7; do python run_experiments.py --method proposed --instances $INST --runs 20 --seed $s --outdir $R/proposed/seed$s; done
  python run_experiments.py --method abl_rcstart --instances $INST --runs 20 --seed 12345 --outdir $R/abl_rcstart/seed12345
}
q1 > $R/logs/queue1.log 2>&1 &
q2 > $R/logs/queue2.log 2>&1 &
wait
python analyze_results.py
