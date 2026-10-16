// build_deck.js - IA-2 presentation (structured deck: theme, layouts, sections)
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const SK = "/root/.claude/skills/synced/cce128f9-238f-4707-859f-3c07c522fe23_07e1d76c-60de-4e09-bb13-09801cd38c17/pptx";
const { applyTheme } = require(SK + "/scripts/apply_theme.js");

const ROOT = path.resolve(__dirname, "..");
const csv = fs.readFileSync(path.join(ROOT, "results/comparison.csv"), "utf8").trim().split("\n");
const hdr = csv[0].split(",");
const CMP = csv.slice(1).map((l) => Object.fromEntries(l.split(",").map((v, i) => [hdr[i], isNaN(+v) ? v : +v])));
const V = JSON.parse(fs.readFileSync(path.join(ROOT, "paper/cmp_values.json"), "utf8"));
const G = JSON.parse(fs.readFileSync(path.join(ROOT, "paper/group.json"), "utf8"));
const byI = Object.fromEntries(CMP.map((r) => [r.instance, r]));

const THEME = {
  name: "Feed Mill Optimisation",
  headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1B2433", lt1: "FFFFFF", dk2: "16324F", lt2: "EEF3F8",
    accent1: "2A78D6", accent2: "EB6834", accent3: "1BAF7A", accent4: "EDA100", accent5: "6250D6", accent6: "52514E",
    hlink: "2A78D6", folHlink: "6250D6" },
};
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";      // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "RG-ILS-SLP for the pooling problem";
pres.author = "Group OPT-09";
const C = pres.SchemeColor;
const W = 13.33;
const FOOT = "IA-2 | Introduction to Optimization Techniques";

// ---------------- layouts
pres.defineSlideMaster({
  title: "TITLE_DARK", background: { color: THEME.colors.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.0, w: 11.7, h: 1.9, fontSize: 40, bold: true, color: C.background1, fontFace: "Cambria", valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 2.2, fontSize: 18, color: C.background2, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontSize: 32, bold: true, color: C.text2, fontFace: "Cambria", valign: "middle" }, text: "" } },
    { text: { text: FOOT, options: { x: 0.6, y: 7.05, w: 8, h: 0.3, fontSize: 10, color: "8A8984" } } },
  ],
  slideNumber: { x: 12.2, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: "8A8984", align: "right" },
});
pres.defineSlideMaster({
  title: "SECTION", background: { color: THEME.colors.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.6, w: 11.7, h: 1.4, fontSize: 36, bold: true, color: C.background1, fontFace: "Cambria" }, text: "" } },
  ],
  slideNumber: { x: 12.2, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: "B8C4D4", align: "right" },
});

let sec = "";
function slide(master, title, section) {
  if (section && section !== sec) { pres.addSection({ title: section }); sec = section; }
  const s = pres.addSlide({ masterName: master, sectionTitle: sec });
  if (title) s.addText(title, { placeholder: "title" });
  return s;
}
const card = (s, x, y, w, h, fill = "EEF3F8", name = "card") =>
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.12, objectName: name });
const txt = (s, t, o) => s.addText(t, { isTextBox: true, fontFace: "Calibri", color: "1B2433", fontSize: 15, valign: "top", margin: 0.08, ...o });
function stat(s, x, y, w, big, label, color) {
  card(s, x, y, w, 1.75, "EEF3F8", "stat " + label);
  txt(s, big, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: 0.9, fontSize: 40, bold: true, color, fontFace: "Cambria", valign: "middle" });
  txt(s, label, { x: x + 0.2, y: y + 1.05, w: w - 0.4, h: 0.6, fontSize: 13, color: "52514E" });
}
const pct = (x) => `${Math.round(x)}%`;

