// build_poster_simple.js - A1 portrait poster, simple version for explaining the work
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const ROOT = path.resolve(__dirname, "..");
const V = JSON.parse(fs.readFileSync(path.join(ROOT, "paper/cmp_values.json"), "utf8"));
const G = JSON.parse(fs.readFileSync(path.join(ROOT, "paper/group.json"), "utf8"));
const csv = fs.readFileSync(path.join(ROOT, "results/comparison.csv"), "utf8").trim().split("\n");
const hdr = csv[0].split(",");
const CMP = csv.slice(1).map((l) => Object.fromEntries(l.split(",").map((v, i) => [hdr[i], isNaN(+v) ? v : +v])));
const byI = Object.fromEntries(CMP.map((r) => [r.instance, r]));

const pres = new pptxgen();
pres.defineLayout({ name: "A1P", width: 23.39, height: 33.11 });
pres.layout = "A1P";
pres.theme = { headFontFace: "Cambria", bodyFontFace: "Calibri" };
const s = pres.addSlide();
s.background = { color: "FFFFFF" };
const NAVY = "16324F", INK = "1B2433", MUTED = "52514E", TINT = "EEF3F8", BLUE = "2A78D6", ORANGE = "EB6834",
  GREEN = "1BAF7A", GREY = "9AA9BC", LINE = "C9C8C2", VIOLET = "6250D6";
const T = (t, o) => s.addText(t, { isTextBox: true, fontFace: "Calibri", color: INK, fontSize: 26, valign: "top", margin: 0.1, ...o });
const box = (x, y, w, h, fill = TINT, line = null) => s.addShape(pres.shapes.ROUNDED_RECTANGLE,
  { x, y, w, h, fill: { color: fill }, line: { color: line || fill, width: line ? 2 : 0 }, rectRadius: 0.25 });
const head = (n, t, x, y, w) => {
  s.addShape(pres.shapes.OVAL, { x, y: y + 0.05, w: 0.85, h: 0.85, fill: { color: NAVY }, line: { color: NAVY } });
  T(String(n), { x, y: y + 0.05, w: 0.85, h: 0.85, fontSize: 30, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
  T(t, { x: x + 1.05, y, w: w - 1.05, h: 0.95, fontSize: 40, bold: true, color: NAVY, fontFace: "Cambria", valign: "middle" });
};
const circle = (x, y, d, fill, label, fs = 16) => {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  if (label) T(label, { x: x - 0.3, y, w: d + 0.6, h: d, fontSize: fs, color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0 });
};
const arrow = (x1, y1, x2, y2, color = "8A8984", width = 3, dash) => s.addShape(pres.shapes.LINE,
  { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipH: x2 < x1, flipV: y2 < y1,
    line: { color, width, endArrowType: "triangle", dashType: dash } });
const bigNum = (x, y, w, h, num, label, color, fsz = 60) => {
  box(x, y, w, h);
  T(num, { x: x + 0.2, y: y + 0.2, w: w - 0.4, h: h * 0.52, fontSize: fsz, bold: true, color, fontFace: "Cambria", align: "center", valign: "middle" });
  T(label, { x: x + 0.25, y: y + h * 0.56, w: w - 0.5, h: h * 0.42, fontSize: 21, color: MUTED, align: "center" });
};
const pct = (x) => `${Math.round(x)}%`;
const L = 0.9, W = 21.6, HALF = 10.5, R = L + HALF + 0.6;

// ---------------- header
s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 23.39, h: 4.5, fill: { color: NAVY }, line: { color: NAVY } });
T("Smarter Restarts for Feed-Blending Optimization", { x: L, y: 0.45, w: W, h: 1.5, fontSize: 64, bold: true, color: "FFFFFF", fontFace: "Cambria" });
T("Improving Sequential Linear Programming (SLP) for the pooling problem: from our IA-1 re-implementation to IA-2",
  { x: L, y: 1.95, w: W, h: 0.8, fontSize: 30, color: "DCE6F2" });
T(`Group ${G.id}  ·  ${[G.s1, G.s2, G.s3].map((x) => x.replace(" | ", " (") + ")").join("  ·  ")}`, { x: L, y: 2.85, w: W, h: 0.6, fontSize: 26, color: "DCE6F2" });
T("Introduction to Optimization Techniques (IA-2)  ·  Dept. of IT, K. J. Somaiya College of Engineering", { x: L, y: 3.5, w: W, h: 0.6, fontSize: 22, color: "B8C4D4" });

