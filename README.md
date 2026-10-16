# OPT-09 · IA-2 — Recipe-Guided Iterated Local Search around SLP for the Pooling Problem

Introduction to Optimization Techniques (IA-2) · Dept. of IT, K. J. Somaiya College of Engineering
Group OPT-09: Razzan Tambe (15) · Saurabh Tripathi (04) · Vivek Sharma (12)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/razzantambe/OPT-09-IA2-Pooling-SLP/blob/main/IA2_Demo_Colab.ipynb)

This repository extends our IA-1 re-implementation of Grothey & McKinnon (2023), *On the effectiveness of sequential linear programming for the pooling problem* (Ann. Oper. Res. 322, 691–711).
- **Baseline:** the IA-1 files `qq_model.py` and `slp.py`, unchanged (qq-formulation, filter SLP, random multistart).
- **Proposed:** RG-ILS-SLP (`rg_ils.py`), which adds a diet-LP relaxation, a recipe-clustering start, product/bin LP repair and polish, and a regret-guided iterated local search with short SLP probes.

## Run the whole project online (Google Colab)
Click **Open in Colab** above, then **Runtime → Run all**. The notebook `IA2_Demo_Colab.ipynb` runs the project from start to end:
1. gets the code and data
2. loads all 11 instances and computes the IA-2 lower bound
3. walks through one IA-1 run and one IA-2 run, step by step
4. runs **IA-1 and IA-2 on all 11 instances**
5. builds the comparison tables, significance tests, Excel workbook and graphs
6. checks the rerun against the stored results
7. downloads everything it produced

Set `MODE` in Step 4:

| MODE | runs | time |
|---|---|---|
| `quick` | 5 per instance | ~15 min |
| `seed` | 20 per instance (seed 12345), plus ablations | ~1.5 h |
| `full` | the paper's experiment, 3 seeds × 20 | ~4 h |

## Run it locally (Windows / Linux / Mac)
```
pip install -r 04_Source_Code/requirements.txt
cd 04_Source_Code
python run_all.py --mode quick        # or: --mode seed / --mode full
```
`run_all.py` runs every experiment (2 in parallel) and then `analyze_results.py`. The results go to `results_rerun/`: `Result_Tables.xlsx`, `Comparison_Table.pdf` and `Graphs/`. For a single comparison:
```
python run_experiments.py --method baseline --instances af-2 --runs 20 --seed 12345
python run_experiments.py --method proposed --instances af-2 --runs 20 --seed 12345
```

## Contents
| Folder | Content |
|---|---|
| `01_Research_Paper/` | IA-2 research paper (PDF, DOCX) |
| `02_PPT/` | presentation (PDF, PPTX) |
| `03_Poster/` | poster (PDF) |
| `04_Source_Code/` | Python code (IA-1 files unchanged + IA-2 module) |
| `05_Dataset/` | the 11 af-series instances (Grothey & McKinnon, 2020) |
| `06_Results/` | per-run CSV files, `Result_Tables.xlsx`, `Comparison_Table.pdf`, graphs, logs |
| `07_Supporting_Material/` | IA-1 report, form answers, flowchart, document build scripts |
| `IA2_Demo_Colab.ipynb` | runnable notebook |

## Main result
Pooled over 3 seeds × 20 runs on all 11 instances, against the IA-1 code:
- %Feas rises from 87.9% to 96.1%.
- %Good rises from 43.6% to 62.0%.
- On the 6 hard instances, %Good rises from 6.4% to 33.9% (paper SLP-CPLEX: 14.8%).
