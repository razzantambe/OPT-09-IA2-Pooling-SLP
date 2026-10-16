"""Writes paper_text.json - all prose of the IA-2 paper. Numbers come from the result files."""
import json
from pathlib import Path

import pandas as pd

H = Path(__file__).parent
ROOT = H.parent
S = pd.read_csv(ROOT / "results" / "summary.csv")
V = json.loads((H / "cmp_values.json").read_text())
G = json.loads((H / "group.json").read_text())


def g(inst, meth, col):
    return S[(S.instance == inst) & (S.method == meth)][col].iloc[0]


def pg(inst, meth):
    return f"{g(inst, meth, 'pct_good'):.1f}%"


def pf(inst, meth):
    return f"{g(inst, meth, 'pct_feas'):.1f}%"


def et(inst, meth):
    x = g(inst, meth, "ETiGood")
    return "∞" if x == float("inf") else f"{x:.1f} s"


A = V["abl"]


def ab(i, m, k=1):
    return f"{A[i][m][k]:.0f}%"


T = {}
T["title"] = ("Recipe-Guided Iterated Local Search around Sequential Linear Programming for the "
              "Fixed-Demand Pooling Problem: an Extension of our IA-1 Filter-SLP Implementation")
T["keywords"] = ("Nonconvex optimization; pooling problem; animal-feed blending; sequential linear programming; "
                 "LP relaxation; iterated local search; time-to-quality")

T["abstract"] = [
    "The pooling problem blends raw materials through a few shared bins into many products with quality limits. The "
    "bin compositions are decision variables, so the quality constraints are bilinear and the problem is nonconvex with "
    "many local optima. In IA-1 we re-implemented the filter Sequential Linear Programming (SLP) method of Grothey and "
    "McKinnon [1] on their qq-formulation in Python with the open-source HiGHS LP solver, and reproduced the best "
    "known af-1 objective (296.44604). Running the same IA-1 code on all eleven af-series instances showed its "
    "weakness: with random starting points, 0% of the runs were Good (within 0.2% of the best known value) on af-2, "
    "af-3 and af-6-fs, 5% on af-6-f and af-7, and only 60–75% of the runs were feasible on af-4, af-6-f and af-7.",
    "In IA-2 we keep the IA-1 model (qq_model.py) and SLP solver (slp.py) unchanged and add one module that changes "
    "where every SLP run starts and what happens to its end point. The method, **RG-ILS-SLP** (recipe-guided iterated "
    "local search around SLP), uses three LP sub-problems that follow from the bilinear structure: a per-product "
    "_diet relaxation_ (ideal recipe and a lower bound), a _product LP_ with the bins fixed and a _bin LP_ with the bin "
    "shares fixed. They give cost-aware feasible starts, repair and polish every SLP end point, and drive an iterated "
    "local search that re-seeds bins with the ideal recipes of the products that lose most from bin sharing (regret). "
    "Candidate moves are ranked with short 10-iteration SLP probes.",
    f"Over 3 seeds × 20 runs on all eleven instances, the proposed method raises the mean %Feas of our IA-1 baseline "
    f"from {V['feas_b']:.1f}% to {V['feas_p']:.1f}% and the mean %Good from {V['good_b']:.1f}% to {V['good_p']:.1f}%. "
    f"On the six hard instances (where the published SLP is Good in at most ~20% of the runs) %Good rises from "
    f"{V['good_b_hard']:.1f}% to {V['good_p_hard']:.1f}%, against {V['good_paper_hard']:.1f}% for the published "
    f"CPLEX-based SLP, and the expected time to a Good solution is {V['spd_hard']:.1f}× shorter on the hard instances "
    "where both methods find one. The diet relaxation gives a lower bound for af-1 (295.932) equal to Baron's bound, "
    "in milliseconds. Limitations: af-6-f (the paper's af-6) is not solved to 0.2% by either method, easy instances "
    "become slightly slower, and af-7 stays just below the published %Good."]

T["intro"] = [
    "Blending problems are among the oldest applications of linear programming. If products are mixed directly from "
    "raw materials, the quality constraints are linear. In feed mills and refineries, however, raw materials often pass "
    "first through a few _mixing bins_ (pools) that several products share. The bin compositions then become variables, "
    "and the quality of a product is a bin composition multiplied by that bin's share in the product. This bilinear "
    "term turns an LP into a nonconvex nonlinear program: the pooling problem [7].",
    "Grothey and McKinnon [1] showed that a trust-region filter SLP method on their qq-formulation, restarted from many "
    "random points, finds good solutions faster than SQP, interior-point methods and the global solver Baron. In IA-1 "
    "our group re-implemented this method (Python, NumPy/SciPy, HiGHS instead of CPLEX), validated it on af-1, and "
    "recorded where it struggles. IA-2 starts from exactly that code and that evidence."]
T["motivation"] = [
    "A feed mill must produce fixed tonnages t~p~ of products p. Every product has lower and upper limits on N "
    "nutrients. Raw materials either go through M shared bins or are added directly ('straights'). The goal is minimum "
    "total raw-material cost. A good set of bin compositions has to serve many products at once, so the problem has "
    "many local optima.",
    "SLP solves a sequence of LPs linearised at the current point. Each run is therefore fast, but it only reaches the "
    "local optimum nearest its start. With uniform random starts, few runs land in a good basin on the harder "
    "instances, and some runs stop at a local minimiser of the constraint violation (infeasible). A better method "
    "should (a) end feasible almost always, (b) start in good basins more often and (c) reuse what earlier runs found, "
    "while the SLP itself stays as it is."]
T["objectives"] = [
    "Use the IA-1 filter-SLP code unchanged as the baseline and measure its %Feas, %Good, Ti, It and ETiGood on all "
    "eleven af-series instances of [1], with 3 seeds × 20 runs.",
    "Derive LP sub-problems from the bilinear structure of the qq-formulation that give feasible, cost-aware starts "
    "and repair or polish SLP end points.",
    "Replace independent random restarts with a recipe-guided iterated local search that builds on the incumbent.",
    "Compare the proposed method with the baseline, the published SLP-CPLEX results and the IA-1 notebook. Use the "
    "paper's metrics plus significance tests and an ablation study.",
    "Deliver reproducible code that extends the IA-1 files without changing them."]