// 1 ---------------- title
{
  const s = slide("TITLE_DARK", "Recipe-Guided Iterated Local Search around SLP for the Fixed-Demand Pooling Problem", "Introduction");
  s.addText([
    { text: "IA-2 · Introduction to Optimization Techniques · extending our IA-1 filter-SLP code", options: { breakLine: true, bold: true } },
    { text: `Group ${G.id}  ·  ${[G.s1, G.s2, G.s3].map((x) => x.replace(" | ", " (") + ")").join("  ·  ")}`, options: { breakLine: true } },
    { text: "Dept. of IT, K. J. Somaiya College of Engineering", options: {} },
  ], { placeholder: "body" });
  s.addNotes("Introduce the team and the topic. In IA-1 we re-implemented Grothey & McKinnon (2023); IA-2 extends that code.");
}
// 2 ---------------- problem
{
  const s = slide("CONTENT", "Shared bins make feed blending nonconvex", "Introduction");
  // simple network: RMs -> bins -> products
  const col = (x, n, label, fill, y0 = 1.75) => {
    for (let k = 0; k < n; k++) s.addShape(pres.shapes.OVAL, { x, y: y0 + k * 0.62, w: 0.42, h: 0.42, fill: { color: fill }, line: { color: fill }, objectName: label + k });
    txt(s, label, { x: x - 0.45, y: y0 + n * 0.62, w: 1.3, h: 0.4, fontSize: 12, align: "center", color: "52514E" });
  };
  col(0.9, 7, "raw materials", "9AA9BC");
  col(3.0, 4, "bins (λ)", "2A78D6", 2.37);
  col(5.1, 7, "products (μ)", "1BAF7A");
  for (let a = 0; a < 7; a++) for (let b = 0; b < 4; b++) if ((a + b) % 2 === 0)
    s.addShape(pres.shapes.LINE, { x: 1.32, y: 1.96 + a * 0.62, w: 1.68, h: (2.58 + b * 0.62) - (1.96 + a * 0.62), line: { color: "C9C8C2", width: 0.75 } });
  for (let b = 0; b < 4; b++) for (let p = 0; p < 7; p++) if ((b + p) % 3 !== 0)
    s.addShape(pres.shapes.LINE, { x: 3.42, y: 2.58 + b * 0.62, w: 1.68, h: (1.96 + p * 0.62) - (2.58 + b * 0.62), line: { color: "C9C8C2", width: 0.75 } });
  s.addShape(pres.shapes.LINE, { x: 1.32, y: 1.96, w: 3.78, h: 0.0, line: { color: "EB6834", width: 1.5, dashType: "dash" } });
  txt(s, "straight (direct, extra cost)", { x: 2.0, y: 1.45, w: 2.6, h: 0.35, fontSize: 11, color: "EB6834" });
  card(s, 6.6, 1.5, 6.1, 5.1, "EEF3F8");
  txt(s, [
    { text: "Fixed demands t_p must meet N nutrient specs", options: { bullet: true, breakLine: true } },
    { text: "Bin compositions λ are decisions, shared by many products", options: { bullet: true, breakLine: true } },
    { text: "Product quality = Σ μ_pm · v_mn  →  bilinear, nonconvex", options: { bullet: true, breakLine: true } },
    { text: "Many local optima even with fixed demands (96 in a 2-nutrient toy example)", options: { bullet: true, breakLine: true } },
    { text: "Mills re-solve many times a day → need near-optimal recipes in seconds", options: { bullet: true } },
  ], { x: 6.9, y: 1.75, w: 5.6, h: 4.7, fontSize: 17, paraSpaceAfter: 12 });
  s.addNotes("Explain the pooling structure; bilinear terms come from mixing bins shared by products.");
}
// 3 ---------------- baseline
{
  const s = slide("CONTENT", "Baseline: the paper's method, as implemented in our IA-1 code", "Baseline & gap");
  card(s, 0.6, 1.5, 6.3, 5.1);
  txt(s, "qq-formulation (Grothey & McKinnon, 2023)", { x: 0.85, y: 1.65, w: 5.9, h: 0.45, bold: true, fontSize: 17 });
  txt(s, [
    { text: "min Σ_p t_p c^D_p", options: { breakLine: true } },
    { text: "v_mn = Σ_i λ_mi r_in", options: { breakLine: true } },
    { text: "d_pn = Σ_i μ_pi r_in + Σ_m μ_pm v_mn      (bilinear)", options: { breakLine: true } },
    { text: "c^D_p = Σ_i μ_pi c_i + Σ_m μ_pm c^M_m        (bilinear)", options: { breakLine: true } },
    { text: "Σ λ = 1,  Σ μ = 1,  d̲ ≤ d ≤ d̄,  bounds", options: {} },
  ], { x: 0.85, y: 2.2, w: 5.9, h: 2.6, fontSize: 15, fontFace: "Cambria", paraSpaceAfter: 8 });
  txt(s, [
    { text: "SLP: linearise, solve LP in an ∞-norm trust region, accept with a filter", options: { bullet: true, breakLine: true } },
    { text: "Random multistart: every run independent", options: { bullet: true, breakLine: true } },
    { text: "IA-1: qq_model.py + slp.py (Python, HiGHS); af-1 best known 296.44604 reproduced", options: { bullet: true } },
  ], { x: 0.85, y: 4.85, w: 5.9, h: 1.7, fontSize: 14, paraSpaceAfter: 6 });
  stat(s, 7.3, 1.5, 2.6, "863×", "faster to a good solution than FilterSQP", "2A78D6");
  stat(s, 10.1, 1.5, 2.6, "20×", "faster than the global solver Baron", "2A78D6");
  card(s, 7.3, 3.5, 5.4, 3.1, "FFFFFF");
  txt(s, [
    { text: "But on the hard instances only", options: { breakLine: true } },
    { text: "4–20%", options: { bold: true, fontSize: 40, color: "EB6834", fontFace: "Cambria", breakLine: true } },
    { text: "of random starts end within 0.2% of the best known cost (af-2, af-3, af-4, af-6, af-6-fs, af-7)", options: {} },
  ], { x: 7.5, y: 3.6, w: 5.0, h: 2.9, fontSize: 16 });
  s.addNotes("Summarise the baseline paper and its headline result; point out the weakness on hard instances.");
}
// 4 ---------------- gap
{
  const s = slide("CONTENT", "Research gap: random restarts waste most of the run time", "Baseline & gap");
  const rows = [["Instance", "Paper %Good", "Paper ETiGood", "IA-1 code %Feas", "IA-1 code %Good"]];
  for (const i of ["af-2", "af-3", "af-4", "af-6-f", "af-6-fs", "af-7"]) rows.push([i, byI[i].paper_good + "%", byI[i].paper_ETiGood + " s", byI[i].ia1_feas + "%", byI[i].ia1_good + "%"]);
  s.addTable(rows.map((r, k) => r.map((c) => ({ text: String(c), options: { bold: k === 0, fill: { color: k === 0 ? "DCE6F2" : "FFFFFF" }, color: "1B2433", fontSize: 15, align: "center" } }))),
    { x: 0.6, y: 1.6, w: 6.6, colW: [1.4, 1.3, 1.4, 1.25, 1.25], border: { type: "solid", color: "C9C8C2", pt: 0.75 }, rowH: 0.45 });
  card(s, 7.6, 1.6, 5.1, 4.9);
  txt(s, [
    { text: "What we observed", options: { bold: true, fontSize: 18, breakLine: true } },
    { text: "Runs land in poor basins; nothing is learned from earlier runs", options: { bullet: true, breakLine: true } },
    { text: "Some runs stall in feasibility restoration (af-4, af-7)", options: { bullet: true, breakLine: true } },
    { text: "The structure is unused: fix the bins, or the bin shares, and the problem is an LP", options: { bullet: true, breakLine: true } },
    { text: "Gap found via: limitation stated by the authors + IA-1 implementation experience + IA-1 results vs the paper", options: { bullet: true } },
  ], { x: 7.85, y: 1.75, w: 4.7, h: 4.6, fontSize: 16, paraSpaceAfter: 10 });
  txt(s, "IA-1 code = our IA-1 notebook, 20 runs, seed 12345 (the IA-1 report validated af-1 only: 20/20 Good; af-2, af-6-f, af-7b-fs re-run with the same code and seed). af-6-f = the paper's af-6. ETiGood = 100·Ti / %Good.", { x: 0.6, y: 5.0, w: 6.6, h: 1.3, fontSize: 13, color: "52514E", italic: true });
  s.addNotes("State the gap precisely with the paper's own numbers and our IA-1 numbers.");
}
// 5 ---------------- method flow
{
  const s = slide("CONTENT", "RG-ILS-SLP: same IA-1 model and solver, smarter search", "Proposed method");
  const steps = [
    ["Diet LP", "each product's ideal recipe + lower bound", "New", "2A78D6"],
    ["Recipe clustering", "weighted k-means on recipes → initial bins", "Modified", "2A78D6"],
    ["LP repair", "product LP / bin LP until the start is feasible", "New", "2A78D6"],
    ["Filter-SLP", "IA-1 slp.py, unchanged", "Retained", "8A8984"],
    ["LP polish", "exactly feasible, never worse", "New", "2A78D6"],
  ];
  const w = 2.25, gap = 0.21;
  steps.forEach(([h, b, tag, col], k) => {
    const x = 0.6 + k * (w + gap);
    card(s, x, 1.6, w, 2.9, k === 3 ? "F1F1EF" : "EEF3F8");
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: 1.8, w: 0.6, h: 0.6, fill: { color: col }, line: { color: col } });
    txt(s, String(k + 1), { x: x + 0.2, y: 1.8, w: 0.6, h: 0.6, align: "center", valign: "middle", color: "FFFFFF", bold: true, fontSize: 18, margin: 0 });
    txt(s, tag, { x: x + 0.9, y: 1.9, w: w - 1.0, h: 0.4, fontSize: 13, color: col, bold: true, valign: "middle" });
    txt(s, h, { x: x + 0.15, y: 2.55, w: w - 0.3, h: 0.5, bold: true, fontSize: 18, color: "16324F" });
    txt(s, b, { x: x + 0.15, y: 3.1, w: w - 0.3, h: 1.3, fontSize: 15, color: "52514E" });
    if (k < 4) s.addShape(pres.shapes.LINE, { x: x + w + 0.01, y: 3.05, w: gap - 0.02, h: 0, line: { color: "8A8984", width: 1.5, endArrowType: "triangle" } });
  });
  card(s, 0.6, 4.85, 12.1, 1.85, "EAF2FC");
  s.addShape(pres.shapes.OVAL, { x: 0.85, y: 5.15, w: 0.6, h: 0.6, fill: { color: "2A78D6" }, line: { color: "2A78D6" } });
  txt(s, "6", { x: 0.85, y: 5.15, w: 0.6, h: 0.6, align: "center", valign: "middle", color: "FFFFFF", bold: true, fontSize: 18, margin: 0 });
  txt(s, [
    { text: "Regret-guided iterated local search (new). ", options: { bold: true } },
    { text: "From the best solution so far, build 4 candidates: re-seed a bin with the ideal recipe of a product that pays a lot for bin sharing (regret), LP-repair, probe with a 10-iteration SLP; continue the full SLP from the best probe. Runs 1–3 and any run after 6 failures use a fresh recipe start. One pass = one run; 20 runs.", options: {} },
  ], { x: 1.65, y: 5.0, w: 10.85, h: 1.6, fontSize: 16 });
  s.addNotes("Walk through the loop; emphasise that the qq model and the SLP are unchanged.");
}
// 6 ---------------- math
{
  const s = slide("CONTENT", "Three exact LPs exploit the bilinear structure", "Proposed method");
  const boxes = [
    ["Diet relaxation", "c*_p = min Σ c_i w_pi\ns.t. specs on Σ w_pi r_in, Σ w = 1\nLB = Σ t_p c*_p ≤ f*", "af-1: LB 295.932 = Baron's 2-hour bound"],
    ["Product LP (bins fixed)", "λ fixed ⇒ v, c^M constants\n(5c), (5g) become linear in μ\n→ optimal recipes, exact feasibility", "used to repair starts and polish SLP end points"],
    ["Bin LP (bin shares fixed)", "μ_pm fixed ⇒ d linear in (λ, μ^S)\nalternate with product LP\n→ cost never increases", "classical recursion / ALT idea (Haverly; Audet et al.)"],
  ];
  boxes.forEach(([h, m, n], k) => {
    const x = 0.6 + k * 4.12;
    card(s, x, 1.5, 3.85, 3.5);
    txt(s, h, { x: x + 0.2, y: 1.62, w: 3.45, h: 0.5, bold: true, fontSize: 18, color: "16324F" });
    txt(s, m, { x: x + 0.2, y: 2.2, w: 3.45, h: 1.8, fontSize: 14, fontFace: "Cambria" });
    txt(s, n, { x: x + 0.2, y: 4.05, w: 3.45, h: 0.8, fontSize: 13, color: "52514E", italic: true });
  });
  card(s, 0.6, 5.25, 12.1, 1.45, "FFFFFF");
  txt(s, [
    { text: "Recipe regret  ", options: { bold: true } },
    { text: "regret_p = t_p · max(0, c^D_p − c*_p).  Pick product p ∝ regret and a bin m, set λ_m ← Proj((1−α) q_p + α λ_m), α ~ U(0, 0.5); 4 such candidates are ranked by a 10-iteration SLP probe.  The model (5a)–(5h) itself is unchanged.", options: {} },
  ], { x: 0.8, y: 5.35, w: 11.7, h: 1.25, fontSize: 15 });
  s.addNotes("Mathematical changes: one convex relaxation and two exact linear restrictions of the bilinear rows.");
}
// 7 ---------------- setup
{
  const s = slide("CONTENT", "Experimental setup", "Experiments");
  const rows = [
    ["Item", "Details"],
    ["Instances", "all 11: af-1, af-2, af-3, af-4, af-5, af-5-fs, af-6-f (= paper's af-6), af-6-fs, af-7, af-7b, af-7b-fs"],
    ["Code", "IA-1 qq_model.py + slp.py unchanged; new rg_ils.py; run_experiments.py --method"],
    ["Software / HW", "Python 3.13, NumPy, SciPy 1.18 (HiGHS LP); 2-vCPU cloud container, 1 thread per run"],
    ["Runs", "3 seeds (12345 = IA-1 seed, 2024, 7) × 20 runs per instance and method"],
    ["IA-1 vs IA-2", "IA-1 = baseline (our IA-1 code, unchanged; seed 12345 reproduces the IA-1 notebook); IA-2 = proposed RG-ILS-SLP"],
    ["Metrics", "%Feas, %Good (≤ 0.2% of best known), Ti, It, ETiGood, gaps; Fisher and Mann–Whitney tests"],
    ["Also compared", "published SLP-CPLEX (500 runs); 2 ablations (seed 12345)"],
  ];
  s.addTable(rows.map((r, k) => r.map((c, j) => ({ text: c, options: { bold: k === 0 || j === 0, fill: { color: k === 0 ? "DCE6F2" : (j === 0 ? "EEF3F8" : "FFFFFF") }, color: "1B2433", fontSize: 15 } }))),
    { x: 0.6, y: 1.5, w: 12.1, colW: [2.4, 9.7], border: { type: "solid", color: "C9C8C2", pt: 0.75 }, rowH: 0.58 });
  s.addNotes("Same code base for baseline and proposed, so the comparison isolates our contribution.");
}
// 7b ---------------- IA-1 vs IA-2 at a glance
{
  const s = slide("CONTENT", "IA-1 vs IA-2 at a glance", "Experiments");
  const rows = [["", "IA-1 (baseline)", "IA-2 (proposed)"],
    ["Model + SLP solver", "qq_model.py + slp.py", "same files, unchanged"],
    ["Starting points", "uniform random", "recipe clustering (diet LP) + LP repair"],
    ["Restarts", "independent random multistart", "regret-guided ILS, 4 SLP-probed moves, fresh starts after 6 failures"],
    ["SLP end point", "returned as is", "LP polish (product LP, bin LP)"],
    ["Lower bound", "none", "diet LP (af-1 = Baron's bound)"],
    ["Mean %Feas (11 inst.)", `${V.feas_b.toFixed(1)}%`, `${V.feas_p.toFixed(1)}%`],
    ["Mean %Good (11 inst.)", `${V.good_b.toFixed(1)}%`, `${V.good_p.toFixed(1)}%`],
    ["%Good, 6 hard inst. (paper 14.8%)", `${V.good_b_hard.toFixed(1)}%`, `${V.good_p_hard.toFixed(1)}%`],
    ["ETiGood, hard inst.", "1.0×", `${V.spd_hard.toFixed(1)}× shorter`]];
  s.addTable(rows.map((r, k) => r.map((c, j) => ({ text: c, options: { bold: k === 0 || j === 0, fill: { color: k === 0 ? "DCE6F2" : (j === 2 ? "EAF2FC" : (j === 0 ? "EEF3F8" : "FFFFFF")) }, color: "1B2433", fontSize: 14, align: j ? "center" : "left" } }))),
    { x: 0.6, y: 1.4, w: 12.1, colW: [3.3, 3.6, 5.2], border: { type: "solid", color: "C9C8C2", pt: 0.75 }, rowH: 0.5 });
  s.addNotes("Side-by-side: what IA-2 changes relative to IA-1, and what it achieves. Same instances, seeds and machine for both.");
}
// 8 ---------------- %Good chart
{
  const s = slide("CONTENT", "IA-2 vs IA-1: many more runs reach a Good solution on the hard instances", "Results");
  const labels = CMP.map((r) => r.instance);
  s.addChart(pres.charts.BAR, [
    { name: "Paper SLP-CPLEX", labels, values: CMP.map((r) => r.paper_good) },
    { name: "IA-1 (baseline)", labels, values: CMP.map((r) => r.base_good) },
    { name: "IA-2 (proposed RG-ILS-SLP)", labels, values: CMP.map((r) => r.prop_good) },
  ], {
    x: 0.6, y: 1.4, w: 8.4, h: 5.3, barDir: "col", barGrouping: "clustered", barGapWidthPct: 60,
    chartColors: ["1BAF7A", "EB6834", "2A78D6"], showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt",
    showTitle: true, title: "%Good (runs within 0.2% of best known)", titleFontSize: 14, titleFontFace: "+mn-lt", titleColor: "1B2433",
    valAxisMaxVal: 100, valAxisLabelFontSize: 11, catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    catAxisLabelColor: "52514E", valAxisLabelColor: "52514E", valGridLine: { color: "E5E4DF", size: 0.5 }, catGridLine: { style: "none" },
  });
  const lab = (i) => `${i} (paper ${byI[i].paper_good}%, IA-1 ${byI[i].base_good.toFixed(1)}%)`;
  stat(s, 9.4, 1.5, 3.3, pct(byI["af-2"].prop_good), lab("af-2"), "2A78D6");
  stat(s, 9.4, 3.4, 3.3, pct(byI["af-4"].prop_good), lab("af-4"), "2A78D6");
  stat(s, 9.4, 5.3, 3.3, pct(byI["af-6-f"].prop_good), lab("af-6-f") + " — not solved", "EB6834");
  s.addNotes("3 seeds x 20 runs. Equal on easy instances, large gains on af-2, af-3, af-4, af-6-fs; af-7 improves but stays just below the paper; af-6-f is not solved by either method.");
}
// 9 ---------------- ETiGood + feasibility
{
  const s = slide("CONTENT", "IA-2 vs IA-1: more feasible runs, faster to a good solution", "Results");
  stat(s, 0.6, 1.5, 3.8, `${Math.round(V.feas_b)}% → ${Math.round(V.feas_p)}%`, "mean %Feas, IA-1 → IA-2", "16324F");
  stat(s, 4.75, 1.5, 3.8, `${Math.round(V.good_b)}% → ${Math.round(V.good_p)}%`, "mean %Good, IA-1 → IA-2", "16324F");
  stat(s, 8.9, 1.5, 3.8, `${V.spd_hard.toFixed(1)}×`, "shorter ETiGood on the hard instances (geo-mean, af-6-f excluded)", "2A78D6");
  const rows = [["Instance", "Paper ETiGood", "IA-1 ETiGood", "IA-2 ETiGood"]];
  for (const i of ["af-2", "af-3", "af-4", "af-6-f", "af-6-fs", "af-7"]) {
    const r = byI[i];
    const f = (x) => (x === "inf" || !isFinite(x) ? "no Good run" : x.toFixed(1) + " s");
    rows.push([i, r.paper_ETiGood.toFixed(1) + " s", f(r.base_ETiGood), f(r.prop_ETiGood)]);
  }
  s.addTable(rows.map((r, k) => r.map((c, j) => ({ text: c, options: { bold: k === 0 || j === 3, fill: { color: k === 0 ? "DCE6F2" : (j === 3 ? "EAF2FC" : "FFFFFF") }, color: "1B2433", fontSize: 15, align: j ? "center" : "left" } }))),
    { x: 0.6, y: 3.55, w: 7.6, colW: [1.6, 2.0, 2.0, 2.0], border: { type: "solid", color: "C9C8C2", pt: 0.75 }, rowH: 0.42 });
  txt(s, [
    { text: "Reading the times", options: { bold: true, breakLine: true } },
    { text: "An IA-2 run costs more (repair, 4 probes, polish) but far fewer runs are wasted", options: { bullet: true, breakLine: true } },
    { text: "Easy instances (af-1, af-5, af-5-fs, af-7b-fs): overhead, ETiGood up to ~2× worse", options: { bullet: true, breakLine: true } },
    { text: "Paper times: CPLEX in C, 500 runs; ours: HiGHS from Python", options: { bullet: true } },
  ], { x: 8.6, y: 3.6, w: 4.1, h: 3.1, fontSize: 15, paraSpaceAfter: 8 });
  s.addNotes("Feasibility and time-to-quality improvements.");
}
// 9b ---------------- significance
{
  const s = slide("CONTENT", "The gains are statistically significant", "Results");
  const ST = fs.readFileSync(path.join(ROOT, "results/stats.csv"), "utf8").trim().split("\n");
  const H2 = ST[0].split(",");
  const rowsS = ST.slice(1).map((l) => Object.fromEntries(l.split(",").map((v, i) => [H2[i], v])));
  const fp = (x) => (+x < 1e-4 ? "< 0.0001" : (+x).toFixed(4));
  const rows = [["Instance", "Good: IA-1 → IA-2", "p (Fisher)", "Feasible: IA-1 → IA-2", "p (Fisher)", "p (Mann–Whitney, gaps)"]];
  rowsS.forEach((r) => rows.push([r.instance, `${r.good_base} → ${r.good_prop}`, fp(r.p_fisher_good), `${r.feas_base} → ${r.feas_prop}`, fp(r.p_fisher_feas), fp(r.p_mannwhitney_gap)]));
  s.addTable(rows.map((r, k) => r.map((c, j) => ({ text: c, options: { bold: k === 0, fill: { color: k === 0 ? "DCE6F2" : ((j === 2 || j === 4 || j === 5) && k > 0 && (c.startsWith("<") || +c < 0.05) ? "EAF2FC" : "FFFFFF") }, color: "1B2433", fontSize: 12, align: j ? "center" : "left" } }))),
    { x: 0.6, y: 1.4, w: 12.1, colW: [1.5, 2.3, 1.7, 2.5, 1.7, 2.4], border: { type: "solid", color: "C9C8C2", pt: 0.75 }, rowH: 0.4 });
  txt(s, "One-sided tests, IA-2 better than IA-1, 60 vs 60 runs per instance (3 seeds × 20). Shaded: p < 0.05. ILS runs within a seed are dependent, so the per-seed results in the paper (Table A1) are the conservative check.", { x: 0.6, y: 6.35, w: 12.1, h: 0.8, fontSize: 13, color: "52514E", italic: true });
  s.addNotes(`More Good runs is significant on ${V.sig_good.join(", ")}; lower gaps on ${V.sig_gap.length} of ${V.NI} instances.`);
}
// 10 ---------------- convergence
{
  const s = slide("CONTENT", "The guided search keeps the incumbent below the 0.2% line (except af-6-f)", "Results");
  const cb = fs.readFileSync(path.join(ROOT, "results/Graphs/fig_convergence.png")); const car = cb.readUInt32BE(20) / cb.readUInt32BE(16);
  s.addImage({ path: path.join(ROOT, "results/Graphs/fig_convergence.png"), x: 0.6, y: 1.35, w: 5.4 / car, h: 5.4, altText: "Best gap vs cumulative time on the six hard instances" });
  txt(s, "Best gap to the best-known cost vs cumulative time (log scale), one line per seed; blue = IA-2, orange = IA-1; dashed = Good threshold.", { x: 0.6, y: 6.75, w: 9.0, h: 0.35, fontSize: 11, color: "52514E" });
  card(s, 9.9, 1.4, 2.8, 5.3);
  txt(s, `IA-2 best found: af-2 = best known (IA-1 +0.20%), af-3 +0.008% (IA-1 +0.048%), af-6-fs +0.04% (IA-1 +0.14%). On af-4 (+0.19%) and af-6-f (+0.50%) an IA-1 run was better: more reliable, not always better in the single best run.`, { x: 10.05, y: 1.55, w: 2.5, h: 5.0, fontSize: 14 });
  s.addNotes("Convergence curves: the incumbent improves quickly once the search is guided.");
}
// 11 ---------------- ablation
{
  const s = slide("CONTENT", "Ablation: the components complement each other", "Results");
  const A = V.abl;
  const rows = [["Instance", "IA-1 (baseline)", "A: random + polish", "B: recipe start, no ILS", "IA-2 (full)"]];
  for (const i of Object.keys(A)) {
    const f = (m) => (A[i][m] ? `${Math.round(A[i][m][0])}% / ${Math.round(A[i][m][1])}%` : "–");
    rows.push([i, f("baseline"), f("abl_polish"), f("abl_rcstart"), f("proposed")]);
  }
  s.addTable(rows.map((r, k) => r.map((c, j) => ({ text: c, options: { bold: k === 0 || j === 4, fill: { color: k === 0 ? "DCE6F2" : (j === 4 ? "EAF2FC" : "FFFFFF") }, color: "1B2433", fontSize: 12, align: j ? "center" : "left" } }))),
    { x: 0.6, y: 1.4, w: 7.7, colW: [1.2, 1.4, 1.5, 1.9, 1.7], border: { type: "solid", color: "C9C8C2", pt: 0.75 }, rowH: 0.42 });
  txt(s, "Cells show %Feas / %Good over 20 runs, seed 12345.", { x: 8.6, y: 6.35, w: 4.1, h: 0.4, fontSize: 12, color: "52514E", italic: true });
  card(s, 8.6, 1.5, 4.1, 4.75);
  txt(s, [
    { text: "Polish alone ", options: { bold: true } },
    { text: "mainly fixes feasibility (af-4 60→70%, af-6-fs 90→100%).", options: { breakLine: true } },
    { text: "Recipe starts alone ", options: { bold: true } },
    { text: "are best on af-6-f, af-6-fs and af-7b, but weak on af-2, af-3 and af-4.", options: { breakLine: true } },
    { text: "The probed ILS ", options: { bold: true } },
    { text: "adds the big gains on af-2 (65%), af-3 (15%) and af-4 (60%), but over-refines on af-6-f (0%).", options: { breakLine: true } },
    { text: "Diversity (fresh starts) + depth (ILS) together.", options: { bold: true, color: "2A78D6" } },
  ], { x: 8.8, y: 1.65, w: 3.7, h: 4.5, fontSize: 15, paraSpaceAfter: 10 });
  s.addNotes("Explain the ablation: each component's contribution.");
}
// 12 ---------------- discussion
{
  const s = slide("CONTENT", "Discussion and limitations", "Conclusion");
  const cols = [
    ["Gap addressed", [`%Good up on 5 of 6 hard instances (af-7 seed 2024: tie)`, `${V.feas_p.toFixed(0)}% of IA-2 runs feasible (IA-1 ${V.feas_b.toFixed(0)}%)`, `Significant: Fisher p < 0.01 on ${V.sig_good.length} instances`, "IA-1 model and SLP unchanged"]],
    ["Trade-offs", ["Extra LPs and probes cost time per run", "Easy instances get slower (ETiGood up to ~2×)", "ILS runs within a seed are dependent → 3 seeds"]],
    ["Limitations", ["af-6-f not solved (IA-2 0% vs paper 4.0%, IA-1 1.7%)", "af-7: 18.3% vs paper 20.4%", "af-4 single best run: IA-1 found the best known value", "3×20 runs vs 500 in the paper; other hardware/LP solver", "Diet bound tight only on af-1"]],
  ];
  cols.forEach(([h, items], k) => {
    const x = 0.6 + k * 4.12;
    card(s, x, 1.5, 3.85, 5.1);
    txt(s, h, { x: x + 0.2, y: 1.65, w: 3.45, h: 0.5, bold: true, fontSize: 19, color: "16324F" });
    txt(s, items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < items.length - 1 } })), { x: x + 0.2, y: 2.25, w: 3.45, h: 4.2, fontSize: 15, paraSpaceAfter: 10 });
  });
  s.addNotes("Be honest about the comparison limits.");
}
// 13 ---------------- conclusion
{
  const s = slide("TITLE_DARK", "Structure-aware restarts make our IA-1 SLP reliable on hard pooling instances", "Conclusion");
  s.addText([
    { text: `Mean %Feas ${V.feas_b.toFixed(1)}% → ${V.feas_p.toFixed(1)}%, %Good ${V.good_b.toFixed(1)}% → ${V.good_p.toFixed(1)}%; hard instances ${V.good_b_hard.toFixed(1)}% → ${V.good_p_hard.toFixed(1)}% (paper ${V.good_paper_hard.toFixed(1)}%), ETiGood ${V.spd_hard.toFixed(1)}× shorter`, options: { breakLine: true } },
    { text: "Future: more seeds / full benchmark, adaptive choice of moves, parallel probes, stronger bounds, capacity limits", options: {} },
  ], { placeholder: "body" });
}
// 14 ---------------- references
{
  const s = slide("CONTENT", "References", "Conclusion");
  txt(s, [
    "[1] A. Grothey, K. McKinnon, Annals of Operations Research 322 (2023) 691–711.",
    "[2] M. Terzi et al., Computers & Operations Research 163 (2024) 106507.",
    "[3] S. Sass et al., European Journal of Operational Research 316 (2024) 36–45.",
    "[4] P. E. Gill, M. Zhang, Computational Optimization and Applications 88 (2024) 37–70.",
    "[5] M. Muehlebach, M. I. Jordan, Mathematical Programming 215 (2026) 407–452.",
    "[6] D. di Serafino et al., Mathematical Programming 205 (2024) 107–134.",
    "[7] C. Audet et al., Management Science 50 (2004) 761–776.   [8] C. A. Haverly, ACM SIGMAP Bulletin 25 (1978).",
    "[9] A. Grothey, K. McKinnon, Pooling problem test data (2020).   [10] R. Fletcher, S. Leyffer, Math. Programming 91 (2002).",
    "[11] H. R. Lourenço et al., Iterated local search, Handbook of Metaheuristics (2019).   [12] D. Arthur, S. Vassilvitskii, k-means++, SODA (2007).",
    "[13] Group OPT-09, IA-1 report: SLP for nonlinear pooling optimization problems (2026).",
  ].map((t, j, a) => ({ text: t, options: { breakLine: j < a.length - 1 } })), { x: 0.6, y: 1.5, w: 12.1, h: 5.2, fontSize: 15, paraSpaceAfter: 8 });
}

(async () => {
  const out = path.join(__dirname, "Presentation.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("written");
})();
