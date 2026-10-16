// build_deck_simple.js - IA-2 presentation, simple version for explaining the work (one idea per slide)
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const SK = "/root/.claude/skills/synced/cce128f9-238f-4707-859f-3c07c522fe23_07e1d76c-60de-4e09-bb13-09801cd38c17/pptx";
const { applyTheme } = require(SK + "/scripts/apply_theme.js");

const ROOT = path.resolve(__dirname, "..");
const csv = fs.readFileSync(path.join(ROOT, "results/comparison.csv"), "utf8").trim().split("\n");
const hdr = csv[0].split(",");
const CMP = csv.slice(1).map((l) => Object.fromEntries(l.split(",").map((v, i) => [hdr[i], isNaN(+v) ? v : +v])));
const byI = Object.fromEntries(CMP.map((r) => [r.instance, r]));
const V = JSON.parse(fs.readFileSync(path.join(ROOT, "paper/cmp_values.json"), "utf8"));
const G = JSON.parse(fs.readFileSync(path.join(ROOT, "paper/group.json"), "utf8"));

const NAVY = "16324F", INK = "1B2433", MUTED = "52514E", TINT = "EEF3F8", BLUE = "2A78D6", ORANGE = "EB6834",
  GREEN = "1BAF7A", GREY = "9AA9BC", LINE = "C9C8C2";
const THEME = {
  name: "Feed Mill Simple", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: INK, lt1: "FFFFFF", dk2: NAVY, lt2: TINT, accent1: BLUE, accent2: ORANGE, accent3: GREEN,
    accent4: "EDA100", accent5: "6250D6", accent6: MUTED, hlink: BLUE, folHlink: "6250D6" },
};
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: "Cambria", bodyFontFace: "Calibri" };
pres.title = "Smarter restarts for feed-blending optimization (IA-2)";
pres.author = "Group OPT-09";
const C = pres.SchemeColor;
const FOOT = "IA-2 | Introduction to Optimization Techniques | Group OPT-09";

pres.defineSlideMaster({ title: "DARK", background: { color: NAVY },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.7, w: 11.7, h: 2.2, fontSize: 40, bold: true, color: C.background1, fontFace: "Cambria", valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.15, w: 11.7, h: 2.6, fontSize: 18, color: C.background2, valign: "top" }, text: "" } },
  ] });
pres.defineSlideMaster({ title: "CONTENT", background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.3, w: 12.1, h: 0.95, fontSize: 30, bold: true, color: C.text2, fontFace: "Cambria", valign: "middle" }, text: "" } },
    { text: { text: FOOT, options: { x: 0.6, y: 7.05, w: 8, h: 0.3, fontSize: 10, color: "8A8984" } } },
  ],
  slideNumber: { x: 12.2, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: "8A8984", align: "right" } });

let sec = "";
function slide(master, title, section, notes) {
  if (section && section !== sec) { pres.addSection({ title: section }); sec = section; }
  const s = pres.addSlide({ masterName: master, sectionTitle: sec });
  if (title) s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}
const T = (s, t, o) => s.addText(t, { isTextBox: true, fontFace: "Calibri", color: INK, fontSize: 20, valign: "top", margin: 0.08, ...o });
const card = (s, x, y, w, h, fill = TINT, line = null) =>
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: line || fill, width: line ? 1.5 : 0 }, rectRadius: 0.12 });
const circle = (s, x, y, d, fill, label, lc = "FFFFFF", fs = 12) => {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  if (label) T(s, label, { x: x - 0.2, y, w: d + 0.4, h: d, fontSize: fs, color: lc, bold: true, align: "center", valign: "middle", margin: 0 });
};
const arrow = (s, x1, y1, x2, y2, color = "8A8984", width = 2, dash) =>
  s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: x2 < x1, flipV: y2 < y1, line: { color, width, endArrowType: "triangle", dashType: dash } });
