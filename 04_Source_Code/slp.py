"""
slp.py
======
Filter-based Sequential Linear Programming (SLP) with trust region, as used in
Section 4/5 of Grothey & McKinnon (2023) - but with HiGHS instead of CPLEX.

Algorithm (one outer iteration, current iterate x with h = ||c(x)||_1, f = obj):

  1. Solve the trust-region LP   min c'x  s.t. linearised constraints,
     bounds, ||(x_new - x)/width||_inf <= rho.        (eq. (10) of the paper)
  2. If the LP is infeasible -> feasibility restoration: solve the elastic LP
     that minimises the l1 norm of the linearised violation in the same TR.
  3. Evaluate the true (h+, f+) at the trial point and test it against the
     filter (Fletcher & Leyffer 2002):
         accept  <=>  for all (h_j,f_j) in filter:  h+ <= beta*h_j  or  f+ <= f_j - gamma*h+
     plus, for "f-type" steps (predicted reduction dq >= delta*h^2), an Armijo
     type condition  f - f+ >= sigma*dq.  "h-type" steps put (h,f) into the filter.
  4. accept -> move (and enlarge rho if the step hit the boundary);
     reject -> shrink rho.  Stop when the LP step vanishes / rho collapses.

LP subproblems are hot-started from the previous optimal basis (the paper does
the same with CPLEX primal simplex + hotstart).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import numpy as np
import scipy.sparse as sp

from qq_model import QQModel

# ------------------------------------------------------------------------
# LP back-ends
# ------------------------------------------------------------------------
try:                                     # bundled with scipy >= 1.15
    import scipy.optimize._highspy._core as _hcore
    HAVE_DIRECT_HIGHS = True
except Exception:                        # pragma: no cover
    HAVE_DIRECT_HIGHS = False


class HighsWarmLP:
    """LP  min c'x, A x = b (rows equal), l <= x <= u  with basis warm start."""

    def __init__(self, indptr, indices, n_rows, n_cols):
        self.indptr, self.indices = indptr, indices
        self.m, self.n = n_rows, n_cols
        self.h = _hcore._Highs()
        self.h.setOptionValue("output_flag", False)
        self.h.setOptionValue("primal_feasibility_tolerance", 1e-9)
        # NB: dual_feasibility_tolerance is left at its default 1e-7.  Setting it to 1e-9
        # makes HiGHS' dual simplex return kError on some SLP subproblems, and the
        # primal simplex (strategy 4) that avoids this is ~10x slower here.
        self.h.setOptionValue("presolve", "off")     # keep the basis meaningful
        self.h.setOptionValue("threads", 1)
        self.lp_time_limit = 3.0                     # per LP; guards against stalled warm starts
        self.basis = None
        self.n_lp = 0
        self.n_simplex = 0
        self.n_cold_retry = 0

    def reset_basis(self):
        self.basis = None

    def solve(self, cost, lo, hi, rhs, data):
        lp = _hcore.HighsLp()
        lp.num_col_, lp.num_row_ = self.n, self.m
        lp.col_cost_, lp.col_lower_, lp.col_upper_ = cost, lo, hi
        lp.row_lower_, lp.row_upper_ = rhs, rhs
        lp.a_matrix_.format_ = _hcore.MatrixFormat.kColwise
        lp.a_matrix_.start_ = self.indptr
        lp.a_matrix_.index_ = self.indices
        lp.a_matrix_.value_ = data
        h = self.h
        h.passModel(lp)
        warm = self.basis is not None
        if warm:
            h.setBasis(self.basis)
        # HiGHS' time_limit is measured on a clock that runs from object creation, so
        # it has to be set relative to the current run time before every solve.
        h.setOptionValue("time_limit", h.getRunTime() + self.lp_time_limit)
        rs = h.run()
        st = str(h.getModelStatus())
        # A warm start from the previous basis can fail (kError / kNotset) when the
        # new linearisation makes that basis singular.  Retry once from scratch.
        # (Also covers kTimeLimit: a stale basis can send the simplex method into a
        # near-endless loop on a problem that solves in ~0.1 s from scratch.)
        if warm and not (st.endswith("kOptimal") or "Infeasible" in st):
            self.basis = None
            self.n_cold_retry += 1
            h.clearSolver()
            h.setOptionValue("time_limit", h.getRunTime() + self.lp_time_limit)
            h.run()
            st = str(h.getModelStatus())
        self.n_lp += 1
        self.n_simplex += max(h.getInfo().simplex_iteration_count, 0)
        if st.endswith("kOptimal"):
            self.basis = h.getBasis()
            return "optimal", np.array(h.getSolution().col_value)
        if "Infeasible" in st:
            return "infeasible", None
        self.basis = None
        return "other", None