// ---------------- 1. problem (left)  /  2. gap (right)
let y = 5.0;
head(1, "The problem", L, y, HALF);
box(L, y + 1.15, HALF, 7.1);
{ // feed-mill network
  const rm = ["maize", "soya", "wheat", "oil", "salt"], bins = ["Bin 1", "Bin 2"], pr = ["Feed A", "Feed B", "Feed C"];
  const d = 0.75, gy = 0.95, x0 = L + 2.0, y0 = y + 1.55, bx = x0 + 3.0, px = x0 + 6.0;
  const ry = (k) => y0 + k * gy, by = (k) => y0 + (0.9 + k * 1.9) * gy, py = (k) => y0 + (0.4 + k * 1.6) * gy;
  rm.forEach((_, i) => bins.forEach((__, j) => { if ((i + j) % 2 === 0 || i === 2)
    s.addShape(pres.shapes.LINE, { x: x0 + d, y: Math.min(ry(i), by(j)) + d / 2, w: bx - x0 - d, h: Math.abs(by(j) - ry(i)), flipV: by(j) < ry(i), line: { color: LINE, width: 1.5 } }); }));
  bins.forEach((_, j) => pr.forEach((__, k) =>
    s.addShape(pres.shapes.LINE, { x: bx + d, y: Math.min(by(j), py(k)) + d / 2, w: px - bx - d, h: Math.abs(py(k) - by(j)), flipV: py(k) < by(j), line: { color: LINE, width: 1.5 } })));
  rm.forEach((r, i) => { circle(x0, ry(i), d, GREY); T(r, { x: x0 - 1.6, y: ry(i) + 0.12, w: 1.5, h: 0.55, fontSize: 18, color: MUTED, align: "right" }); });
  bins.forEach((b, j) => circle(bx - 0.2, by(j) - 0.2, d + 0.4, BLUE, b, 17));
  pr.forEach((p, k) => { circle(px, py(k), d, GREEN); T(p, { x: px + d + 0.05, y: py(k) + 0.12, w: 1.6, h: 0.55, fontSize: 18, color: MUTED }); });
}
T([
  { text: "Raw materials go through a few ", options: {} }, { text: "shared bins", options: { bold: true, color: BLUE } },
  { text: " into many feeds. Every feed must meet nutrient limits. ", options: {} },
  { text: "Goal: the lowest total cost.", options: { bold: true } },
], { x: L + 0.35, y: y + 6.3, w: HALF - 0.7, h: 1.8, fontSize: 24 });

head(2, "Why it is hard, and the gap", R, y, HALF);
box(R, y + 1.15, HALF, 7.1);
T([
  { text: "A bin that suits one feed can hurt another: quality = share × content (two unknowns multiplied), so the problem has many ", options: {} },
  { text: "'valleys'", options: { bold: true } }, { text: " (local optima).", options: { breakLine: true } },
  { text: "The paper's SLP (our IA-1 code) restarts from ", options: {} }, { text: "random", options: { bold: true, color: ORANGE } },
  { text: " points, so it often ends in a poor valley.", options: {} },
], { x: R + 0.35, y: y + 1.4, w: HALF - 0.7, h: 3.0, fontSize: 25, paraSpaceAfter: 14 });
bigNum(R + 0.35, y + 4.45, 4.75, 3.55, pct(V.good_b_hard), "Good runs on the 6 hard instances (IA-1)", ORANGE);
bigNum(R + 5.4, y + 4.45, 4.75, 3.55, `${Math.round(100 - V.feas_b)}%`, "of all IA-1 runs end infeasible", ORANGE);

// ---------------- 3. idea
y = 13.4;
head(3, "Our idea (IA-2): restart smart, not random", L, y, W);
const ideas = [
  ["1", "Smart start", "Compute each feed's ideal recipe (a small LP) and group similar recipes into the bins.", BLUE],
  ["2", "Fix one, solve the other", "With the bins fixed the rest is an easy LP: it repairs and polishes every answer.", GREEN],
  ["3", "Learn from the best", "Each new run starts from the best answer so far and changes the bin that hurts one feed most.", VIOLET],
];
ideas.forEach(([n, h, b, col], k) => {
  const x = L + k * 7.3, w = 7.0;
  box(x, y + 1.15, w, 4.6);
  circle(x + w / 2 - 0.55, y + 1.45, 1.1, col, n, 34);
  T(h, { x: x + 0.3, y: y + 2.7, w: w - 0.6, h: 0.75, fontSize: 30, bold: true, color: NAVY, align: "center" });
  T(b, { x: x + 0.35, y: y + 3.5, w: w - 0.7, h: 2.1, fontSize: 22, color: MUTED, align: "center" });
});
T("The model and the SLP solver from IA-1 stay unchanged. Check on af-1 (our IA-1 instance): IA-1 and IA-2 are both Good in 100% of runs, and IA-2's lower bound (295.93 = BARON's) proves the cost 296.446 is within 0.17% of the optimum.",
  { x: L, y: y + 5.9, w: W, h: 0.9, fontSize: 22, bold: true, color: BLUE, align: "center" });

// ---------------- 4. flow
y = 20.35;
head(4, "How IA-2 runs (20 runs per instance)", L, y, W);
const flow = [["Ideal recipes", "LP per feed", BLUE], ["Smart start", "recipes → bins", BLUE], ["SLP", "same as IA-1", GREY],
  ["Polish", "two exact LPs", GREEN], ["Best so far", "cheapest valid", NAVY], ["Learn & change", "re-mix one bin", VIOLET]];
