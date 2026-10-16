"""make_flowchart.py - methodology flowchart of the IA-2 method (matplotlib, orthogonal arrows)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

ROOT = Path(__file__).resolve().parent.parent
OUT = next((d for d in [ROOT / "06_Results", ROOT / "results"] if d.exists()), ROOT / "results") / "Graphs"
OUT.mkdir(parents=True, exist_ok=True)

BLUE, BLUEF, ORANGE, ORANGEF, GREY, INK, INK2 = "#2a78d6", "#eaf2fc", "#eb6834", "#fdeee6", "#b9b8b2", "#0b0b0b", "#52514e"
fig, ax = plt.subplots(figsize=(8.6, 11.6), dpi=200)
ax.set_xlim(0, 10); ax.set_ylim(-2.1, 13.6); ax.axis("off")

CX, W = 4.3, 6.6


def box(y, h, text, fc="#fcfcfb", ec=GREY, title=None, w=W, cx=CX, fs=8.6):
    ax.add_patch(FancyBboxPatch((cx - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fc, ec=ec, lw=1.2))
    if title:
        ax.text(cx, y + h / 2 - 0.2, title, ha="center", va="top", fontsize=fs + 0.6, weight="bold", color=INK)
        ax.text(cx, y + h / 2 - 0.45, text, ha="center", va="top", fontsize=fs, color=INK, linespacing=1.35)
    else:
        ax.text(cx, y, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.35)
    return (cx, y, w, h)


def diamond(y, text, w=3.0, h=0.95, cx=CX):
    ax.add_patch(Polygon([(cx - w / 2, y), (cx, y + h / 2), (cx + w / 2, y), (cx, y - h / 2)], closed=True,
                         fc="#fcfcfb", ec=GREY, lw=1.2))
    ax.text(cx, y, text, ha="center", va="center", fontsize=8.3, color=INK, linespacing=1.3)
    return (cx, y, w, h)


def arrow(pts, color="#8a8984", ls="-", label=None, lpos=None, lcol=None):
    xs, ys = zip(*pts)
    ax.plot(xs[:-1] + (xs[-1],), ys, color=color, lw=1.2, ls=ls, solid_capstyle="butt")
    ax.annotate("", xy=pts[-1], xytext=pts[-2],
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2, mutation_scale=11, shrinkA=0, shrinkB=0))
    if label:
        ax.text(*lpos, label, fontsize=7.8, color=lcol or color, ha="left", va="center")


def down(b1, b2, **k):
    arrow([(b1[0], b1[1] - b1[3] / 2), (b2[0], b2[1] + b2[3] / 2)], **k)


y = 13.15
A = box(y, 0.62, "Problem / input: af-series feed-mill pooling instances  (load_instance, IA-1)")
B = box(y - 1.0, 0.82, "qq-formulation (5a)–(5h), price as extra attribute, bilinear terms μ_pm·V_mq",
        title="Baseline model — IA-1 qq_model.py (unchanged)")
C = box(y - 2.17, 1.08, "random-multistart filter-SLP: 0% Good on af-2, af-3, af-6-fs; 5% on af-6-f, af-7;\n"
        "only 60–75% of the runs feasible on af-4, af-6-f, af-7", fc=ORANGEF, ec=ORANGE,
        title="Identified limitation — IA-1 experiments")
# proposed cluster
top, bot = y - 2.9, 1.2
ax.add_patch(FancyBboxPatch((0.45, bot), 7.75, top - bot, boxstyle="round,pad=0.02,rounding_size=0.2",
                            fc="none", ec=BLUE, lw=1.1, ls=(0, (5, 3))))
ax.text(0.65, top - 0.12, "Proposed: RG-ILS-SLP (rg_ils.py)", fontsize=9.2, color=BLUE, weight="bold", va="top")
D1 = box(y - 3.75, 0.72, "1. Diet LP relaxation (one small LP per product)\n→ ideal recipes q_p, unit costs c*_p, lower bound LB",
         fc=BLUEF, ec=BLUE)
D2 = box(y - 4.7, 0.72, "2. Recipe-clustering start: weighted k-means++ on the recipes q_p\n→ initial bin compositions (ℓ1 projection LP)",
         fc=BLUEF, ec=BLUE)
D3 = box(y - 5.65, 0.72, "3. LP repair: product LP (bins fixed) ⇄ bin LP (bin shares fixed),\n"
         "elastic, alternated ≤ 6 rounds → feasible start", fc=BLUEF, ec=BLUE)
E = box(y - 6.55, 0.6, "4. Filter trust-region SLP  (IA-1 slp.py, unchanged)")
D4 = box(y - 7.45, 0.72, "5. LP polish of the SLP end point:\nproduct LP, then bin LP (cost never increases)", fc=BLUEF, ec=BLUE)
R = diamond(y - 8.5, "runs left?", w=2.2, h=0.8)
Q = diamond(y - 9.7, "run < 3, or 6 runs\nwithout improvement?", w=3.3, h=1.05)
D5 = box(y - 11.1, 1.05, "6. Regret-guided perturbation of the incumbent: 4 candidates, each re-seeds\n"
         "one bin with the recipe of a high-regret product + LP repair + 10-iteration\n"
         "SLP probe; the full SLP continues from the best probe", fc=BLUEF, ec=BLUE, fs=8.3)
for a, b in [(A, B), (B, C), (C, D1), (D1, D2), (D2, D3), (D3, E), (E, D4), (D4, R)]:
    down(a, b)
down(R, Q, label="yes", lpos=(CX + 0.08, R[1] - 0.55))
down(Q, D5, label="no", lpos=(CX + 0.08, Q[1] - 0.72))
# yes: fresh recipe start  (left side, up to D2)
xl = CX - W / 2 - 0.35
arrow([(CX - Q[2] / 2, Q[1]), (xl, Q[1]), (xl, D2[1]), (CX - W / 2, D2[1])], color=BLUE, ls=(0, (4, 2)))
ax.text(xl + 0.08, (Q[1] + D2[1]) / 2 - 1.2, "yes:\nfresh\nrecipe\nstart", fontsize=7.6, color=BLUE, va="center")
# ILS: continue SLP from best probe (right side, up to E)
xr = CX + W / 2 + 0.35
arrow([(CX + D5[2] / 2, D5[1]), (xr, D5[1]), (xr, E[1]), (CX + W / 2, E[1])], color=BLUE, ls=(0, (4, 2)))
ax.text(xr - 0.08, (D5[1] + Q[1]) / 2 + 0.5, "next run:\ncontinue\nSLP from\nbest probe", fontsize=7.6, color=BLUE,
        va="center", ha="right")
# output: below the cluster, reached from "runs left? -> no" along the far right
bot = D5[1] - D5[3] / 2 - 0.35
F = box(bot - 0.75, 0.82, "best feasible bins / recipes, cost and gap to the lower bound LB", title="Solution")
xo = 9.1
arrow([(CX + R[2] / 2, R[1]), (xo, R[1]), (xo, F[1]), (CX + W / 2, F[1])])
ax.text(CX + R[2] / 2 + 0.1, R[1] + 0.15, "no (20 runs done)", fontsize=7.6, color=INK2)
G = box(F[1] - 1.2, 1.1, "3 seeds × 20 runs × all 11 instances: %Feas, %Good, Ti, It, ETiGood, gaps;\n"
        "Fisher / Mann–Whitney tests; vs baseline (IA-1 code), paper SLP-CPLEX, ablations", title="Evaluation", fs=8.0)
down(F, G)
fig.savefig(OUT / "fig_flowchart.png", bbox_inches="tight", facecolor="white")
print("written", OUT / "fig_flowchart.png")
