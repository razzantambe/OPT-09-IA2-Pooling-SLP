// build_poster.js - A1 portrait research poster (single slide -> PDF)
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const ROOT = path.resolve(__dirname, "..");
const V = JSON.parse(fs.readFileSync(path.join(ROOT, "paper/cmp_values.json"), "utf8"));
const G = JSON.parse(fs.readFileSync(path.join(ROOT, "paper/group.json"), "utf8"));
const csv = fs.readFileSync(path.join(ROOT, "results/comparison.csv"), "utf8").trim().split("\n");
const hdr = csv[0].split(",");
const CMP = Object.fromEntries(csv.slice(1).map((l) => { const r = Object.fromEntries(l.split(",").map((v, i) => [hdr[i], isNaN(+v) ? v : +v])); return [r.instance, r]; }));

const pres = new pptxgen();
pres.defineLayout({ name: "A1P", width: 23.39, height: 33.11 });
pres.layout = "A1P";
pres.theme = { headFontFace: "Cambria", bodyFontFace: "Calibri" };
const s = pres.addSlide();
s.background = { color: "FFFFFF" };
const NAVY = "16324F", INK = "1B2433", MUTED = "52514E", TINT = "EEF3F8", BLUE = "2A78D6", ORANGE = "EB6834";
const T = (t, o) => s.addText(t, { isTextBox: true, fontFace: "Calibri", color: INK, fontSize: 24, valign: "top", margin: 0.1, ...o });
const box = (x, y, w, h, fill = TINT) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.2 });
const head = (t, x, y, w) => T(t, { x, y, w, h: 0.9, fontSize: 40, bold: true, color: NAVY, fontFace: "Cambria" });
const img = (f, x, y, w, ar) => s.addImage({ path: path.join(ROOT, "results/Graphs", f), x, y, w, h: w * ar, altText: f });
const ar = (f) => { const b = fs.readFileSync(path.join(ROOT, "results/Graphs", f)); return b.readUInt32BE(20) / b.readUInt32BE(16); };

// header band
s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 23.39, h: 4.9, fill: { color: NAVY }, line: { color: NAVY } });
T("Recipe-Guided Iterated Local Search around SLP for the Fixed-Demand Pooling Problem: Extending our IA-1 Filter-SLP Code",
  { x: 0.9, y: 0.45, w: 21.6, h: 2.75, fontSize: 54, bold: true, color: "FFFFFF", fontFace: "Cambria" });
T(`Group ${G.id}  ·  ${[G.s1, G.s2, G.s3].map((x) => x.replace(" | ", " (") + ")").join("  ·  ")}`, { x: 0.9, y: 3.35, w: 21.6, h: 0.6, fontSize: 28, color: "DCE6F2" });
T("Introduction to Optimization Techniques (IA-2)  ·  Dept. of IT, K. J. Somaiya College of Engineering", { x: 0.9, y: 3.95, w: 21.6, h: 0.6, fontSize: 24, color: "B8C4D4" });

const L = 0.9, CW = 10.4, R = 12.09, GY = 5.4;
// --- left column
head("1. Problem", L, GY, CW);
T([
  { text: "Feed mills blend raw materials through a few shared mixing bins into many products with nutrient specs and fixed demands.", options: { breakLine: true } },
  { text: "Bin compositions are decisions, so product quality Σ μ_pm v_mn is bilinear: nonconvex, with very many local optima.", options: {} },
], { x: L, y: GY + 0.95, w: CW, h: 2.6, fontSize: 25, paraSpaceAfter: 10 });

head("2. Baseline & research gap", L, GY + 3.7, CW);
box(L, GY + 4.65, CW, 4.6);
T([
  { text: "Baseline: ", options: { bold: true } },
  { text: "qq-formulation + trust-region filter SLP + random multistart [1], as re-implemented in our IA-1 code (qq_model.py, slp.py; Python + HiGHS).", options: { breakLine: true } },
  { text: "Gap: ", options: { bold: true, color: ORANGE } },
  { text: "in [1] only 4–20% of random starts are Good on the hard instances. With our IA-1 code, af-2, af-3 and af-6-fs never reached 0.2% and af-4 had 40% infeasible runs. Runs are independent and the LP structure is unused.", options: {} },
], { x: L + 0.3, y: GY + 4.85, w: CW - 0.6, h: 4.2, fontSize: 24, paraSpaceAfter: 12 });