class ScipyColdLP:
    """Fallback (public API only): every LP is solved from scratch."""

    def __init__(self, indptr, indices, n_rows, n_cols):
        self.indptr, self.indices, self.m, self.n = indptr, indices, n_rows, n_cols
        self.n_lp = 0
        self.n_simplex = 0

    def reset_basis(self):
        pass

    def solve(self, cost, lo, hi, rhs, data):
        from scipy.optimize import linprog
        A = sp.csc_matrix((data, self.indices, self.indptr), shape=(self.m, self.n))
        r = linprog(cost, A_eq=A, b_eq=rhs, bounds=np.c_[lo, hi], method="highs-ds")
        self.n_lp += 1
        if r.status == 0:
            return "optimal", r.x
        return ("infeasible" if r.status == 2 else "other"), None


# ------------------------------------------------------------------------
@dataclass
class SLPOptions:
    rho0: float = 0.5          # initial TR radius (relative to variable range)
    rho_max: float = 1.0
    rho_min: float = 1e-9
    max_iter: int = 400
    feas_tol: float = 1e-6     # paper: constraint violation < 1e-6  => feasible
    step_tol: float = 1e-9     # LP step (scaled inf-norm) below this => stationary
    dq_tol: float = 1e-9       # relative predicted reduction below this => stationary
    beta: float = 0.99
    gamma: float = 0.01
    sigma: float = 0.1
    sigma_r: float = 0.1       # restoration: actual/predicted decrease of violation
    block_restoration: bool = True   # alternating exact-LP restoration (see _block_restoration)
    block_cycles: int = 40
    delta: float = 1e-4
    shrink: float = 0.5
    expand: float = 2.0
    backend: str = "highs"     # "highs" (warm start)  |  "scipy" (cold)


@dataclass
class SLPResult:
    x: np.ndarray
    f: float
    h1: float                  # l1 violation
    hinf: float                # linf violation
    feasible: bool
    iters: int
    lps: int
    status: str
    time: float


