// build_paper.js - IA-2 research paper draft (follows the course template section by section)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Footer, AlignmentType,
  WidthType, BorderStyle, ShadingType, LevelFormat, HeadingLevel, PageNumber, TabStopType,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const D = JSON.parse(fs.readFileSync(path.join(__dirname, "paper_data.json"), "utf8"));
const T = JSON.parse(fs.readFileSync(path.join(__dirname, "paper_text.json"), "utf8"));
const G = D.group;

const BODY = "Times New Roman", HEAD = "Calibri", BLUE = "2E74B5", BLUE2 = "4F81BD";
const PAGE_W = 12240, MARG = 1300, CW = PAGE_W - 2 * MARG;   // content width (DXA)

// ---------- inline markup:  **bold**  _italic_  ^sup^  ~sub~ ----------
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|(?<![A-Za-z0-9])_[^_]+_(?![A-Za-z0-9])|\^[^^]+\^|~[^~]+~)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else if (t.startsWith("_")) out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    else if (t.startsWith("^")) out.push(new TextRun({ text: t.slice(1, -1), superScript: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), subScript: true, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}
const P = (text, opt = {}) => new Paragraph({
  children: runs(text, opt.run || {}), alignment: opt.align || AlignmentType.JUSTIFIED,
  spacing: { after: opt.after ?? 120, before: opt.before ?? 0, line: 264 }, indent: opt.indent,
  keepNext: opt.keepNext,
});
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)], spacing: { before: 280, after: 120 }, keepNext: true });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)], spacing: { before: 200, after: 80 }, keepNext: true });
const BUL = (t, lvl = 0) => new Paragraph({ numbering: { reference: "bul", level: lvl }, children: runs(t), spacing: { after: 60, line: 260 }, alignment: AlignmentType.JUSTIFIED });
const NUM = (t, ref = "num") => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(t), spacing: { after: 60, line: 260 }, alignment: AlignmentType.JUSTIFIED });
const EQ = (t, tag) => new Paragraph({
  alignment: AlignmentType.LEFT, spacing: { after: 60, before: 40 }, indent: { left: 500 },
  tabStops: [{ type: TabStopType.RIGHT, position: CW - 100 }],
  children: [...runs(t, { font: "Cambria Math", size: 21 }), ...(tag ? [new TextRun({ text: "\t(" + tag + ")", size: 21 })] : [])],
});
const CAP = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 }, children: runs(t, { size: 19, italics: false }) });
const CODE = (lines) => lines.map((l, i) => new Paragraph({
  spacing: { after: 0, line: 240 }, shading: { type: ShadingType.CLEAR, color: "auto", fill: "F4F4F2" },
  indent: { left: 200, right: 200 },
  children: [new TextRun({ text: l.length ? l : " ", font: "Consolas", size: 15 })],
}));
function IMG(file, wInches, caption) {
  const buf = fs.readFileSync(file);
  // read PNG size
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  const W = wInches * 96, H = W * h / w;
  return [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 }, keepNext: true,
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: W, height: H },
      altText: { title: caption, description: caption, name: path.basename(file) } })] }), CAP(caption)];
}
const border = { style: BorderStyle.SINGLE, size: 4, color: "8A8984" };
const borders = { top: border, bottom: border, left: border, right: border };
function TABLE(header, rows, widthsRel, opt = {}) {
  const tot = widthsRel.reduce((a, b) => a + b, 0);
  const widths = widthsRel.map((w) => Math.floor(CW * w / tot));
  widths[widths.length - 1] += CW - widths.reduce((a, b) => a + b, 0);
  const size = opt.size || 18;
  const cell = (t, i, hdr, shade) => new TableCell({
    borders, width: { size: widths[i], type: WidthType.DXA },
    shading: hdr ? { fill: "DCE6F2", type: ShadingType.CLEAR, color: "auto" } : (shade ? { fill: shade, type: ShadingType.CLEAR, color: "auto" } : undefined),
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    children: String(t).split("\n").map((line) => new Paragraph({
      alignment: (i === 0 || opt.left) ? AlignmentType.LEFT : AlignmentType.CENTER, spacing: { after: 0, line: 240 },
      children: runs(line, { size, bold: hdr ? true : undefined }) })),
  });
  const trs = [];
  if (header) trs.push(new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, i, true)) }));
  rows.forEach((r, k) => trs.push(new TableRow({ children: r.map((c, i) => cell(c, i, false, opt.hl && opt.hl(k, i) ? "EAF2FC" : null)) })));
  return new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: widths, rows: trs });
}
const TCAP = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 60 }, keepNext: true, children: runs(t, { size: 19, bold: true }) });
const SP = () => new Paragraph({ spacing: { after: 60 }, children: [] });