T["contributions"] = [
    "**Diet relaxation (new auxiliary formulation):** one LP per product that ignores bin sharing. It gives each "
    "product's ideal recipe and a valid lower bound on the qq-optimum, equal to Baron's bound on af-1.",
    "**Exact LP repair and polish (new):** with the bins fixed, or with the bin shares fixed, the qq-constraints become "
    "linear. Alternating the two LPs makes approximate points exactly feasible and never increases the cost.",
    "**Recipe-clustering initialisation (modified initialisation):** weighted k-means++ on the ideal recipes gives the "
    "initial bin compositions, instead of uniform random proportions.",
    "**Regret-guided ILS with SLP probes (modified search strategy / hybridisation):** a bin is re-seeded with the "
    "ideal recipe of a product that pays a high price for bin sharing. Four such moves are probed with a 10-iteration "
    "SLP, and the best one is continued.",
    "**Evaluation beyond IA-1:** all 11 instances × 3 seeds × 20 runs, Fisher and Mann–Whitney tests, and a two-part "
    "ablation. IA-1 reported 20 runs on af-1 only."]

T["related_intro"] = [
    "IA-1 reviewed six papers [1]–[6] on nonlinear and nonconvex optimisation. We summarise those that shape the gap "
    "and add the pooling literature on alternating LPs and neighbourhood search [7]–[9], the iterated-local-search "
    "framework [13] and k-means++ seeding [14], on which the extension builds."]
T["baseline_paper"] = [
    "Grothey and McKinnon [1] study the pooling problem with fixed demands from the animal-feed industry. Their "
    "**qq-formulation** uses only proportions: λ~mi~ (share of raw material i in bin m), μ~pi~ (straight share of i in "
    "product p) and μ~pm~ (share of bin m in product p), together with the bin and product qualities v~mn~, d~pn~ and "
    "unit costs c^M^~m~, c^D^~p~. The only nonlinear terms are μ~pm~v~mn~ and μ~pm~c^M^~m~.",
    "A trust-region SLP with a Fletcher–Leyffer filter [11] is solved from many random points (CPLEX primal simplex "
    "with hot starts). Over 500 runs per instance, SLP-CPLEX takes 0.5–14.7 s per run and is Good in 4–100% of the "
    "runs. Its expected time to a Good solution (ETiGood) is on average 863×, 507× and 20× smaller than for "
    "FilterSQP, IPOpt and Baron.",
    "**Our IA-1 implementation** of this method (qq_model.py, slp.py) treats price as an extra attribute so that "
    "(5c) and (5g) form one family of bilinear rows. It scales every attribute by the median of its positive "
    "entries, tightens the bounds of v and d, and uses an ∞-norm trust region relative to each variable's range "
    "(ρ~0~ = 0.5, ρ~max~ = 1). Filter parameters are β = 0.99, γ = 0.01, σ = 0.1, with at most 400 iterations. "
    "Restoration is block-wise (exact LPs with μ or (λ, v) fixed) followed by an elastic ℓ~1~ LP, and the LPs are "
    "warm-started in HiGHS."]
T["comparison_lead"] = ("Table 1 compares the approaches by formulation, algorithm, cost, solution quality and "
                        "relevance to the identified gap.")
T["related_table"] = [
    ["Grothey & McKinnon [1] (selected paper) and our IA-1 code", "qq-formulation; trust-region filter SLP + random multistart", "low per run (LPs only); many restarts needed", "best time-to-quality among tested solvers; 4–20% Good on hard instances", "baseline; restart strategy is our target"],
    ["Baron / spatial B&B (in [1]); Sass et al. [3]", "convex relaxations + branch-and-bound; [3] grows the data set during B&B", "very high (hours)", "global bounds, slow to find good feasible points on af-series", "motivates a cheap bound; our diet LB is a fast relaxation"],
    ["Gill & Zhang [4]", "shifted primal-dual interior point + projected search", "Newton systems per iteration", "robust local method", "IPOpt-type methods were slower than SLP in [1]"],
    ["Muehlebach & Jordan [5]", "accelerated first-order method with velocity constraints", "cheap, many iterations", "stationary points", "local only; does not choose basins"],
    ["di Serafino et al. [6]", "stationarity measures, active-set methods for polyhedral constraints", "low", "better active-set decisions near a solution", "our LP sub-problems are polyhedral; supports LP polish"],
    ["Terzi et al. [2]", "matheuristics (metaheuristic + exact sub-solver) vs metaheuristics", "moderate", "matheuristics win", "supports 'heuristic outer loop + exact LP inner solve'"],
    ["Haverly [8]; Audet et al. [9]", "recursion / alternating LPs (ALT); variable neighbourhood search", "low", "good local solutions on small pooling instances", "basis of our product-LP / bin-LP alternation"],
    ["Lourenço et al. [13]; Arthur & Vassilvitskii [14]", "iterated local search; k-means++ seeding", "low", "standard frameworks", "outer loop and initial bins of RG-ILS-SLP"]]

T["gap_lead"] = ("The gap was identified from three sources: limitations reported by the authors, our IA-1 implementation "
                 "experience, and IA-1 experimental results compared with the paper.")
T["gap"] = [
    "**Limitation in the literature.** The SLP results in [1] rest on random multistart. Every run is independent, and "
    "nothing learned in earlier runs is reused. Tables 2 and 4 of [1] show only 4–20% Good runs on af-3, af-4, af-6, "
    "af-6-fs and af-7, so ETiGood reaches 6.5–125 s although one run takes 1.3–6.5 s. The authors also note that SLP "
    "can stop at a local minimum of the feasibility problem.",
    "**Evidence from IA-1.** The IA-1 report validated af-1 only (20/20 runs feasible and Good). Our IA-1 notebook also "
    "ran the code on seven more instances with the same seed (12345); for af-2, af-6-f and af-7b-fs we ran the same "
    "code and seed in IA-2. Table 2 shows the result: af-2, af-3 and af-6-fs never reached a Good solution, af-6-f and "
    "af-7 only once, and af-4, af-6-f and af-7 ended infeasible in 25–40% of the runs (stuck in restoration with "
    "violation ≈ 1.3 × 10^-3^ on af-4). Re-running that code in IA-2 reproduces the notebook numbers exactly (only Ti "
    "differs with the machine)."]
