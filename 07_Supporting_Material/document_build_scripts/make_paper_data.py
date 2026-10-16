"""Builds paper_data.json (tables) and cmp_values.json (numbers for the prose) from the IA-2 results."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results"
S = pd.read_csv(R / "summary.csv")
SS = pd.read_csv(R / "summary_by_seed.csv")
T = pd.read_csv(R / "stats.csv").set_index("instance")
GROUP = json.loads((Path(__file__).parent / "group.json").read_text())
sys.path.insert(0, str(ROOT / "code"))
from analyze_results import PAPER, IA1, BEST, ORDER, HARD       # noqa: E402  (11 instances, 6 hard)
from qq_model import load_instance, QQModel                      # noqa: E402
from rg_ils import diet_relaxation                               # noqa: E402

BARON_LB = {"af-2": 235751.11, "af-6-f": 2937.68, "af-7b-fs": 130147.66, "af-1": 295.93153, "af-3": 120498.73, "af-4": 183620.39, "af-5-fs": 118763.29, "af-5": 123243.60,
            "af-6-fs": 2881.41, "af-7": 145928.01, "af-7b": 145928.01}


def fm(x, d=2):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if isinstance(x, float) and math.isinf(x):
        return "∞"
    if isinstance(x, float) and abs(x) < 0.5 * 10 ** -d:
        x = 0.0
    return f"{x:,.{d}f}"


def row(inst, meth, seed=None):
    if seed is None:
        r = S[(S.instance == inst) & (S.method == meth)]
    else:
        r = SS[(SS.instance == inst) & (SS.method == meth) & (SS.seed == seed)]
    return None if r.empty else r.iloc[0]


D = {"group": GROUP}
# ---- gap evidence: paper vs IA-1 notebook
D["gap_rows"] = [[i, fm(PAPER[i][1], 1), fm(PAPER[i][2], 1), fm(PAPER[i][4], 1), fm(IA1[i][1], 0),
                  fm(IA1[i][2], 0), fm(IA1[i][3], 1)] for i in ORDER]
# ---- instances
inst_rows, LBs = [], {}
for i in ORDER:
    ins = load_instance(str(ROOT / "data" / f"{i}.txt")); m = QQModel(ins)
    lb = diet_relaxation(m)["LB"]; LBs[i] = lb
    inst_rows.append([i, ins.N, ins.I, ins.M, ins.P, m.n, m.m_total, fm(BEST[i], 2), fm(lb, 2), fm(BARON_LB[i], 2),
                      f"{100 * (BEST[i] - lb) / BEST[i]:.2f}"])
D["inst_rows"] = inst_rows


def method_rows(meth):
    out = []
    for i in ORDER:
        r = row(i, meth)
        out.append([i, fm(r.Ti), fm(r.pct_feas, 1), f"{r.pct_good:.1f} ± {r.pct_good_sd:.1f}", fm(r.It, 1),
                    fm(r.ETiGood, 1), fm(r.best_f, 2), fm(r.best_gap_pct, 3)])
    return out


D["base_rows"] = method_rows("baseline")
D["prop_rows"] = method_rows("proposed")
b = S[S.method == "baseline"].set_index("instance").loc[ORDER]
p = S[S.method == "proposed"].set_index("instance").loc[ORDER]
geo = lambda s: float(np.exp(np.log(s).mean()))
both = (b.ETiGood < np.inf) & (p.ETiGood < np.inf)
spd = b.ETiGood[both] / p.ETiGood[both]
hb = [i for i in HARD if np.isfinite(b.loc[i].ETiGood) and np.isfinite(p.loc[i].ETiGood)]
spd_hard = (b.ETiGood / p.ETiGood).loc[hb]
sig_good = [i for i in ORDER if T.loc[i].p_fisher_good < 0.01]
sig_feas = [i for i in ORDER if T.loc[i].p_fisher_feas < 0.05]
sig_gap = [i for i in ORDER if T.loc[i].p_mannwhitney_gap < 0.01]
NI, NH = len(ORDER), len(HARD)
V = dict(feas_b=b.pct_feas.mean(), feas_p=p.pct_feas.mean(), good_b=b.pct_good.mean(), good_p=p.pct_good.mean(),
         good_b_hard=b.pct_good.loc[HARD].mean(), good_p_hard=p.pct_good.loc[HARD].mean(),
         good_paper_hard=float(np.mean([PAPER[i][2] for i in HARD])),
         ti_b=b.Ti.mean(), ti_p=p.Ti.mean(), it_b=b.It.mean(), it_p=p.It.mean(),
         mgap_b=b.median_gap_pct.mean(), mgap_p=p.median_gap_pct.mean(),
         spd_geo=geo(spd), spd_hard=geo(spd_hard),
         n_feas100_b=int((b.pct_feas == 100).sum()), n_feas100_p=int((p.pct_feas == 100).sum()),
         n_beat_paper=int(sum(p.loc[i].pct_good > PAPER[i][2] for i in ORDER)),
         beat_paper=[i for i in ORDER if p.loc[i].pct_good > PAPER[i][2]],
         below_paper=[i for i in ORDER if p.loc[i].pct_good < PAPER[i][2]],
         spd_hard_insts=hb, sig_good=sig_good, sig_feas=sig_feas, sig_gap=sig_gap, NI=NI, NH=NH,
         slower=[i for i in ORDER if p.loc[i].ETiGood > b.loc[i].ETiGood],
         lbgap_min=min(100 * (BEST[i] - LBs[i]) / BEST[i] for i in ORDER if i != "af-1"),
         lbgap_max=max(100 * (BEST[i] - LBs[i]) / BEST[i] for i in ORDER),
         lb_af1=LBs["af-1"])
D["cmp_rows"] = [
    ["Model and SLP solver", "qq_model.py + slp.py", "same files, unchanged", "retained", "only what happens around the SLP changes"],
    ["Starting points", "uniform random proportions", "recipe clustering (diet LP + k-means++) + LP repair", "modified", "cost-aware, near-feasible starts"],
    ["Restarts", "independent random multistart", "regret-guided ILS from the incumbent; 4 moves ranked by 10-iteration SLP probes", "new", "later runs reuse the best solution found"],
    ["SLP end point", "returned as is", "LP polish (product LP, then bin LP)", "new", "exact feasibility, cost never increases"],
    ["Lower bound", "none", "diet LP (af-1: equal to Baron's bound)", "new", "quality certificate in milliseconds"],
    ["Evaluation", "IA-1 report: af-1, 20 runs", f"{NI} instances × 3 seeds × 20 runs, tests, ablation", "extended", "same protocol for both methods"],

    [f"%Feas (mean of {NI})", fm(V["feas_b"], 1), fm(V["feas_p"], 1), f"{V['feas_p'] - V['feas_b']:+.1f} pts",
     f"all runs feasible on {V['n_feas100_p']}/{NI} instances (baseline {V['n_feas100_b']}/{NI})"],
    [f"%Good (mean of {NI})", fm(V["good_b"], 1), fm(V["good_p"], 1), f"{V['good_p'] - V['good_b']:+.1f} pts",
     "significant (Fisher, p < 0.01) on " + ", ".join(sig_good)],
    [f"%Good, {NH} hard instances", fm(V["good_b_hard"], 1), fm(V["good_p_hard"], 1),
     f"{V['good_p_hard'] - V['good_b_hard']:+.1f} pts", f"paper SLP-CPLEX: {V['good_paper_hard']:.1f}%"],
    ["Ti, s per run (mean)", fm(V["ti_b"]), fm(V["ti_p"]), f"{100 * (V['ti_p'] / V['ti_b'] - 1):+.0f}%",
     "LP repair, probes and polish cost time per run"],
    ["SLP iterations per run (mean)", fm(V["it_b"], 1), fm(V["it_p"], 1), f"{100 * (V['it_p'] / V['it_b'] - 1):+.0f}%",
     "incl. the 4 × 10 probe iterations of ILS runs"],
    [f"ETiGood speed-up, hard inst. (geo-mean)", "1.0×", f"{V['spd_hard']:.1f}×", f"{V['spd_hard']:.1f}× faster",
     "over " + ", ".join(hb) + " (af-6-f: proposed has no Good run)"],
    [f"ETiGood speed-up, all with Good runs (geo-mean)", "1.0×", f"{V['spd_geo']:.1f}×", f"{V['spd_geo']:.1f}×",
     "slower on " + ", ".join(V["slower"])],
    [f"Median gap of feasible runs, % (mean of {NI})", fm(V["mgap_b"], 3), fm(V["mgap_p"], 3),
     f"{V['mgap_p'] - V['mgap_b']:+.3f} pts", f"Mann–Whitney p < 0.01 on {len(sig_gap)} of {NI} instances"],
]
D["paper_rows"] = [[i, fm(PAPER[i][2], 1), fm(b.loc[i].pct_good, 1), fm(p.loc[i].pct_good, 1),
                    fm(PAPER[i][4], 1), fm(b.loc[i].ETiGood, 1), fm(p.loc[i].ETiGood, 1)] for i in ORDER]
stat = []
for i in ORDER:
    t = T.loc[i]
    stat.append([i, t.good_base, t.good_prop, f"{t.p_fisher_good:.4f}" if t.p_fisher_good >= 1e-4 else "< 0.0001",
                 t.feas_base, t.feas_prop, f"{t.p_fisher_feas:.4f}" if t.p_fisher_feas >= 1e-4 else "< 0.0001",
                 f"{t.median_gap_base:.3f}" if t.median_gap_base < 1e8 else "infeas.",
                 f"{t.median_gap_prop:.3f}", f"{t.p_mannwhitney_gap:.4f}" if t.p_mannwhitney_gap >= 1e-4 else "< 0.0001"])
D["stat_rows"] = stat
seed_rows = []
for i in ORDER:
    for meth, lab in [("baseline", "IA-1 (baseline)"), ("proposed", "IA-2 (proposed)")]:
        cells = []
        for sd in [12345, 2024, 7]:
            r = row(i, meth, sd)
            cells.append(f"{r.pct_feas:.0f} / {r.pct_good:.0f}")
        r = row(i, meth)
        seed_rows.append([i, lab, *cells, f"{fm(r.mean_f, 2)} ± {fm(r.std_f, 2)}", fm(r.worst_f, 2)])
D["seed_rows"] = seed_rows
labs = {"baseline": "IA-1 (baseline)", "abl_polish": "A: random + polish", "abl_rcstart": "B: recipe start, no ILS",
        "proposed": "IA-2 (proposed)"}
D["abl_rows"] = []
ABL = {}
for i in ORDER:
    ABL[i] = {m: (row(i, m, 12345).pct_feas, row(i, m, 12345).pct_good, row(i, m, 12345).Ti) for m in labs}
    D["abl_rows"].append([i] + [f"{ABL[i][m][0]:.0f} / {ABL[i][m][1]:.0f}" for m in labs])
full = []
for i in ORDER:
    for meth in ["baseline", "proposed"]:
        r = row(i, meth)
        full.append([i, labs[meth], fm(r.Ti), fm(r.pct_feas, 1), fm(r.pct_good, 1), f"{r.good_min:.0f}–{r.good_max:.0f}",
                     fm(r.It, 1), fm(r.ETiGood, 1), fm(r.time_to_first_good_mean, 1), fm(r.median_gap_pct, 3)])
D["full_rows"] = full
# best af-4 / af-3 bins of the proposed method
best = None
for f in sorted((R / "proposed").glob("seed*/best_x_af-3.npy")):
    x = np.load(f)
    ins = load_instance(str(ROOT / "data" / "af-3.txt")); m = QQModel(ins)
    if best is None or m.objective(x) < best[0]:
        best = (m.objective(x), x, m, ins)
fbest, x, m, ins = best
from rg_ils import proportions                                   # noqa: E402
Lam, Mur, Mub = proportions(m, x)
use = m.tons @ Mub
cols = [k for k in range(ins.M)]
rms = [i for i in range(ins.I) if Lam[:, i].max() > 1e-4]
D["bins_header"] = ["Raw material"] + [f"{ins.MI[k]}" for k in cols]
D["bins_rows"] = [[ins.RM[i]] + [f"{100 * Lam[k, i]:.1f}" if Lam[k, i] > 1e-4 else "" for k in cols] for i in rms] + \
    [["**tonnage served**"] + [f"**{use[k]:.0f}**" for k in cols]]
D["bins_f"] = fbest
# console excerpt (seed 12345, af-4)
log = (R / "logs" / "queue2.log").read_text().splitlines()
st = [k for k, l in enumerate(log) if l.startswith("== af-4: method=proposed") and "seed=12345" in l][0]
con = log[st:st + 13]
D["console"] = ["$ python run_experiments.py --method proposed --instances af-4 --runs 20 --seed 12345"] + \
    [l.strip() for l in con[1:]] + ["  ..."]
(Path(__file__).parent / "paper_data.json").write_text(json.dumps(D, indent=1, ensure_ascii=False))
(Path(__file__).parent / "cmp_values.json").write_text(json.dumps({**V, "abl": ABL}, indent=1, default=float))
print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in V.items()}, indent=0))
for r in D["abl_rows"]:
    print(r)
print(D["console"][:5], fbest)
