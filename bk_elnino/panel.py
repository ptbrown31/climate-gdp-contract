"""The paper's PWT country-panel local projection (eq. 3), equal-weighted (Fig. IV) or GDP-weighted (App. Fig. B.10).

Replicates `xtscc ..., fe lag(4)` in the authors' s03S_lp_panel_globalshock.do. For h = 0..10,

    y_{i,t+h} - y_{i,t-1} = theta_h s_t + sum_{j=1}^{2} s_{t-j} + sum_{j=1}^{2} dy_{i,t-j}
                            + L(0/2) recession dummy + L(1/2) of world GDP growth, oil-price growth and the
                            1-year Treasury rate + subregion x linear trend + country fixed effect,

on 1960-2019, with Driscoll-Kraay errors (Bartlett kernel, 4 lags). The equal-weighted fit reproduces the
authors' saved Fig. IV response. App. Fig. B.10 weights each country by its lagged share of world GDP
([w = L.gdp_share]): weighted least squares with country fixed effects, i.e. the weighted within
transformation followed by sqrt(w) row scaling.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

Y, SHOCK = "lnrgdppc_pwt", "gtmp_bkly_aw_dtfe2s"
START, END, P, PS, REC_LAGS, DK_LAGS, H_MAX = 1960, 2019, 2, 2, 2, 4, 10
GLOB_GROWTH, GLOB_LEVEL = ("lnrgdppc_world_pwt", "lnpoil_wti"), ("treasury1y",)
SHARE = ("rgdpna_pwt", "rgdpna_world0_pwt")      # gdp_share = country GDP / world GDP


def _shift(v: np.ndarray, k: int) -> np.ndarray:
    """out[..., t] = v[..., t - k] along the last (year) axis; k > 0 is a lag, k < 0 a lead."""
    out = np.full(np.shape(v), np.nan)
    if k == 0:
        out[...] = v
    elif k > 0:
        out[..., k:] = v[..., :-k]
    else:
        out[..., :k] = v[..., -k:]
    return out


def _demean(X: np.ndarray, ci: np.ndarray, w: np.ndarray) -> np.ndarray:
    """(Weighted) within-country demeaning; ci is sorted (observations are in country-year order)."""
    starts = np.flatnonzero(np.r_[True, ci[1:] != ci[:-1]])
    cnt = np.diff(np.r_[starts, len(ci)])
    wx = X * (w if X.ndim == 1 else w[:, None])
    means = np.add.reduceat(wx, starts, axis=0) / (np.add.reduceat(w, starts) if X.ndim == 1
                                                   else np.add.reduceat(w, starts)[:, None])
    return X - np.repeat(means, cnt, axis=0)


def _orth(X: np.ndarray, tol: float = 1e-9) -> np.ndarray:
    """Orthonormal basis of the column space of X; drops collinear columns."""
    nrm = np.linalg.norm(X, axis=0)
    keep = nrm > 1e-12 * max(nrm.max(), 1.0)
    U, sv, _ = np.linalg.svd(X[:, keep] / nrm[keep], full_matrices=False)
    return U[:, sv > tol * sv[0]]


class Panel:
    """The authors' PWT panel on a country x year grid."""

    def __init__(self, bk_dir: Path):
        df = pd.read_stata(bk_dir / "1_empirics/data/micc_pwt_panel.dta", convert_categoricals=False)
        df["year"] = df["year"].astype(int)
        self.years = np.arange(df.year.min(), df.year.max() + 1)
        countries = np.sort(df.country_code_en.unique())
        wide = lambda v: (df.pivot(index="country_code_en", columns="year", values=v)  # noqa: E731
                          .reindex(index=countries, columns=self.years).to_numpy(float))
        self.inr = (self.years >= START) & (self.years <= END)
        self.y = wide(Y)
        self.share = wide(SHARE[0]) / wide(SHARE[1])
        g = df.groupby("year")
        self.g = {v: g[v].first().reindex(self.years).to_numpy(float)
                  for v in (SHOCK, "recessiondates", *GLOB_GROWTH, *GLOB_LEVEL)}
        self.sub = df.groupby("country_code_en").subregion_en.first().reindex(countries).to_numpy()

    def R(self, a: np.ndarray) -> np.ndarray:
        """The sample restriction (keep if year >= 1960 & year <= 2019)."""
        return np.where(self.inr, a, np.nan)

    def design(self, h: int, weighted: bool) -> dict:
        """Observation-level arrays for horizon h on the authors' estimation sample."""
        yr = self.R(self.y)
        dy = yr - _shift(yr, 1)                    # PWT builds growth rates after the sample cut
        s = self.R(self.g[SHOCK])
        S = [_shift(s, j) for j in range(PS + 1)]
        rec = self.R(self.g["recessiondates"])
        ctrl = [_shift(dy, j) for j in range(1, P + 1)] + [_shift(rec, j) for j in range(REC_LAGS + 1)]
        for x in GLOB_GROWTH:
            gx = self.R(self.g[x]) - _shift(self.R(self.g[x]), 1)
            ctrl += [_shift(gx, j) for j in range(1, P + 1)]
        for x in GLOB_LEVEL:
            ctrl += [_shift(self.R(self.g[x]), j) for j in range(1, P + 1)]
        dep = _shift(yr, -h) - _shift(yr, 1)
        w = _shift(self.R(self.share), 1) if weighted else np.ones_like(dep)
        full = lambda a: np.broadcast_to(a, dep.shape)  # noqa: E731
        ok = np.isfinite(dep) & np.isfinite(w) & (w > 0)
        for a in S + ctrl:
            ok &= np.isfinite(full(a))
        ci, ti = np.nonzero(ok)
        t = (self.years[ti] - START + 1).astype(float)  # the authors' lintrend
        trend = (self.sub[ci][:, None] == np.unique(self.sub[ci])[None, :]) * t[:, None]
        return {"ci": ci, "ti": ti, "dep": dep[ok], "w": w[ok], "S": np.column_stack([full(a)[ok] for a in S]),
                "X": np.column_stack([full(a)[ok] for a in ctrl] + [trend])}

    def fit(self, h: int, weighted: bool = False) -> dict:
        """theta_h and its Driscoll-Kraay s.e. (xtscc's small-sample factor)."""
        d = self.design(h, weighted)
        ci, w = d["ci"], d["w"]
        sw = np.sqrt(w)
        T = lambda M: (sw if M.ndim == 1 else sw[:, None]) * _demean(M, ci, w)  # noqa: E731
        Q = _orth(T(d["X"]))
        yd, Sd = T(d["dep"]), T(d["S"])
        yt, St = yd - Q @ (Q.T @ yd), Sd - Q @ (Q.T @ Sd)
        A = St.T @ St
        b = np.linalg.solve(A, St.T @ yt)
        e = yt - St @ b
        tix = d["ti"] - d["ti"].min()
        g = np.zeros((tix.max() + 1, St.shape[1]))
        np.add.at(g, tix, St * e[:, None])
        meat = g.T @ g
        for j in range(1, DK_LAGS + 1):
            G = g[j:].T @ g[:-j]
            meat += (1 - j / (DK_LAGS + 1)) * (G + G.T)
        Ai = np.linalg.inv(A)
        n, k, nT = len(yt), Q.shape[1] + St.shape[1] + 1, len(np.unique(tix))
        se = float(np.sqrt((Ai @ meat @ Ai)[0, 0] * (n - 1) / (n - k) * nT / (nT - 1)))
        return {"h": h, "b": float(b[0]), "se": se, "n": n}


def panel_irf(bk_dir: Path, weighted: bool = False) -> pd.DataFrame:
    """theta_h, h = 0..10, in percent per 1 C (index h; columns b, se, n)."""
    pan = Panel(bk_dir)
    return pd.DataFrame([pan.fit(h, weighted) for h in range(H_MAX + 1)]).set_index("h")
