# IA-2 Form — Answers (copy-paste ready) · Group OPT-09

## What limitation/research gap did you identify?
In IA-1 we re-implemented Grothey & McKinnon (2023): the qq-formulation solved by trust-region filter SLP with **independent random multistart**, in Python with HiGHS instead of CPLEX (qq_model.py, slp.py). The paper itself reports that on the hard instances only 4–20% of random starts end within 0.2% of the best-known cost (af-2 19.4%, af-3 20%, af-4 19.8%, af-6 4.0%, af-6-fs 5.2%, af-7 20.4%).

Running our IA-1 code (20 runs, seed 12345) on all 11 instances made the problem clearer:
- af-2, af-3 and af-6-fs never reached a Good solution, and af-6-f and af-7 only once.
- af-4, af-6-f and af-7 ended infeasible in 25–40% of the runs (SLP stuck in feasibility restoration).

**Gap:** random restarts waste most of the run time in poor or infeasible basins. Nothing learned in earlier runs is reused. The problem's structure is not used to choose starts or to repair end points, although the problem becomes an LP as soon as either the bins or the bin shares are fixed.

## How did you identify this gap?
☑ Limitation mentioned by authors ☑ Implementation experience ☑ Experimental results ☑ Comparison (IA-1 code vs paper) ☑ Literature review

## What is your proposed contribution?
**RG-ILS-SLP** (recipe-guided iterated local search around SLP). It is one new module, `rg_ils.py`, built on our unchanged IA-1 files:
1. **Diet relaxation LP:** one small LP per product gives that product's ideal recipe and a valid lower bound. On af-1 the bound is 295.932, equal to Baron's bound, and it takes milliseconds.
2. **Recipe-clustering start:** weighted k-means++ on the ideal recipes gives the initial bin compositions.
3. **Exact LP repair and polish:** a product LP (bins fixed) and a bin LP (bin shares fixed) make starts and SLP end points exactly feasible and never increase the cost.
4. **Regret-guided ILS with SLP probes:** from the best solution so far, 4 candidates are built. Each re-seeds a bin with the ideal recipe of a product that pays a lot for bin sharing (regret_p = t_p·max(0, c^D_p − c*_p)). Each candidate is LP-repaired and probed with a 10-iteration SLP, and the full IA-1 SLP continues from the best probe. Runs 1–3, and any run after 6 runs without improvement, use a fresh recipe start instead.

## What is different from the original paper (and our IA-1)?
The model (qq-formulation) and the local solver (filter SLP, our IA-1 slp.py) are **unchanged**.

| | Paper / IA-1 | IA-2 |
|---|---|---|
| Starting points | uniform random proportions | recipe clustering + LP repair |
| Restarts | independent random | iterated local search from the incumbent: regret-guided moves, best of 4 by short SLP probes, periodic fresh starts |
| SLP end point | used as returned | polished by exact product/bin LPs |
| Lower bound | none (Baron: hours) | diet-LP bound in milliseconds |
| Evaluation | IA-1: 20 runs on af-1 | all 11 instances × 3 seeds × 20 runs, significance tests, ablation |

## Which part of the optimization method/problem have you modified?
☑ Initialization ☑ Search strategy ☑ Hybridization (LP relaxation + clustering + LP repair + SLP = matheuristic) ☑ Other: new auxiliary LP formulations (diet relaxation, product LP, bin LP).

The objective function, the decision variables, the constraints and the SLP algorithm/parameters are **not** modified.

## Upload proposed methodology/flowchart
→ `07_Supporting_Material/Methodology_Flowchart.png` (also Figure 1 of the paper)

## Original mathematical formulation
qq-formulation (Grothey & McKinnon 2023, eq. 5a–5h):

min Σ_p t_p c^D_p

s.t.
- v_mn = Σ_i λ_mi r_in
- c^M_m = Σ_i λ_mi c_i
- d_pn = Σ_i μ_pi r_in + Σ_m μ_pm v_mn (bilinear)
- c^D_p = Σ_i μ_pi c_i + Σ_m μ_pm c^M_m (bilinear)
- Σ_i λ_mi = 1
- Σ_i μ_pi + Σ_m μ_pm = 1
- d̲_pn ≤ d_pn ≤ d̄_pn, v̲ ≤ v ≤ v̄
- bounds on λ and μ

Solved by filter SLP: min cᵀx s.t. the bilinear rows linearised at x_k, |x − x_k| ≤ ρ·w (ρ0 = 0.5, ρmax = 1), with a Fletcher–Leyffer filter (β = 0.99, γ = 0.01, σ = 0.1).

