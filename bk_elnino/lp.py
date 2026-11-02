"""Time-series local projections replicating Bilal-Kaenzig's Stata/MATLAB code.

PWT specification (s01S_lp_ts_globalshock.do, 1960-2019):

    y_{t+h} - y_{t-1} = a_h + theta_h s_t + sum_{j=1..2} g_j s_{t-j}
                        + sum_{j=1..2} d_j dy_{t-j} + sum_{j=0..2} r_j rec_{t-j}
                        + c * trend + e_{t+h}

with y = 100*log world real GDP per capita, Newey-West(4) standard errors. BU uses 4
lags of everything (1860-2019). The wild-bootstrap ARX procedure follows
s02a_lp_ts_globalshock_bootstrap.m and yields joint draws of (theta_0..theta_10).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class LPSpec:
    y: str                 # level variable (100*log)
    shock: str
    rec: str = "dummyrecession"
    start: int = 1960
    end: int = 2019
    p: int = 2             # lags of dy
    ps: int = 2            # lags of shock (besides contemporaneous)
    pr: int = 2            # lags of recession dummy (besides contemporaneous)
    horizon: int = 10
    nw_lags: int = 4
    dy_before_restrict: bool = False  # BU creates dy before `keep if`, PWT after


def _restricted(df: pd.DataFrame, spec: LPSpec) -> pd.DataFrame:
    full = df.sort_index()
    dy_full = full[spec.y].diff()
    d = full.loc[spec.start:spec.end].copy()
    years = d.index.values
    if (np.diff(years) != 1).any():
        raise ValueError("LP sample must be consecutive years")
    d["dy"] = dy_full.loc[spec.start:spec.end] if spec.dy_before_restrict else d[spec.y].diff()
    d["trend"] = np.arange(1, len(d) + 1, dtype=float)
    return d


def regressors(d: pd.DataFrame, spec: LPSpec, shock: pd.Series | None = None) -> pd.DataFrame:
    s = d[spec.shock] if shock is None else shock
    X = pd.DataFrame(index=d.index)
    X["shock"] = s
    for j in range(1, spec.ps + 1):
        X[f"shock_L{j}"] = s.shift(j)
    for j in range(1, spec.p + 1):
        X[f"dy_L{j}"] = d["dy"].shift(j)
    for j in range(0, spec.pr + 1):
        X[f"rec_L{j}"] = d[spec.rec].shift(j)
    X["trend"] = d["trend"]
    X["const"] = 1.0
    return X


def newey_west(X: np.ndarray, e: np.ndarray, lags: int) -> np.ndarray:
    """Stata `newey` covariance: Bartlett kernel with n/(n-k) small-sample factor."""
    n, k = X.shape
    Xe = X * e[:, None]
    S = Xe.T @ Xe
    for lag in range(1, lags + 1):
        w = 1.0 - lag / (lags + 1.0)
        G = Xe[lag:].T @ Xe[:-lag]
        S += w * (G + G.T)
    S *= n / (n - k)
    XtXi = np.linalg.inv(X.T @ X)
    return XtXi @ S @ XtXi


def _ols(y: np.ndarray, X: np.ndarray):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return b, y - X @ b


def lp_irf(df: pd.DataFrame, spec: LPSpec, outcome: str | None = None,
           y_override: pd.Series | None = None) -> pd.DataFrame:
    """IRF of ``outcome`` (default spec.y, cumulative change y_{t+h}-y_{t-1}).

    Returns a frame indexed by h with columns b, se (Newey-West), n, first, last.
    """
    d = _restricted(df, spec)
    if y_override is not None:
        d[spec.y] = y_override.loc[d.index]
        d["dy"] = d[spec.y].diff()
    var = spec.y if outcome is None else outcome
    lvl = d[var]
    own_dy = lvl.diff()
    X = regressors(d, spec)
    if outcome is not None and outcome != spec.y:
        # Stata: L(1/p).d<var> plus the cntrls (which already hold world-GDP growth lags)
        for j in range(1, spec.p + 1):
            X.insert(spec.ps + 1 + j - 1, f"dvar_L{j}", own_dy.shift(j))
    rows = []
    for h in range(spec.horizon + 1):
        dep = lvl.shift(-h) - lvl.shift(1)
        Z = pd.concat([dep.rename("dep"), X], axis=1).dropna()
        Xm = Z.drop(columns="dep")
        Xm = Xm.loc[:, ~Xm.T.duplicated()]  # Stata drops collinear duplicates
        yv, Xv = Z["dep"].values, Xm.values
        b, e = _ols(yv, Xv)
        V = newey_west(Xv, e, spec.nw_lags)
        j = list(Xm.columns).index("shock")
        rows.append({"h": h, "b": b[j], "se": float(np.sqrt(V[j, j])), "n": len(yv),
                     "first": int(Z.index.min()), "last": int(Z.index.max())})
    return pd.DataFrame(rows).set_index("h")


def wild_bootstrap_irf(df: pd.DataFrame, spec: LPSpec, nboot: int = 4000,
                       seed: int = 123) -> np.ndarray:
    """Joint bootstrap draws of the GDP IRF (nboot x horizon+1), following s02a.

    1. Fit the h=0 ARX regression of dy on (shock, shock lags, dy lags, recession
       dummies, trend, const).
    2. Multiply its residuals by Rademacher draws, regenerate dy recursively from the
       ARX coefficients (shock and dummies held fixed), rebuild levels from y_start.
    3. Re-estimate the LP at every horizon on the bootstrap sample.
    """
    rng = np.random.default_rng(seed)
    d = _restricted(df, spec)
    X = regressors(d, spec)
    years = d.index.values
    T = len(years)

    dy = d["dy"].values.astype(float)
    y = d[spec.y].values.astype(float)
    Xv = X.values.astype(float)
    cols = list(X.columns)
    shock_j = cols.index("shock")
    ar_cols = [cols.index(f"dy_L{j}") for j in range(1, spec.p + 1)]
    other = [i for i in range(len(cols)) if i not in ar_cols]

    # h=0 ARX regression for growth
    ok0 = ~np.isnan(dy) & ~np.isnan(Xv).any(axis=1)
    est = np.flatnonzero(ok0)
    b, e = _ols(dy[est], Xv[est])
    fixed = Xv[est][:, other] @ b[other]          # shock, dummies, trend, const part
    b_ar = b[ar_cols]

    # LP masks per horizon do not change across draws (NaN pattern of bdy == dy)
    masks = []
    for h in range(spec.horizon + 1):
        idx = np.arange(T)
        ok = (idx - 1 >= 0) & (idx + h < T) & ~np.isnan(Xv).any(axis=1)
        masks.append(np.flatnonzero(ok))

    draws = np.empty((nboot, spec.horizon + 1))
    for ib in range(nboot):
        u = e * rng.choice([-1.0, 1.0], size=len(e))
        bdy = dy.copy()   # values before the first estimation year stay observed
        for k, i in enumerate(est):
            lagged = np.array([bdy[i - j] for j in range(1, spec.p + 1)])
            bdy[i] = fixed[k] + lagged @ b_ar + u[k]
        by = np.full(T, np.nan)
        by[0] = y[0]
        by[1:] = y[0] + np.cumsum(bdy[1:])
        bX = Xv.copy()
        for j, c in enumerate(ar_cols, start=1):
            bX[:, c] = np.r_[np.full(j, np.nan), bdy[:-j]]
        for h in range(spec.horizon + 1):
            m = masks[h]
            dep = by[m + h] - by[m - 1]
            bb, _ = _ols(dep, bX[m])
            draws[ib, h] = bb[shock_j]

    return draws


def recentre(draws: np.ndarray, point: np.ndarray) -> np.ndarray:
    """Shift bootstrap draws so their median equals the point estimate (authors' CI rule)."""
    return draws - np.median(draws, axis=0) + np.asarray(point)[None, :]


def percentile_band(draws: np.ndarray, point: np.ndarray, alpha: float) -> tuple[np.ndarray, np.ndarray]:
    med = np.median(draws, axis=0)
    lo = np.quantile(draws, alpha / 2, axis=0) - med + point
    hi = np.quantile(draws, 1 - alpha / 2, axis=0) - med + point
    return lo, hi


def transitory_irf(y_irf: np.ndarray, x_irf: np.ndarray, x_path: np.ndarray | None = None) -> np.ndarray:
    """Sims (1986) counterfactual, as in the authors' gettransirf.m.

    Finds the sequence of shocks that produces temperature path ``x_path`` (default: +1C
    in year 0 only) given the temperature IRF ``x_irf`` (normalised to 1 on impact),
    and returns the implied outcome path. ``y_irf`` must be per unit of the shock that
    raises temperature by x_irf[0] on impact; both are rescaled by x_irf[0] here.
    """
    y = np.asarray(y_irf, float) / x_irf[0]
    x = np.asarray(x_irf, float) / x_irf[0]
    H = len(y) - 1
    if x_path is None:
        x_path = np.zeros(H + 1)
        x_path[0] = 1.0
    B = np.eye(H + 1)
    for h in range(1, H + 1):
        for i in range(1, h + 1):
            B[h, i - 1] = x[h - i + 1]
    eps = np.linalg.solve(B, x_path)
    S = np.eye(H + 1)
    for i in range(H + 1):
        for j in range(i, H + 1):
            S[i, j] = eps[j - i]
    return S.T @ y