T["gap_after"] = [
    "**Gap:** random-multistart SLP spends most of its time in poor or infeasible basins. The structure of the problem "
    "is not used to choose better starts or to repair end points, even though the problem becomes linear once either "
    "the bins or the bin shares are fixed."]
T["problem_statement"] = [
    "Given a fixed-demand pooling instance in qq-form, find a strategy around the unchanged IA-1 filter-SLP that "
    "(i) increases %Feas, (ii) increases %Good on the hard instances and therefore (iii) reduces the expected time to a "
    "Good solution. The optimisation model must not change, and the LP solver stays open-source."]
T["team_contribution"] = [
    "We do **not** change the objective, the constraints or the SLP algorithm of IA-1. We change what happens "
    "_around_ the SLP: how starting points are produced, how SLP end points are finished, and how successive runs are "
    "linked. This should help because the hard decision is the bin compositions. Once the bins are fixed, the rest is "
    "an LP that can be solved exactly, and the diet relaxation tells us which recipe each product would like a bin "
    "to have."]
T["diff_table"] = [
    ["Model", "qq-formulation (5a)–(5h); IA-1 qq_model.py", "unchanged (same file)", "Retained"],
    ["Local solver", "filter trust-region SLP; IA-1 slp.py (HiGHS)", "unchanged (same file, same parameters)", "Retained"],
    ["Starting points", "uniform random proportions (QQModel.random_start)", "recipe-clustering start + LP repair", "Modified (initialisation)"],
    ["Restarts", "independent random multistart", "regret-guided ILS from the incumbent; 4 candidates ranked by 10-iteration SLP probes; fresh recipe start after 6 non-improving runs", "New (search strategy / hybridisation)"],
    ["End point", "SLP point as returned", "LP polish: product LP, then bin LP", "New"],
    ["Bound", "none (Baron in [1], hours)", "diet-relaxation lower bound in milliseconds", "New (auxiliary formulation)"],
    ["Experiment", "20 runs, af-1 (IA-1 report)", "all 11 instances × 3 seeds × 20 runs, tests, ablation", "Extended"]]

T["method_lead"] = [
    "The method keeps the original problem and solver and adds a layer of LP sub-problems around them. Section 4.1 "
    "gives the original model and the new auxiliary formulations, and Section 4.2 gives the algorithm."]
T["form_sets"] = [
    "**Sets and parameters.** i ∈ I raw materials (af files list straight copies separately), m ∈ M bins, p ∈ P "
    "products, n ∈ N nutrients; r~in~ nutrient content, c~i~ unit cost, t~p~ demand, [d̲~pn~, d̄~pn~] product specs, "
    "[v̲~mn~, v̄~mn~] optional bin specs, bounds on λ and μ (a zero upper bound means the link does not exist). "
    "**Variables:** λ~mi~, μ~pi~, μ~pm~, v~mn~, d~pn~, c^M^~m~, c^D^~p~."]
T["eq_qq"] = [
    ["min  Σ~p~ t~p~ c^D^~p~", "5a"],
    ["v~mn~ = Σ~i~ λ~mi~ r~in~ ,   c^M^~m~ = Σ~i~ λ~mi~ c~i~                 ∀ m, n", "5b,f"],
    ["d~pn~ = Σ~i~ μ~pi~ r~in~ + Σ~m~ μ~pm~ v~mn~ ,  c^D^~p~ = Σ~i~ μ~pi~ c~i~ + Σ~m~ μ~pm~ c^M^~m~   (bilinear)", "5c,g"],
    ["Σ~i~ λ~mi~ = 1  ∀ m ;     Σ~i~ μ~pi~ + Σ~m~ μ~pm~ = 1  ∀ p", "5d,e"],
    ["d̲~pn~ ≤ d~pn~ ≤ d̄~pn~ ;   v̲~mn~ ≤ v~mn~ ≤ v̄~mn~ ;   bounds on λ, μ", "5h"]]
T["form_after_qq"] = [
    "In IA-1 the price is attribute n = N+1 (r~i,N+1~ = c~i~), so (5b,f) and (5c,g) are one family: V~mq~ = Σ λ~mi~R~iq~ "
    "and D~pq~ = Σ μ~pi~R~iq~ + Σ μ~pm~V~mq~. SLP linearises the bilinear term at x^k^ (∂/∂μ~pm~ = −V~mq~, "
    "∂/∂V~mq~ = −μ~pm~) and solves min c^T^x subject to the linearised rows and |x − x^k^| ≤ ρ·w. This model and solver "
    "are **unchanged** in IA-2."]
T["eq_diet"] = [
    ["c^*^~p~ = min~w≥0~ Σ~i~ c~i~ w~pi~   s.t.  Σ~i~ w~pi~ = 1,  d̲~pn~ ≤ Σ~i~ w~pi~ r~in~ ≤ d̄~pn~,  w~pi~ ∈ [μ̲~pi~, μ̄~pi~] for straights,  Σ~i∈B(p)~ w~pi~ ≤ Σ~m~ μ̄~pm~", "D1"],
    ["LB = Σ~p~ t~p~ c^*^~p~  ≤  f^*^~qq~ ;     ideal bin recipe  q~p~ = w^B^~p~ / Σ~i~ w^B^~pi~", "D2"]]
T["form_after_diet"] = [
    "B(p) is the set of raw materials that can reach product p through some bin. Any qq-feasible point gives product p "
    "the effective recipe Σ~m~ μ~pm~λ~m·~ + μ~p·~, which is feasible for (D1). Hence (D2) is a valid lower bound. "
    "(D1) ignores bin sharing, bin bounds and bin specs."]
T["eq_plp"] = [
    ["min~μ~ Σ~p~ t~p~ (Σ~i~ μ~pi~ c~i~ + Σ~m~ μ~pm~ c̄^M^~m~)  s.t.  d̲~pn~ ≤ Σ~i~ μ~pi~ r~in~ + Σ~m~ μ~pm~ v̄~mn~ ≤ d̄~pn~,  (5e), bounds", "PLP"]]
