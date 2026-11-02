"""Temperature-shock construction, validation and provisional event-year values.

Only *observed* annual means produce "observed" shocks. 2026 and 2027 values here are
explicitly provisional: a nowcast for 2026 (nine observed months plus an analog-based
Oct-Dec estimate) and an ENSO-conditioned regression forecast for the 2027 shock.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import hamilton as H

VOLCANIC_YEARS = (1963, 1964, 1965, 1982, 1983, 1984, 1991, 1992, 1993, 1994)  # Agung, El Chichon, Pinatubo


@dataclass
class ShockSet:
    product: str
    fit: H.HamiltonFit
    T: pd.Series                 # observed annual series used (complete years only)
    shocks: pd.Series            # in-sample + any later observed years
    reference: pd.Series         # pre-event reference distribution for ranks

    def fitted(self, years) -> pd.Series:
        return H.predict(self.fit, self.T, years)

    def rank(self, value: float) -> float:
        return H.percentile_rank(value, self.reference)


def build(product: str, T: pd.Series, data_start: int, calib_end: int, h: int = 2, p: int = 2,
          convention: str = "bk_data", reference: tuple[int, int] | None = None) -> ShockSet:
    """Fit the filter on data from ``data_start`` with dependent years up to ``calib_end``.

    Shocks are reported for every observed year (years after ``calib_end`` use the frozen
    coefficients and are out-of-sample). The reference distribution defaults to the
    in-sample shocks.
    """
    T = T.dropna().loc[data_start:]
    f = H.fit(T, h, p, end=calib_end, convention=convention)
    s = H.shocks(f, T)
    ref = s.loc[f.fit_years[0]:f.fit_years[1]] if reference is None else s.loc[reference[0]:reference[1]]
    return ShockSet(product, f, T, s, ref)


def compare(a: pd.Series, b: pd.Series) -> dict:
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1, join="inner").dropna()
    d = j.a - j.b
    return {"n": int(len(j)), "first": int(j.index.min()), "last": int(j.index.max()),
            "corr": float(j.corr().iloc[0, 1]), "rmse": float(np.sqrt((d ** 2).mean())),
            "max_abs_diff": float(d.abs().max()), "sd_a": float(j.a.std()), "sd_b": float(j.b.std())}


def exact_linear_weights(shock: pd.Series, T: pd.Series, lags=(0, 2, 3, 4)) -> dict:
    """Regress a published shock on [1, T_{t-l}...]; an exact fit reveals its formula."""
    df = pd.DataFrame({"s": shock})
    for l in lags:
        df[f"L{l}"] = T.shift(l)
    df = df.dropna()
    X = np.column_stack([np.ones(len(df))] + [df[f"L{l}"] for l in lags])
    b, *_ = np.linalg.lstsq(X, df["s"].values, rcond=None)
    resid = df["s"].values - X @ b
    out = {"const": float(b[0])}
    out.update({f"T(t-{l})": float(v) for l, v in zip(lags, b[1:])})
    out["max_abs_resid"] = float(np.abs(resid).max())
    return out


# --------------------------------------------------------------------- provisional annual values

ONSET, DECAY = "onset", "decay"


@dataclass
class Provisional:
    """Best current value of an annual global mean that may not be final yet."""
    year: int
    mean: float
    sd: float
    method: str
    months_observed: int
    detail: dict = field(default_factory=dict)
    analogs: pd.DataFrame | None = field(default=None, repr=False)

    @property
    def observed(self) -> bool:
        return self.sd == 0.0


def months_observed(monthly: pd.DataFrame, year: int) -> int:
    """Consecutive observed months from January (0 if the year is absent)."""
    if year not in monthly.index:
        return 0
    return int(monthly.loc[year].notna().cumprod().sum())


def analog_years(oni: pd.DataFrame, monthly: pd.DataFrame, phase: str, before: int) -> list[int]:
    """El Nino onset years (ONI JAS >= 1 and rising into OND) or decay years (ONI DJF >= 1:
    an El Nino peaking in the winter that opens the year), with all 12 months observed."""
    piv = oni.pivot_table(index="year", columns="season", values="anom")
    complete = set(monthly.dropna().index)
    out = []
    for y in piv.index:
        if y >= before or y not in complete:
            continue
        if phase == ONSET and piv.loc[y, "JAS"] >= 1.0 and piv.loc[y, "OND"] > piv.loc[y, "JAS"]:
            out.append(int(y))
        elif phase == DECAY and piv.loc[y, "DJF"] >= 1.0:
            out.append(int(y))
    return out


def nowcast_annual(monthly: pd.DataFrame, oni: pd.DataFrame, year: int, phase: str = ONSET) -> Provisional:
    """Annual mean from the k observed months plus an analog forecast of the rest.

    Remaining months = mean of the last three observed months + the mean change from those
    months to the rest of the year in historical analog years of the same ENSO phase; the
    analogs' spread gives the uncertainty. The rule is fixed in code, not tuned to a year.
    """
    k = months_observed(monthly, year)
    if not 1 <= k <= 11:
        raise ValueError(f"nowcast needs 1-11 observed months for {year}, got {k}")
    cols = list(monthly.columns)
    last, rest = cols[max(0, k - 3):k], cols[k:]
    years = analog_years(oni, monthly, phase, year)
    jump = monthly.loc[years, rest].mean(axis=1) - monthly.loc[years, last].mean(axis=1)
    row = monthly.loc[year]
    rem = float(row[last].mean() + jump.mean())
    ytd = float(row[cols[:k]].mean())
    mean = (k * ytd + (12 - k) * rem) / 12
    sd = (12 - k) * float(jump.std(ddof=1)) / 12
    detail = {"ytd_mean": ytd, "remaining_mean": rem, "jump_mean": float(jump.mean()),
              "jump_sd": float(jump.std(ddof=1)), "n_analogs": len(years), "phase": phase}
    return Provisional(year, mean, sd, f"nowcast ({k} months observed, {phase} analogs)", k, detail,
                       pd.DataFrame({"jump": jump}))


def provisional_temperature(annual: pd.Series, monthly: pd.DataFrame, oni: pd.DataFrame, year: int,
                            phase: str, regression: tuple[float, float, dict] | None = None,
                            min_months: int = 6, label: str = "annual value") -> Provisional:
    """Observed annual value if published; else a nowcast once ``min_months`` are observed;
    else the ENSO-regression forecast ``(mean, sd, detail)``."""
    if year in annual.index:
        return Provisional(year, float(annual.loc[year]), 0.0, f"observed ({label})", 12)
    k = months_observed(monthly, year)
    if k >= min_months:
        return nowcast_annual(monthly, oni, year, phase)
    if regression is None:
        raise ValueError(f"{year}: only {k} months observed and no regression forecast supplied")
    mean, sd, detail = regression
    return Provisional(year, mean, sd, f"ENSO regression ({k} months observed)", k, detail)


# --------------------------------------------------------------------- ENSO model for shocks

@dataclass
class EnsoShockModel:
    index_name: str
    season: str
    coef: np.ndarray        # [const, x(y), x(y-1), x(y-2)]
    cov: np.ndarray
    resid_sd: float
    r2: float
    n: int
    excluded: tuple[int, ...]

    def predict(self, x0: float, x1: float, x2: float) -> tuple[float, float]:
        """Mean and predictive sd (parameter + residual), excluding index uncertainty."""
        z = np.array([1.0, x0, x1, x2])
        mean = float(z @ self.coef)
        sd = float(np.sqrt(z @ self.cov @ z + self.resid_sd ** 2))
        return mean, sd

    def describe(self) -> str:
        c = self.coef
        return (f"s_y = {c[0]:+.3f} {c[1]:+.3f}*{self.index_name}_{self.season}(y) "
                f"{c[2]:+.3f}*{self.index_name}_{self.season}(y-1) {c[3]:+.3f}*{self.index_name}_{self.season}(y-2); "
                f"resid sd {self.resid_sd:.3f} C, R2 {self.r2:.2f}, n={self.n} (volcanic years excluded)")


def fit_enso_shock_model(shocks: pd.Series, index: pd.DataFrame, index_name: str = "RONI",
                         season: str = "DJF", exclude=VOLCANIC_YEARS,
                         years: tuple[int, int] = (1953, 2025)) -> EnsoShockModel:
    """Regress the Hamilton shock on the ENSO index in the winter peaking in years y, y-1, y-2.

    The y-2 term matters because the h=2 filter predicts T_y from T_{y-2}, T_{y-3}: an El
    Nino two years earlier raises the prediction and so lowers the shock.
    """
    piv = index.pivot_table(index="year", columns="season", values="anom")[season]
    yy = [y for y in range(years[0], years[1] + 1)
          if y in shocks.index and y not in exclude and (y - 2) in piv.index and y in piv.index]
    X = np.column_stack([np.ones(len(yy)), piv.loc[yy].values,
                         piv.loc[[y - 1 for y in yy]].values, piv.loc[[y - 2 for y in yy]].values])
    yv = shocks.loc[yy].values
    b, *_ = np.linalg.lstsq(X, yv, rcond=None)
    e = yv - X @ b
    s2 = e @ e / (len(yv) - X.shape[1])
    cov = s2 * np.linalg.inv(X.T @ X)
    return EnsoShockModel(index_name, season, b, cov, float(np.sqrt(s2)), float(1 - e.var() / yv.var()),
                          len(yv), tuple(exclude))