// ---------------------------------------------------------------- content
const C = [];
C.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new TextRun({ text: "INTRODUCTION TO OPTIMIZATION TECHNIQUES", bold: true, size: 24 })] }));
C.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new TextRun({ text: "IA-2 RESEARCH PAPER DRAFT", bold: true, size: 30, color: "C00000" })] }));
C.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: "Research Gap, Proposed Methodology, Experimental Evaluation & Results", italics: true, size: 21 })] }));
C.push(TABLE(null, [["Group ID", G.id], ["Student 1", G.s1], ["Student 2", G.s2], ["Student 3", G.s3], ["Research Title", T.title]], [32, 68], { left: true, size: 20 }));
C.push(P("**Note:** IA-2 extends our IA-1 work [15]: the IA-1 files qq_model.py and slp.py (re-implementation of Grothey & McKinnon, 2023) are used **unchanged** as the baseline, and the proposed method is a new module (rg_ils.py) built on top of them.", { before: 160 }));

C.push(H1("Abstract"));
T.abstract.forEach((p) => C.push(P(p)));
C.push(P("**Keywords:** " + T.keywords));

C.push(H1("1. Introduction"));
T.intro.forEach((p) => C.push(P(p)));
C.push(H2("1.1 Problem Context and Motivation"));
T.motivation.forEach((p) => C.push(P(p)));
C.push(H2("1.2 Objectives"));
T.objectives.forEach((p) => C.push(NUM(p, "obj")));
C.push(H2("1.3 Contributions of the Work"));
T.contributions.forEach((p) => C.push(BUL(p)));

C.push(H1("2. Related Work"));
T.related_intro.forEach((p) => C.push(P(p)));
C.push(H2("2.1 Selected Baseline Paper"));
T.baseline_paper.forEach((p) => C.push(P(p)));
C.push(H2("2.2 Comparison with Existing Approaches"));
C.push(P(T.comparison_lead));
C.push(TCAP("Table 1. Comparison of approaches relevant to the identified gap"));
C.push(TABLE(["Work", "Formulation / algorithm", "Computational cost", "Solution quality", "Relevance to this work"], T.related_table, [16, 24, 18, 20, 22], { size: 16, left: true }));

C.push(H1("3. Research Gap & Team Contribution"));
C.push(P(T.gap_lead));
C.push(H2("3.1 Identified Research Gap"));
T.gap.forEach((p) => C.push(P(p)));
C.push(TCAP("Table 2. Evidence for the gap: published SLP-CPLEX [1] vs our IA-1 code (IA-1 notebook, 20 runs, seed 12345)"));
C.push(TABLE(["Instance", "Paper %Feas", "Paper %Good", "Paper ETiGood (s)", "IA-1 %Feas", "IA-1 %Good", "IA-1 It"], D.gap_rows, [14, 14, 14, 15, 13, 13, 13]));
T.gap_after.forEach((p) => C.push(P(p, { before: 120 })));
C.push(H2("3.2 Problem Statement"));
T.problem_statement.forEach((p) => C.push(P(p)));
C.push(H2("3.3 Team's Proposed Contribution"));
T.team_contribution.forEach((p) => C.push(P(p)));
C.push(TCAP("Table 3. What is retained, modified and newly introduced"));
C.push(TABLE(["Component", "Baseline (paper [1] / our IA-1 code)", "Proposed (IA-2)", "Status"], T.diff_table, [16, 30, 38, 16], { size: 17, left: true }));

