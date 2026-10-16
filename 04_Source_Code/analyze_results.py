"""
analyze_results.py - IA-2 result tables (Excel) and graphs.

Reads   <results>/<method>/seed<s>/runs_<instance>.csv   written by run_experiments.py
        (methods: baseline = IA-1 code unchanged, proposed = RG-ILS-SLP, abl_polish, abl_rcstart)
Writes  <results>/Result_Tables.xlsx, summary_by_seed.csv, summary.csv, comparison.csv, stats.csv
        <results>/Graphs/*.png
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RES = next((d for d in [ROOT / "06_Results", ROOT / "results"] if d.exists()), ROOT / "results")
GR = RES / "Graphs"
GR.mkdir(parents=True, exist_ok=True)

ORDER = ["af-1", "af-2", "af-3", "af-4", "af-5", "af-5-fs", "af-6-f", "af-6-fs", "af-7", "af-7b", "af-7b-fs"]
# hard = instances where the published SLP-CPLEX is Good in <= 20.4% of the runs
HARD = ["af-2", "af-3", "af-4", "af-6-f", "af-6-fs", "af-7"]
# Grothey & McKinnon (2023), SLP-CPLEX, Tables 2/4/5 (500 runs): Ti, %Feas, %Good, It, ETiGood
PAPER = {
    "af-1": (0.5, 100.0, 79.0, 38.0, 0.6), "af-3": (1.3, 99.2, 20.0, 50.6, 6.5),
    "af-4": (1.7, 98.5, 19.8, 49.1, 8.6), "af-5-fs": (1.7, 100.0, 99.6, 61.2, 1.7),
    "af-5": (1.5, 99.8, 100.0, 53.9, 1.5), "af-6-fs": (6.5, 95.0, 5.2, 47.0, 125.0),
    "af-7": (4.6, 99.0, 20.4, 61.5, 22.5), "af-7b": (12.3, 98.8, 71.8, 72.0, 17.1),
    # af-6 of the paper = data file af-6-f.txt; ETiGood = 100*Ti/%Good from Tables 2/4
    "af-2": (1.3, 100.0, 19.4, 58.7, 6.7), "af-6-f": (4.5, 78.4, 4.0, 47.7, 112.5),
    "af-7b-fs": (14.7, 99.0, 52.6, 48.5, 27.9),
}
# IA-1 notebook (final.ipynb, 20 runs, seed 12345, Razzan's laptop): Ti, %Feas, %Good, It, best f
IA1 = {
    "af-1": (1.26, 100.0, 100.0, 72.5, 296.44604), "af-3": (3.08, 100.0, 0.0, 48.2, 122979.56889),
    "af-4": (7.56, 60.0, 25.0, 77.3, 186097.10172), "af-5-fs": (13.17, 90.0, 90.0, 250.8, 119021.91389),
    "af-5": (4.63, 100.0, 100.0, 139.2, 124019.76629), "af-7": (7.33, 75.0, 5.0, 188.0, 151452.43605),
    "af-7b": (12.18, 95.0, 70.0, 137.0, 147318.56602), "af-6-fs": (11.79, 90.0, 0.0, 199.1, 2930.85106),
    # not run in the IA-1 notebook: IA-1 code re-run in IA-2 with the IA-1 seed 12345 (Ti on the IA-2 machine)
    "af-2": (1.03, 95.0, 0.0, 114.8, 240602.23211), "af-6-f": (6.59, 65.0, 5.0, 159.4, 3074.73610),
    "af-7b-fs": (48.10, 100.0, 100.0, 114.8, 130294.89872),
}
BEST = {"af-2": 239334.02, "af-6-f": 3074.23, "af-7b-fs": 130290.06, "af-1": 296.44604, "af-3": 122257.45, "af-4": 186097.11, "af-5-fs": 119016.92, "af-5": 124003.48,
        "af-6-fs": 2921.30, "af-7": 151381.81, "af-7b": 147285.00}
BARON_LB = {"af-1": 295.93153}
LABEL = {"baseline": "IA-1 (baseline)", "proposed": "IA-2 (proposed RG-ILS-SLP)",
         "abl_polish": "Random start + LP polish", "abl_rcstart": "Recipe start + polish (no ILS)"}
BLUE, ORANGE, AQUA, GREY, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984", "#8a5cd0"
INK, INK2 = "#0b0b0b", "#52514e"


def load():
    dfs = []
    for f in sorted(RES.glob("*/seed*/runs_*.csv")):
        d = pd.read_csv(f)
        d["seed"] = int(f.parent.name.replace("seed", ""))
        dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df["feasible"] = df.feasible.astype(bool)
    df["good"] = df.good.astype(bool)
    return df


def ttfg(g):
    """time (s) until the first Good run, runs taken in their order (cumulative run time)"""
    g = g.sort_values("run")
    cum = g.time.cumsum().values
    return float(cum[np.argmax(g.good.values)]) if g.good.any() else np.inf


def summarise_seed(df):
    rows = []
    for (inst, meth, seed), g in df.groupby(["instance", "method", "seed"]):
        pg = 100 * g.good.mean(); ti = g.time.mean(); feas = g[g.feasible]
        rows.append(dict(instance=inst, method=meth, seed=seed, runs=len(g), Ti=ti, pct_feas=100 * g.feasible.mean(),
                         pct_good=pg, It=g.iters.mean(), ETiGood=100 * ti / pg if pg > 0 else np.inf,
                         time_to_first_good=ttfg(g), total_time=g.time.sum(),
                         best_f=feas.f.min() if len(feas) else np.nan,
                         mean_gap_pct=feas.gap_pct.mean() if len(feas) else np.nan))
    return pd.DataFrame(rows)


def summarise(df, ss):
    rows = []
    for (inst, meth), g in df.groupby(["instance", "method"]):
        s = ss[(ss.instance == inst) & (ss.method == meth)]
        feas = g[g.feasible]
        pg = 100 * g.good.mean(); ti = g.time.mean()
        fin = s.time_to_first_good[np.isfinite(s.time_to_first_good)]
        rows.append(dict(
            instance=inst, method=meth, seeds=len(s), runs=len(g), Ti=ti,
            pct_feas=100 * g.feasible.mean(), pct_feas_sd=s.pct_feas.std(ddof=1) if len(s) > 1 else np.nan,
            pct_good=pg, pct_good_sd=s.pct_good.std(ddof=1) if len(s) > 1 else np.nan,
            good_min=s.pct_good.min(), good_max=s.pct_good.max(),
            It=g.iters.mean(), ETiGood=100 * ti / pg if pg > 0 else np.inf,
            seeds_with_good=int((s.pct_good > 0).sum()),
            time_to_first_good_mean=fin.mean() if len(fin) else np.inf,
            best_f=feas.f.min() if len(feas) else np.nan, worst_f=feas.f.max() if len(feas) else np.nan,
            mean_f=feas.f.mean() if len(feas) else np.nan, std_f=feas.f.std(ddof=1) if len(feas) > 1 else np.nan,
            best_gap_pct=feas.gap_pct.min() if len(feas) else np.nan,
            median_gap_pct=feas.gap_pct.median() if len(feas) else np.nan,
            mean_gap_pct=feas.gap_pct.mean() if len(feas) else np.nan,
            ci95_gap=1.96 * feas.gap_pct.std(ddof=1) / np.sqrt(len(feas)) if len(feas) > 1 else np.nan))
    s = pd.DataFrame(rows)
    s["instance"] = pd.Categorical(s.instance, ORDER, ordered=True)
    return s.sort_values(["instance", "method"]).reset_index(drop=True)


def comparison(s):
    rows = []
    for inst in ORDER:
        b = s[(s.instance == inst) & (s.method == "baseline")]
        p = s[(s.instance == inst) & (s.method == "proposed")]
        if b.empty or p.empty:
            continue
        b, p = b.iloc[0], p.iloc[0]
        pa, ia = PAPER[inst], IA1[inst]
        rows.append(dict(instance=inst,
                         paper_Ti=pa[0], paper_feas=pa[1], paper_good=pa[2], paper_It=pa[3], paper_ETiGood=pa[4],
                         ia1_Ti=ia[0], ia1_feas=ia[1], ia1_good=ia[2], ia1_It=ia[3], ia1_best=ia[4],
                         base_Ti=b.Ti, base_feas=b.pct_feas, base_good=b.pct_good, base_good_sd=b.pct_good_sd,
                         base_It=b.It, base_ETiGood=b.ETiGood, base_ttfg=b.time_to_first_good_mean,
                         prop_Ti=p.Ti, prop_feas=p.pct_feas, prop_good=p.pct_good, prop_good_sd=p.pct_good_sd,
                         prop_It=p.It, prop_ETiGood=p.ETiGood, prop_ttfg=p.time_to_first_good_mean,
                         base_best=b.best_f, prop_best=p.best_f, best_known=BEST[inst],
                         base_best_gap_pct=b.best_gap_pct, prop_best_gap_pct=p.best_gap_pct,
                         base_median_gap=b.median_gap_pct, prop_median_gap=p.median_gap_pct,
                         base_mean_gap=b.mean_gap_pct, prop_mean_gap=p.mean_gap_pct,
                         base_seeds_good=b.seeds_with_good, prop_seeds_good=p.seeds_with_good))
    return pd.DataFrame(rows)


def tests(df):
    """per instance: Fisher exact test on Good counts, Mann-Whitney U on final gaps (infeasible = +inf)"""
    rows = []
    for inst in ORDER:
        b = df[(df.instance == inst) & (df.method == "baseline")]
        p = df[(df.instance == inst) & (df.method == "proposed")]
        if b.empty or p.empty:
            continue
        tab = [[int(p.good.sum()), int((~p.good).sum())], [int(b.good.sum()), int((~b.good).sum())]]
        _, p_f = stats.fisher_exact(tab, alternative="greater")
        tf = [[int(p.feasible.sum()), int((~p.feasible).sum())], [int(b.feasible.sum()), int((~b.feasible).sum())]]
        _, p_feas = stats.fisher_exact(tf, alternative="greater")
        gb = np.where(b.feasible, b.gap_pct, 1e9); gp = np.where(p.feasible, p.gap_pct, 1e9)
        u = stats.mannwhitneyu(gp, gb, alternative="less")
        rows.append(dict(instance=inst, good_prop=f"{tab[0][0]}/{len(p)}", good_base=f"{tab[1][0]}/{len(b)}",
                         p_fisher_good=p_f, feas_prop=f"{tf[0][0]}/{len(p)}", feas_base=f"{tf[1][0]}/{len(b)}",
                         p_fisher_feas=p_feas, median_gap_prop=float(np.median(gp)), median_gap_base=float(np.median(gb)),
                         p_mannwhitney_gap=u.pvalue))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------ graphs
def style(ax):
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    for sp in ["left", "bottom"]:
        ax.spines[sp].set_color("#c9c8c2")
    ax.tick_params(colors=INK2, labelsize=9)
    ax.yaxis.grid(True, color="#ecebe7", linewidth=0.8)
    ax.set_axisbelow(True)


def bar3(c, key_b, key_p, key_paper, ylabel, fname, title, log=False, cap=None, err=None):
    fig, ax = plt.subplots(figsize=(10.0, 3.9), dpi=200)
    x = np.arange(len(c)); w = 0.26
    vals = [c[key_paper].values, c[key_b].values, c[key_p].values]
    errs = [None, c[err[0]].values if err else None, c[err[1]].values if err else None]
    labs = ["Paper SLP-CPLEX (500 runs)", "IA-1 baseline (3×20 runs)", "IA-2 proposed RG-ILS-SLP (3×20 runs)"]
    cols = [AQUA, ORANGE, BLUE]
    for k in range(3):
        v = np.array(vals[k], float)
        if cap is not None:
            v = np.where(np.isfinite(v), v, cap)
        ax.bar(x + (k - 1) * w, v, w * 0.92, color=cols[k], label=labs[k], zorder=3,
               yerr=errs[k], error_kw=dict(ecolor=INK2, lw=0.9, capsize=2) if errs[k] is not None else None)
        if cap is not None:
            for j, raw in enumerate(np.array(vals[k], float)):
                if not np.isfinite(raw):
                    ax.text(x[j] + (k - 1) * w, cap * 1.15, "no Good\nrun", ha="center", va="bottom", fontsize=7, color=INK2)
    ax.set_xticks(x); ax.set_xticklabels(c.instance, color=INK)
    ax.set_ylabel(ylabel, color=INK2, fontsize=9)
    if log:
        ax.set_yscale("log")
    style(ax)
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left", bbox_to_anchor=(0, -0.12))
    fig.tight_layout(); fig.savefig(GR / fname); plt.close(fig)


def convergence(df, insts, fname):
    nc = 3 if len(insts) > 4 else len(insts); nr = int(np.ceil(len(insts) / nc))
    fig, axes = plt.subplots(nr, nc, figsize=(3.3 * nc, 2.9 * nr), dpi=200, squeeze=False)
    axes = axes.ravel()
    for ax in axes[len(insts):]:
        ax.axis("off")
    for ax, inst in zip(axes, insts):
        for meth, col, lab in [("baseline", ORANGE, "IA-1 (baseline)"), ("proposed", BLUE, "IA-2 (proposed)")]:
            for j, (seed, g) in enumerate(df[(df.instance == inst) & (df.method == meth)].groupby("seed")):
                g = g.sort_values("run")
                t = g.time.cumsum().values
                fbest = np.minimum.accumulate(np.where(g.feasible, g.f, np.inf))
                gap = 100 * (fbest - BEST[inst]) / BEST[inst]
                ok = np.isfinite(gap)
                ax.step(t[ok], np.maximum(gap[ok], 1e-3), where="post", color=col, lw=1.6, alpha=0.85,
                        label=lab if j == 0 else None)
        ax.axhline(0.2, color=GREY, lw=1, ls="--")
        ax.text(0.02, 0.2, " 0.2% (Good)", transform=ax.get_yaxis_transform(), va="bottom", fontsize=7, color=INK2)
        ax.set_yscale("log"); style(ax)
        ax.set_title(inst, loc="left", fontsize=10, color=INK)
        ax.set_xlabel("cumulative time (s)", fontsize=8, color=INK2)
    for k in range(0, len(insts), nc):
        axes[k].set_ylabel("best gap to best known (%)", fontsize=8, color=INK2)
    axes[0].legend(frameon=False, fontsize=7)
    fig.tight_layout(); fig.savefig(GR / fname); plt.close(fig)


def gaps_strip(df, fname):
    fig, ax = plt.subplots(figsize=(10.0, 3.6), dpi=200)
    for k, inst in enumerate(ORDER):
        for j, (meth, col) in enumerate([("baseline", ORANGE), ("proposed", BLUE)]):
            g = df[(df.instance == inst) & (df.method == meth) & df.feasible]
            if g.empty:
                continue
            xs = k + (j - 0.5) * 0.34 + np.random.default_rng(k).uniform(-0.09, 0.09, len(g))
            ax.scatter(xs, np.maximum(g.gap_pct, 1e-3), s=9, color=col, alpha=0.6, linewidths=0, zorder=3,
                       label=("IA-1 (baseline)" if meth == "baseline" else "IA-2 (proposed)") if k == 0 else None)
    ax.axhline(0.2, color=GREY, lw=1, ls="--"); ax.text(len(ORDER) - 0.55, 0.21, "0.2%", fontsize=7, color=INK2)
    ax.set_yscale("log"); ax.set_xticks(range(len(ORDER))); ax.set_xticklabels(ORDER)
    ax.set_ylabel("final gap to best known (%)\nfeasible runs, log scale", fontsize=8, color=INK2)
    style(ax); ax.set_title("Solution quality of every feasible run (3 seeds × 20 runs)", loc="left", fontsize=11, color=INK)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout(); fig.savefig(GR / fname); plt.close(fig)


def ablation_plot(ab, fname):
    meths = ["baseline", "abl_polish", "abl_rcstart", "proposed"]
    cols = [ORANGE, GREY, VIOLET, BLUE]
    fig, axes = plt.subplots(2, 1, figsize=(10.0, 5.6), dpi=200, sharex=True)
    x = np.arange(len(ORDER)); w = 0.2
    for ax, key, ttl in [(axes[0], "pct_feas", "%Feas"), (axes[1], "pct_good", "%Good")]:
        for k, m in enumerate(meths):
            sel = lambda i: ab[(ab.instance == i) & (ab.method == m)]
            v = [sel(i)[key].iloc[0] if len(sel(i)) else np.nan for i in ORDER]
            ax.bar(x + (k - 1.5) * w, v, w * 0.92, color=cols[k], label=LABEL[m], zorder=3)
        style(ax); ax.set_ylim(0, 105)
        ax.set_title(ttl + "  (ablation, seed 12345, 20 runs per method)", loc="left", fontsize=10, color=INK)
    axes[1].set_xticks(x); axes[1].set_xticklabels(ORDER, fontsize=9)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=8, ncol=4, loc="lower center")
    fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(GR / fname); plt.close(fig)


def comparison_pdf(c, t, fname="Comparison_Table.pdf"):
    """one-page PDF of the baseline-vs-proposed table (for single-file uploads)"""
    from matplotlib.backends.backend_pdf import PdfPages
    hdr = ["Instance", "Paper\n%Good", "IA-1\n%Feas", "IA-2\n%Feas", "IA-1\n%Good", "IA-2\n%Good",
           "p Fisher\n(Good)", "Paper\nETiGood", "IA-1\nETiGood", "IA-2\nETiGood", "IA-1\nbest gap %",
           "IA-2\nbest gap %"]
    f = lambda x, d=1: "∞" if not np.isfinite(x) else f"{(0.0 if abs(x) < 0.5 * 10 ** -d else x):.{d}f}"
    rows = []
    for _, r in c.iterrows():
        pf = t.set_index("instance").loc[r.instance].p_fisher_good
        rows.append([r.instance, f(r.paper_good), f(r.base_feas), f(r.prop_feas), f(r.base_good), f(r.prop_good),
                     "<0.0001" if pf < 1e-4 else f"{pf:.4f}", f(r.paper_ETiGood), f(r.base_ETiGood), f(r.prop_ETiGood),
                     f(r.base_best_gap_pct, 3), f(r.prop_best_gap_pct, 3)])
    mean = lambda k: c[k].mean()
    rows.append(["Mean", f(mean("paper_good")), f(mean("base_feas")), f(mean("prop_feas")), f(mean("base_good")),
                 f(mean("prop_good")), "", "", "", "", f(mean("base_best_gap_pct"), 3), f(mean("prop_best_gap_pct"), 3)])
    with PdfPages(RES / fname) as pdf:
        fig, ax = plt.subplots(figsize=(11.7, 6.4)); ax.axis("off")
        ax.set_title("OPT-09: IA-1 (baseline filter-SLP) vs IA-2 (proposed RG-ILS-SLP), all 11 af-series instances, 3 seeds × 20 runs each\n"
                     "Paper = Grothey & McKinnon (2023) SLP-CPLEX, 500 runs. Good = within 0.2% of best known. "
                     "ETiGood = 100·Ti/%Good (s).", fontsize=10, loc="left")
        tb = ax.table(cellText=rows, colLabels=hdr, loc="center", cellLoc="center")
        tb.auto_set_font_size(False); tb.set_fontsize(8.5); tb.scale(1, 1.9)
        for (i, j), cell in tb.get_celld().items():
            cell.set_edgecolor("#c9c8c2")
            if i == 0:
                cell.set_facecolor("#dce6f2"); cell.set_text_props(weight="bold")
            elif j in (3, 5, 9, 11):
                cell.set_facecolor("#eaf2fc")
            if i == len(rows):
                cell.set_text_props(weight="bold")
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)


def main():
    global RES, GR
    import argparse
    ap = argparse.ArgumentParser(description="IA-2 result tables and graphs")
    ap.add_argument("--results", default=None,
                    help="results folder with <method>/seed<s>/runs_*.csv (default: ../06_Results)")
    a = ap.parse_args()
    if a.results:
        RES = Path(a.results).resolve()
        GR = RES / "Graphs"
        GR.mkdir(parents=True, exist_ok=True)
    df = load()
    ss = summarise_seed(df)
    s = summarise(df, ss)
    c = comparison(s)
    t = tests(df)
    ab = ss[ss.seed == 12345].copy()
    with pd.ExcelWriter(RES / "Result_Tables.xlsx") as xw:
        c.to_excel(xw, sheet_name="Comparison", index=False)
        s.to_excel(xw, sheet_name="Summary_by_method", index=False)
        ss.to_excel(xw, sheet_name="Summary_by_seed", index=False)
        t.to_excel(xw, sheet_name="Statistical_tests", index=False)
        ab.to_excel(xw, sheet_name="Ablation_seed12345", index=False)
        df.to_excel(xw, sheet_name="All_runs", index=False)
        pd.DataFrame([dict(instance=k, Ti=v[0], pct_feas=v[1], pct_good=v[2], It=v[3], ETiGood=v[4])
                      for k, v in PAPER.items()]).to_excel(xw, sheet_name="Paper_SLP_CPLEX", index=False)
        pd.DataFrame([dict(instance=k, Ti=v[0], pct_feas=v[1], pct_good=v[2], It=v[3], best_f=v[4])
                      for k, v in IA1.items()]).to_excel(xw, sheet_name="IA1_notebook", index=False)
    s.to_csv(RES / "summary.csv", index=False)
    ss.to_csv(RES / "summary_by_seed.csv", index=False)
    c.to_csv(RES / "comparison.csv", index=False)
    t.to_csv(RES / "stats.csv", index=False)
    if len(c):
        bar3(c, "base_good", "prop_good", "paper_good", "% runs within 0.2% of best known",
             "fig_pct_good.png", "%Good: share of runs that reach a Good solution (error bar = sd over 3 seeds)",
             err=("base_good_sd", "prop_good_sd"))
        bar3(c, "base_feas", "prop_feas", "paper_feas", "% feasible runs", "fig_pct_feas.png",
             "%Feas: share of runs ending feasible")
        bar3(c, "base_ETiGood", "prop_ETiGood", "paper_ETiGood", "ETiGood (s), log scale",
             "fig_etigood.png", "Expected time to a Good solution, ETiGood = 100·Ti/%Good (lower is better)",
             log=True, cap=2000)
        bar3(c, "base_Ti", "prop_Ti", "paper_Ti", "seconds per run", "fig_time.png", "Average time per run")
    comparison_pdf(c, t)
    convergence(df, HARD, "fig_convergence.png")
    gaps_strip(df, "fig_gaps.png")
    if ab.method.isin(["abl_polish", "abl_rcstart"]).any():
        ablation_plot(ab, "fig_ablation.png")
    pd.set_option("display.width", 260)
    print(c[["instance", "paper_good", "base_feas", "prop_feas", "base_good", "prop_good", "base_ETiGood",
             "prop_ETiGood", "base_best_gap_pct", "prop_best_gap_pct"]].round(2).to_string())
    print(t.round(4).to_string())


if __name__ == "__main__":
    main()
