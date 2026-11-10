"""IMF World Economic Outlook baseline for world GDP per capita (the H0 path) and its spread.

Baseline: per-capita growth implied by the IMF's world real GDP growth and world population
projections (one WEO vintage, frozen), plus the mean gap between WDI per-capita growth and
the IMF-implied figure over 1991-2025, so it is in the units of the settlement series
(WDI NY.GDP.PCAP.PP.KD). Past the last IMF projection year the last projected rate is held.
World population growth is the IMF's world total's, except in a projection year where the total
breaks: there it is summed over the countries with figures in both years (``countries.json``,
the DataMapper's country list). The October 2026 total drops Afghanistan in 2026, the first year
without a figure for it, so its growth falls to 0.28% against 0.82% for the countries.

Spread: the IMF's own historical forecast errors (realized minus forecast world real GDP
growth, by years ahead of the vintage), resampled as whole vintage error paths so that
multi-year misses (recessions, slowdowns) keep their persistence. Until the IMF's historical
forecast file is in data/raw/imf_hist/, ``trend_errors`` supplies a labeled stand-in: the
errors of a 20-year trend forecast of WDI world GDP per capita (USD, 1960-2025).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import baseline as B
from . import xlsx as XL

GAP_YEARS = (1991, 2025)
BREAK_PP = 0.1      # a projection year whose world population growth is this far from the countries' is a break


@dataclass(frozen=True)
class Baseline:
    vintage: str
    growth: pd.Series          # per-capita growth, 100 x log, by year (WDI units)
    imf_growth: pd.Series      # IMF-implied per-capita growth before the WDI gap
    projected_through: int
    wdi_gap: float
    population_repairs: dict = field(default_factory=dict)    # year -> the world total's and the countries' growth

    def window_mean(self, base: int, end: int) -> float:
        return float(self.growth.loc[base + 1:end].mean())

    def cumulative(self, base: int, end: int) -> float:
        return float(self.growth.loc[base + 1:end].sum())


def _datamapper_series(path: Path, indicator: str, area: str = "WEOWORLD") -> pd.Series:
    d = json.loads(path.read_text())["values"][indicator][area]
    return pd.Series({int(k): float(v) for k, v in d.items()}).sort_index()


def population_growth(imf_dir: Path, after: int) -> tuple[pd.Series, dict]:
    """World population growth (100 x log) from the IMF's world total, with each projection year
    (after ``after``) that breaks replaced by growth summed over the countries with figures in
    both years. Breaks in earlier years, when countries joined the IMF's data, stay: the WDI gap
    is fitted on them, and the total tracks WDI growth more closely there than the countries' sum."""
    lp = json.loads((imf_dir / "LP.json").read_text())["values"]["LP"]
    pop = pd.Series({int(k): float(v) for k, v in lp["WEOWORLD"].items()}).sort_index()
    growth = 100 * np.log(pop / pop.shift(1))
    countries = [lp[c] for c in json.loads((imf_dir / "countries.json").read_text())["countries"] if c in lp]
    repairs = {}
    for t in growth.index[growth.index > after]:
        both = [c for c in countries if str(t - 1) in c and str(t) in c]
        own = float(100 * np.log(sum(c[str(t)] for c in both) / sum(c[str(t - 1)] for c in both)))
        if abs(own - growth[t]) > BREAK_PP:
            repairs[int(t)] = {"world_total_pp": float(growth[t]), "countries_pp": own, "n_countries": len(both)}
            growth[t] = own
    return growth, repairs


def load_baseline(imf_dir: Path, wdi: pd.Series, last_year: int, vintage: str) -> Baseline:
    g = _datamapper_series(imf_dir / "NGDP_RPCH.json", "NGDP_RPCH")
    wdi_g = B.log_growth(wdi)
    pop_g, repairs = population_growth(imf_dir, int(wdi_g.index.max()))
    imf_pc = (100 * np.log1p(g / 100) - pop_g).dropna()
    common = imf_pc.index.intersection(wdi_g.index)
    common = [t for t in common if GAP_YEARS[0] <= t <= GAP_YEARS[1]]
    gap = float((wdi_g.loc[common] - imf_pc.loc[common]).mean())
    through = int(g.index.max())
    grown = imf_pc + gap
    ext = pd.Series({t: grown.loc[through] for t in range(through + 1, last_year + 1)})
    full = pd.concat([grown, ext]).sort_index()
    return Baseline(vintage, full, imf_pc, through, gap, repairs)