C.push(H1("4. Proposed Methodology"));
T.method_lead.forEach((p) => C.push(P(p)));
C.push(H2("4.1 Proposed Optimization Formulation"));
T.form_sets.forEach((p) => C.push(P(p)));
C.push(P("**(a) Original problem — qq-formulation (retained unchanged, IA-1 qq_model.py).**", { keepNext: true }));
T.eq_qq.forEach(([e, t]) => C.push(EQ(e, t)));
T.form_after_qq.forEach((p) => C.push(P(p)));
C.push(P("**(b) Diet relaxation (new) — ideal recipe and lower bound.** For every product p, sharing of bins is relaxed: the product may draw any bin-eligible raw material directly at bin cost.", { keepNext: true }));
T.eq_diet.forEach(([e, t]) => C.push(EQ(e, t)));
T.form_after_diet.forEach((p) => C.push(P(p)));
C.push(P("**(c) Product LP with bins fixed (new).** For fixed λ̄, v and c^M^ are constants, so (5c) and (5g) become linear:", { keepNext: true }));
T.eq_plp.forEach(([e, t]) => C.push(EQ(e, t)));
C.push(P("**(d) Bin LP with bin shares fixed (new).** For fixed μ̄^B^, substituting (5b) into (5c) gives d linear in (λ, μ^S^):", { keepNext: true }));
T.eq_blp.forEach(([e, t]) => C.push(EQ(e, t)));
C.push(P("**(e) Recipe regret and guided perturbation (new).**", { keepNext: true }));
T.eq_reg.forEach(([e, t]) => C.push(EQ(e, t)));
T.form_after_reg.forEach((p) => C.push(P(p)));

C.push(H2("4.2 Proposed Algorithm / Method"));
T.algo_steps.forEach((p) => C.push(NUM(p, "steps")));
T.algo_after.forEach((p) => C.push(P(p, { before: 80 })));
C.push(H2("4.3 Methodology Flowchart"));
IMG(path.join(ROOT, "results/Graphs/fig_flowchart.png"), 5.2, "Figure 1. Methodology flowchart: IA-1 model and solver (grey, unchanged), identified limitation (orange) and the proposed RG-ILS-SLP loop (blue = new).").forEach((x) => C.push(x));
C.push(H2("4.4 Algorithm / Pseudocode"));
C.push(P("**Algorithm 1 — RG-ILS-SLP (proposed).**", { keepNext: true }));
CODE(T.pseudo).forEach((x) => C.push(x));
C.push(P("**Algorithm 2 — Filter-SLP core (IA-1 slp.py, retained unchanged).**", { keepNext: true, before: 160 }));
CODE(T.pseudo_slp).forEach((x) => C.push(x));

C.push(H1("5. Implementation & Experimental Evaluation"));
T.impl_lead.forEach((p) => C.push(P(p)));
C.push(H2("5.1 Implementation Environment"));
C.push(TCAP("Table 4. Implementation environment"));
C.push(TABLE(["Item", "Details"], T.env_table, [26, 74], { left: true, size: 18 }));
C.push(H2("5.2 Dataset / Problem Instances"));
T.dataset.forEach((p) => C.push(P(p)));
C.push(TCAP("Table 5. Test instances (sizes of the qq-model built by the IA-1 code) and lower bounds"));
C.push(TABLE(["Instance", "N", "I", "M", "P", "n (vars)", "m (cons)", "Best known [1]", "Diet LB (ours)", "Baron LB [1]", "Diet gap %"], D.inst_rows, [12, 5, 5, 5, 5, 8, 8, 14, 13, 13, 9], { size: 16 }));
T.dataset_after.forEach((p) => C.push(P(p, { before: 120 })));
C.push(H2("5.3 Experimental Design"));
T.design.forEach((p) => C.push(P(p)));
C.push(TCAP("Table 6. Experimental design"));
C.push(TABLE(["Experiment", "Method", "Parameters", "Metric(s)", "Purpose"], T.design_table, [16, 20, 24, 18, 22], { size: 16, left: true }));
C.push(H2("5.4 Implementation Evidence"));
T.evidence.forEach((p) => C.push(P(p)));
C.push(P("**Listing 1.** Product LP with the bins fixed, built on the IA-1 variable indexing (rg_ils.py, abridged).", { keepNext: true }));
CODE(T.code1).forEach((x) => C.push(x));
C.push(P("**Listing 2.** Regret-guided perturbation of the incumbent (rg_ils.py).", { keepNext: true, before: 160 }));
CODE(T.code2).forEach((x) => C.push(x));
C.push(P("**Listing 3.** Console output (excerpt) of the proposed method on af-4, seed 12345 (rc = recipe start, ils = probed ILS run).", { keepNext: true, before: 160 }));
CODE(D.console).forEach((x) => C.push(x));