flow.forEach(([h, b, col], k) => {
  const x = L + k * 3.62, w = 3.2;
  box(x, y + 1.2, w, 2.3);
  s.addShape(pres.shapes.RECTANGLE, { x, y: y + 1.2, w, h: 0.16, fill: { color: col }, line: { color: col } });
  T(h, { x: x + 0.1, y: y + 1.5, w: w - 0.2, h: 0.7, fontSize: 25, bold: true, color: NAVY, align: "center" });
  T(b, { x: x + 0.1, y: y + 2.25, w: w - 0.2, h: 0.9, fontSize: 20, color: MUTED, align: "center" });
  if (k < 5) arrow(x + w + 0.03, y + 2.35, x + w + 0.4, y + 2.35);
});
// loop back from "Learn & change" to "SLP"
const xl = L + 5 * 3.62 + 1.6, xs = L + 2 * 3.62 + 1.6;
s.addShape(pres.shapes.LINE, { x: xl, y: y + 3.5, w: 0, h: 0.55, line: { color: VIOLET, width: 3, dashType: "dash" } });
s.addShape(pres.shapes.LINE, { x: xs, y: y + 4.05, w: xl - xs, h: 0, line: { color: VIOLET, width: 3, dashType: "dash" } });
arrow(xs, y + 4.05, xs, y + 3.52, VIOLET, 3, "dash");
T("next run starts from the best answer", { x: xs + 0.3, y: y + 4.05, w: xl - xs - 0.6, h: 0.55, fontSize: 20, color: VIOLET, align: "center" });

// ---------------- 5. results
y = 24.95;
head(5, "Results: IA-1 vs IA-2 (11 instances, 3 × 20 runs each, same computer)", L, y, W);
s.addChart(pres.charts.BAR, [{ name: "%Good", labels: ["IA-1", "Paper", "IA-2"],
  values: [V.good_b_hard, V.good_paper_hard, V.good_p_hard].map((x) => Math.round(x * 10) / 10) }], {
  x: L, y: y + 1.15, w: 8.2, h: 4.75, barDir: "col", chartColors: [ORANGE, GREEN, BLUE], showLegend: false,
  showValue: true, dataLabelFontSize: 22, dataLabelFormatCode: '0"%"', dataLabelColor: INK, valAxisMaxVal: 40, valAxisLabelFontSize: 14,
  catAxisLabelFontSize: 20, valGridLine: { color: "E5E4DF", size: 0.5 }, catGridLine: { style: "none" }, barGapWidthPct: 50,
  showTitle: true, title: "% Good runs, 6 hard instances", titleFontSize: 20, titleColor: MUTED });
bigNum(L + 8.5, y + 1.2, 4.2, 3.0, `${V.spd_hard.toFixed(0)}×`, "faster to a Good answer (hard)", BLUE);
bigNum(L + 12.95, y + 1.2, 4.2, 3.0, `${Math.round(V.feas_b)}→${pct(V.feas_p)}`, "feasible runs (all 11)", BLUE, 48);
bigNum(L + 17.4, y + 1.2, 4.2, 3.0, `${Math.round(V.good_b)}→${pct(V.good_p)}`, "Good runs (all 11)", BLUE, 48);
box(L + 8.5, y + 4.45, 13.1, 1.45, "FFFFFF", LINE);
T([
  { text: `Biggest gains: af-2 ${pct(byI["af-2"].base_good)} → ${pct(byI["af-2"].prop_good)}, af-4 ${pct(byI["af-4"].base_good)} → ${pct(byI["af-4"].prop_good)} Good runs. `, options: { bold: true, color: NAVY } },
  { text: "Limits: af-6-f unsolved by both; easy instances a bit slower.", options: { color: MUTED } },
], { x: L + 8.7, y: y + 4.55, w: 12.7, h: 1.3, fontSize: 21, valign: "middle" });

// ---------------- take-away + footer
s.addShape(pres.shapes.RECTANGLE, { x: L, y: 31.95, w: W, h: 0.04, fill: { color: LINE }, line: { color: LINE } });
T([{ text: "Take-away: ", options: { bold: true, color: NAVY } },
  { text: "using simple LPs to start smart and to learn from the best answer makes SLP find good feed recipes about 5× more often on hard problems.", options: {} }],
  { x: L, y: 31.05, w: W, h: 0.85, fontSize: 24 });
T("[1] A. Grothey, K. McKinnon, On the effectiveness of sequential linear programming for the pooling problem, Ann. Oper. Res. 322 (2023) 691–711.  [2] Group OPT-09, IA-1 report (2026).  Code + Colab demo: github.com/razzantambe/OPT-09-IA2-Pooling-SLP",
  { x: L, y: 32.05, w: W, h: 0.9, fontSize: 16, color: MUTED });

pres.writeFile({ fileName: path.join(__dirname, "Poster.pptx") }).then(() => console.log("written"));