## Proposed mathematical formulation
The same qq-problem, plus four auxiliary formulations:
- **(D) Diet relaxation:** c*_p = min Σ_i c_i w_pi s.t. Σ_i w_pi = 1, d̲_pn ≤ Σ_i w_pi r_in ≤ d̄_pn, straight bounds, bin-reachable share ≤ Σ_m μ̄_pm. Then LB = Σ_p t_p c*_p ≤ f*, and q_p is the ideal bin recipe.
- **(PLP) Product LP, λ fixed:** min Σ_p t_p(Σ_i μ_pi c_i + Σ_m μ_pm c̄^M_m) s.t. d̲ ≤ Σ_i μ_pi r_in + Σ_m μ_pm v̄_mn ≤ d̄, Σμ = 1.
- **(BLP) Bin LP, μ_pm fixed:** min Σ_p t_p(Σ_i μ_pi c_i + Σ_m μ̄_pm Σ_i λ_mi c_i) s.t. d̲ ≤ Σ_i μ_pi r_in + Σ_m μ̄_pm Σ_i λ_mi r_in ≤ d̄, v̲ ≤ λr ≤ v̄, convexity.
- **(R) Regret-guided move:** regret_p = t_p·max(0, c^D_p − c*_p). Pick p ∝ regret_p and a bin m uniformly, then set λ_m ← Proj((1−α) q_p + α λ_m) with α ~ U(0, 0.5). Proj is an ℓ1-projection LP onto the bin constraints.

Elastic versions of PLP and BLP add penalised slacks (penalty 10⁴) when they are infeasible.

## Explain the mathematical changes introduced by your team
The nonconvexity comes only from the products μ_pm·v_mn and μ_pm·c^M_m. Fixing either factor makes every constraint linear:
- Fixing λ (and with it v and c^M) gives PLP.
- Fixing μ_pm gives BLP.

Both are exact LPs. We alternate them to turn approximate points into exactly feasible ones, and the cost never increases.

Dropping bin sharing gives a convex relaxation (D). Its solution is each product's ideal recipe and a lower bound on the optimum. The gap between a product's actual unit cost and its ideal cost (its regret) tells us which bin composition to change in the next ILS move.

The original objective, constraints and SLP subproblem are unchanged. All new LPs use the IA-1 variable indexing, so their solutions go straight into FilterSLP.solve().

## What experiments were conducted?
All 11 af-series instances of the paper: af-1, af-2, af-3, af-4, af-5, af-5-fs, af-6-f (= the paper's af-6), af-6-fs, af-7, af-7b and af-7b-fs.
- **E1 Baseline:** IA-1 code unchanged (random start + filter-SLP), 3 seeds × 20 runs per instance. Seed 12345 reproduces the IA-1 notebook exactly.
- **E2 Proposed:** RG-ILS-SLP on the same 11 instances and seeds.
- **E3 Ablation A:** random start + SLP + LP polish (seed 12345, 11 instances).
- **E4 Ablation B:** recipe start + repair + SLP + polish, without ILS (seed 12345, 11 instances).
- **E5:** comparison with the published SLP-CPLEX results (500 runs).
- **Statistics:** one-sided Fisher exact test on Good and feasible counts, and a Mann–Whitney U test on final gaps.

In total: 1,320 main runs plus 440 ablation runs.

## Evaluation metrics
- %Feas: share of runs that end feasible (max scaled violation ≤ 1e-6)
- %Good: share of runs within 0.2% of the best-known cost
- Ti: seconds per run
- It: SLP iterations per run
- ETiGood = 100·Ti/%Good: expected time to a Good solution
- best gap and median gap to the best known
- %Good spread over seeds
- time to the first Good solution
- p-values of the tests above

## Upload experimental results/comparison table
→ `06_Results/Comparison_Table.pdf` (single file). The full workbook is `06_Results/Result_Tables.xlsx`.

## Did the proposed method improve upon the implemented method?
**Yes, overall: on feasibility, on %Good for the hard instances, and on time-to-quality.** Pooled over 3 seeds × 20 runs on all 11 instances, against our IA-1 code:
- **Mean %Feas:** 87.9% → 96.1%. Every run is feasible on 8 of 11 instances (baseline: 1 of 11).
- **Mean %Good:** 43.6% → 62.0%.
- **Hard instances (af-2, af-3, af-4, af-6-f, af-6-fs, af-7):** %Good 6.4% → 33.9% (paper SLP-CPLEX: 14.8%).
  - af-2: 1.7% → 68.3% (paper 19.4%)
  - af-3: 1.7% → 31.7% (paper 20%)
  - af-4: 20% → 58.3% (paper 19.8%)
  - af-6-fs: 3.3% → 26.7% (paper 5.2%)
  - af-7: 10% → 18.3% (paper 20.4%)
  - af-6-f: 1.7% → 0% (paper 4.0%)
- **Higher %Good than the paper** on 7 of 11 instances (af-1, af-2, af-3, af-4, af-6-fs, af-7b, af-7b-fs).
- **ETiGood:** 5.0× shorter on the hard instances where both methods find a Good run (geometric mean).
- **Significance:** more Good runs at p < 0.01 (Fisher) on af-2, af-3, af-4, af-5-fs and af-6-fs. Lower gaps at p < 0.01 (Mann–Whitney) on 9 of 11 instances.

**Limitations:**
- af-6-f (the paper's af-6) is not solved by either method. The recipe start alone reaches 15% there, so the ILS step over-refines a poor incumbent.
- af-7 stays slightly below the paper's %Good.
- The easy instances (af-1, af-5, af-5-fs, af-7b-fs) get up to ~2× slower because of the extra LPs.
- On af-4 the single best baseline run (the best-known value) is better than the proposed best (+0.19%).

## Upload/Share the Google Drive Folder Link containing all final IA-2
→ Upload the `OPT-09_IA2` folder, set access to "Anyone with the link – Viewer", and paste the folder link here.
