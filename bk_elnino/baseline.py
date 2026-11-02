"""No-temperature-effect (H0) baseline for world real GDP per capita.

Growth is always computed on the contiguous level series first (100 x log differences)
and only then filtered by calendar year, so dropping 2020-2021 never manufactures a
2019->2022 growth observation.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def log_growth(levels: pd.Series) -> pd.Series:
    """100 x log growth of a contiguous annual level series (first year is dropped)."""
    lv = levels.dropna().astype(float)
    idx = lv.index.astype(int)
    if (np.diff(idx) != 1).any():
        raise ValueError("level series has gaps; growth would span multiple years")
    if (lv <= 0).any():
        raise ValueError("non-positive levels")
    g = 100 * np.log(lv).diff().dropna()
    g.index = g.index.astype(int)
    return g.rename("growth")


@dataclass(frozen=True)
class NullModel:
    """Frozen null forecast: log y_t = log y_A + mu * (t - A) (all in 100 x log units)."""
    anchor_year: int
    anchor_log_level: float     # 100 x log level at A in the inception vintage
    mu: float                   # mean annual growth over the calibration years
    sigma: float
    calib_growth: np.ndarray    # growth observations used (for resampling)
    calib_years: tuple[int, ...]
    excluded_years: tuple[int, ...]

    def forecast(self, years) -> np.ndarray:
        years = np.asarray(list(years))
        return self.anchor_log_level + self.mu * (years - self.anchor_year)


def fit_null(levels: pd.Series, calib: tuple[int, int], exclude=(), anchor_year: int | None = None) -> NullModel:
    g = log_growth(levels)
    yrs = [y for y in g.index if calib[0] <= y <= calib[1] and y not in set(exclude)]
    x = g.loc[yrs].values
    A = int(levels.dropna().index.max()) if anchor_year is None else anchor_year
    return NullModel(A, float(100 * np.log(levels.loc[A])), float(x.mean()), float(x.std(ddof=1)),
                     x, tuple(yrs), tuple(exclude))


def simulate_deviation(model: NullModel, years, n: int, rng: np.random.Generator, method: str = "iid",
                       block: int = 3, param_uncertainty: bool = True) -> np.ndarray:
    """Simulated log deviations from the frozen forecast, D[n, t] = log y_t - log yhat_t.

    Growth in each future year = mu* + e, where e is resampled from the calibration
    residuals (iid, or moving blocks of length ``block``) and mu* is either mu or, with
    ``param_uncertainty``, the mean of a bootstrap resample of the calibration growth
    (the frozen forecast keeps using mu, so drift error shows up in D).
    """
    years = np.asarray(list(years))
    k = len(years)
    if not (years == np.arange(model.anchor_year + 1, model.anchor_year + 1 + k)).all():
        raise ValueError("simulation years must run consecutively from anchor_year + 1")
    x = model.calib_growth
    resid = x - x.mean()
    m = len(x)
    if method == "iid":
        e = resid[rng.integers(0, m, size=(n, k))]
    elif method == "block":
        nb = int(np.ceil(k / block))
        starts = rng.integers(0, m - block + 1, size=(n, nb))
        idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n, nb * block)[:, :k]
        e = resid[idx]
    else:
        raise ValueError(method)
    if param_uncertainty:
        mu_star = x[rng.integers(0, m, size=(n, m))].mean(axis=1)
    else:
        mu_star = np.full(n, x.mean())
    g = mu_star[:, None] + e
    return np.cumsum(g - model.mu, axis=1)


def backtest(levels: pd.Series, calib_len: int, window: tuple[int, int], origins=None,
             exclude=()) -> pd.DataFrame:
    """Historical pseudo-out-of-sample errors of the frozen-drift rule.

    For each origin A: mu = mean growth over the ``calib_len`` years ending at A
    (excluding ``exclude``), then M = mean over t in [A+window[0], A+window[1]] of
    (log y_t - log y_A - mu (t-A)). Same units as the wager statistic (percent).
    """
    lv = levels.dropna()
    g = log_growth(lv)
    ly = 100 * np.log(lv)
    rows = []
    first, last = int(lv.index.min()), int(lv.index.max())
    cand = range(first + calib_len, last - window[1] + 1) if origins is None else origins
    for A in cand:
        yrs = [y for y in range(A - calib_len + 1, A + 1) if y not in set(exclude) and y in g.index]
        if len(yrs) < calib_len * 0.8:
            continue
        mu = g.loc[yrs].mean()
        ts = np.arange(A + window[0], A + window[1] + 1)
        if ts.max() > last:
            continue
        dev = ly.loc[ts].values - ly.loc[A] - mu * (ts - A)
        rows.append({"origin": A, "mu": mu, "M": dev.mean()})
    return pd.DataFrame(rows, columns=["origin", "mu", "M"]).set_index("origin")