C.push(H1("6. Results, Comparison & Discussion"));
T.res_lead.forEach((p) => C.push(P(p)));
C.push(H2("6.1 Results of IA-1 (Baseline Method)"));
T.res_base.forEach((p) => C.push(P(p)));
C.push(TCAP("Table 7. IA-1 results (baseline: our IA-1 code, random-multistart filter-SLP), 3 seeds × 20 runs per instance"));
C.push(TABLE(["Instance", "Ti (s)", "%Feas", "%Good (mean ± sd over seeds)", "It", "ETiGood (s)", "Best f", "Best gap %"], D.base_rows, [11, 9, 9, 17, 8, 11, 19, 12], { size: 17 }));
C.push(H2("6.2 Results of IA-2 (Proposed Method)"));
T.res_prop.forEach((p) => C.push(P(p)));
C.push(TCAP("Table 8. IA-2 results (proposed RG-ILS-SLP), 3 seeds × 20 runs per instance"));
C.push(TABLE(["Instance", "Ti (s)", "%Feas", "%Good (mean ± sd over seeds)", "It", "ETiGood (s)", "Best f", "Best gap %"], D.prop_rows, [11, 9, 9, 17, 8, 11, 19, 12], { size: 17 }));
C.push(H2("6.3 Comparison: IA-1 (Baseline) vs IA-2 (Proposed)"));
T.res_cmp.forEach((p) => C.push(P(p)));
C.push(TCAP("Table 9. IA-1 vs IA-2: what changed and what it achieved (results pooled over 11 instances × 3 seeds × 20 runs)"));
C.push(TABLE(["Aspect / metric", "IA-1 (baseline)", "IA-2 (proposed)", "Change", "Observation"], D.cmp_rows, [19, 17, 19, 14, 31], { size: 16, hl: (k, i) => i === 2 }));
C.push(TCAP("Table 10. Per instance: published SLP-CPLEX [1] vs IA-1 vs IA-2 (%Good and ETiGood in s; IA-1 and IA-2 pooled over 3 × 20 runs)"));
C.push(TABLE(["Instance", "Paper %Good", "IA-1 %Good", "IA-2 %Good", "Paper ETiGood", "IA-1 ETiGood", "IA-2 ETiGood"], D.paper_rows, [13, 14, 14, 14, 15, 15, 15], { size: 16, hl: (k, i) => i === 3 || i === 6 }));
T.res_cmp_after.forEach((p) => C.push(P(p, { before: 120 })));
C.push(H2("6.4 Statistical / Repeated-Run Analysis"));
T.res_stats.forEach((p) => C.push(P(p)));
C.push(TCAP("Table 11. One-sided tests, IA-2 better than IA-1 (60 vs 60 runs per instance)"));
C.push(TABLE(["Instance", "Good IA-1", "Good IA-2", "p Fisher", "Feas IA-1", "Feas IA-2", "p Fisher", "Median gap IA-1 %", "Median gap IA-2 %", "p Mann–Whitney"], D.stat_rows, [10, 8, 8, 10, 8, 8, 10, 13, 13, 12], { size: 15 }));
C.push(H2("6.5 Graphical Results"));
IMG(path.join(ROOT, "results/Graphs/fig_pct_good.png"), 6.2, "Figure 2. %Good per instance: paper SLP-CPLEX (500 runs), IA-1 (baseline) and IA-2 (proposed) (3 × 20 runs; error bars = sd over seeds).").forEach((x) => C.push(x));
IMG(path.join(ROOT, "results/Graphs/fig_etigood.png"), 6.2, "Figure 3. Expected time to a Good solution, paper vs IA-1 vs IA-2 (log scale; bars at the top of the axis mean no Good solution found).").forEach((x) => C.push(x));
IMG(path.join(ROOT, "results/Graphs/fig_convergence.png"), 6.4, "Figure 4. IA-1 vs IA-2: best gap to the best known value against cumulative time on the six hard instances (one line per seed).").forEach((x) => C.push(x));
IMG(path.join(ROOT, "results/Graphs/fig_gaps.png"), 6.2, "Figure 5. IA-1 vs IA-2: final gap of every feasible run (log scale); dashed line = 0.2% Good threshold.").forEach((x) => C.push(x));
IMG(path.join(ROOT, "results/Graphs/fig_pct_feas.png"), 6.2, "Figure 6. %Feas per instance: paper vs IA-1 vs IA-2.").forEach((x) => C.push(x));
IMG(path.join(ROOT, "results/Graphs/fig_ablation.png"), 6.0, "Figure 7. Ablation (seed 12345, 20 runs each): %Feas and %Good of IA-1, the two partial IA-2 variants and the full IA-2 method.").forEach((x) => C.push(x));
C.push(TCAP("Table 12. Ablation, seed 12345: %Feas / %Good over 20 runs"));
C.push(TABLE(["Instance", "IA-1 (baseline)", "A: random start + polish", "B: recipe start + polish, no ILS", "IA-2 full (RG-ILS-SLP)"], D.abl_rows, [14, 18, 22, 26, 20], { size: 17, hl: (k, i) => i === 4 }));
C.push(H2("6.6 Discussion"));
T.discussion.forEach((p) => C.push(P(p)));