T["eq_blp"] = [
    ["min~λ,μS~ Σ~p~ t~p~ (Σ~i~ μ~pi~ c~i~ + Σ~m~ μ̄~pm~ Σ~i~ λ~mi~ c~i~)  s.t.  d̲~pn~ ≤ Σ~i~ μ~pi~ r~in~ + Σ~m~ μ̄~pm~ Σ~i~ λ~mi~ r~in~ ≤ d̄~pn~,  v̲ ≤ λr ≤ v̄,  (5d), (5e)", "BLP"]]
T["eq_reg"] = [
    ["regret~p~ = t~p~ · max(0, c^D^~p~ − c^*^~p~) ;     P(p) ∝ regret~p~ ,   m ~ uniform", "R1"],
    ["λ̃~m·~ = Proj( (1−α) q~p~ + α λ~m·~ ),  α ~ U(0, 0.5);   all bins × exp(0.05 ξ),  ξ ~ N(0, 1)", "R2"]]
T["form_after_reg"] = [
    "Elastic versions of (PLP) and (BLP) add penalised slacks e ≥ 0 to the quality rows (normalised cost + 10^4^ Σe). "
    "They are used when the fixed part makes the LP infeasible. Proj(·) is an ℓ~1~ projection LP onto the bin's "
    "simplex, its λ bounds and its nutrient bounds. **The mathematical change in short:** the nonconvex problem "
    "(5a)–(5h) is unchanged. We add the convex relaxation (D1)–(D2) and the two exact linear restrictions (PLP) and "
    "(BLP) of the bilinear rows (5c,g), and use their solutions to generate, repair and polish SLP points. All LPs are "
    "built on the IA-1 variable indexing (lam_var, mur_var, mub_var, V_var, D_var), so every point can be passed "
    "straight to FilterSLP.solve()."]

T["algo_steps"] = [
    "**[New] Diet relaxation.** Solve (D1) for every product to get the ideal recipes q~p~, unit costs c^*^~p~ and "
    "the bound LB. This happens once per instance.",
    "**[Modified] Recipe-clustering start.** Mix each q~p~ with 30% Dirichlet noise, run weighted k-means++ "
    "(weights t~p~ × bin share) with M clusters, and project the centres onto the bin constraints.",
    "**[New] LP repair.** Solve the elastic (PLP) with these bins. While the violation is > 10^-7^, alternate the "
    "elastic (BLP) and (PLP), at most 6 rounds.",
    "**[Retained] Filter-SLP.** Run FilterSLP.solve() of IA-1 from this point, unchanged.",
    "**[New] LP polish.** Fix the final bins and solve (PLP), then fix the bin shares and solve (BLP), for at most 10 "
    "rounds. Keep a point only if it is feasible and cheaper. If the SLP ended infeasible, LP repair with its bins is "
    "tried first. Update the incumbent.",
    "**[New] Restart rule.** Runs 1–3, and any run after 6 ILS runs without improving the incumbent, go back to "
    "Step 2 (diversification).",
    "**[New] Regret-guided ILS run.** Otherwise build 4 candidates from the incumbent with (R1)–(R2), repair each "
    "(Step 3), probe each with a 10-iteration SLP, continue the full SLP (Step 4) from the best probe (feasible first, "
    "then lowest cost), and go to Step 5."]
T["algo_after"] = [
    "Each pass through Steps 2–7 counts as one _run_, including the probes. Run-based metrics (%Feas, %Good, Ti, It) "
    "are therefore comparable with the baseline, whose run is one random start followed by SLP. The probe step came "
    "from implementation experience: from an af-3 incumbent stuck 0.96% above the best known value, we tried all "
    "56 single re-seeding moves (8 highest-regret products × 7 bins). Only 3 of them led the full SLP to a Good "
    "solution. The LP cost of the repaired point did not identify them, but a 10- or 25-iteration SLP probe ranked an "
    "escaping move first in both cases."]
T["pseudo"] = [
    "Input : instance, number of runs K = 20, seed",
    "Output: best feasible point x*, lower bound LB",
    "1  (q, c*, LB) <- DietRelaxation()                 # P small LPs (once)",
    "2  x* <- None ; stall <- 0",
    "3  for k = 0 .. K-1 do",
    "4      if k < 3 or stall >= 6:                      # diversification",
    "5          x0 <- Repair(Project(WeightedKMeans(q + noise, M))) ; stall <- 0",
    "6      else:                                        # regret-guided ILS",
    "7          for j = 1..4:  p ~ regret(x*), m ~ U{1..M}, alpha ~ U(0, 0.5)",
    "8              Lam_j <- Project(Lam(x*) with row m <- (1-alpha) q_p + alpha Lam_m(x*))",
    "9              y_j  <- FilterSLP_10it(Repair(Lam_j))  # short probe",
    "10         x0 <- best y_j  (feasible first, then cost)",
    "11     x <- Polish(FilterSLP(x0))                   # IA-1 SLP unchanged + LP polish",
    "12     if feasible(x) and f(x) < f(x*): x* <- x ; stall <- 0   else if ILS run: stall += 1",
    "13 end for",
    "14 return x*, LB"]
T["pseudo_slp"] = [
    "FilterSLP.solve(x)   (IA-1 slp.py, unchanged): rho <- 0.5 ; filter F <- {}",
    "for k = 1..400:",
    "   LP: min c'y  s.t. linearised rows at x, lb <= y <= ub, |y - x| <= rho*width    (HiGHS, warm basis)",
    "   if LP infeasible: block restoration (exact LPs, mu or (lam,V) fixed), else elastic l1 LP",
    "   if h(x) <= 1e-6 and (step <= 1e-9 or dq <= 1e-9(1+|f|)): stop (converged)",
    "   accept if sufficient decrease (sigma = 0.1) and not dominated by F (beta = 0.99, gamma = 0.01)",
    "   accept: x <- y ; rho <- min(1, 2 rho) at the boundary;   reject: rho <- 0.5 min(rho, step)",
    "until rho < 1e-9"]

T["impl_lead"] = [
    "Both methods use the same IA-1 files: the parser and qq-model (qq_model.py), the filter-SLP (slp.py) and the "
    "experiment runner (run_experiments.py, extended with --method). The only new algorithmic file is rg_ils.py. The "
    "baseline and proposed runs differ only in the starting points, the end-point polish and the restart strategy, so "
    "the comparison isolates the team's contribution."]
