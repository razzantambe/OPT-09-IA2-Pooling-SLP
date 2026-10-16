"""
rg_ils.py  -  IA-2 extension of our IA-1 filter-SLP code
==========================================================
Recipe-Guided Iterated Local Search around SLP  ("RG-ILS-SLP").

IA-1 (qq_model.py + slp.py, unchanged) solves the qq-formulation from RANDOM
starting points.  IA-2 keeps that SLP core exactly as it was and changes only
WHERE each SLP run starts and WHAT is done with its end point:

  Step 1  Diet relaxation (one small LP per product, bins ignored)
          -> ideal recipe q_p and unit cost c*_p of every product
          -> valid lower bound  LB = sum_p t_p c*_p   (no global solver needed)
  Step 2  Recipe-clustering start: weighted k-means++ on the recipes q_p
          (weights t_p * bin share, Dirichlet noise for diversity) gives M
          candidate bin compositions, projected onto the bin constraints.
  Step 3  LP repair: with the bins fixed the qq-constraints are LINEAR in the
          product fractions (product LP); with the bin shares mu_pm fixed they
          are LINEAR in (lambda, mu_pi) (bin LP).  Alternating the two elastic
          LPs drives the start to (near) feasibility.
  Step 4  Filter-SLP of IA-1 (FilterSLP.solve) from this start.
  Step 5  LP polish of the SLP end point (product LP, then bin LP; each is an
          exact LP, so the cost never increases and feasibility is exact).
  Step 6  Regret-guided iterated local search.  regret_p = t_p * max(0, c_p - c*_p)
          measures what bin sharing costs product p.  An ILS run builds 4 candidates:
          a bin (uniform) is pulled towards the ideal recipe of a product drawn with
          probability ~ regret,  lambda_m <- Proj((1-a) q_p + a lambda_m), a ~ U(0,0.5),
          plus multiplicative noise exp(0.05 xi) on all bins; each candidate is LP-repaired
          and probed with a 10-iteration SLP; the full SLP continues from the best probe.
          The first 3 runs, and any run after 6 ILS runs without improvement, use a fresh
          recipe-clustering start instead (diversification).

All quantities live in the scaled units of QQModel (attribute scaling of IA-1);
the variable vector x has exactly the IA-1 layout, so FilterSLP is reused as is.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, hstack, identity, vstack

from qq_model import QQModel
from slp import FilterSLP

PEN = 1e4            # penalty on (scaled) spec violation in the elastic LPs
LPOPT = dict(time_limit=30.0)


# ---------------------------------------------------------------------------
# helpers: proportions <-> IA-1 variable vector
# ---------------------------------------------------------------------------
def proportions(mod: QQModel, x):
    """(Lam (M,I), Mur (P,I), Mub (P,M)) read from an IA-1 variable vector."""
    Lam = np.zeros((mod.M, mod.I)); Mur = np.zeros((mod.P, mod.I)); Mub = np.zeros((mod.P, mod.M))
    s = mod.lam_var >= 0; Lam[s] = x[mod.lam_var[s]]
    s = mod.mur_var >= 0; Mur[s] = x[mod.mur_var[s]]
    s = mod.mub_var >= 0; Mub[s] = x[mod.mub_var[s]]
    return Lam, Mur, Mub


def assemble(mod: QQModel, Lam, Mur, Mub):
    """IA-1 variable vector from proportions; V and D computed EXACTLY (5b,5c,5f,5g)."""
    x = np.zeros(mod.n)
    s = mod.lam_var >= 0; x[mod.lam_var[s]] = Lam[s]
    s = mod.mur_var >= 0; x[mod.mur_var[s]] = Mur[s]
    s = mod.mub_var >= 0; x[mod.mub_var[s]] = Mub[s]
    V = Lam @ mod.R
    D = Mur @ mod.R + Mub @ V
    x[mod.V_var] = V
    x[mod.D_var] = D
    return np.clip(x, mod.lb, mod.ub)


def hinf(mod: QQModel, x):
    return mod.violation(x)[1]


def _tight_rows(A, lo, hi, tol=1e-12):
    """rows of a nutrient map that can actually bind (skip 'no bound' values like 999984)."""
    amax, amin = A.max(1), A.min(1)
    up = hi < amax - tol
    dn = lo > amin + tol
    return up, dn


# ---------------------------------------------------------------------------
# Step 1: diet relaxation
# ---------------------------------------------------------------------------
def diet_relaxation(mod: QQModel):
    R, N, P, I = mod.R, mod.N, mod.P, mod.I
    recipes_bin = np.zeros((P, I)); unit_cost = np.zeros(P); bin_share = np.zeros(P)
    ok = np.ones(P, bool)
    for k in range(P):
        bins = np.where(mod.mub_var[k] >= 0)[0]
        binable = np.where((mod.lam_var[bins] >= 0).any(0))[0] if len(bins) else np.array([], int)
        straight = np.where(mod.mur_var[k] >= 0)[0]
        cols = np.concatenate([binable, straight]).astype(int)
        nb = len(binable)
        if len(cols) == 0:
            ok[k] = False; continue
        Rc = R[cols]                                     # (nv, Q)
        c = Rc[:, N]
        dv = mod.D_var[k, :N]
        lo, hi = mod.lb[dv], mod.ub[dv]
        up, dn = _tight_rows(Rc[:, :N].T, lo, hi)
        A = [Rc[:, :N].T[up], -Rc[:, :N].T[dn]]; b = [hi[up], -lo[dn]]
        mb = mod.mub_var[k][bins]
        blo, bhi = float(mod.lb[mb].sum()), float(min(1.0, mod.ub[mb].sum()))
        if nb:
            row = np.concatenate([np.ones(nb), np.zeros(len(straight))])
            A += [row[None], -row[None]]; b += [[bhi], [-blo]]
        A = np.vstack(A); b = np.concatenate(b)
        mv = mod.mur_var[k][straight]
        bounds = [(0.0, bhi)] * nb + list(zip(mod.lb[mv], mod.ub[mv]))
        res = linprog(c, A_ub=A if len(b) else None, b_ub=b if len(b) else None,
                      A_eq=np.ones((1, len(cols))), b_eq=[1.0], bounds=bounds,
                      method="highs", options=LPOPT)
        if res.status != 0:
            ok[k] = False
            if nb:
                recipes_bin[k, binable] = 1.0 / nb
            continue
        w = res.x
        unit_cost[k] = res.fun * mod.attr_scale[N]
        sb = w[:nb].sum()
        bin_share[k] = sb
        if sb > 1e-9:
            recipes_bin[k, binable] = w[:nb] / sb
    LB = float(mod.tons @ unit_cost)
    return dict(recipes_bin=recipes_bin, unit_cost=unit_cost, bin_share=bin_share, LB=LB, ok=ok)


# ---------------------------------------------------------------------------
# bin projection (l1-closest bin compositions satisfying the bin constraints)
# ---------------------------------------------------------------------------
def project_bins(mod: QQModel, target):
    M, N = mod.M, mod.N
    Lam = np.zeros((M, mod.I))
    for m in range(M):
        ii = np.where(mod.lam_var[m] >= 0)[0]
        k = len(ii)
        t = target[m, ii]
        if t.sum() > 1e-12:
            t = t / t.sum()
        Rm = mod.R[ii, :N].T                               # (N, k)
        vv = mod.V_var[m, :N]
        up, dn = _tight_rows(Rm, mod.lb[vv], mod.ub[vv])
        A = [np.hstack([np.eye(k), -np.eye(k)]), np.hstack([-np.eye(k), -np.eye(k)])]
        b = [t, -t]
        if up.any():
            A.append(np.hstack([Rm[up], np.zeros((up.sum(), k))])); b.append(mod.ub[vv][up])
        if dn.any():
            A.append(np.hstack([-Rm[dn], np.zeros((dn.sum(), k))])); b.append(-mod.lb[vv][dn])
        lv = mod.lam_var[m, ii]
        bounds = list(zip(mod.lb[lv], mod.ub[lv])) + [(0, None)] * k
        res = linprog(np.concatenate([np.zeros(k), np.ones(k)]), A_ub=np.vstack(A), b_ub=np.concatenate(b),
                      A_eq=np.concatenate([np.ones(k), np.zeros(k)])[None], b_eq=[1.0],
                      bounds=bounds, method="highs", options=LPOPT)
        if res.status != 0:
            raise RuntimeError(f"bin {m}: no composition satisfies its bounds")
        Lam[m, ii] = res.x[:k]
    return Lam


# ---------------------------------------------------------------------------
# Step 3 / 5: the two exact LPs of the bilinear structure
# ---------------------------------------------------------------------------
def product_lp(mod: QQModel, Lam, elastic=False):
    """Bins (lambda) FIXED -> qq-constraints linear in mu.  The P product blocks are
    independent; they are stacked into ONE block-diagonal LP (one HiGHS call).
    Returns (x, total slack) or (None, inf)."""
    N = mod.N
    V = Lam @ mod.R
    ub_r, ub_c, ub_v, b_ub = [], [], [], []
    eq_r, eq_c = [], []
    cost, lo_b, hi_b, blocks = [], [], [], []
    nvar = 0
    for k in range(mod.P):
        js = np.where(mod.mur_var[k] >= 0)[0]; jb = np.where(mod.mub_var[k] >= 0)[0]
        comp = np.vstack([mod.R[js], V[jb]])               # (nv, Q)
        nv = len(js) + len(jb)
        c = comp[:, N]
        dv = mod.D_var[k, :N]
        lo, hi = mod.lb[dv], mod.ub[dv]
        CT = comp[:, :N].T
        up, dn = _tight_rows(CT, lo, hi)
        A = np.vstack([CT[up], -CT[dn]]); bb = np.concatenate([hi[up], -lo[dn]])
        vidx = np.concatenate([mod.mur_var[k][js], mod.mub_var[k][jb]])
        c0 = nvar
        blocks.append((k, js, jb, c0, nv))
        cost.append(c / max(1.0, np.abs(c).max()) if elastic else c * max(mod.tons[k], 1e-6))
        lo_b.append(mod.lb[vidx]); hi_b.append(mod.ub[vidx])
        nvar += nv
        ne = len(bb)
        r0 = len(b_ub)
        rr, cc = np.nonzero(A)
        ub_r += list(r0 + rr); ub_c += list(c0 + cc); ub_v += list(A[rr, cc])
        if elastic and ne:                                 # slack e >= 0 on every row
            ub_r += list(r0 + np.arange(ne)); ub_c += list(nvar + np.arange(ne)); ub_v += [-1.0] * ne
            cost.append(PEN * np.ones(ne)); lo_b.append(np.zeros(ne)); hi_b.append(np.full(ne, np.inf))
            nvar += ne
        b_ub += list(bb)
        eq_r += [k] * nv; eq_c += list(c0 + np.arange(nv))
    A_ub = coo_matrix((ub_v, (ub_r, ub_c)), shape=(len(b_ub), nvar)).tocsr() if b_ub else None
    A_eq = coo_matrix((np.ones(len(eq_r)), (eq_r, eq_c)), shape=(mod.P, nvar)).tocsr()
    res = linprog(np.concatenate(cost), A_ub=A_ub, b_ub=np.array(b_ub) if b_ub else None,
                  A_eq=A_eq, b_eq=np.ones(mod.P),
                  bounds=np.c_[np.concatenate(lo_b), np.concatenate(hi_b)], method="highs", options=LPOPT)
    if res.status != 0:
        return None, np.inf
    z = res.x
    Mur = np.zeros((mod.P, mod.I)); Mub = np.zeros((mod.P, mod.M))
    used = np.zeros(nvar, bool)
    for k, js, jb, c0, nv in blocks:
        Mur[k, js] = z[c0:c0 + len(js)]; Mub[k, jb] = z[c0 + len(js):c0 + nv]
        used[c0:c0 + nv] = True
    viol = float(z[~used].sum()) if elastic else 0.0
    return assemble(mod, Lam, Mur, Mub), viol


def bin_lp(mod: QQModel, x, elastic=False):
    """Bin shares mu_pm FIXED -> qq-constraints linear in (lambda, mu_pi): one LP.
    Returns (x, total slack) or (None, inf)."""
    N, M, P, R = mod.N, mod.M, mod.P, mod.R
    _, _, Mub = proportions(mod, x)
    lm, li = np.where(mod.lam_var >= 0)
    sp_, si = np.where(mod.mur_var >= 0)
    nl, ns = len(lm), len(sp_)
    nz = nl + ns
    # product nutrients: D[k,q] = sum_s R[si,q] mur_s + sum_l Mub[k,lm] R[li,q] lam_l
    rows, cols, vals = [], [], []
    for k in range(P):
        wk = Mub[k, lm]
        lsel = np.where(wk > 0)[0]
        ssel = np.where(sp_ == k)[0]
        for q in range(N):
            v1 = wk[lsel] * R[li[lsel], q]
            v2 = R[si[ssel], q]
            r = k * N + q
            rows += [r] * (len(lsel) + len(ssel))
            cols += list(lsel) + list(nl + ssel)
            vals += list(v1) + list(v2)
    Dm = coo_matrix((vals, (rows, cols)), shape=(P * N, nz)).tocsr()
    dlo, dhi = mod.lb[mod.D_var[:, :N]].ravel(), mod.ub[mod.D_var[:, :N]].ravel()
    # D and V are convex combinations of raw-material attributes, so a bound can only
    # bind if it lies strictly inside the attribute range (skips 'no bound' values)
    rmax = np.tile(R[:, :N].max(0), P); rmin = np.tile(R[:, :N].min(0), P)
    up_d, dn_d = dhi < rmax - 1e-12, dlo > rmin + 1e-12
    # bin nutrients V[m,q] = sum_l R[li,q] lam_l
    vr, vc, vv = [], [], []
    for m in range(M):
        sel = np.where(lm == m)[0]
        for q in range(N):
            vr += [m * N + q] * len(sel); vc += list(sel); vv += list(R[li[sel], q])
    Vm = coo_matrix((vv, (vr, vc)), shape=(M * N, nz)).tocsr()
    vlo, vhi = mod.lb[mod.V_var[:, :N]].ravel(), mod.ub[mod.V_var[:, :N]].ravel()
    up_v = vhi < np.tile(R[:, :N].max(0), M) - 1e-12
    dn_v = vlo > np.tile(R[:, :N].min(0), M) + 1e-12
    A_ub = vstack([Dm[up_d], -Dm[dn_d], Vm[up_v], -Vm[dn_v]]).tocsr()
    b_ub = np.concatenate([dhi[up_d], -dlo[dn_d], vhi[up_v], -vlo[dn_v]])
    # equalities: bin convexity, product convexity of the straights
    Er, Ec, be = [], [], []
    for m in range(M):
        sel = np.where(lm == m)[0]; Er += [len(be)] * len(sel); Ec += list(sel); be.append(1.0)
    for k in range(P):
        js = np.where(sp_ == k)[0]
        if len(js) == 0:
            continue
        Er += [len(be)] * len(js); Ec += list(nl + js); be.append(max(0.0, 1.0 - Mub[k].sum()))
    E = coo_matrix((np.ones(len(Er)), (Er, Ec)), shape=(len(be), nz)).tocsr()
    # cost: sum_k t_k D[k,N]
    cobj = np.zeros(nz)
    cobj[:nl] = (mod.tons @ Mub)[lm] * R[li, N]
    cobj[nl:] = mod.tons[sp_] * R[si, N]
    cobj = cobj / max(1.0, np.abs(cobj).max())
    bounds = list(zip(mod.lb[mod.lam_var[lm, li]], mod.ub[mod.lam_var[lm, li]])) + \
        list(zip(mod.lb[mod.mur_var[sp_, si]], mod.ub[mod.mur_var[sp_, si]]))
    if elastic:
        ne = A_ub.shape[0]
        A_ub = hstack([A_ub, -identity(ne)]).tocsr()
        E = hstack([E, csr_matrix((E.shape[0], ne))]).tocsr()
        cobj = np.concatenate([cobj, PEN * np.ones(ne)])
        bounds += [(0, None)] * ne
    res = linprog(cobj, A_ub=A_ub, b_ub=b_ub, A_eq=E, b_eq=np.array(be), bounds=bounds,
                  method="highs", options=LPOPT)
    if res.status != 0:
        return None, np.inf
    z = res.x
    Lam = np.zeros((M, mod.I)); Lam[lm, li] = z[:nl]
    Mur = np.zeros((P, mod.I)); Mur[sp_, si] = z[nl:nz]
    viol = float(z[nz:].sum()) if elastic else 0.0
    return assemble(mod, Lam, Mur, Mub), viol


def repair(mod: QQModel, Lam, max_alt=6):
    """Step 3: elastic product LP with the bins fixed; alternate with the elastic
    bin LP until the start is feasible (or max_alt rounds)."""
    x, viol = product_lp(mod, Lam, elastic=True)
    k = 0
    while x is not None and viol > 1e-7 and k < max_alt:
        xb, _ = bin_lp(mod, x, elastic=True)
        if xb is not None:
            x = xb
        x, viol = product_lp(mod, proportions(mod, x)[0], elastic=True)
        k += 1
    return x, viol


def polish(mod: QQModel, x, feas_tol=1e-6, rounds=2):
    """Step 5: exact-LP polish of an SLP end point; never returns a worse feasible point."""
    best = x
    best_f = mod.objective(x) if hinf(mod, x) <= feas_tol else np.inf
    cur = x
    if best_f == np.inf:                       # SLP ended infeasible: LP repair with its bins
        xr, vr = repair(mod, proportions(mod, x)[0])
        if xr is not None and hinf(mod, xr) <= feas_tol:
            best, best_f, cur = xr, mod.objective(xr), xr
    for _ in range(rounds):
        Lam = proportions(mod, cur)[0]
        xp, _ = product_lp(mod, Lam, elastic=False)
        if xp is None:
            break
        if hinf(mod, xp) <= feas_tol and mod.objective(xp) < best_f:
            best, best_f = xp, mod.objective(xp)
        xb, _ = bin_lp(mod, xp, elastic=False)
        if xb is not None and hinf(mod, xb) <= feas_tol and mod.objective(xb) < best_f - 1e-9:
            best, best_f = xb, mod.objective(xb)
            cur = xb
        else:
            break
    return best


# ---------------------------------------------------------------------------
# Step 2: recipe-clustering start
# ---------------------------------------------------------------------------
def weighted_kmeans(X, w, k, rng, iters=50):
    n = len(X)
    w = np.asarray(w, float) + 1e-9
    C = [X[rng.choice(n, p=w / w.sum())]]
    for _ in range(1, k):
        d2 = np.min(((X[:, None, :] - np.array(C)[None]) ** 2).sum(-1), axis=1)
        pr = w * d2
        C.append(X[rng.choice(n)] if pr.sum() <= 1e-15 else X[rng.choice(n, p=pr / pr.sum())])
    C = np.array(C)
    for _ in range(iters):
        lab = np.argmin(((X[:, None, :] - C[None]) ** 2).sum(-1), axis=1)
        newC = C.copy()
        for j in range(k):
            s = lab == j
            if s.any():
                newC[j] = (w[s, None] * X[s]).sum(0) / w[s].sum()
        if np.allclose(newC, C):
            break
        C = newC
    return C


class RecipeStarter:
    def __init__(self, mod: QQModel, noise=0.3):
        self.mod = mod
        self.diet = diet_relaxation(mod)
        self.noise = noise
        self.w = mod.tons * self.diet["bin_share"] + 1e-3 * max(mod.tons.mean(), 1e-9)

    def start(self, rng, max_alt=6):
        mod = self.mod
        Q = self.diet["recipes_bin"].copy()
        use = Q.sum(1) > 0
        Q, w = Q[use], self.w[use]
        if self.noise > 0:
            Z = rng.dirichlet(np.ones(Q.shape[1]), size=Q.shape[0])
            Q = (1 - self.noise) * Q + self.noise * (Z * (Q > 0) + 1e-12)
            Q /= Q.sum(1, keepdims=True)
        C = weighted_kmeans(Q, w, mod.M, rng)
        return repair(mod, project_bins(mod, C), max_alt)


# ---------------------------------------------------------------------------
# Step 6: regret-guided perturbation
# ---------------------------------------------------------------------------
def regret(mod: QQModel, x, diet):
    cD = x[mod.D_var[:, mod.N]] * mod.attr_scale[mod.N]
    return np.maximum(0.0, mod.tons * (cD - diet["unit_cost"]))


def recipe_guided_perturb(mod: QQModel, x, diet, rng, n_bins=1):
    """Re-seed `n_bins` (default 1) bins, chosen uniformly, with the ideal recipes of
    products drawn with probability proportional to their regret (+ small noise)."""
    Lam, _, Mub = proportions(mod, x)
    reg = regret(mod, x, diet) * (diet["recipes_bin"].sum(1) > 0) + 1e-9
    target = Lam.copy()
    bins = rng.choice(mod.M, size=min(n_bins, mod.M), replace=False, p=np.full(mod.M, 1.0 / mod.M))
    for m in bins:
        p = rng.choice(mod.P, p=reg / reg.sum())
        a = rng.uniform(0.0, 0.5)
        target[m] = (1 - a) * diet["recipes_bin"][p] + a * Lam[m]
    target *= np.exp(0.05 * rng.standard_normal(target.shape))
    target /= np.maximum(target.sum(1, keepdims=True), 1e-12)
    return project_bins(mod, target)


# ---------------------------------------------------------------------------
# the proposed method: one ILS chain of `runs` SLP solves
# ---------------------------------------------------------------------------
@dataclass
class RunRecord:
    run: int
    kind: str
    f: float
    viol_inf: float
    feasible: int
    iters: int
    lps: int
    time: float
    status: str
    f_slp: float
    start_viol: float
    incumbent: float


def solve_one(mod, solver: FilterSLP, x0, polish_rounds=2):
    res = solver.solve(x0)
    xb = polish(mod, res.x, rounds=polish_rounds) if polish_rounds > 0 else res.x
    return res, xb


def rg_ils(mod: QQModel, solver: FilterSLP, starter: RecipeStarter, rng, runs=20, log=None,
           patience=6, screen=4, probe_iter=10, polish_rounds=10, n_init=3):
    """ILS chain of `runs` runs.

    The first `n_init` runs (and any run after `patience` ILS runs without improving
    the incumbent) start from a fresh recipe-clustering start (diversification).  Every other run is an
    ILS step from the incumbent (intensification):
      - `screen` regret-guided perturbations are generated and LP-repaired;
      - each is probed with a SHORT filter-SLP (`probe_iter` iterations);
      - the full filter-SLP continues from the best probe (feasible first, then cost);
      - the end point is LP-polished.
    A short SLP ranks the candidates far better than the LP cost of the repaired
    point (which ignores what the SLP can still gain).
    """
    from dataclasses import replace
    probe = FilterSLP(mod, replace(solver.o, max_iter=probe_iter)) if screen > 1 else None
    diet = starter.diet
    recs = []
    inc_x, inc_f = None, np.inf
    stall = 0
    for k in range(runs):
        t0 = time.perf_counter()
        x0, v0, it_probe, lp_probe = None, np.nan, 0, 0
        if inc_x is None or k < n_init or stall >= patience:
            x0, v0 = starter.start(rng); kind = "rc"; stall = 0
        else:
            kind = "ils"
            best = None
            for _ in range(screen):
                try:
                    xc, vc = repair(mod, recipe_guided_perturb(mod, inc_x, diet, rng))
                except RuntimeError:
                    continue
                if xc is None:
                    continue
                if probe is not None:
                    pr = probe.solve(xc)
                    it_probe += pr.iters; lp_probe += pr.lps
                    key = (pr.hinf > solver.o.feas_tol, pr.f if pr.hinf <= solver.o.feas_tol else pr.hinf)
                    cand = (key, pr.x, vc)
                else:
                    cand = ((False, 0.0), xc, vc)
                if best is None or cand[0] < best[0]:
                    best = cand
            if best is not None:
                x0, v0 = best[1], best[2]
        if x0 is None:
            x0 = mod.random_start(rng); v0 = np.nan; kind = "rand"
        res, xb = solve_one(mod, solver, x0, polish_rounds)
        f, h = mod.objective(xb), hinf(mod, xb)
        feas = h <= solver.o.feas_tol
        if feas and f < inc_f * (1 - 1e-7):
            inc_x, inc_f = xb.copy(), f
            stall = 0
        elif kind == "ils":
            stall += 1
        rec = RunRecord(k, kind, f, h, int(feas), res.iters + it_probe, res.lps + lp_probe,
                        time.perf_counter() - t0, res.status, res.f, float(v0), inc_f)
        recs.append(rec)
        if log:
            log(rec)
    return recs, inc_x
