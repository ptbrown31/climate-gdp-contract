"""Simulated global temperature shocks after the event years, for the H1 prediction.

Strong El Niños are usually followed by cooler years: after the seven strong El Niño
winters since 1950 (winter RONI >= 1.5: 1958, 1966, 1973, 1983, 1992, 1998, 2016) the next
two winters averaged about -0.5. A linear autoregression misses that asymmetry, so a path
whose 2027 winter is a strong El Niño replays the winters that followed one of those
analog events. Otherwise winter RONI follows an AR(2) fitted to 1951-2026.

Each simulated year's Hamilton shock is the ENSO regression's prediction from winter RONI
in y, y-1 and y-2 plus a residual resampled from that regression's residuals in all years
1953-2025. Volcanic years stay in the residual pool, so eruptions occur at their historical
frequency.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import temperature as TM

STRONG = 1.5        # winter RONI threshold for a strong El Niño
HORIZON = 10        # years of post-event winters kept per analog


@dataclass(frozen=True)
class EnsoPaths:
    ar_coef: np.ndarray            # AR(2) for winter RONI: [c, a1, a2]
    ar_resid: np.ndarray           # AR residual pool
    analog_years: tuple[int, ...]  # strong El Niño winters used as analogs
    analog_seqs: np.ndarray        # (m, HORIZON) winter RONI in the years after each analog
    shock_resid: np.ndarray        # ENSO-regression residuals, all years (volcanic included)
    enso: TM.EnsoShockModel

    def describe(self) -> str:
        a = self.ar_coef
        return (f"winter RONI after a strong El Niño: replay of {len(self.analog_years)} analogs "
                f"{list(self.analog_years)}; otherwise AR(2) R_y = {a[0]:+.3f} {a[1]:+.3f} R_(y-1) {a[2]:+.3f} R_(y-2); "
                f"shock = ENSO regression + resampled residual (sd {self.shock_resid.std(ddof=1):.3f} C, "
                f"n={len(self.shock_resid)}, volcanic years included)")


def winter_series(roni: pd.DataFrame) -> pd.Series:
    return roni.pivot_table(index="year", columns="season", values="anom")["DJF"].dropna()


def fit(djf: pd.Series, shocks: pd.Series, enso: TM.EnsoShockModel, last_winter: int = 2026,
        shock_years: tuple[int, int] = (1953, 2025)) -> EnsoPaths:
    d = djf.loc[:last_winter]
    idx = [t for t in d.loc[1951:].index if (t - 1) in d.index and (t - 2) in d.index]
    X = np.column_stack([np.ones(len(idx)), d.loc[[t - 1 for t in idx]].values, d.loc[[t - 2 for t in idx]].values])
    y = d.loc[idx].values
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    ar_resid = y - X @ b
    analogs = tuple(int(t) for t, v in d.items() if v >= STRONG and t + HORIZON <= last_winter)
    seqs = np.array([[d.loc[t + j] for j in range(1, HORIZON + 1)] for t in analogs])
    yy = [t for t in range(shock_years[0], shock_years[1] + 1)
          if t in shocks.index and all((t - j) in djf.index for j in (0, 1, 2))]
    c = enso.coef
    pred = c[0] + c[1] * djf.loc[yy].values + c[2] * djf.loc[[t - 1 for t in yy]].values \
        + c[3] * djf.loc[[t - 2 for t in yy]].values
    return EnsoPaths(b, ar_resid, analogs, seqs, shocks.loc[yy].values - pred, enso)


def simulate(model: EnsoPaths, known: dict[int, float | np.ndarray], years, n: int,
             rng: np.random.Generator) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
    """Shocks and winter RONI for ``years`` (consecutive, starting the year after ``known``).

    ``known`` maps the last three winters before the first simulated year to scalars or
    per-path (n,) arrays, e.g. {2025: R25, 2026: R26, 2027: R27 draws}.
    """
    years = list(years)
    if not years:
        return {}, {}
    if len(years) > HORIZON:
        raise ValueError(f"at most {HORIZON} simulated years (analog sequences are {HORIZON} long)")
    R = {t: np.broadcast_to(np.asarray(v, float), (n,)).copy() for t, v in known.items()}
    event = years[0] - 1
    strong = R[event] >= STRONG
    pick = rng.integers(0, len(model.analog_years), size=n)
    a = model.ar_coef
    c = model.enso.coef
    shocks = {}
    for j, t in enumerate(years):
        ar = a[0] + a[1] * R[t - 1] + a[2] * R[t - 2] + model.ar_resid[rng.integers(0, len(model.ar_resid), n)]
        R[t] = np.where(strong, model.analog_seqs[pick, j], ar)
        shocks[t] = (c[0] + c[1] * R[t] + c[2] * R[t - 1] + c[3] * R[t - 2]
                     + model.shock_resid[rng.integers(0, len(model.shock_resid), n)])
    return shocks, {t: R[t] for t in years}