T["env_table"] = [
    ["Programming Language", "Python 3.13"],
    ["Libraries / Tools", "NumPy, SciPy 1.18 (bundled HiGHS LP solver: warm-started dual simplex in slp.py, linprog in rg_ils.py), pandas, matplotlib, openpyxl"],
    ["Hardware / Runtime", "Linux cloud container, 2 vCPU, 7 GB RAM; single-threaded runs, two experiment queues in parallel. IA-1 notebook: Windows laptop (Anaconda). Paper [1]: Xeon E5-2670 2.6 GHz, CPLEX"],
    ["Dataset", "af-1, af-3, af-4, af-5, af-5-fs, af-6-fs, af-7, af-7b (Grothey & McKinnon [10]); the same files as IA-1"],
    ["Baseline Algorithm", "IA-1 code unchanged: QQModel.random_start + FilterSLP (ρ0 = 0.5, ρmax = 1, β = 0.99, γ = 0.01, σ = 0.1, ≤ 400 it.)"],
    ["Proposed Algorithm", "RG-ILS-SLP (rg_ils.py) around the same FilterSLP"],
    ["Parameter Settings", "Dirichlet noise 0.3; ≤ 6 repair rounds; elastic penalty 1e4; ≤ 10 polish rounds; 3 initial recipe starts; patience 6; 4 candidates × 10-iteration probes; α ~ U(0, 0.5); bin noise 0.05"],
    ["Stopping Criteria", "SLP as in IA-1. Feasible: max scaled violation ≤ 1e-6. Good: feasible and ≤ 1.002 × best known. 20 runs per seed and instance"]]
T["dataset"] = [
    "The instances come from industrial animal-feed practice and were published with [1] [10]. They are AMPL data "
    "files with nutrient contents, product specs, tonnages, raw-material costs, bounds on bin and product proportions "
    "and, in some files, bin nutrient bounds. We use all eleven instances; the paper's af-6 is the file af-6-f.txt. The "
    "IA-1 parser is reused unchanged, including its handling of the swapped λ/μ names in the files."]
T["dataset_after"] = [
    "Problem sizes (n, m) are those of the IA-1 qq-model. The last three columns compare our diet-relaxation bound "
    "with Baron's bound from [1]. On af-1 they agree to five digits; on the instances with restricted bins the diet "
    f"bound is weaker ({V['lbgap_min']:.1f}–{V['lbgap_max']:.0f}% below the best known value), because it ignores bin sharing. There is no train/test split, since each instance is "
    "an independent optimisation problem."]
T["design"] = [
    "Each method is run on each instance with 3 seeds (12345, the IA-1 seed, then 2024 and 7) × 20 runs. In total "
    "that is 1,320 runs, plus 440 ablation runs with seed 12345. The metrics follow [1]: %Feas, %Good, Ti (s per run), "
    "It (SLP iterations per run) and ETiGood = 100·Ti/%Good, pooled over the 60 runs. We add the per-seed spread, "
    "the median gap of feasible runs, the time to the first Good run, a one-sided Fisher exact test on Good and "
    "feasible counts, and a one-sided Mann–Whitney U test on final gaps (infeasible runs count as worst)."]
T["design_table"] = [
    ["E1 Baseline", "IA-1 code, random multistart", "3 seeds × 20 runs × 11 instances", "%Feas, %Good, Ti, It, ETiGood", "reference; seed 12345 = IA-1 notebook"],
    ["E2 Proposed", "RG-ILS-SLP", "3 seeds × 20 runs × 11 instances", "same + gaps, tests", "evaluate the contribution"],
    ["E3 Ablation A", "random start + SLP + LP polish", "seed 12345, 20 runs × 11", "%Feas, %Good", "effect of polish alone"],
    ["E4 Ablation B", "recipe start + repair + SLP + polish, independent runs", "seed 12345, 20 runs × 11", "%Feas, %Good", "effect of the start without ILS"],
    ["E5 External", "published SLP-CPLEX [1]; IA-1 notebook", "500 runs [1]; 20 runs (IA-1)", "%Good, ETiGood", "position against the literature"]]
T["evidence"] = [
    "Before the experiments we checked the implementation. With seed 12345 the baseline reproduces the IA-1 notebook "
    "exactly on all eight instances that the notebook ran (same %Feas, %Good, It and best objective, e.g. af-1: 100%, 72.5 iterations, "
    "296.44604). Points assembled from LP solutions satisfy every qq-equation to ~10^-14^. The af-1 diet bound "
    "(295.93153) equals Baron's bound. Re-running the final code reproduces the stored per-run results bit-for-bit. "
    "Listings 1–3 show key code and console output. The full code, logs and per-run CSV files are in the submission "
    "folder."]
T["code1"] = [
    "def product_lp(mod, Lam, elastic=False):      # bins fixed -> LP in mu (all products, one HiGHS call)",
    "    V = Lam @ mod.R                            # bin attributes incl. price column (IA-1 scaling)",
    "    for k in range(mod.P):                     # block k: composition = mur R + mub V",
    "        comp = vstack([mod.R[js], V[jb]])      # js / jb = allowed straights / bins (IA-1 index arrays)",
    "        rows: lb[D_var[k,:N]] <= comp[:, :N].T z <= ub[D_var[k,:N]],  sum z = 1",
    "    z <- linprog(cost, block-diagonal rows, bounds from mod.lb / mod.ub)",
    "    return assemble(mod, Lam, Mur, Mub)        # IA-1 vector x with V, D computed exactly"]
T["code2"] = [
    "def recipe_guided_perturb(mod, x, diet, rng):",
    "    Lam, _, Mub = proportions(mod, x)",
    "    reg = regret(mod, x, diet) + 1e-9          # t_p * max(0, cD_p - c*_p)",
    "    m = rng.choice(mod.M, 1, replace=False, p=uniform)",
    "    p = rng.choice(mod.P, p=reg / reg.sum())   # product that pays most for bin sharing",
    "    a = rng.uniform(0.0, 0.5)",
    "    target = Lam.copy(); target[m] = (1 - a) * diet['recipes_bin'][p] + a * Lam[m]",
    "    target *= exp(0.05 * rng.standard_normal(target.shape))",
    "    return project_bins(mod, target / target.sum(1))      # l1-projection LP"]