const big = (s, x, y, w, num, label, color = BLUE, sub) => {
  card(s, x, y, w, 2.2);
  T(s, num, { x: x + 0.15, y: y + 0.15, w: w - 0.3, h: 1.1, fontSize: 44, bold: true, color, fontFace: "Cambria", align: "center", valign: "middle" });
  T(s, label, { x: x + 0.15, y: y + 1.25, w: w - 0.3, h: 0.85, fontSize: 16, color: MUTED, align: "center" });
};
const pct = (x) => `${Math.round(x)}%`;

// feed-mill network picture used on two slides
function network(s, x0, y0, scale = 1) {
  const rm = ["maize", "soya", "wheat", "oil", "salt"], bins = ["Bin 1", "Bin 2"], pr = ["Feed A", "Feed B", "Feed C"];
  const d = 0.62 * scale, gy = 0.95 * scale;
  const rx = x0, bx = x0 + 2.4 * scale, px = x0 + 4.8 * scale;
  const ry = (k) => y0 + k * gy, by = (k) => y0 + (0.9 + k * 1.9) * gy, py = (k) => y0 + (0.4 + k * 1.6) * gy;
  rm.forEach((_, i) => bins.forEach((__, j) => { if ((i + j) % 2 === 0 || i === 2)
    s.addShape(pres.shapes.LINE, { x: rx + d, y: Math.min(ry(i), by(j)) + d / 2, w: bx - rx - d, h: Math.abs(by(j) - ry(i)), flipV: by(j) < ry(i), line: { color: LINE, width: 1 } }); }));
  bins.forEach((_, j) => pr.forEach((__, k) =>
    s.addShape(pres.shapes.LINE, { x: bx + d, y: Math.min(by(j), py(k)) + d / 2, w: px - bx - d, h: Math.abs(py(k) - by(j)), flipV: py(k) < by(j), line: { color: LINE, width: 1 } })));
  rm.forEach((r, i) => { circle(s, rx, ry(i), d, GREY); T(s, r, { x: rx - 1.25 * scale, y: ry(i) + 0.08, w: 1.2 * scale, h: 0.45, fontSize: 13 * scale, color: MUTED, align: "right" }); });
  bins.forEach((b, j) => circle(s, bx - 0.15 * scale, by(j) - 0.15 * scale, d + 0.3 * scale, BLUE, b, "FFFFFF", 12 * scale));
  pr.forEach((p, k) => { circle(s, px, py(k), d, GREEN); T(s, p, { x: px + d + 0.05, y: py(k) + 0.08, w: 1.3 * scale, h: 0.45, fontSize: 13 * scale, color: MUTED }); });
  T(s, "raw materials", { x: rx - 0.5, y: ry(4) + d + 0.1, w: 1.8 * scale, h: 0.4, fontSize: 13 * scale, color: MUTED, align: "center", bold: true });
  T(s, "shared mixing bins", { x: bx - 0.55, y: ry(4) + d + 0.1, w: 2.2 * scale, h: 0.4, fontSize: 13 * scale, color: BLUE, align: "center", bold: true });
  T(s, "products", { x: px - 0.45, y: ry(4) + d + 0.1, w: 1.6 * scale, h: 0.4, fontSize: 13 * scale, color: GREEN, align: "center", bold: true });
}