head("3. Proposed: RG-ILS-SLP", L, GY + 9.6, CW);
img("fig_flowchart.png", L + 1.5, GY + 10.5, 7.4, ar("fig_flowchart.png"));
const fy = GY + 10.5 + 7.4 * ar("fig_flowchart.png") + 0.2;
head("4. Key formulations (new)", L, fy, CW);
box(L, fy + 0.95, CW, 4.3);
T([
  { text: "Diet relaxation  ", options: { bold: true } },
  { text: "c*_p = min Σ c_i w_pi  s.t. specs, Σ w = 1;  LB = Σ t_p c*_p ≤ f*", options: { breakLine: true, fontFace: "Cambria" } },
  { text: "Product LP  ", options: { bold: true } },
  { text: "bins λ fixed ⇒ (5c),(5g) linear in μ  → exact feasibility", options: { breakLine: true, fontFace: "Cambria" } },
  { text: "Bin LP  ", options: { bold: true } },
  { text: "shares μ_pm fixed ⇒ d linear in (λ, μ^S)", options: { breakLine: true, fontFace: "Cambria" } },
  { text: "Regret  ", options: { bold: true } },
  { text: "regret_p = t_p max(0, c^D_p − c*_p): re-seed a bin with a high-regret product's recipe; best of 4 by 10-iteration SLP probe", options: { fontFace: "Cambria" } },
], { x: L + 0.3, y: fy + 1.1, w: CW - 0.6, h: 4.1, fontSize: 21, paraSpaceAfter: 8 });

// --- right column
head("5. Results (11 instances, 3×20 runs)", R, GY, CW);
const st = (x, y, big, lab, col) => { box(x, y, 3.25, 2.5, TINT); T(big, { x: x + 0.15, y: y + 0.2, w: 2.95, h: 1.2, fontSize: 54, bold: true, color: col, fontFace: "Cambria", align: "center", valign: "middle" }); T(lab, { x: x + 0.15, y: y + 1.45, w: 2.95, h: 0.95, fontSize: 19, color: MUTED, align: "center" }); };
st(R, GY + 1.0, `${Math.round(V.good_p_hard)}%`, `IA-2 %Good, 6 hard inst. (IA-1 ${Math.round(V.good_b_hard)}%, paper ${Math.round(V.good_paper_hard)}%)`, BLUE);
st(R + 3.575, GY + 1.0, `${Math.round(V.feas_p)}%`, `IA-2 mean %Feas (IA-1 ${Math.round(V.feas_b)}%)`, BLUE);
st(R + 7.15, GY + 1.0, `${V.spd_hard.toFixed(1)}×`, "IA-2 vs IA-1: shorter time to a Good solution", BLUE);
img("fig_pct_good.png", R, GY + 3.8, CW, ar("fig_pct_good.png"));
const y2 = GY + 3.8 + CW * ar("fig_pct_good.png") + 0.2;
const y3 = y2;
img("fig_convergence.png", R, y3, CW, ar("fig_convergence.png"));
const y4 = y3 + CW * ar("fig_convergence.png") + 0.4;
box(R, y4, CW, 3.3);
T([
  { text: "Highlights", options: { bold: true, breakLine: true } },
  { text: `IA-2 %Good: af-2 ${CMP["af-2"].prop_good.toFixed(0)}% (paper 19.4%), af-4 ${CMP["af-4"].prop_good.toFixed(0)}% (19.8%), af-3 ${CMP["af-3"].prop_good.toFixed(0)}% (20%), af-6-fs ${CMP["af-6-fs"].prop_good.toFixed(0)}% (5.2%); af-7 ${CMP["af-7"].prop_good.toFixed(0)}% (20.4%) and af-6-f 0% (4.0%) stay below the paper`, options: { bullet: true, breakLine: true } },
  { text: `IA-2 vs IA-1 significant: Fisher p < 0.01 on ${V.sig_good.length} instances, Mann–Whitney on ${V.sig_gap.length} of ${V.NI}`, options: { bullet: true, breakLine: true } },
  { text: "Diet LP bound on af-1 = Baron's bound (295.93), in milliseconds; easy instances ~2× slower", options: { bullet: true } },
], { x: R + 0.3, y: y4 + 0.15, w: CW - 0.6, h: 3.0, fontSize: 22, paraSpaceAfter: 6 });
const y5 = y4 + 3.6;
head("6. Conclusion", R, y5, CW);
T("Keeping our IA-1 model and SLP solver unchanged but making restarts structure-aware (LP repair, LP polish, regret-guided re-seeding with SLP probes) turns random-multistart SLP into a reliable method on the hard feed-mill instances. Next: more seeds, adaptive moves, parallel probes, stronger bounds.",
  { x: R, y: y5 + 0.95, w: CW, h: 2.6, fontSize: 23 });

// footer
s.addShape(pres.shapes.LINE, { x: 0.9, y: 31.75, w: 21.6, h: 0, line: { color: "C9C8C2", width: 1 } });
T("[1] A. Grothey, K. McKinnon, On the effectiveness of sequential linear programming for the pooling problem, Ann. Oper. Res. 322 (2023) 691–711.   [2] C. Audet et al., Pooling problem: alternate formulations and solution methods, Manag. Sci. 50 (2004).   [3] Group OPT-09, IA-1 report (2026). Data: Grothey & McKinnon (2020). Code: Python + SciPy/HiGHS.",
  { x: 0.9, y: 31.85, w: 21.6, h: 0.9, fontSize: 16, color: MUTED });

pres.writeFile({ fileName: path.join(__dirname, "Poster.pptx") }).then(() => console.log("written"));