L = lambda xs: ", ".join(xs[:-1]) + " and " + xs[-1] if len(xs) > 1 else (xs[0] if xs else "none")
T["res_lead"] = [
    "In this section **IA-1** denotes the baseline, our unchanged IA-1 code (random-multistart filter-SLP), and "
    "**IA-2** the proposed RG-ILS-SLP; both are run with the same instances, seeds and machine. All numbers below come "
    "from the per-run CSV files in 06_Results. Paper "
    "values are SLP-CPLEX from Tables 2, 4 and 5 of [1] (500 runs; the paper's af-6 is our af-6-f). IA-1 values are "
    "from our IA-1 notebook (20 runs, seed 12345); for af-2, af-6-f and af-7b-fs, which the notebook did not run, they "
    "come from the same code and seed run in IA-2."]
T["res_base"] = [
    f"The baseline solves the easy instances reliably: af-1, af-5 and af-7b-fs are Good in {pg('af-1','baseline')}, "
    f"{pg('af-5','baseline')} and {pg('af-7b-fs','baseline')} of the runs. The hard instances confirm the gap: %Good is "
    f"{pg('af-2','baseline')} on af-2, {pg('af-3','baseline')} on af-3, {pg('af-4','baseline')} on af-4, "
    f"{pg('af-6-f','baseline')} on af-6-f, {pg('af-6-fs','baseline')} on af-6-fs and {pg('af-7','baseline')} on af-7. "
    f"Only {pf('af-4','baseline')}, {pf('af-6-f','baseline')} and {pf('af-7','baseline')} of the af-4, af-6-f and af-7 "
    f"runs end feasible, and on af-5-fs {100 - g('af-5-fs','baseline','pct_feas'):.0f}% of the runs fail because of "
    "infeasibility, not quality. Once the baseline reaches a good basin it finds very good points: the best known value "
    "on af-4 and af-7b-fs and 0.0015% above it on af-7."]
T["res_prop"] = [
    f"The proposed method ends feasible in {V['feas_p']:.1f}% of the runs; every run is feasible on {V['n_feas100_p']} of "
    f"{V['NI']} instances (af-2: {pf('af-2','proposed')}, af-4: {pf('af-4','proposed')}, af-6-f: "
    f"{pf('af-6-f','proposed')}). On the hard instances %Good is {pg('af-2','proposed')} (af-2), "
    f"{pg('af-3','proposed')} (af-3), {pg('af-4','proposed')} (af-4), {pg('af-6-fs','proposed')} (af-6-fs) and "
    f"{pg('af-7','proposed')} (af-7), but {pg('af-6-f','proposed')} on af-6-f, where its best run is "
    f"{g('af-6-f','proposed','best_gap_pct'):.2f}% above the best known value. It finds the best known value on af-2, "
    "122,267.31 on af-3 (+0.008%) and 2,922.56 on af-6-fs (+0.04%), all better than any baseline run. A proposed run "
    "costs more time on average (LP repair, four probes, polish), but the ILS runs need fewer SLP iterations on the "
    f"larger instances (af-7: {g('af-7','proposed','It'):.0f} vs {g('af-7','baseline','It'):.0f})."]
T["res_cmp"] = [
    f"Table 9 sets IA-1 and IA-2 side by side: its first six rows list what IA-2 changes, the remaining rows what it "
    f"achieves. Averaged over all {V['NI']} instances, IA-2 improves %Feas over IA-1 by "
    f"{V['feas_p'] - V['feas_b']:+.1f} points and %Good by {V['good_p'] - V['good_b']:+.1f} points. On the "
    f"{V['NH']} hard instances %Good rises from {V['good_b_hard']:.1f}% to {V['good_p_hard']:.1f}%, and the expected "
    f"time to a Good solution is {V['spd_hard']:.1f}× shorter (geometric mean over {L(V['spd_hard_insts'])}; on af-6-f "
    f"the proposed method has no Good run). Over all instances where both methods find a Good run the speed-up is "
    f"{V['spd_geo']:.1f}×, lower because the easy instances become slower."]
T["res_cmp_after"] = [
    f"Table 10 adds the published SLP-CPLEX results. IA-2 has a higher %Good than the paper on "
    f"{V['n_beat_paper']} of {V['NI']} instances ({L(V['beat_paper'])}). The differences are largest on the "
    f"instances that motivated the gap: af-2 {pg('af-2','proposed')} vs 19.4%, af-4 {pg('af-4','proposed')} vs 19.8%, "
    f"af-6-fs {pg('af-6-fs','proposed')} vs 5.2% and af-3 {pg('af-3','proposed')} vs 20.0%. It is lower on af-6-f "
    f"({pg('af-6-f','proposed')} vs 4.0%) and af-7 ({pg('af-7','proposed')} vs 20.4%), and marginally lower on af-5 "
    f"and af-5-fs (98.3% vs 100% and 99.6%). ETiGood beats the paper on af-2 ({et('af-2','proposed')} vs 6.7 s), "
    f"af-6-fs ({et('af-6-fs','proposed')} vs 125 s), af-7b and af-1, is close on af-3 ({et('af-3','proposed')} vs "
    "6.5 s), and is slower elsewhere: Python/HiGHS is slower per LP than C/CPLEX, and the paper used 500 runs on "
    "different hardware. The comparison with our own baseline uses identical code, machine and seeds."]
T["res_stats"] = [
    f"Table 11 tests whether IA-2 is better than IA-1 on the pooled 60 runs per method. More Good runs is significant at the "
    f"1% level on {L(V['sig_good'])}, and more feasible runs at the 5% level on {L(V['sig_feas'])}. Lower final gaps "
    f"(Mann–Whitney, 1% level) are significant on {len(V['sig_gap'])} of {V['NI']} instances; the exceptions are af-1, "
    "where both methods are always Good, and af-6-f, where neither is reliable. Table A1 shows the per-seed results: "
    "on the hard instances the proposed method beats the baseline's %Good for every seed except af-7 with seed 2024 "
    "(10% vs 10%) and af-6-f (0% vs 5%, 0% and 0%). The spread between seeds is large on af-6-fs (5–60%) because a "
    "chain either finds the good basin early and stays there, or does not. ILS runs within one seed are not "
    "independent, so the tests treat each run as one sample of 'one run of the search' and slightly overstate the "
    "effective sample size. The between-seed spread is the more conservative measure."]