class FilterSLP:
    def __init__(self, model: QQModel, opts: Optional[SLPOptions] = None):
        self.M = model
        self.o = opts or SLPOptions()
        self.c = model.cost_vector()
        indptr, indices = model.csc_structure()
        n, m = model.n, model.m_total
        LP = HighsWarmLP if (self.o.backend == "highs" and HAVE_DIRECT_HIGHS) else ScipyColdLP
        self.lp = LP(indptr, indices, m, n)
        # elastic (restoration) LP: [A | +I_bl | -I_bl] on the bilinear rows
        nb = model.nb
        rows = model.bl_row
        ind_aug = np.concatenate([indices, rows, rows]).astype(np.int32)
        ptr_aug = np.concatenate([indptr, indptr[-1] + np.arange(1, 2 * nb + 1)]).astype(np.int32)
        self.rest = LP(ptr_aug, ind_aug, m, n + 2 * nb)
        self.slack_vals = np.concatenate([np.ones(nb), -np.ones(nb)])
        wb = model.row_w[model.bl_row]                  # scaled l1 elastic cost
        self.rest_cost = np.concatenate([np.zeros(n), wb, wb])
        self.rest_hi = np.full(2 * nb, 1e30)
        self.rest_lo = np.zeros(2 * nb)
        self.nb = nb
        # variable blocks for the bilinear-block restoration
        self.idx_mu = np.concatenate([model.mur_var[model.mur_var >= 0],
                                      model.mub_var[model.mub_var >= 0]])
        self.idx_lamV = np.concatenate([model.lam_var[model.lam_var >= 0],
                                        model.V_var.ravel()])

    # ------------------------------------------------------------------
    def _acceptable(self, filt, h_t, f_t):
        o = self.o
        for hj, fj in filt:
            if not (h_t <= o.beta * hj or f_t <= fj - o.gamma * h_t):
                return False
        return True

    def _block_restoration(self, x):
        """Feasibility restoration exploiting the bilinear structure.

        Every constraint is  D - sum mu*R - sum mu_bin*V = 0.  With the product
        fractions mu FIXED the rows are linear in (lambda, V, D); with (lambda, V)
        FIXED they are linear in (mu, D).  Each block therefore is an *exact* LP
        (the linearisation carries no second-order error), so it can take full
        steps instead of trust-region-sized ones.  We alternate the two elastic
        (l1) LPs until the violation stops decreasing.  Returns (x, h).
        """
        M = self.M
        xc = x.copy()
        hc, _ = M.violation(xc)
        for _ in range(self.o.block_cycles):
            h_cycle = hc
            for fixed in (self.idx_mu, self.idx_lamV):
                lo = M.lb.copy(); hi = M.ub.copy()
                lo[fixed] = hi[fixed] = np.clip(xc[fixed], M.lb[fixed], M.ub[fixed])
                data, rhs = M.linearization(xc)
                st, xt = self.rest.solve(
                    self.rest_cost,
                    np.concatenate([lo, self.rest_lo]), np.concatenate([hi, self.rest_hi]),
                    rhs, np.concatenate([data, self.slack_vals]))
                if st != "optimal":
                    continue
                xn = np.clip(xt[:M.n], M.lb, M.ub)
                hn, _ = M.violation(xn)
                if hn < hc:
                    xc, hc = xn, hn
            if hc <= 0.1 * self.o.feas_tol or h_cycle - hc <= 1e-3 * h_cycle:
                break
        return xc, hc

    def solve(self, x_start) -> SLPResult:
        M, o, c = self.M, self.o, self.c
        t0 = time.perf_counter()
        x = np.clip(x_start, M.lb, M.ub)
        f = M.objective(x)
        h, hinf = M.violation(x)
        filt = []
        rho = o.rho0
        self.lp.reset_basis(); self.rest.reset_basis()
        status = "max_iter"
        in_rest = False
        block_stuck = False
        k = 0
        for k in range(1, o.max_iter + 1):
            lo = np.maximum(M.lb, x - rho * M.width)
            hi = np.minimum(M.ub, x + rho * M.width)
            data, rhs = M.linearization(x)

            st, xt = self.lp.solve(c, lo, hi, rhs, data)
            restoration = False
            if st == "infeasible":
                restoration = True
                if not in_rest:                       # entering restoration:
                    filt.append((h, f))               # forbid coming back here
                    in_rest = True
                if o.block_restoration and not block_stuck:
                    xr, hr = self._block_restoration(x)
                    if hr < 0.99 * h:                 # made real progress: jump there
                        x = xr; f = M.objective(x); h, hinf = M.violation(x)
                        continue
                    block_stuck = True                # fall back to the trust-region LP
                st, xt = self.rest.solve(
                    self.rest_cost,
                    np.concatenate([lo, self.rest_lo]),
                    np.concatenate([hi, self.rest_hi]),
                    rhs, np.concatenate([data, self.slack_vals]))
                if st == "optimal":
                    h_lin = float(self.rest_cost[M.n:] @ xt[M.n:])   # predicted violation
                    xt = xt[:M.n]
            if st != "optimal":
                rho *= o.shrink
                if rho < o.rho_min:
                    status = "lp_fail"; break
                continue

            xt = np.clip(xt, lo, hi)
            step = float(np.max(np.abs(xt - x) / M.width))
            ft = M.objective(xt)
            ht, htinf = M.violation(xt)
            dq = f - float(c @ xt)                     # predicted reduction

            # ---- convergence tests (only meaningful for the normal LP) ------
            if not restoration:
                in_rest = False
                if h <= o.feas_tol and (step <= o.step_tol or dq <= o.dq_tol * (1.0 + abs(f))):
                    status = "converged"; break

            # ---- filter acceptance ------------------------------------------
            if restoration:
                # monotone decrease of the violation; sufficient-decrease ratio test
                pred = h - h_lin
                accept = pred > 0 and ht < h and (h - ht) >= o.sigma_r * pred
                htype = False
            else:
                ftype = (dq >= o.delta * h * h) and (h <= 1e3 * o.feas_tol or dq > 0)
                if ftype and dq > 0:
                    accept = (f - ft >= o.sigma * dq) and self._acceptable(filt, ht, ft)
                    htype = False
                else:
                    accept = ((ht <= o.beta * h) or (ft <= f - o.gamma * ht)) \
                        and self._acceptable(filt, ht, ft)
                    htype = True

            if accept:
                if htype:
                    filt.append((h, f))
                    filt = [e for e in filt if not (e[0] >= h and e[1] >= f) or e == (h, f)]
                x, f, h, hinf = xt, ft, ht, htinf
                if not restoration:
                    block_stuck = False
                if step >= 0.99 * rho:
                    rho = min(o.rho_max, rho * o.expand)
            else:
                rho = min(rho, step) * o.shrink if step > 0 else rho * o.shrink
                if rho < o.rho_min:
                    status = "rho_min" if not restoration else "infeasible_stationary"
                    break

        feas = hinf <= o.feas_tol
        return SLPResult(x, f, h, hinf, feas, k, self.lp.n_lp + self.rest.n_lp,
                         status, time.perf_counter() - t0)
