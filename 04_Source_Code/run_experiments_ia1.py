#!/usr/bin/env python3
"""
run_experiments.py - random-multistart experiment for filter-SLP on the qq-formulation.

Reproduces the protocol behind Tables 2/4/5 of Grothey & McKinnon (2023) for the
SLP-CPLEX column (here: HiGHS instead of CPLEX):

  * N random starting points per instance (paper: 500)
  * a run is FEASIBLE  if the final max constraint violation < 1e-6
  * a run is GOOD      if feasible and objective within 0.2 % of the best known value
  * Ti = mean time/run [s], It = mean #SLP iterations/run, ETiGood = 100*Ti/%Good

Usage
-----
  python run_experiments.py --instances af-1 af-2 --runs 500 --start simplex
  python run_experiments.py --instances af-1 --runs 50 --start box --tag test
"""
import argparse
import csv
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from qq_model import QQModel, load_instance          # noqa: E402
from slp import FilterSLP, SLPOptions                 # noqa: E402

# Table 1 of the paper: best known objective from any method
BEST_KNOWN = {
    "af-1": 296.44604, "af-2": 239334.02, "af-3": 122257.45, "af-4": 186097.11,
    "af-5-fs": 119016.92, "af-5": 124003.48, "af-6-fs": 2921.30, "af-6": 3074.23,
    "af-7b-fs": 130290.06, "af-7": 151381.81, "af-7b": 147285.00,
}
# Tables 2 / 4 (SLP-CPLEX, 500 runs): Ti [s], %Feas, %Good, It
PAPER = {
    "af-1": dict(Ti=0.5, feas=100.0, good=79.0, It=38.0),
    "af-2": dict(Ti=1.3, feas=100.0, good=19.4, It=58.7),
    "af-3": dict(Ti=1.3, feas=99.2, good=20.0, It=50.6),
    "af-4": dict(Ti=1.7, feas=98.5, good=19.8, It=49.1),
    "af-5-fs": dict(Ti=1.7, feas=100.0, good=99.6, It=61.2),
    "af-5": dict(Ti=1.5, feas=99.8, good=100.0, It=53.9),
    "af-6-fs": dict(Ti=6.5, feas=95.0, good=5.2, It=47.0),
    "af-6": dict(Ti=4.5, feas=78.4, good=4.0, It=47.7),
    "af-7b-fs": dict(Ti=14.7, feas=99.0, good=52.6, It=48.5),
    "af-7": dict(Ti=4.6, feas=99.0, good=20.4, It=61.5),
    "af-7b": dict(Ti=12.3, feas=98.8, good=71.8, It=72.0),
}
GOOD_TOL = 0.002          # 0.2 %
 
GOOD_TOL = 0.002          # 0.2 %


def random_start_box(mod: QQModel, rng):
    """Alternative start distribution: every variable uniform in its (tightened) box."""
    return mod.lb + rng.random(mod.n) * (mod.ub - mod.lb)


def run_instance(name, runs, seed, start, opts, verbose=True):
    inst = load_instance(os.path.join(HERE, "data", name + ".txt"))
    mod = QQModel(inst)
    solver = FilterSLP(mod, opts)
    rng = np.random.default_rng(seed)
    best_known = BEST_KNOWN[name]
    rows, best = [], None
    t_start = time.perf_counter()
    for r in range(runs):
        x0 = mod.random_start(rng) if start == "simplex" else random_start_box(mod, rng)
        res = solver.solve(x0)
        good = res.feasible and res.f <= best_known * (1.0 + GOOD_TOL)
        rows.append(dict(instance=name, run=r, f=res.f, viol_inf=res.hinf, feasible=int(res.feasible),
                         good=int(good), iters=res.iters, lps=res.lps, time=res.time, status=res.status))
        if res.feasible and (best is None or res.f < best[0]):
            best = (res.f, res.x.copy())
        if verbose and (r + 1) % max(1, runs // 10) == 0:
            g = 100.0 * np.mean([q["good"] for q in rows])
            print(f"  [{name}] {r + 1:4d}/{runs}  %Good so far {g:5.1f}   best f {best[0] if best else float('nan'):.5f}"
                  f"   elapsed {time.perf_counter() - t_start:6.1f}s", flush=True)
    return mod, rows, best


def summarize(name, rows):
    a = lambda k: np.array([q[k] for q in rows], float)
    feas, good = 100 * a("feasible").mean(), 100 * a("good").mean()
    Ti, It = a("time").mean(), a("iters").mean()
    ffeas = a("f")[a("feasible") == 1]
    return dict(instance=name, runs=len(rows), Ti=Ti, feas=feas, good=good, It=It,
                ETiGood=(100 * Ti / good) if good > 0 else float("inf"),
                best=float(ffeas.min()) if len(ffeas) else float("nan"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", nargs="+", default=["af-1", "af-2", "af-3", "af-4"])
    ap.add_argument("--runs", type=int, default=500)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--start", choices=["simplex", "box"], default="simplex")
    ap.add_argument("--rho0", type=float, default=None)
    ap.add_argument("--backend", choices=["highs", "scipy"], default="highs")
    ap.add_argument("--tag", default="")
    ap.add_argument("--outdir", default=os.path.join(HERE, "results"))
    a = ap.parse_args()

    opts = SLPOptions(backend=a.backend)
    if a.rho0 is not None:
        opts.rho0 = a.rho0
    os.makedirs(a.outdir, exist_ok=True)
    tag = f"_{a.tag}" if a.tag else ""

    summaries = []
    for nm in a.instances:
        print(f"== {nm}: {a.runs} runs, start={a.start}, seed={a.seed}", flush=True)
        mod, rows, best = run_instance(nm, a.runs, a.seed, a.start, opts)
        with open(os.path.join(a.outdir, f"runs_{nm}{tag}.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        if best is not None:
            np.save(os.path.join(a.outdir, f"best_x_{nm}{tag}.npy"), best[1])
        summaries.append(summarize(nm, rows))

    hdr = f"{'Instance':9s}{'Ti[s]':>8s}{'%Feas':>8s}{'%Good':>8s}{'It':>8s}{'ETiGood':>9s}{'best f':>14s}  |" \
          f"{'paper Ti':>9s}{'%Feas':>7s}{'%Good':>7s}{'It':>7s}"
    lines = [hdr, "-" * len(hdr)]
    for s in summaries:
        p = PAPER[s["instance"]]
        lines.append(f"{s['instance']:9s}{s['Ti']:8.2f}{s['feas']:8.1f}{s['good']:8.1f}{s['It']:8.1f}"
                     f"{s['ETiGood']:9.1f}{s['best']:14.5f}  |{p['Ti']:9.1f}{p['feas']:7.1f}{p['good']:7.1f}{p['It']:7.1f}")
    table = "\n".join(lines)
    print("\n" + table)
    with open(os.path.join(a.outdir, f"summary{tag}.txt"), "w") as fh:
        fh.write(f"runs={a.runs} start={a.start} seed={a.seed} rho0={opts.rho0} backend={a.backend}\n{table}\n")


if __name__ == "__main__":
    main()