@dataclass(frozen=True)
class ErrorModel:
    """Realized-minus-forecast annual growth by lead, one row per historical forecast.

    Lead k is the k-th year after the last year the forecast observed: for an October WEO
    of year V (which observes V-1), lead 1 is V and lead 3 is V+2.
    """
    source: str
    paths: np.ndarray            # (m, L): errors for leads 1..L
    origins: tuple[int, ...]     # last observed year of each forecast

    @property
    def max_lead(self) -> int:
        return self.paths.shape[1]


def trend_errors(levels: pd.Series, calib_len: int = 20, max_lead: int = 12) -> ErrorModel:
    """Stand-in spread: realized minus 20-year-mean growth, by lead, for every origin with
    ``max_lead`` later years observed. Origin A = last observed year (lead 1 = A + 1)."""
    g = B.log_growth(levels)
    rows, origins = [], []
    for A in g.index:
        past = g.loc[:A].iloc[-calib_len:]
        fut = g.loc[A + 1:A + max_lead]
        if len(past) < calib_len or len(fut) < max_lead:
            continue
        rows.append(fut.values - past.mean())
        origins.append(int(A))
    return ErrorModel(f"stand-in: errors of a {calib_len}-year trend forecast of WDI world GDP per capita "
                      f"(USD), origins {origins[0]}-{origins[-1]}", np.array(rows), tuple(origins))


def simulate_deviation(model: ErrorModel, years, n: int, rng: np.random.Generator, last_observed: int,
                       smooth: float = 0.5) -> np.ndarray:
    """D[n, t]: cumulative realized-minus-baseline growth from the first simulated year on.

    Smoothed bootstrap: each path starts from one historical forecast's error path (so
    multi-year misses keep their persistence) shrunk toward the mean, plus correlated
    Gaussian noise with the same covariance across leads scaled by ``smooth``; the mixture
    keeps the historical mean and covariance but is continuous rather than a handful of
    discrete paths. Years past the model's longest lead are drawn independently, each from that
    lead's errors: the IMF's misses in neighbouring years are close to uncorrelated (about
    -0.1 between leads 2-6), so repeating one path's last error would overstate the spread.
    """
    years = np.asarray(list(years))
    leads = years - last_observed
    if (leads < 1).any():
        raise ValueError("simulation starts before the forecast's first lead")
    k = int((leads <= model.max_lead).sum())
    shrink = 1.0 / np.sqrt(1.0 + smooth ** 2)
    e = np.empty((n, 0))
    if k:
        P = model.paths[:, leads[:k] - 1]
        mean = P.mean(axis=0)
        cov = np.cov(P, rowvar=False).reshape(k, k) + 1e-9 * np.eye(k)
        pick = rng.integers(0, P.shape[0], size=n)
        noise = rng.multivariate_normal(np.zeros(k), cov, size=n, method="eigh")
        e = mean + shrink * (P[pick] - mean) + shrink * smooth * noise
    if k < len(years):
        last = model.paths[:, -1]
        m, sd = last.mean(), last.std(ddof=1)
        pick = rng.integers(0, len(last), size=(n, len(years) - k))
        z = rng.standard_normal((n, len(years) - k))
        e = np.c_[e, m + shrink * (last[pick] - m) + shrink * smooth * sd * z]
    return np.cumsum(e, axis=1)


