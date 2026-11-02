"""Hamilton (2018) regression filter for annual global-mean temperature.

Shock in year t (Bilal-Kaenzig notation):

    s_t = T_t - (a + b_1 T_{t-h} + ... + b_p T_{t-h-p+1})

i.e. ``p`` lagged regressors starting at lag ``h``. For the PWT specification
(h=2, p=2) the regressors are T_{t-2} and T_{t-3}.

Why ``p`` and not ``p+1`` regressors: equation (1) of the QJE paper is typeset with
coefficients b_1..b_{p+1}, but the shock series the authors actually used
(``gtmp_bkly_aw_dtfe2`` in their replication data) is an exact linear function of
T_t, T_{t-2}, T_{t-3} with a zero weight on T_{t-4}, and the BU series (p=6) starts in
1857 from data beginning in 1850, which is only possible with lags 2..7. The
``paper_eq1`` convention (lags h..h+p) is kept for sensitivity analysis only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

CONVENTIONS = ("bk_data", "paper_eq1")


def lag_set(h: int, p: int, convention: str = "bk_data") -> tuple[int, ...]:
    if convention == "bk_data":
        return tuple(range(h, h + p))
    if convention == "paper_eq1":
        return tuple(range(h, h + p + 1))
    raise ValueError(f"unknown convention {convention!r}; expected one of {CONVENTIONS}")


def _check_annual(T: pd.Series) -> pd.Series:
    T = T.dropna().astype(float)
    idx = T.index.astype(int)
    if idx.has_duplicates:
        raise ValueError("duplicate years in temperature series")
    if (np.diff(np.sort(idx)) != 1).any():
        raise ValueError("temperature series must be consecutive annual years without gaps")
    return pd.Series(T.values, index=idx).sort_index()


def design(T: pd.Series, years, lags: tuple[int, ...]) -> np.ndarray:
    """Rows [1, T_{t-l} for l in lags] for each year t (explicit year lookup)."""
    T = _check_annual(T)
    rows = []
    for t in years:
        rows.append([1.0] + [T.loc[t - l] for l in lags])
    return np.asarray(rows, dtype=float)


@dataclass(frozen=True)
class HamiltonFit:
    h: int
    p: int
    convention: str
    lags: tuple[int, ...]
    coef: np.ndarray  # [const, b_lag1, b_lag2, ...]
    fit_years: tuple[int, int]
    n: int
    resid_sd: float

    def describe(self) -> str:
        terms = " + ".join(f"{b:.4f} T(t-{l})" for b, l in zip(self.coef[1:], self.lags))
        return (f"T(t) = {self.coef[0]:.4f} + {terms};  fit years {self.fit_years[0]}-"
                f"{self.fit_years[1]} (n={self.n}), resid sd {self.resid_sd:.4f} C")


def available_years(T: pd.Series, lags: tuple[int, ...]) -> list[int]:
    T = _check_annual(T)
    first = T.index.min() + max(lags)
    return [t for t in T.index if t >= first]


def fit(T: pd.Series, h: int = 2, p: int = 2, start: int | None = None, end: int | None = None,
        convention: str = "bk_data") -> HamiltonFit:
    """OLS of T_t on a constant and the lag set, for dependent years t in [start, end].

    ``start``/``end`` bound the *dependent-variable* years; lagged regressors may come
    from earlier years. If ``start`` is None the first year with all lags is used.
    """
    T = _check_annual(T)
    lags = lag_set(h, p, convention)
    yrs = [t for t in available_years(T, lags)
           if (start is None or t >= start) and (end is None or t <= end)]
    if len(yrs) < len(lags) + 5:
        raise ValueError("too few observations for the Hamilton regression")
    X = design(T, yrs, lags)
    y = T.loc[yrs].values
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    dof = len(y) - X.shape[1]
    return HamiltonFit(h, p, convention, lags, coef, (yrs[0], yrs[-1]), len(yrs),
                       float(np.sqrt(resid @ resid / dof)))


def predict(f: HamiltonFit, T: pd.Series, years) -> pd.Series:
    """Filter prediction of T_t from lags only (needs T_{t-l} for all lags, not T_t)."""
    T = _check_annual(T)
    years = list(years)
    X = design(T, years, f.lags)
    return pd.Series(X @ f.coef, index=years, name="hamilton_fitted")


def shocks(f: HamiltonFit, T: pd.Series, years=None) -> pd.Series:
    """s_t = T_t - prediction, for years where T_t and all lags are observed."""
    T = _check_annual(T)
    if years is None:
        years = available_years(T, f.lags)
    years = [t for t in years if t in T.index]
    pred = predict(f, T, years)
    return pd.Series(T.loc[years].values - pred.values, index=years, name="shock")


def shock_from_value(f: HamiltonFit, T: pd.Series, year: int, value: float | np.ndarray):
    """Shock for ``year`` if T_year took ``value`` (lags taken from the observed series).

    Used for provisional/forecast years: the lagged inputs are already observed, only
    T_year is uncertain, so the shock is ``value - prediction``.
    """
    pred = float(predict(f, T, [year]).iloc[0])
    return np.asarray(value, dtype=float) - pred


def percentile_rank(value: float, reference: pd.Series) -> float:
    """Share (0-100) of reference shocks strictly below ``value`` (ties count half)."""
    r = np.asarray(reference.dropna(), dtype=float)
    return float(100.0 * ((r < value).sum() + 0.5 * (r == value).sum()) / len(r))