T["discussion"] = [
    "**Does the method close the gap?** Mostly yes. The gap was low %Good and failed runs on the hard instances, "
    "caused by memory-less random restarts. The proposed method makes almost every run feasible and multiplies %Good "
    f"on af-2 (×{g('af-2','proposed','pct_good') / g('af-2','baseline','pct_good'):.0f}), af-3 (×{g('af-3','proposed','pct_good') / max(g('af-3','baseline','pct_good'), 1e-9):.0f}), af-4 "
    f"(×{g('af-4','proposed','pct_good') / g('af-4','baseline','pct_good'):.1f}) and af-6-fs "
    f"(×{g('af-6-fs','proposed','pct_good') / g('af-6-fs','baseline','pct_good'):.0f}). It does not close the gap on "
    "af-6-f (the paper's af-6), where both methods stay about 1% above the best known value. Figure 4 shows how it "
    "works on the others: "
    "after the first recipe starts the incumbent is already close to 0.2%, and the probed ILS moves search its "
    "neighbourhood instead of restarting from scratch.",
    f"**Which component matters? (Table 12, Figure 7, seed 12345.)** The LP polish alone mainly fixes feasibility (af-4 "
    f"{ab('af-4','baseline',0)} → {ab('af-4','abl_polish',0)}, af-5-fs {ab('af-5-fs','baseline',0)} → "
    f"{ab('af-5-fs','abl_polish',0)}, af-6-fs {ab('af-6-fs','baseline',0)} → {ab('af-6-fs','abl_polish',0)}) and "
    f"leaves %Good on the hard instances almost unchanged. Independent recipe-clustering starts help most on af-6-fs "
    f"({ab('af-6-fs','abl_rcstart')}), af-7 ({ab('af-7','abl_rcstart')}) and af-7b ({ab('af-7b','abl_rcstart')}), "
    f"but not on af-3 ({ab('af-3','abl_rcstart')}) or af-4 ({ab('af-4','abl_rcstart')}). The full ILS adds the large "
    f"gains on af-2 ({ab('af-2','abl_rcstart')} → {ab('af-2','proposed')}), af-3 ({ab('af-3','proposed')}) and af-4 "
    f"({ab('af-4','proposed')}). With this seed, recipe starts alone are better on af-6-fs ({ab('af-6-fs','abl_rcstart')} "
    f"vs {ab('af-6-fs','proposed')}) and, notably, on af-6-f ({ab('af-6-f','abl_rcstart')} vs {ab('af-6-f','proposed')}): "
    "there the ILS keeps refining an incumbent that is about 1% above the best known value instead of exploring. The "
    "components therefore complement each other: fresh cost-aware starts give diversity, and the ILS gives depth.",
    "**Why does it work?** In the qq-formulation the hard decisions are the bin compositions. Once they are fixed, "
    "the product LP gives the optimal recipes exactly. The diet relaxation shows which product pays most for bin "
    "sharing, so re-seeding a bin with that product's ideal recipe is a targeted move rather than a random jump. The "
    "short SLP probe tells whether the move leads anywhere before the full SLP is spent on it.",
    "**What did not work (implementation experience).** Before the final design we tested, on af-3, af-4 and af-7, a "
    "smaller initial trust region for the guided starts (ρ~0~ = 0.05 or 0.1), a trust region on the proportions only, "
    "choosing the bin by 1/usage, re-seeding more bins after failures, and ranking candidates by their LP cost. None "
    "of these was consistently better, and the small trust region was clearly worse (%Feas fell to 55–80%). Results "
    "from a single seed varied by up to 45 points between configurations, which is why the final comparison uses "
    "three seeds.",
    "**Limitations.** (i) af-6-f is not solved: no proposed run reaches 0.2% (baseline 1 of 60, paper 4.0%), and "
    "af-7 stays slightly below the paper's %Good. "
    f"(ii) On af-4 the proposed best is {g('af-4','proposed','best_gap_pct'):.2f}% above the best known value, while "
    "one baseline run found the best known value exactly: the proposed method is more reliable, but not always better "
    "in the single best run. (iii) On easy instances (af-1, af-5, af-5-fs, af-7b-fs) the extra LPs make ETiGood up to about 2× worse. "
    "(iv) Parameters were set once, but on the same instances that are reported. (v) 3 × 20 runs is fewer than the "
    "500 runs of [1]. (vi) The diet bound proves near-optimality only on af-1."]
T["conclusion"] = [
    "IA-1 showed that random-multistart SLP on the qq-formulation [1], as implemented by our group, is fast but wastes "
    "many restarts on poor or infeasible basins on the harder feed-mill instances. In IA-2 we kept the IA-1 model and "
    "SLP files unchanged and added three LP sub-problems that follow from the bilinear structure: a diet relaxation, a "
    "product LP with bins fixed and a bin LP with bin shares fixed. RG-ILS-SLP uses them to build cost-aware feasible "
    "starts, polish every SLP end point and guide restarts by product regret, with short SLP probes to choose among "
    "candidate moves.",
    f"Over 3 seeds × 20 runs on all {V['NI']} instances, mean %Feas rose from {V['feas_b']:.1f}% to {V['feas_p']:.1f}% and "
    f"mean %Good from {V['good_b']:.1f}% to {V['good_p']:.1f}%. On the hard instances %Good rose from "
    f"{V['good_b_hard']:.1f}% to {V['good_p_hard']:.1f}% (paper: {V['good_paper_hard']:.1f}%), and the expected time "
    f"to a Good solution fell by {V['spd_hard']:.1f}×. The gains are statistically significant on "
    f"{len(V['sig_good'])} instances for %Good and {len(V['sig_gap'])} for solution gaps. af-6-f remains unsolved by "
    "both methods. Structure-aware restarts are therefore a cheap and effective way to improve "
    "SLP for fixed-demand pooling, at the cost of some overhead on easy instances."]