def load_errors(hist_dir: Path, imf_dir: Path, usd_levels: pd.Series) -> ErrorModel:
    """IMF historical forecast errors if the IMF file is present and readable, else the labeled
    stand-in (whose source then says why the file was not used)."""
    files = sorted(f for f in hist_dir.glob("*.xls*") if not f.name.startswith("~$")) if hist_dir.exists() else []
    if not files:
        return trend_errors(usd_levels)
    try:
        return imf_errors(files[0], _datamapper_series(imf_dir / "NGDP_RPCH.json", "NGDP_RPCH"))
    except Exception as e:  # noqa: BLE001 - keep the refresh running on the labeled stand-in
        m = trend_errors(usd_levels)
        return ErrorModel(f"{m.source} [IMF file {files[0].name} not used: {type(e).__name__}: {e}]", m.paths, m.origins)


VINTAGE = re.compile(r"F(\d{4})ngdp_rpch", re.IGNORECASE)


def imf_errors(path: Path, realized: pd.Series, last_realized: int = 2025, max_lead: int = 6,
               min_forecasts: int = 10) -> ErrorModel:
    """World real GDP growth errors of the October WEO vintages in the IMF's historical forecast
    file (WEOhistorical.xlsx, sheet ``ngdp_rpch``: one row per country and target year, one column
    per vintage, ``F2019ngdp_rpch`` = October 2019 WEO).

    Lead k of the October vintage of year V targets year V+k-1 (it observes V-1). Realized values
    are the current DataMapper estimates. Errors are 100 x log points; population forecast errors
    are ignored (they are tiny next to growth errors), so these stand for per-capita errors.
    """
    parts = XL.sheet_parts(path)
    name = next((k for k in parts if str(k).strip().lower() == "ngdp_rpch"), None)
    if name is None:
        raise ValueError(f"no ngdp_rpch sheet (sheets: {list(parts)[:8]})")
    rows = XL.read_sheet(path, name)
    width = max(len(r) for r in rows)
    raw = pd.DataFrame([r + [None] * (width - len(r)) for r in rows])
    hdr = next((i for i in range(min(len(raw), 30))
                if raw.iloc[i].astype(str).str.strip().str.fullmatch(VINTAGE.pattern, case=False).any()), None)
    if hdr is None:
        raise ValueError("no October-vintage columns like F2019ngdp_rpch")
    df = raw.iloc[hdr + 1:].copy()
    df.columns = [str(c).strip() for c in raw.iloc[hdr]]
    ycol = next(c for c in df.columns if c.lower() == "year")
    ccol = next((c for c in df.columns if c.lower() == "country"), None)
    codes = next((c for c in df.columns if c.lower() == "weo_country_code"), None)
    world = df[df[ccol].astype(str).str.strip().str.lower() == "world"] if ccol else df.iloc[:0]
    if world.empty and codes:
        world = df[pd.to_numeric(df[codes], errors="coerce") == 1]
    if world.empty:
        raise ValueError("no World rows")
    world = world.assign(_y=pd.to_numeric(world[ycol], errors="coerce")).dropna(subset=["_y"])
    world = world.set_index(world["_y"].astype(int))
    vintages = sorted((int(VINTAGE.fullmatch(c).group(1)), c) for c in df.columns if VINTAGE.fullmatch(c))

    def lg(g):
        return 100 * np.log1p(np.asarray(g, float) / 100)

    rows, origins = [], []
    for V, col in vintages:
        targets = list(range(V, V + max_lead))
        if targets[-1] > last_realized:
            continue
        f = pd.to_numeric(world[col], errors="coerce").reindex(targets)
        r = realized.reindex(targets)
        if f.isna().any() or r.isna().any():
            continue
        rows.append(lg(r.values) - lg(f.values))
        origins.append(V - 1)
    if len(rows) < min_forecasts:
        raise ValueError(f"only {len(rows)} complete October vintages")
    return ErrorModel(f"IMF WEO historical forecasts: world real GDP growth, October vintages {origins[0] + 1}-"
                      f"{origins[-1] + 1} ({len(rows)} forecasts), realized = October 2026 WEO estimates",
                      np.array(rows), tuple(origins))