C.push(H1("7. Conclusion and Future Scope"));
T.conclusion.forEach((p) => C.push(P(p)));
C.push(H2("7.1 Future Scope"));
T.future.forEach((p) => C.push(BUL(p)));

C.push(H1("References"));
T.refs.forEach((r, i) => C.push(new Paragraph({ spacing: { after: 80, line: 250 }, indent: { left: 440, hanging: 440 }, alignment: AlignmentType.LEFT, children: runs(`[${i + 1}]\t${r}`, { size: 20 }), tabStops: [{ type: TabStopType.LEFT, position: 440 }] })));

C.push(H1("Appendix A – Additional Experimental Results"));
T.appA.forEach((p) => C.push(P(p)));
C.push(TCAP("Table A1. %Feas / %Good per seed, and objective over feasible runs"));
C.push(TABLE(["Instance", "Method", "seed 12345", "seed 2024", "seed 7", "Mean f ± sd", "Worst f"], D.seed_rows, [11, 12, 12, 12, 12, 24, 17], { size: 16 }));
C.push(TCAP("Table A2. Further metrics (pooled over 3 seeds)"));
C.push(TABLE(["Instance", "Method", "Ti", "%Feas", "%Good", "%Good range", "It", "ETiGood", "Time to 1st Good (s)", "Median gap %"], D.full_rows, [10, 13, 7, 8, 8, 9, 8, 10, 13, 11], { size: 15 }));
C.push(TCAP("Table A3. Bin compositions (% of each raw material) of the best af-3 solution of IA-2 (f = " + D.bins_f.toFixed(2) + ")"));
C.push(TABLE(D.bins_header, D.bins_rows, D.bins_header.map(() => 1), { size: 15 }));
C.push(H1("Appendix B – Source Code / Supporting Material"));
T.appB.forEach((p) => C.push(P(p)));
CODE(T.folder).forEach((x) => C.push(x));

// ---------------------------------------------------------------- document
const doc = new Document({
  creator: "IA-2 team", title: T.title,
  styles: {
    default: { document: { run: { font: BODY, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true, font: HEAD, color: BLUE }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 25, bold: true, font: HEAD, color: BLUE2 }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 340 } } } }] },
    { reference: "obj", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "O%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 600, hanging: 440 } } } }] },
    { reference: "steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "Step %1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 900, hanging: 800 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1200, bottom: 1200, left: MARG, right: MARG } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: "IA-2 | Introduction to Optimization Techniques | Research Paper Draft   |   Page ", size: 18 }),
      new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
    children: C,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(path.join(__dirname, "Research_Paper_Draft.docx"), b); console.log("written"); });