// 1 ---------------------------------------------------------------- title
{
  const s = slide("DARK", "Smarter Restarts for Feed-Blending Optimization", "Introduction",
    "Introduce the team. One sentence: we took the SLP method from the paper (IA-1) and made its restarts smarter (IA-2).");
  s.addText([
    { text: "Improving Sequential Linear Programming (SLP) for the pooling problem", options: { breakLine: true, bold: true, fontSize: 22 } },
    { text: "IA-2 · Introduction to Optimization Techniques · Dept. of IT, K. J. Somaiya College of Engineering", options: { breakLine: true } },
    { text: `Group ${G.id}: ${[G.s1, G.s2, G.s3].map((x) => x.replace(" | ", " (") + ")").join(" · ")}`, options: {} },
  ], { placeholder: "body" });
}
// 2 ---------------------------------------------------------------- problem
{
  const s = slide("CONTENT", "The problem: make animal feed at the lowest cost", "The problem",
    "Explain with the picture: raw materials go into a few shared bins; each product is mixed from bins (and some direct raw materials). Each product must meet nutrient limits.");
  network(s, 1.6, 1.6);
  card(s, 7.9, 1.5, 4.8, 5.1);
  T(s, [
    { text: "A feed mill must deliver fixed orders of many feeds.", options: { bullet: true, breakLine: true } },
    { text: "Each feed needs its nutrients (protein, fat, fibre, …) within limits.", options: { bullet: true, breakLine: true } },
    { text: "Raw materials are first mixed in a few shared bins.", options: { bullet: true, breakLine: true } },
    { text: "Goal: choose what goes into each bin and each feed so that the total cost is lowest.", options: { bullet: true, bold: true } },
  ], { x: 8.15, y: 1.75, w: 4.3, h: 4.7, fontSize: 19, paraSpaceAfter: 14 });
}
// 3 ---------------------------------------------------------------- why hard
{
  const s = slide("CONTENT", "Why it is hard: shared bins create many 'valleys'", "The problem",
    "A bin that suits Feed A may be wrong for Feed B. Mathematically: feed quality = (share of bin) x (bin content), a product of two unknowns, so the problem is nonconvex with many local optima. A local method ends in the valley where it starts.");
  card(s, 0.6, 1.5, 5.4, 5.1);
  T(s, "One bin, two feeds", { x: 0.85, y: 1.65, w: 5, h: 0.5, bold: true, fontSize: 21, color: NAVY });
  T(s, [
    { text: "A bin recipe that is good for Feed A can be bad for Feed B.", options: { bullet: true, breakLine: true } },
    { text: "Feed quality = (share of the bin) × (what is in the bin): two unknowns multiplied.", options: { bullet: true, breakLine: true } },
    { text: "This makes the problem nonconvex: it has many local best answers.", options: { bullet: true } },
  ], { x: 0.85, y: 2.25, w: 5.0, h: 4.2, fontSize: 18, paraSpaceAfter: 14 });
  const xs = [], ys = [];
  for (let k = 0; k <= 60; k++) { const t = k / 60 * 10; xs.push(String(k)); ys.push(5 + 1.6 * Math.sin(1.3 * t) + 1.1 * Math.sin(3.1 * t + 1) + 0.25 * (t - 6) * (t - 6) / 4); }
  s.addChart(pres.charts.LINE, [{ name: "total cost", labels: xs, values: ys }], {
    x: 6.3, y: 1.5, w: 6.4, h: 4.2, lineSize: 3, lineDataSymbol: "none", chartColors: [BLUE], showLegend: false,
    catAxisHidden: true, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showTitle: true, title: "cost of all possible recipes (simplified)", titleFontSize: 14, titleColor: MUTED, lineSmooth: true });
  T(s, "Many valleys = many local optima. A local method slides into the valley next to where it starts, and the deepest valley is easy to miss.",
    { x: 6.4, y: 5.8, w: 6.3, h: 0.9, fontSize: 16, color: MUTED, italic: true });
}
// 4 ---------------------------------------------------------------- baseline
{
  const s = slide("CONTENT", "IA-1: the paper's method (SLP with random restarts)", "IA-1 and the gap",
    "In IA-1 we re-implemented Grothey & McKinnon (2023). SLP: approximate the curved problem by a straight-line (linear) one near the current point, solve that LP, move, repeat. To escape bad valleys they restart from many random points and keep the best.");
  const steps = [["Random start", "pick any mixture", GREY], ["SLP", "solve a linear approximation, move, repeat", BLUE], ["Local answer", "bottom of one valley", GREEN], ["Keep the best", "of 20 restarts", NAVY]];
  steps.forEach(([h, b, col], k) => {
    const x = 0.6 + k * 3.1;
    card(s, x, 1.7, 2.75, 2.2, TINT);
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.7, w: 2.75, h: 0.12, fill: { color: col }, line: { color: col } });
    T(s, h, { x: x + 0.15, y: 1.95, w: 2.45, h: 0.55, bold: true, fontSize: 21, color: NAVY, align: "center" });
    T(s, b, { x: x + 0.15, y: 2.55, w: 2.45, h: 1.2, fontSize: 16, color: MUTED, align: "center" });
    if (k < 3) arrow(s, x + 2.78, 2.8, x + 3.07, 2.8);
  });
  s.addShape(pres.shapes.LINE, { x: 1.95, y: 3.95, w: 9.3, h: 0, line: { color: ORANGE, width: 1.5, dashType: "dash", beginArrowType: "triangle" } });
  T(s, "repeat from a new random point", { x: 4.6, y: 3.95, w: 4, h: 0.4, fontSize: 14, color: ORANGE, align: "center" });
  card(s, 0.6, 4.75, 12.1, 1.85, "FFFFFF", LINE);
  T(s, [
    { text: "SLP (Sequential Linear Programming): ", options: { bold: true } },
    { text: "near the current point the curved problem is replaced by a simple linear one (an LP). Solve the LP, take the step if it really improves, and repeat until it stops improving. It is fast, but it only finds the bottom of the valley it started in.", options: {} },
  ], { x: 0.85, y: 4.9, w: 11.6, h: 1.6, fontSize: 18 });
}
// 5 ---------------------------------------------------------------- gap
{
  const s = slide("CONTENT", "The gap we found in IA-1", "IA-1 and the gap",
    "Our IA-1 code on all 11 instances: on the 6 hard instances only about 6% of runs end within 0.2% of the best known cost; about 1 in 8 runs ends infeasible; and every restart is random, it learns nothing from earlier runs.");
  big(s, 0.6, 1.6, 3.8, pct(V.good_b_hard), "of runs reach a Good solution on the 6 hard instances", ORANGE);
  big(s, 4.75, 1.6, 3.8, `${Math.round(100 - V.feas_b)}%`, "of all runs end infeasible (break a constraint)", ORANGE);
  big(s, 8.9, 1.6, 3.8, "0", "information reused between restarts: every start is random", ORANGE);
  card(s, 0.6, 4.2, 12.1, 2.4, "FFFFFF", LINE);
  T(s, [
    { text: "Good solution = ", options: { bold: true } }, { text: "cost within 0.2% of the best cost ever found for that instance.", options: { breakLine: true } },
    { text: "Gap: ", options: { bold: true, color: ORANGE } },
    { text: "random restarts waste most of the time in bad valleys. Yet the problem has a simple structure that nobody used: if the bins are fixed, the rest is an easy LP.", options: {} },
  ], { x: 0.85, y: 4.35, w: 11.6, h: 2.1, fontSize: 19, paraSpaceAfter: 10 });
}
// 6 ---------------------------------------------------------------- idea
{
  const s = slide("CONTENT", "IA-2: restart smart, not random", "Our idea (IA-2)",
    "Three ideas, all built on simple LPs. The model and the SLP solver of IA-1 are not changed; only where each run starts and what happens after it.");
  const ideas = [
    ["1", "Smart start", "Compute each feed's ideal recipe (a small LP), then group similar recipes into the bins.", BLUE],
    ["2", "Fix one, solve the other", "With the bins fixed, the rest is an easy LP. We use it to repair and polish every answer.", GREEN],
    ["3", "Learn from the best", "The next run starts from the best answer so far and changes the bin that costs one feed the most.", "6250D6"],
  ];
  ideas.forEach(([n, h, b, col], k) => {
    const x = 0.6 + k * 4.12;
    card(s, x, 1.55, 3.85, 4.2);
    circle(s, x + 1.5, 1.8, 0.85, col, n, "FFFFFF", 26);
    T(s, h, { x: x + 0.2, y: 2.8, w: 3.45, h: 0.6, bold: true, fontSize: 22, color: NAVY, align: "center" });
    T(s, b, { x: x + 0.25, y: 3.45, w: 3.35, h: 2.2, fontSize: 18, color: MUTED, align: "center" });
  });
  T(s, "The model and the SLP solver from IA-1 stay exactly the same: only the starting points and the restarts change.",
    { x: 0.6, y: 6.0, w: 12.1, h: 0.6, fontSize: 18, bold: true, color: BLUE, align: "center" });
}
// 7 ---------------------------------------------------------------- flow
{
  const s = slide("CONTENT", "How IA-2 runs", "Our idea (IA-2)",
    "Walk through the loop: ideal recipes once; smart start; the same SLP as IA-1; polish with the LPs; keep the best; change one bin using the 'regret' (how much a feed pays for sharing bins); try 4 such changes quickly and continue with the most promising.");
  const boxes = [
    ["Ideal recipes", "one LP per feed\n+ lower bound", BLUE, 0.6, 1.7],
    ["Smart start", "group recipes\ninto bins", BLUE, 3.7, 1.7],
    ["SLP", "same as IA-1", GREY, 6.8, 1.7],
    ["Polish", "fix bins → LP\nfix shares → LP", GREEN, 9.9, 1.7],
    ["Learn & change", "re-mix the bin that\nhurts one feed most;\ntry 4, keep the best", "6250D6", 6.8, 4.45],
    ["Best so far", "keep the cheapest\nvalid answer", NAVY, 9.9, 4.45],
  ];
  for (const [h, b, col, x, y] of boxes) {
    card(s, x, y, 2.8, 2.05, TINT);
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 2.8, h: 0.12, fill: { color: col }, line: { color: col } });
    T(s, h, { x: x + 0.1, y: y + 0.25, w: 2.6, h: 0.5, bold: true, fontSize: 20, color: NAVY, align: "center" });
    T(s, b, { x: x + 0.1, y: y + 0.8, w: 2.6, h: 1.2, fontSize: 15, color: MUTED, align: "center" });
  }
  arrow(s, 3.42, 2.72, 3.68, 2.72); arrow(s, 6.52, 2.72, 6.78, 2.72); arrow(s, 9.62, 2.72, 9.88, 2.72);
  arrow(s, 11.3, 3.78, 11.3, 4.43);
  arrow(s, 9.88, 5.47, 9.62, 5.47, "6250D6");
  arrow(s, 8.2, 4.43, 8.2, 3.78, "6250D6", 2, "dash");
  T(s, "next run", { x: 8.3, y: 3.85, w: 1.4, h: 0.45, fontSize: 14, color: "6250D6" });
  card(s, 0.6, 4.45, 5.9, 2.05, "FFFFFF", LINE);
  T(s, [
    { text: "20 runs per instance. ", options: { bold: true } },
    { text: "The first 3 runs use smart starts. Each later run starts from the best answer and changes one bin. After 6 runs without progress, IA-2 takes a fresh smart start.", options: {} },
  ], { x: 0.8, y: 4.6, w: 5.5, h: 1.8, fontSize: 16 });
}
// 8 ---------------------------------------------------------------- trick
{
  const s = slide("CONTENT", "The key trick: fix one part, and the rest is easy", "Our idea (IA-2)",
    "Quality = share x content. Fix the content of the bins: only shares remain, linear, an LP, solved exactly and fast. Fix the shares: only bin contents remain, again an LP. Alternating can only lower the cost. Relaxing the bins altogether gives each feed's ideal recipe and a lower bound on the best possible cost.");
  const two = [["Fix what is in the bins", "Then choosing how much of each bin goes into each feed is a plain LP: exact and fast.", BLUE],
    ["Fix how much of each bin goes into each feed", "Then choosing what goes into each bin is also a plain LP.", GREEN]];
  two.forEach(([h, b, col], k) => {
    const x = 0.6 + k * 6.2;
    card(s, x, 1.55, 5.9, 2.6);
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.55, w: 0.14, h: 2.6, fill: { color: col }, line: { color: col } });
    T(s, h, { x: x + 0.35, y: 1.7, w: 5.4, h: 0.85, bold: true, fontSize: 21, color: NAVY, valign: "top" });
    T(s, b, { x: x + 0.35, y: 2.6, w: 5.4, h: 1.45, fontSize: 18, color: MUTED });
  });
  card(s, 0.6, 4.4, 5.9, 2.2, "FFFFFF", LINE);
  T(s, [{ text: "Use: ", options: { bold: true } }, { text: "alternating the two LPs repairs broken answers and polishes good ones, and the cost never goes up.", options: {} }],
    { x: 0.85, y: 4.55, w: 5.4, h: 1.9, fontSize: 18 });
  card(s, 6.8, 4.4, 5.9, 2.2, "FFFFFF", LINE);
  T(s, [{ text: "Bonus: ", options: { bold: true } }, { text: `ignoring bin sharing gives each feed's ideal recipe and a lower bound on the best cost. On af-1 it equals the bound of the global solver BARON (295.93), in milliseconds.`, options: {} }],
    { x: 7.05, y: 4.55, w: 5.4, h: 1.9, fontSize: 18 });
}
// 9 ---------------------------------------------------------------- test
{
  const s = slide("CONTENT", "How we tested IA-1 against IA-2", "Results",
    "Fair test: same 11 instances, same computer, same random seeds, same number of runs. Explain the three measures in plain words.");
  const rows = [
    ["Instances", "all 11 real feed-mill problems of the paper (af-1 … af-7b-fs)"],
    ["Methods", "IA-1 = our IA-1 code (baseline)  ·  IA-2 = the new method"],
    ["Runs", "3 seeds × 20 runs per method and instance, same computer"],
    ["Feasible %", "share of runs whose answer meets every constraint"],
    ["Good %", "share of runs within 0.2% of the best cost ever found"],
    ["Time to Good", "expected seconds until a Good answer appears"],
  ];
  s.addTable(rows.map((r, k) => r.map((c, j) => ({ text: c, options: { bold: j === 0, fill: { color: j === 0 ? TINT : "FFFFFF" }, color: INK, fontSize: 19, valign: "middle" } }))),
    { x: 0.6, y: 1.6, w: 12.1, colW: [2.6, 9.5], border: { type: "solid", color: LINE, pt: 0.75 }, rowH: 0.78 });
}
// 9b ---------------------------------------------------------------- af-1 check
{
  const s = slide("CONTENT", "First check: af-1, the instance we validated in IA-1", "Results",
    "af-1 is the instance from our IA-1 report. Both methods solve it in every run, so it shows that IA-2 keeps everything IA-1 got right. IA-2 adds a proof of quality: its lower bound (295.93) equals the bound of the global solver BARON, so the cost 296.446 is at most 0.17% above the true optimum.");
  const r = byI["af-1"];
  const rows = [["af-1", "Paper (CPLEX)", "IA-1 (our IA-1 code)", "IA-2 (new method)"],
    ["Runs that are Good", `${r.paper_good}%`, pct(r.base_good), pct(r.prop_good)],
    ["Runs that are feasible", `${r.paper_feas}%`, pct(r.base_feas), pct(r.prop_feas)],
    ["Best cost found", "296.446", r.base_best.toFixed(3), r.prop_best.toFixed(3)],
    ["Lower bound (proof of quality)", "BARON: 295.932 (hours)", "none", "295.932 (milliseconds)"]];
  s.addTable(rows.map((row, k) => row.map((c, j) => ({ text: c, options: { bold: k === 0 || j === 0, fill: { color: k === 0 ? "DCE6F2" : (j === 3 ? "EAF2FC" : (j === 0 ? TINT : "FFFFFF")) }, color: INK, fontSize: 19, align: j ? "center" : "left", valign: "middle" } }))),
    { x: 0.6, y: 1.55, w: 12.1, colW: [3.7, 2.8, 2.8, 2.8], border: { type: "solid", color: LINE, pt: 0.75 }, rowH: 0.72 });
  card(s, 0.6, 5.4, 12.1, 1.25, "FFFFFF", LINE);
  T(s, [{ text: "IA-2 keeps everything IA-1 got right on af-1 ", options: { bold: true, color: NAVY } },
    { text: "and adds a proof: the best cost is at most 0.17% above the true optimum.", options: {} }],
    { x: 0.85, y: 5.5, w: 11.6, h: 1.05, fontSize: 20, valign: "middle" });
}
// 10 ---------------------------------------------------------------- headline result
{
  const s = slide("CONTENT", "Result: IA-2 finds Good solutions 5× more often on hard problems", "Results",
    "On the 6 hard instances (where the paper itself is Good in at most about 20% of runs): IA-1 6%, paper 15%, IA-2 34%.");
  s.addChart(pres.charts.BAR, [{ name: "%Good", labels: ["IA-1 (our IA-1 code)", "Paper (CPLEX, 500 runs)", "IA-2 (our new method)"],
    values: [V.good_b_hard, V.good_paper_hard, V.good_p_hard].map((x) => Math.round(x * 10) / 10) }], {
    x: 0.6, y: 1.45, w: 7.4, h: 5.3, barDir: "col", chartColors: [ORANGE, GREEN, BLUE], showLegend: false,
    showValue: true, dataLabelFontSize: 20, dataLabelColor: INK, dataLabelFormatCode: '0"%"', valAxisMaxVal: 40, valAxisLabelFontSize: 12,
    catAxisLabelFontSize: 15, valGridLine: { color: "E5E4DF", size: 0.5 }, catGridLine: { style: "none" }, barGapWidthPct: 55,
    showTitle: true, title: "% of runs that reach a Good solution, 6 hard instances", titleFontSize: 15, titleColor: MUTED });
  big(s, 8.4, 1.5, 4.3, `${V.spd_hard.toFixed(0)}×`, "faster to a Good solution (hard instances)", BLUE);
  card(s, 8.4, 3.95, 4.3, 2.75, "FFFFFF", LINE);
  T(s, [
    { text: `af-2:  ${pct(byI["af-2"].base_good)} → ${pct(byI["af-2"].prop_good)}`, options: { breakLine: true } },
    { text: `af-3:  ${pct(byI["af-3"].base_good)} → ${pct(byI["af-3"].prop_good)}`, options: { breakLine: true } },
    { text: `af-4:  ${pct(byI["af-4"].base_good)} → ${pct(byI["af-4"].prop_good)}`, options: { breakLine: true } },
    { text: `af-6-fs:  ${pct(byI["af-6-fs"].base_good)} → ${pct(byI["af-6-fs"].prop_good)}`, options: {} },
  ], { x: 8.6, y: 4.1, w: 3.9, h: 2.5, fontSize: 20, bold: true, color: NAVY, paraSpaceAfter: 6 });
}
// 11 ---------------------------------------------------------------- per instance
{
  const s = slide("CONTENT", "Result on every instance", "Results",
    "Easy instances (af-1, af-5, af-5-fs, af-7b-fs): both methods are near 100%. Hard ones: IA-2 is far ahead except af-6-f, which neither method solves.");
  const labels = CMP.map((r) => r.instance);
  s.addChart(pres.charts.BAR, [
    { name: "IA-1 (baseline)", labels, values: CMP.map((r) => r.base_good) },
    { name: "IA-2 (new method)", labels, values: CMP.map((r) => r.prop_good) },
    { name: "Paper", labels, values: CMP.map((r) => r.paper_good) },
  ], { x: 0.6, y: 1.4, w: 12.1, h: 4.6, barDir: "col", barGrouping: "clustered", barGapWidthPct: 50,
    chartColors: [ORANGE, BLUE, "B9C9B8"], showLegend: true, legendPos: "t", legendFontSize: 14, valAxisMaxVal: 100,
    catAxisLabelFontSize: 13, valAxisLabelFontSize: 12, valGridLine: { color: "E5E4DF", size: 0.5 }, catGridLine: { style: "none" },
    showValAxisTitle: true, valAxisTitle: "% Good runs", valAxisTitleFontSize: 13 });
  T(s, "Easy instances: both near 100%.   Hard instances: IA-2 far ahead, except af-6-f, which neither method solves.",
    { x: 0.6, y: 6.15, w: 12.1, h: 0.6, fontSize: 17, color: MUTED, align: "center" });
}
// 12 ---------------------------------------------------------------- reliability
{
  const s = slide("CONTENT", "Result: more reliable on all 11 instances", "Results",
    "Averages over all 11 instances and 60 runs per method. The difference is statistically significant (Fisher test, p < 0.01) on 5 instances.");
  big(s, 0.6, 1.6, 3.8, `${pct(V.feas_b)} → ${pct(V.feas_p)}`, "runs that end feasible (IA-1 → IA-2)", NAVY);
  big(s, 4.75, 1.6, 3.8, `${pct(V.good_b)} → ${pct(V.good_p)}`, "runs that are Good (IA-1 → IA-2)", NAVY);
  big(s, 8.9, 1.6, 3.8, "5 of 11", "instances where the gain is statistically significant", NAVY);
  card(s, 0.6, 4.2, 12.1, 2.4, "FFFFFF", LINE);
  T(s, [
    { text: "Why: ", options: { bold: true } },
    { text: "smart starts begin in better valleys, the LP polish turns 'almost valid' answers into valid ones, and learning from the best answer means later runs search near it instead of starting over.", options: {} },
  ], { x: 0.85, y: 4.4, w: 11.6, h: 2.0, fontSize: 20 });
}
// 13 ---------------------------------------------------------------- limits
{
  const s = slide("CONTENT", "Honest limits", "Conclusion",
    "Be upfront: af-6-f remains unsolved; on easy instances the extra LPs make IA-2 slower (up to about 2x); af-7 is slightly below the paper (18% vs 20%).");
  const L = [["af-6-f is not solved", "Neither method gets within 0.2% (the paper also only 4%)."],
    ["Easy problems get a bit slower", "The extra LPs cost time when random starts already work (up to ~2×)."],
    ["af-7 just below the paper", `IA-2 ${pct(byI["af-7"].prop_good)} vs paper 20% (IA-1 ${pct(byI["af-7"].base_good)}).`]];
  L.forEach(([h, b], k) => {
    const y = 1.6 + k * 1.7;
    card(s, 0.6, y, 12.1, 1.45);
    T(s, h, { x: 0.9, y: y + 0.15, w: 4.6, h: 1.15, bold: true, fontSize: 21, color: NAVY, valign: "middle" });
    T(s, b, { x: 5.6, y: y + 0.15, w: 6.9, h: 1.15, fontSize: 18, color: MUTED, valign: "middle" });
  });
}
// 14 ---------------------------------------------------------------- conclusion
{
  const s = slide("DARK", "Restarting smartly makes SLP find good feed recipes far more often", "Conclusion",
    "Summarise in one sentence and invite questions. Demo: Colab notebook from the GitHub repo.");
  s.addText([
    { text: `Same model and solver as IA-1, plus simple LPs: Good runs on hard problems ${pct(V.good_b_hard)} → ${pct(V.good_p_hard)}, feasible runs ${pct(V.feas_b)} → ${pct(V.feas_p)}, ${V.spd_hard.toFixed(0)}× faster to a Good answer.`, options: { breakLine: true } },
    { text: "Next: choose between smart starts and learning automatically; run the probes in parallel.", options: { breakLine: true } },
    { text: "Code and demo: GitHub repository + Google Colab notebook.   Thank you!", options: { bold: true } },
  ], { placeholder: "body" });
}
// 15 ---------------------------------------------------------------- references
{
  const s = slide("CONTENT", "References", "Conclusion");
  T(s, [
    "[1] A. Grothey, K. McKinnon, “On the effectiveness of sequential linear programming for the pooling problem,” Annals of Operations Research 322 (2023) 691–711.",
    "[2] A. Grothey, K. McKinnon, Pooling problem test data (2020).",
    "[3] C. A. Haverly, “Studies of the behavior of recursion for the pooling problem,” ACM SIGMAP Bulletin 25 (1978).",
    "[4] C. Audet et al., “Pooling problem: alternate formulations and solution methods,” Management Science 50 (2004) 761–776.",
    "[5] H. R. Lourenço et al., “Iterated local search,” Handbook of Metaheuristics (2019).",
    "[6] Group OPT-09, IA-1 report: SLP for nonlinear pooling optimization problems (2026).",
  ].map((t, j, a) => ({ text: t, options: { breakLine: j < a.length - 1 } })), { x: 0.6, y: 1.5, w: 12.1, h: 5.2, fontSize: 16, paraSpaceAfter: 10 });
}

(async () => {
  const out = path.join(__dirname, "Presentation.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("written");
})();
