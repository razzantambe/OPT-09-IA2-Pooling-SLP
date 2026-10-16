"""
qq_model.py
===========
Data parser and the *qq-formulation* of the fixed-demand pooling problem from

    Grothey & McKinnon, "On the effectiveness of sequential linear programming
    for the pooling problem", Ann. Oper. Res. 322 (2023), eq. (5a)-(5h).

Notation (paper)                     Notation in the AMPL data files
------------------------------------ -------------------------------
lambda[m,i]  bin m  <- raw material i   ``mu_lb / mu_ub``   (rows MI, cols RM)
mu[p,i]      product p <- raw i (straight) ``lam_lb / lam_ub`` (rows DE, cols RM)
mu[p,m]      product p <- bin m           ``lam_lb / lam_ub`` (rows DE, cols MI)

(The data files use the two names the other way round from the paper; this
module uses the paper's names internally.)

Trick used throughout: the *price* is handled exactly like an extra nutrient.
With attribute matrix R (I x (N+1)), whose last column holds the raw material
costs, the constraints (5b)-(5c) and (5f)-(5g) become one family

    V[m,q] = sum_i lambda[m,i] R[i,q]                       (linear)
    D[p,q] = sum_i mu[p,i] R[i,q] + sum_m mu[p,m] V[m,q]     (bilinear)

for q = 0..N-1 (nutrients) and q = N (cost: V[:,N]=cM, D[:,N]=cD).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import scipy.sparse as sp

INF = 1e30


# --------------------------------------------------------------------------
# 1. Parsing of the AMPL-style data files
# --------------------------------------------------------------------------
@dataclass
class Instance:
    name: str
    NU: List[str]
    RM: List[str]
    MI: List[str]
    DE: List[str]
    r: np.ndarray            # (I, N)  nutrient content of raw material i
    cost: np.ndarray         # (I,)    RMcost
    spec_lb: np.ndarray      # (P, N)
    spec_ub: np.ndarray      # (P, N)
    tons: np.ndarray         # (P,)
    lam_lb: np.ndarray       # (M, I)  bin <- raw     (paper: lambda)
    lam_ub: np.ndarray
    mu_lb: np.ndarray        # (P, I+M) product <- [raw | bins] (paper: mu)
    mu_ub: np.ndarray
    numi_lb: Optional[np.ndarray] = None   # (M, N) bounds on bin composition
    numi_ub: Optional[np.ndarray] = None

    @property
    def N(self): return len(self.NU)
    @property
    def I(self): return len(self.RM)
    @property
    def M(self): return len(self.MI)
    @property
    def P(self): return len(self.DE)


def _statements(text: str) -> List[str]:
    text = text.replace("\r", "")
    return [s.strip() for s in text.split(";") if s.strip()]


def _table(body: str, ncols_hint: Optional[int] = None):
    """Parse 'rowname v1 v2 ... vk' records.  Rows may be wrapped over several
    lines, so we tokenise the whole body and cut it into records by detecting
    the row-label tokens (anything non-numeric)."""
    toks = body.split()
    rows, cur, lab = {}, [], None
    for t in toks:
        try:
            cur.append(float(t))
        except ValueError:
            if lab is not None:
                rows[lab] = cur
            lab, cur = t, []
    if lab is not None:
        rows[lab] = cur
    return rows


def load_instance(path: str, name: Optional[str] = None) -> Instance:
    import os
    text = open(path, "r", errors="ignore").read()
    sets: Dict[str, List[str]] = {}
    params: Dict[str, np.ndarray] = {}
    raw: Dict[str, dict] = {}
    cols_of: Dict[str, List[str]] = {}

    for st in _statements(text):
        if st.startswith("set"):
            m = re.match(r"set\s+(\w+)\s*:=\s*(.*)", st, re.S)
            sets[m.group(1)] = m.group(2).split()
        elif st.startswith("param"):
            head, body = st.split(":=", 1)
            head = head[len("param"):].strip()
            if head.startswith(":"):                    # "param: tons"  -> vector
                pname = head[1:].strip()
                raw[pname] = {k: v[0] for k, v in _table(body).items()}
            else:                                       # "param name: c1 c2 ... "
                pname, cols = head.split(":", 1)
                pname = pname.strip()
                cols_of[pname] = cols.split()
                raw[pname] = _table(body)

    NU, RM, MI, DE = sets["NU"], sets["RM"], sets["MI"], sets["DE"]
    I, M, P, N = len(RM), len(MI), len(DE), len(NU)

    # nuinrm(tr): rows are NU, columns are RM (transposed AMPL parameter)
    nuinrm = raw["nuinrm(tr)"]
    r = np.array([nuinrm[nu] for nu in NU]).T                     # (I, N)
    assert r.shape == (I, N), r.shape

    def mat(pname, rows, cols):
        d = raw[pname]
        return np.array([[d[rw][cols.index(c)] for c in cols] for rw in rows]) \
            if False else np.array([d[rw] for rw in rows], dtype=float)

    spec_ub = mat("specs_ub", DE, NU)
    spec_lb = mat("specs_lb", DE, NU)
    tons = np.array([raw["tons"][d] for d in DE], dtype=float)
    cost = np.array([raw["RMcost"][k] for k in RM], dtype=float)

    # data-file "mu"  == paper lambda   (rows MI, cols RM + MI; MI cols unused)
    lam_lb = mat("mu_lb", MI, RM)[:, :I]
    lam_ub = mat("mu_ub", MI, RM)[:, :I]
    # data-file "lam" == paper mu       (rows DE, cols RM + MI)
    mu_lb = mat("lam_lb", DE, RM)
    mu_ub = mat("lam_ub", DE, RM)
    assert mu_ub.shape == (P, I + M), mu_ub.shape

    numi_lb = numi_ub = None
    if "numi_lb" in raw:
        numi_lb = mat("numi_lb", MI, NU)
        numi_ub = mat("numi_ub", MI, NU)

    return Instance(name or os.path.splitext(os.path.basename(path))[0],
                    NU, RM, MI, DE, r, cost, spec_lb, spec_ub, tons,
                    lam_lb, lam_ub, mu_lb, mu_ub, numi_lb, numi_ub)


# --------------------------------------------------------------------------
# 2. The qq-formulation as a structured NLP with only bilinear nonlinearity
# --------------------------------------------------------------------------
class QQModel:
    """
    min  sum_p tons[p] * D[p,N]                                  (5a)
    s.t. V[m,q] - sum_i lam[m,i] R[i,q] = 0                       (5b),(5f)
         D[p,q] - sum_i mu[p,i] R[i,q] - sum_m mu[p,m] V[m,q] = 0 (5c),(5g)
         sum_i lam[m,i] = 1 ;  sum_i mu[p,i] + sum_m mu[p,m] = 1  (5d),(5e)
         bounds (5h) etc.

    Only variables whose upper bound is > 0 are created (sparse network).
    Variable vector x = [ lam | mu_raw | mu_bin | V(nutrients) | cM | D(nutr.) | cD ].
    """

    def __init__(self, inst: Instance, drop_zero_ton_products: bool = False,
                 scale: bool = True, width_cap: float = 4.0):
        self.inst = inst
        I, M, P, N = inst.I, inst.M, inst.P, inst.N
        self.I, self.M, self.N = I, M, N
        keepP = np.arange(P) if not drop_zero_ton_products else np.where(inst.tons > 0)[0]
        self.prod_idx = keepP
        P = self.P = len(keepP)
        self.tons = inst.tons[keepP]
        self.Q = N + 1                                  # nutrients + price
        R0 = np.hstack([inst.r, inst.cost[:, None]])    # (I, Q) original units
        # ---- attribute scaling (paper: presolve "scaling of variables") ----------
        # every attribute q (nutrient or price) is divided by a robust typical
        # magnitude s_q (median of its positive entries).  V[.,q], D[.,q] and the
        # rows (5b),(5c),(5f),(5g) then all live on an O(1) scale, so that trust
        # region steps and the l1 constraint violation are not dominated by, e.g.,
        # a raw material with a "big-M" price of 99999.
        sc = np.ones(self.Q)
        if scale:
            for q in range(self.Q):
                pos = R0[:, q][R0[:, q] > 0]
                if len(pos):
                    sc[q] = float(np.median(pos))
        self.attr_scale = sc
        R = R0 / sc
        self.R = R
        spec_lb = inst.spec_lb / sc[:N]
        spec_ub = inst.spec_ub / sc[:N]
        numi_lb = None if inst.numi_lb is None else inst.numi_lb / sc[:N]
        numi_ub = None if inst.numi_ub is None else inst.numi_ub / sc[:N]

        # ---- variable indexing ------------------------------------------
        lo: List[float] = []
        hi: List[float] = []
        self.lam_var = -np.ones((M, I), dtype=int)
        self.mur_var = -np.ones((P, I), dtype=int)
        self.mub_var = -np.ones((P, M), dtype=int)
        self.V_var = -np.ones((M, self.Q), dtype=int)
        self.D_var = -np.ones((P, self.Q), dtype=int)

        def new(l, u):
            lo.append(l); hi.append(u); return len(lo) - 1

        for m in range(M):
            for i in range(I):
                if inst.lam_ub[m, i] > 0:
                    self.lam_var[m, i] = new(inst.lam_lb[m, i], inst.lam_ub[m, i])
        for k, p in enumerate(keepP):
            for i in range(I):
                if inst.mu_ub[p, i] > 0:
                    self.mur_var[k, i] = new(inst.mu_lb[p, i], inst.mu_ub[p, i])
            for m in range(M):
                if inst.mu_ub[p, I + m] > 0:
                    self.mub_var[k, m] = new(inst.mu_lb[p, I + m], inst.mu_ub[p, I + m])

        # attainable range of every attribute (bound tightening)
        rmin = np.zeros((M, self.Q)); rmax = np.zeros((M, self.Q))
        for m in range(M):
            ii = np.where(self.lam_var[m] >= 0)[0]
            rmin[m] = R[ii].min(0); rmax[m] = R[ii].max(0)
        for m in range(M):
            for q in range(self.Q):
                l, u = rmin[m, q], rmax[m, q]
                if q < N and numi_ub is not None:
                    l = max(l, numi_lb[m, q]); u = min(u, numi_ub[m, q])
                self.V_var[m, q] = new(l, u)
        for k, p in enumerate(keepP):
            allowed = list(np.where(self.mur_var[k] >= 0)[0])
            cand = R[allowed] if allowed else np.zeros((0, self.Q))
            bins = np.where(self.mub_var[k] >= 0)[0]
            lo_q = np.full(self.Q, np.inf); hi_q = np.full(self.Q, -np.inf)
            if len(cand):
                lo_q = np.minimum(lo_q, cand.min(0)); hi_q = np.maximum(hi_q, cand.max(0))
            for m in bins:
                lo_q = np.minimum(lo_q, rmin[m]); hi_q = np.maximum(hi_q, rmax[m])
            for q in range(self.Q):
                if q < N:
                    l = max(spec_lb[p, q], lo_q[q]); u = min(spec_ub[p, q], hi_q[q])
                    if l > u:                             # spec unreachable
                        l, u = spec_lb[p, q], spec_ub[p, q]
                else:
                    l, u = lo_q[q], hi_q[q]
                self.D_var[k, q] = new(l, u)

        self.lb = np.array(lo, float); self.ub = np.array(hi, float)
        self.n = len(self.lb)
        # trust-region scaling widths (paper: variable scaling in presolve)
        w = self.ub - self.lb
        self.width = np.where(w > 1e-9, w, 1.0)
        # V/D variables live on the (scaled) attribute scale.  A loose bound such as
        # a 99999 "big-M" price would make the trust-region box astronomically wide
        # for these variables, so the box width is capped at `width_cap` units.
        if width_cap is not None:
            vd = np.concatenate([self.V_var.ravel(), self.D_var.ravel()])
            self.width[vd] = np.minimum(self.width[vd], width_cap)

        # ---- constraints ---------------------------------------------------
        self._build_constraints()

    # ------------------------------------------------------------------
    def _build_constraints(self):
        M, P, Q, N, I = self.M, self.P, self.Q, self.N, self.I
        R = self.R
        rows, cols, vals = [], [], []
        rhs = []

        rscale = []                      # original-unit scale of every row

        def add_row(entries, b, scale=1.0):
            r = len(rhs)
            for c, v in entries:
                rows.append(r); cols.append(c); vals.append(v)
            rhs.append(b)
            rscale.append(scale)
            return r

        # (5b)/(5f) linear definition of V
        for m in range(M):
            for q in range(Q):
                ent = [(self.V_var[m, q], 1.0)]
                for i in range(I):
                    j = self.lam_var[m, i]
                    if j >= 0 and R[i, q] != 0.0:
                        ent.append((j, -R[i, q]))
                add_row(ent, 0.0, self.attr_scale[q])
        self.n_lin_def = len(rhs)

        # (5d) convexity for bins, (5e) for products
        for m in range(M):
            add_row([(j, 1.0) for j in self.lam_var[m] if j >= 0], 1.0)
        for k in range(P):
            ent = [(j, 1.0) for j in self.mur_var[k] if j >= 0] + \
                  [(j, 1.0) for j in self.mub_var[k] if j >= 0]
            add_row(ent, 1.0)
        self.n_lin = len(rhs)

        # (5c)/(5g) bilinear rows: D - sum mu_pi R - sum mu_pm V = 0
        self.bl_row0 = len(rhs)
        bl_row, bl_mu, bl_V = [], [], []
        self.row_of_pq = np.zeros((P, Q), dtype=int)
        static_pos = {}
        for k in range(P):
            for q in range(Q):
                ent = [(self.D_var[k, q], 1.0)]
                for i in range(I):
                    j = self.mur_var[k, i]
                    if j >= 0 and R[i, q] != 0.0:
                        ent.append((j, -R[i, q]))
                r = add_row(ent, 0.0, self.attr_scale[q])
                self.row_of_pq[k, q] = r
                for m in range(M):
                    j = self.mub_var[k, m]
                    if j >= 0:
                        bl_row.append(r); bl_mu.append(j); bl_V.append(self.V_var[m, q])
        self.bl_row = np.array(bl_row, int)
        self.bl_mu = np.array(bl_mu, int)     # var index of mu[p,m]
        self.bl_V = np.array(bl_V, int)       # var index of V[m,q]
        self.m_total = len(rhs)
        self.rhs_lin = np.array(rhs, float)
        self.row_scale = np.array(rscale, float)

        # static part of the Jacobian in COO, plus placeholders for the
        # 2*len(bl_row) bilinear entries (kept at the END so that the CSC
        # data vector layout is fixed once and only "values" get refreshed).
        nb = len(self.bl_row)
        self.nb = nb
        self.static_rows = np.array(rows, int)
        self.static_cols = np.array(cols, int)
        self.static_vals = np.array(vals, float)
        self._A_static = sp.csr_matrix((self.static_vals, (self.static_rows, self.static_cols)),
                                       shape=(self.m_total, self.n))
        all_rows = np.concatenate([self.static_rows, self.bl_row, self.bl_row])
        all_cols = np.concatenate([self.static_cols, self.bl_mu, self.bl_V])
        self._coo_rows, self._coo_cols = all_rows, all_cols
        # CSC pattern with a permutation that lets us drop in new values fast
        tmp = sp.coo_matrix((np.arange(1, len(all_rows) + 1, dtype=float),
                             (all_rows, all_cols)), shape=(self.m_total, self.n))
        csc = tmp.tocsc()
        csc.sum_duplicates()
        self._csc_indptr = csc.indptr.astype(np.int32)
        self._csc_indices = csc.indices.astype(np.int32)
        self._perm = (csc.data.astype(int) - 1)            # csc slot -> coo entry
        # (row,col) pairs are unique by construction, so a plain permutation works
        assert len(self._perm) == len(all_rows)

        # ---- violation measure ----------------------------------------------
        # With attribute scaling every row is already expressed in units of the
        # median magnitude of its attribute, so no further row weighting is needed
        # (an extra weighting by the attribute *maximum* would hide violations of
        # tightly specified nutrients).
        self.row_w = np.ones(self.m_total)
        self.qscale = self.attr_scale

        # sizes as reported in Table 1 of the paper
        self.n_vars = self.n
        self.n_cons = self.m_total

    # ------------------------------------------------------------------
    # evaluation
    def objective(self, x):
        return float(self.attr_scale[self.N] * (self.tons @ x[self.D_var[:, self.N]]))

    def cost_vector(self):
        c = np.zeros(self.n)
        c[self.D_var[:, self.N]] = self.tons * self.attr_scale[self.N]
        return c

    def violation_unscaled(self, x):
        """(l1, linf) violation measured in the ORIGINAL units of the data."""
        r = np.abs(self.residual(x)) * self.row_scale
        return float(r.sum()), float(r.max())

    def _mu_V(self, x):
        return x[self.bl_mu], x[self.bl_V]

    def residual(self, x):
        """Residual of all equality constraints  A_static x + bilinear - rhs."""
        res = self._A_static @ x - self.rhs_lin
        mu, V = self._mu_V(x)
        np.subtract.at(res, self.bl_row, mu * V)
        return res

    def violation(self, x):
        """(scaled l1, scaled linf) constraint violation of x."""
        r = np.abs(self.residual(x)) * self.row_w
        return float(r.sum()), float(r.max())

    def linearization(self, x0):
        """Values of the LP coefficient matrix (CSC data) and RHS at x0."""
        mu0, V0 = self._mu_V(x0)
        # d/dmu = -V0 ; d/dV = -mu0 ; constant: -(mu*V) + (mu0 V0 + V0 mu0) ... derived:
        # g(x) ~ D - sum mu_pi R - sum (mu0 V + V0 mu - mu0 V0) = 0
        # => coefficients (-V0 on mu, -mu0 on V), rhs = -sum mu0*V0
        coo_vals = np.concatenate([self.static_vals, -V0, -mu0])
        data = coo_vals[self._perm]
        rhs = self.rhs_lin.copy()
        np.subtract.at(rhs, self.bl_row, mu0 * V0)
        return data, rhs

    def csc_structure(self):
        return self._csc_indptr, self._csc_indices

    # ------------------------------------------------------------------
    # random starting points
    def _box_simplex(self, rng, lo, hi):
        """random point of {x: sum x = 1, lo <= x <= hi} (random target, then
        Euclidean projection by bisection on the shift)."""
        z = rng.random(len(lo)) * np.maximum(hi, 0)
        a, b = -2.0, 2.0
        for _ in range(60):
            t = 0.5 * (a + b)
            s = np.clip(z - t, lo, hi).sum()
            if s > 1: a = t
            else: b = t
        return np.clip(z - 0.5 * (a + b), lo, hi)

    def random_start(self, rng):
        x = np.zeros(self.n)
        for m in range(self.M):
            js = np.where(self.lam_var[m] >= 0)[0]
            v = self.lam_var[m, js]
            x[v] = self._box_simplex(rng, self.lb[v], self.ub[v])
        for k in range(self.P):
            v = np.concatenate([self.mur_var[k][self.mur_var[k] >= 0],
                                self.mub_var[k][self.mub_var[k] >= 0]])
            x[v] = self._box_simplex(rng, self.lb[v], self.ub[v])
        # derived variables computed from their definitions ...
        for m in range(self.M):
            for q in range(self.Q):
                x[self.V_var[m, q]] = sum(x[self.lam_var[m, i]] * self.R[i, q]
                                          for i in range(self.I) if self.lam_var[m, i] >= 0)
        for k in range(self.P):
            for q in range(self.Q):
                s = sum(x[self.mur_var[k, i]] * self.R[i, q]
                        for i in range(self.I) if self.mur_var[k, i] >= 0)
                s += sum(x[self.mub_var[k, m]] * x[self.V_var[m, q]]
                         for m in range(self.M) if self.mub_var[k, m] >= 0)
                x[self.D_var[k, q]] = s
        # ... then projected onto the bounds (as any NLP solver would do)
        return np.clip(x, self.lb, self.ub)


if __name__ == "__main__":
    import sys, os
    here = os.path.dirname(os.path.abspath(__file__))
    for nm in ["af-1", "af-2", "af-3", "af-4"]:
        inst = load_instance(os.path.join(here, "data", nm + ".txt"))
        mod = QQModel(inst)
        print(f"{nm}: N={inst.N} I={inst.I} M={inst.M} P={inst.P}  "
              f"qq-size: n={mod.n_vars} m={mod.n_cons}")