T["future"] = [
    "Use more seeds or 500 runs to match the statistical power of [1], and study why af-6-f resists both methods.",
    "Choose adaptively between recipe restarts and ILS moves (e.g. a bandit rule), since the ablation shows recipe starts "
    "are stronger on af-6-fs and af-7b and the ILS on af-3 and af-4.",
    "Run the 4 probes in parallel and skip the extra LPs on easy instances to remove the overhead.",
    "Strengthen the diet bound with McCormick or pq-type cuts to obtain certified gaps on the harder instances.",
    "Extend to bin capacities, raw-material availability and bin-to-bin flows (generalised pooling)."]
T["refs"] = [
    "A. Grothey and K. McKinnon, “On the effectiveness of sequential linear programming for the pooling problem,” _Annals of Operations Research_, vol. 322, pp. 691–711, 2023, doi: 10.1007/s10479-022-05156-7.",
    "M. Terzi, Y. Ouazene, A. Yalaoui and F. Yalaoui, “Matheuristics vs. metaheuristics for joint lot-sizing and dynamic pricing problem with nonlinear demands,” _Computers & Operations Research_, vol. 163, 106507, 2024, doi: 10.1016/j.cor.2023.106507.",
    "S. Sass, A. Mitsos, D. Bongartz, I. H. Bell, N. I. Nikolov and A. Tsoukalas, “A branch-and-bound algorithm with growing datasets for large-scale parameter estimation,” _European Journal of Operational Research_, vol. 316, pp. 36–45, 2024, doi: 10.1016/j.ejor.2024.02.020.",
    "P. E. Gill and M. Zhang, “A projected-search interior-point method for nonlinearly constrained optimization,” _Computational Optimization and Applications_, vol. 88, pp. 37–70, 2024, doi: 10.1007/s10589-023-00549-1.",
    "M. Muehlebach and M. I. Jordan, “Accelerated first-order optimization under nonlinear constraints,” _Mathematical Programming_, vol. 215, pp. 407–452, 2026, doi: 10.1007/s10107-025-02224-1.",
    "D. di Serafino, W. W. Hager, G. Toraldo and M. Viola, “On the stationarity for nonlinear optimization problems with polyhedral constraints,” _Mathematical Programming_, vol. 205, pp. 107–134, 2024, doi: 10.1007/s10107-023-01979-9.",
    "R. Misener and C. A. Floudas, “Advances for the pooling problem: modeling, global optimization, and computational studies,” _Applied and Computational Mathematics_, vol. 8, pp. 3–22, 2009.",
    "C. A. Haverly, “Studies of the behavior of recursion for the pooling problem,” _ACM SIGMAP Bulletin_, no. 25, pp. 19–28, 1978.",
    "C. Audet, J. Brimberg, P. Hansen, S. Le Digabel and N. Mladenović, “Pooling problem: alternate formulations and solution methods,” _Management Science_, vol. 50, no. 6, pp. 761–776, 2004.",
    "A. Grothey and K. McKinnon, “Pooling problem test data,” 2020. [Online]. Available: https://www.maths.ed.ac.uk/~agr/PoolingProbs/",
    "R. Fletcher and S. Leyffer, “Nonlinear programming without a penalty function,” _Mathematical Programming_, vol. 91, pp. 239–269, 2002.",
    "Q. Huangfu and J. A. J. Hall, “Parallelizing the dual revised simplex method,” _Mathematical Programming Computation_, vol. 10, pp. 119–142, 2018.",
    "H. R. Lourenço, O. C. Martin and T. Stützle, “Iterated local search: framework and applications,” in _Handbook of Metaheuristics_, 3rd ed., Springer, 2019, pp. 129–168.",
    "D. Arthur and S. Vassilvitskii, “k-means++: the advantages of careful seeding,” in _Proc. 18th ACM-SIAM Symposium on Discrete Algorithms (SODA)_, 2007, pp. 1027–1035.",
    f"Group {G['id']} (R. Tambe, S. Tripathi, V. Sharma), “Sequential Linear Programming for Nonlinear Pooling Optimization Problems: a literature review and re-implementation,” IA-1 report, Introduction to Optimization Techniques, K. J. Somaiya College of Engineering, 2026."]
T["appA"] = [
    "Table A1 gives %Feas / %Good for every seed, with the mean ± standard deviation and the worst objective over "
    "feasible runs. Table A2 lists further metrics, including the time to the first Good run (mean over the seeds that "
    "found one). Table A3 shows the bin compositions of the best af-3 solution found by the proposed method."]
T["appB"] = [
    "All final IA-2 deliverables are in the group's Google Drive folder (access: anyone with the link – viewer): "
    + G.get("drive", "[Drive link]") + ". Source code online (GitHub, with a runnable Google Colab notebook "
    "IA2_Demo_Colab.ipynb): " + G.get("code", "[GitHub link]") + ". The folder structure is:"]
T["folder"] = [
    f"{G['id']}_IA2/",
    "├── 01_Research_Paper/    Research_Paper_Draft.pdf (+ .docx)",
    "├── 02_PPT/               Presentation.pdf, Presentation.pptx",
    "├── 03_Poster/            Poster.pdf",
    "├── 04_Source_Code/       qq_model.py, slp.py (IA-1, unchanged), run_experiments.py (extended),",
    "│                         rg_ils.py (new), analyze_results.py, make_flowchart.py, run_all.sh, README.md",
    "├── 05_Dataset/           af-1.txt ... af-7b-fs.txt",
    "├── 06_Results/           Result_Tables.xlsx, Graphs/, baseline|proposed|abl_*/seed*/runs_*.csv, logs/",
    "└── 07_Supporting_Material/  IA-1 report, form answers, flowchart"]

def _fix(o):                      # a lone "~" would be read as a subscript marker by build_paper.js
    if isinstance(o, str):
        return o.replace(" ~ ", " ∼ ")
    if isinstance(o, list):
        return [_fix(v) for v in o]
    return o


T = {k: (v if k in ("pseudo", "pseudo_slp", "code1", "code2", "folder") else _fix(v)) for k, v in T.items()}
(H / "paper_text.json").write_text(json.dumps(T, indent=1, ensure_ascii=False))
print("ok")
