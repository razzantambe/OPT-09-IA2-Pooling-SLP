#!/usr/bin/env python3
"""
run_all.py - runs the whole IA-2 experiment from scratch (Windows, Linux, Mac, Colab), then the analysis.

  python run_all.py --mode quick     # all 11 instances, IA-1 + IA-2, 1 seed x 5 runs          (~10-15 min, 2 cores)
  python run_all.py --mode seed      # all 11 instances, IA-1 + IA-2 + ablations, seed 12345 x 20 runs
                                     #   = exactly the seed-12345 runs of the paper           (~1.3 h)
  python run_all.py --mode full      # the paper's experiment: 3 seeds x 20 runs + ablations   (~3.5-4 h)

Options: --out DIR (default ../results_rerun), --jobs N (parallel processes, default 2), --instances ...
Results go to DIR/<method>/seed<s>/runs_<instance>_<group>.csv; then analyze_results.py builds
DIR/Result_Tables.xlsx, DIR/Comparison_Table.pdf and DIR/Graphs/*.png.
"""
import argparse
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ALL = ["af-1", "af-2", "af-3", "af-4", "af-5", "af-5-fs", "af-6-f", "af-6-fs", "af-7", "af-7b", "af-7b-fs"]
HEAVY = ["af-7b-fs", "af-6-fs", "af-7b"]          # long instances get their own task for load balancing


def tasks_for(mode, instances):
    seeds = [12345] if mode in ("quick", "seed") else [12345, 2024, 7]
    runs = 5 if mode == "quick" else 20
    methods = ["baseline", "proposed"] + ([] if mode == "quick" else ["abl_polish", "abl_rcstart"])
    heavy = [i for i in instances if i in HEAVY]
    light = [i for i in instances if i not in HEAVY]
    groups = ([("light", light)] if light else []) + [(h, [h]) for h in heavy]
    T = []
    for m in methods:
        for s in (seeds if m in ("baseline", "proposed") else [12345]):
            for g, ins in groups:
                T.append((m, s, g, ins, runs))
    # heaviest first
    T.sort(key=lambda t: (t[2] == "light", t[0].startswith("abl")))
    return T


def run_task(t, out, logdir):
    m, s, g, ins, runs = t
    od = os.path.join(out, m, f"seed{s}")
    os.makedirs(od, exist_ok=True)
    log = os.path.join(logdir, f"{m}_seed{s}_{g}.log")
    cmd = [sys.executable, "run_experiments.py", "--method", m, "--instances", *ins, "--runs", str(runs),
           "--seed", str(s), "--outdir", od, "--tag", g]
    t0 = time.time()
    with open(log, "w") as fh:
        rc = subprocess.run(cmd, cwd=HERE, stdout=fh, stderr=subprocess.STDOUT,
                            env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}).returncode
    last = open(log).read().strip().splitlines()
    tbl = [l for l in last if l.startswith("af-")]
    print(f"done  {m:11s} seed {s:<5d} {g:9s} {time.time() - t0:7.1f}s  rc={rc}", flush=True)
    for l in tbl:
        print("      " + l, flush=True)
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["quick", "seed", "full"], default="quick")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "results_rerun"))
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--instances", nargs="+", default=ALL)
    ap.add_argument("--no-analysis", action="store_true")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    logdir = os.path.join(out, "logs")
    os.makedirs(logdir, exist_ok=True)
    T = tasks_for(a.mode, a.instances)
    print(f"mode={a.mode}: {len(T)} tasks on {a.jobs} parallel processes -> {out}", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        rcs = list(ex.map(lambda t: run_task(t, out, logdir), T))
    print(f"all experiments finished in {(time.time() - t0) / 60:.1f} min; failures: {sum(r != 0 for r in rcs)}", flush=True)
    if not a.no_analysis:
        subprocess.run([sys.executable, "analyze_results.py", "--results", out], cwd=HERE, check=True)
        print(f"tables and graphs written to {out}", flush=True)


if __name__ == "__main__":
    main()
