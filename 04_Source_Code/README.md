# OPT-09 – IA-2 source code

IA-2 extends our IA-1 code (re-implementation of Grothey & McKinnon 2023, *On the effectiveness of
sequential linear programming for the pooling problem*). The IA-1 files are **unchanged**. They are the baseline.

| File | Origin | Role |
|---|---|---|
| `qq_model.py` | IA-1, unchanged | data parser + qq-formulation (variables, bilinear rows, linearisation, random start) |
| `slp.py` | IA-1, unchanged | filter trust-region SLP with HiGHS warm start and block/elastic restoration |
| `run_experiments.py` | IA-1, **extended** | multistart experiment; IA-2 adds `--method baseline / proposed / abl_polish / abl_rcstart` |
| `rg_ils.py` | **new (IA-2)** | proposed RG-ILS-SLP: diet LP relaxation, recipe-clustering start, product/bin LP repair and polish, regret-guided ILS with short-SLP probes |
| `run_all.py` | new | runs the whole experiment from scratch on any OS (`--mode quick / seed / full`), then the analysis |
| `analyze_results.py` | new | result tables (`Result_Tables.xlsx`), statistics, graphs (`--results DIR` for a rerun folder) |
| `make_flowchart.py` | new | methodology flowchart |
| `run_experiments_ia1.py` | IA-1 | original runner, kept for reference |

## Requirements
Python ≥ 3.10, NumPy, SciPy ≥ 1.15 (it bundles the HiGHS LP solver), pandas, matplotlib, openpyxl.

```
pip install numpy scipy pandas matplotlib openpyxl
```

## Reproduce
The data files are read from `../05_Dataset` (or `./data`). The results are written to `../06_Results/<method>/seed<s>/`.

```
# baseline = IA-1 protocol (random start, filter-SLP), seed 12345 as in IA-1
python run_experiments.py --method baseline --instances af-1 af-2 af-3 af-4 af-5 af-5-fs af-6-f af-6-fs af-7 af-7b af-7b-fs --runs 20 --seed 12345 --outdir ../06_Results/baseline/seed12345
# proposed method
python run_experiments.py --method proposed --instances af-1 af-2 af-3 af-4 af-5 af-5-fs af-6-f af-6-fs af-7 af-7b af-7b-fs --runs 20 --seed 12345 --outdir ../06_Results/proposed/seed12345
# repeat with --seed 2024 and --seed 7; ablations: --method abl_polish / abl_rcstart
python analyze_results.py      # -> ../06_Results/Result_Tables.xlsx and ../06_Results/Graphs/
```
`run_all.py --mode full` (any OS) or `run_all.sh` (Linux/Mac) runs the complete experiment: 2 methods × 3 seeds × all 11 instances × 20 runs, plus the ablations. It takes about 3.5 h on 2 cores (af-7b-fs alone needs about 1 min per run). The paper's instance af-6 is the file `af-6-f.txt`.

Proposed-method options (defaults were used in the paper):
`--screen 4` (perturbation candidates per ILS run), `--probe-iter 10` (SLP iterations per probe),
`--patience 6` (ILS runs without improvement before a fresh recipe start), `--n-init 3` (initial recipe starts),
`--polish-rounds 10`.
