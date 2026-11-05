"""End-to-end pipeline: data -> shocks -> IRFs -> H0/H1 simulation -> contract metrics.

Everything that defines the design lives in :class:`Design` (one frozen dataclass), so a
variant is ``replace(PRIMARY, field=value)`` and every number in the outputs can be
traced to a named design.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
import pandas as pd

from . import baseline as B
from . import future_temps as FT
from . import hamilton as H
from . import imf_baseline as IB
from . import irf as I
from . import sources as S
from . import temperature as TM
from . import wager as W

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
BK = ROOT / "data" / "external" / "micc_replication"
BK_SHOCKS = ROOT / "data" / "external" / "global-temperature-shocks" / "1 Temperature shocks"

EVENT_YEARS = (2026, 2027)
ANCHOR = 2025                     # last WDI observation before the event's GDP effects
IRF_SAMPLE = {"PWT_ts": "PWT", "PWT_ts_NWscaled": "PWT", "PWT_ts_wide": "PWT", "PWT_panel": "PWT",
              "PWT_panel_gdpw": "PWT", "PWT_ts_transitory": "PWT", "PWT_ts_noaa": "PWT", "PWT_ts_wdi": "PWT",
              "BU_ts": "BU", "BU_panel": "BU", "BU_ts_transitory": "BU"}


@dataclass(frozen=True)
class Design:
    name: str = "primary"
    # temperature-shock definition: NOAA throughout (decided 23 Oct 2026). PWT-family IRFs use
    # NOAA h=2 p=2: the paper built those shocks from Berkeley Earth, whose public series is not
    # updated monthly, and reports that its Berkeley measure tracks NOAA almost perfectly.
    # BU-family IRFs use NOAA h=2 p=6, as in the paper.
    data_start: int | None = None          # None -> 1950 (PWT family) / 1850 (BU family)
    calib_end: int = 2022                  # decided 30 Oct 2026: the paper's own filter window (data through 2022),
                                           # so the 2023-27 warmth is measured out of sample, not fitted as trend
    convention: str = "bk_data"
    # IRF and how it is applied
    irf: str = "PWT_ts"
    irf_uncertainty: bool = True
    composition: str = "innovation"        # innovation | raw
    scope: str = "full"                    # decided 17 Oct 2026: full (all shocks with post-2025 effects) | recent (2023-27) | incremental (2026-27)
    beyond: str = "hold"                   # IRF beyond h=10: hold theta_10 | zero
    # frozen null (H0)
    calib: tuple[int, int] = (2000, 2019)
    exclude: tuple[int, ...] = ()
    null_method: str = "iid"
    param_uncertainty: bool = True
    drift_sd_extra: float = 0.0            # structural drift uncertainty, pp/yr (frozen baseline only)
    baseline: str = "imf"                  # decided 30 Oct 2026: IMF WEO projection (imf) | frozen 2000-2019 drift (frozen)
    h1_background: str = "net"             # paper's world: IMF misses net of the paper's implied temperature part (net) | raw
    future_temps: str = "simulate"         # decided 30 Oct 2026: simulate post-2027 shocks (simulate) | none
    # contract statistic: M = 100*[log y_end - log y_base] minus baseline growth over the same years
    base_year: int = 2026                  # decided 30 Oct 2026: growth from the 2026 level. Contracts list right
                                           # after NOAA's 2026 annual value (mid-Jan 2027), before any 2027 growth
    window: tuple[int, int] = (2030, 2030)   # end year: picked by the horizon scan each run until locked
    note: str = ""


PRIMARY = Design(note="PWT time-series IRF (paper Fig. III) with bootstrap uncertainty; NOAA h=2 p=2 "
                      "shocks, filter fitted on the paper's window (data 1950-2022); innovation composition; "
                      "all shocks with post-2025 effects plus simulated post-2027 shocks; no-effect path = IMF "
                      "WEO projection (October 2026) in WDI units with the IMF's historical forecast errors "
                      "(average miss kept); in the paper's world the background is net of the part of those "
                      "misses the paper's estimates attribute to temperature shocks; statistic = per-capita "
                      "growth from 2026 to the end year minus IMF baseline growth over the same years.")

# End year of the growth period. Rule (decided 30 Oct 2026): the end year in SCAN_END_YEARS with
# the highest Youden J between the two hypotheses, to two decimals, ties to the earlier year.
# It uses only information available before listing (the paper's IRF, the IMF baseline and its
# error record, temperature forecasts), never GDP after 2025. Frozen when the conditional
# contracts list (right after NOAA's 2026 annual value, mid-Jan 2027); set END_YEAR_LOCKED then.
SCAN_END_YEARS = range(2028, 2038)
END_YEAR_LOCKED: int | None = None

# The trend baseline's start-year test (Patrick, 5 Nov 2026): average growth from a start year
# through 2019, the last year before the pandemic, with its spread drawn from the same years.
# Starts stop at 2005 so every window holds the 2009 recession; a window from 2010 on holds no
# recession, and its spread is too narrow to be credible (J of 0.91-0.96).
TREND_END = 2019
TREND_STARTS = tuple(range(1991, 2006))


# ----------------------------------------------------------------------------- context

@dataclass
class Context:
    gistemp: pd.Series
    gistemp_monthly: pd.DataFrame
    noaa: pd.Series                        # contract record: NOAA annual, deg C vs 1901-2000
    noaa_monthly: pd.DataFrame
    berkeley: pd.Series
    oni: pd.DataFrame
    roni: pd.DataFrame
    wdi: pd.Series
    wdi_meta: dict
    wdi_usd: pd.Series
    irfs: dict
    filters: dict
    prov26: TM.Provisional                 # placeholder or observed NOAA annual means
    prov27: TM.Provisional
    enso: TM.EnsoShockModel
    T26: tuple[float, float]               # (mean, sd); sd = 0 once observed
    T27: tuple[float, float]
    s27_forecast: tuple[float, float]      # ENSO-regression forecast of the 2027 shock
    roni_djf_assumption: tuple[float, float]
    roni_djf_2027_observed: bool
    noaa_offset: float
    vintages: dict = field(default_factory=dict)
    imf: IB.Baseline | None = None          # H0 path: IMF WEO projection in WDI units
    imf_errors: IB.ErrorModel | None = None  # spread of H0 around it
    enso_paths: FT.EnsoPaths | None = None   # post-2027 temperature shocks under H1
    djf: pd.Series | None = None             # winter (DJF) RONI
    forecast_filter: H.HamiltonFit | None = None  # filter on all data through 2025: temperature forecasts and the
                                                  # simulated post-2027 shocks are expressed relative to it


def read_roni(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=r"\s+")
    df.columns = ["season", "year", "anom"]
    df["year"] = df["year"].astype(int)
    return df


def load_context(nboot: int = 4000, seed: int = 123, refresh: bool = False,
                 roni_djf_2027: tuple[float, float] = (2.6, 0.35)) -> Context:
    paths = S.fetch_all(RAW, refresh=refresh)
    gis, mon = S.read_gistemp(paths["gistemp"])
    noaa = S.read_noaa_cag(paths["noaa"])
    noaa_mon = S.read_noaa_monthly(paths["noaa_monthly"])
    full = noaa_mon.dropna()
    gap = (full.mean(axis=1) - noaa.reindex(full.index)).abs().max()
    if not gap <= 0.011:
        raise ValueError(f"NOAA annual values do not match monthly means (max gap {gap})")
    berk = S.read_berkeley_summary(paths["berkeley"])
    oni = S.read_oni(paths["oni"])
    roni_path = RAW / "context" / "RONI.ascii.txt"
    if not roni_path.exists() or refresh:
        S.fetch(S.Source("context", "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt",
                         "RONI.ascii.txt"), RAW, refresh=True)
    roni = read_roni(roni_path)
    wdi, meta = S.read_wdi_json(paths["wdi_gdppc_ppp"])
    usd, _ = S.read_wdi_json(paths["wdi_gdppc_usd"])
    irfs = I.load_irfs(BK, nboot=nboot, seed=seed)
    filters = {"PWT": I.fit_innovation_filter(BK, "PWT"), "BU": I.fit_innovation_filter(BK, "BU")}

    # event-year temperatures: observed when NOAA publishes the annual value, otherwise a
    # placeholder (nowcast from observed months, or the ENSO regression early in the year)
    primary = TM.build("NOAA", noaa.loc[:2025], 1950, 2025)
    enso = TM.fit_enso_shock_model(primary.shocks, roni, "RONI", "DJF")
    djf = roni.pivot_table(index="year", columns="season", values="anom")["DJF"]
    djf27_obs = 2027 in djf.index and np.isfinite(djf.loc[2027])
    djf27 = (float(djf.loc[2027]), 0.0) if djf27_obs else roni_djf_2027
    f26, f27 = primary.fitted([2026, 2027]).values
    m26, sd26 = enso.predict(djf.loc[2026], djf.loc[2025], djf.loc[2024])
    m27, sd27 = enso.predict(djf27[0], djf.loc[2026], djf.loc[2025])
    sd27 = float(np.sqrt(sd27 ** 2 + (enso.coef[1] * djf27[1]) ** 2))
    prov26 = TM.provisional_temperature(noaa, noaa_mon, oni, 2026, TM.ONSET,
                                        (f26 + m26, sd26, {"shock_forecast": m26}), label="NOAA annual")
    prov27 = TM.provisional_temperature(noaa, noaa_mon, oni, 2027, TM.DECAY,
                                        (f27 + m27, sd27, {"shock_forecast": m27, "roni_djf_2027": djf27,
                                                           "roni_djf_2027_observed": bool(djf27_obs)}),
                                        label="NOAA annual")
    offset = float((gis - noaa).dropna().loc[2016:2025].mean())
    vint = {k: S.vintage(RAW, k) for k in S.SOURCES}
    vint["wdi_lastupdated"] = meta.get("lastupdated")
    vint["bk_replication_commit"] = _git_head(BK)
    vint["bk_shocks_commit"] = _git_head(BK_SHOCKS.parent)
    imf_file = RAW / "imf" / "NGDP_RPCH.json"
    imf = IB.load_baseline(RAW / "imf", wdi, 2040, "IMF World Economic Outlook, October 2026 (DataMapper, retrieved "
                           + pd.Timestamp(imf_file.stat().st_mtime, unit="s").strftime("%d %b %Y") + ")")
    imf_errors = IB.load_errors(RAW / "imf_hist", RAW / "imf", usd)
    djf_all = FT.winter_series(roni)
    enso_paths = FT.fit(djf_all, primary.shocks, enso)
    vint["imf_baseline"] = imf.vintage
    vint["imf_errors"] = imf_errors.source
    return Context(gis, mon, noaa, noaa_mon, berk, oni, roni, wdi, meta, usd, irfs, filters, prov26, prov27, enso,
                   (prov26.mean, prov26.sd), (prov27.mean, prov27.sd), (float(m27), sd27), roni_djf_2027,
                   bool(djf27_obs), offset, vint, imf=imf, imf_errors=imf_errors, enso_paths=enso_paths, djf=djf_all,
                   forecast_filter=primary.fit)


def _git_head(path: Path) -> str | None:
    head = path / ".git" / "HEAD"
    if not head.exists():
        return None
    ref = head.read_text().strip()
    if ref.startswith("ref:"):
        p = path / ".git" / ref.split()[1]
        return p.read_text().strip() if p.exists() else None
    return ref


# ----------------------------------------------------------------------------- shocks

def shock_set(ctx: Context, d: Design) -> TM.ShockSet:
    sample = IRF_SAMPLE[d.irf]
    if sample == "PWT":
        return TM.build("NOAA", ctx.noaa.loc[:2025], d.data_start or 1950, d.calib_end, 2, 2, d.convention)
    return TM.build("NOAA", ctx.noaa.loc[:2025], d.data_start or 1850, d.calib_end, 2, 6, d.convention)


def event_shocks(ctx: Context, d: Design, T26, T27) -> tuple[dict, TM.ShockSet]:
    """Raw shocks by year: observed through 2025, provisional/conditional for 2026-27.

    ``T26``/``T27`` are NOAA annual anomalies (scalars or per-path arrays), the record both
    IRF families' shocks are built from.
    """
    ss = shock_set(ctx, d)
    off = 0.0
    s = {int(t): float(v) for t, v in ss.shocks.items()}
    f26, f27 = ss.fitted([2026, 2027]).values
    s[2026] = np.asarray(T26, float) - off - f26
    s[2027] = np.asarray(T27, float) - off - f27
    return s, ss


def impulses(ctx: Context, d: Design, T26, T27, future: dict | None = None) -> dict:
    """Impulses for every shock that moves GDP after the anchor; ``future`` adds simulated
    post-2027 shocks (per path), which are part of the outcome under H1 whatever the scope."""
    s, _ = event_shocks(ctx, d, T26, T27)
    fut = sorted(future) if future else []
    if future:
        s.update(future)
    if d.scope == "incremental":
        years = list(EVENT_YEARS)
    elif d.scope == "recent":
        years = list(range(2023, EVENT_YEARS[-1] + 1))
    elif d.scope == "full":
        years = list(range(ANCHOR - I.H_MAX, EVENT_YEARS[-1] + 1))
    else:
        raise ValueError(d.scope)
    years = years + fut
    if d.irf.endswith("_transitory") or d.composition == "raw":
        return {t: s[t] for t in years}
    if d.composition != "innovation":
        raise ValueError(d.composition)
    return ctx.filters[IRF_SAMPLE[d.irf]].apply(s, years)


def remeasure(ctx: Context, d: Design, T26, T27, future: dict) -> dict:
    """Simulated post-2027 shocks, re-expressed with the design's filter.

    They are simulated relative to ``ctx.forecast_filter`` (all data through 2025). Rebuilding
    the temperature path from them and measuring it with the design's filter keeps one shock
    definition throughout: with the paper's 2022 window, a lasting warmer level keeps
    registering as positive shocks, exactly as it does for 2023-27.
    """
    fit = shock_set(ctx, d).fit
    ff = ctx.forecast_filter
    if fit.lags == ff.lags and np.allclose(fit.coef, ff.coef):
        return future
    T = {int(t): float(v) for t, v in ctx.noaa.loc[:2025].items()}
    T[2026], T[2027] = np.asarray(T26, float), np.asarray(T27, float)
    out = {}
    for t in sorted(future):
        T[t] = ff.coef[0] + sum(b * T[t - lag] for b, lag in zip(ff.coef[1:], ff.lags)) + future[t]
        out[t] = T[t] - (fit.coef[0] + sum(b * T[t - lag] for b, lag in zip(fit.coef[1:], fit.lags)))
    return out


_PAST: dict = {}


def paper_effects_on_imf_windows(ctx: Context, d: Design) -> np.ndarray:
    """(m, L) growth effects, by forecast lead, that the paper's estimates imply for the temperature
    shocks behind each of the IMF's historical forecast windows (October vintages; point IRF)."""
    key = (d.irf, d.calib_end, d.data_start, d.convention, d.composition, d.beyond, id(ctx.imf_errors))
    if key not in _PAST:
        s = shock_set(ctx, d).shocks
        filt = ctx.filters[IRF_SAMPLE[d.irf]]
        raw = d.irf.endswith("_transitory") or d.composition == "raw"
        imp = {int(t): float(v) for t, v in s.items()} if raw else \
            filt.apply(s, [int(t) for t in s.index if t - filt.lags in s.index])
        em, th = ctx.imf_errors, ctx.irfs[d.irf].theta
        L = em.max_lead
        _PAST[key] = np.array([np.diff(I.effect_path(th, {t: v for t, v in imp.items() if t <= o + L},
                                                     list(range(o, o + L + 1)), beyond=d.beyond)[0])
                               for o in em.origins])
    return _PAST[key]


def paper_drag_by_lead(ctx: Context, d: Design) -> np.ndarray:
    """Mean of :func:`paper_effects_on_imf_windows` by lead. Under H1 the IMF's past misses are
    background plus these effects; the paper's world keeps the background only, because its own
    climate damage enters through the shocks since 2015."""
    return paper_effects_on_imf_windows(ctx, d).mean(axis=0)


# ----------------------------------------------------------------------------- simulation

@dataclass
class SimResult:
    design: Design
    years: np.ndarray
    null: B.NullModel
    D0: np.ndarray
    D1: np.ndarray
    effect: np.ndarray
    m0: np.ndarray
    m1: np.ndarray
    future: dict | None = None      # simulated post-2027 shocks by year (per path)
    inputs: dict | None = None      # the path-level draws (IRF draw index, 2026-27 temperatures, post-2027
                                    # shocks before re-measuring), so the site's model can replay them

    def oc(self) -> W.OperatingCharacteristics:
        return W.youden_threshold(self.m0, self.m1)


@dataclass(frozen=True)
class ImfNull:
    """H0 built on the IMF projection; ``mu`` is its mean growth over the statistic's years."""
    mu: float
    baseline: IB.Baseline
    errors: IB.ErrorModel
    anchor_year: int
    anchor_log_level: float     # 100 x log WDI level at the anchor

    def forecast(self, years) -> np.ndarray:
        years = np.asarray(list(years))
        g = self.baseline.growth
        return self.anchor_log_level + np.array([g.loc[self.anchor_year + 1:t].sum() for t in years])


def null_deviations(ctx: Context, d: Design, years, n: int, seed: int):
    if d.baseline == "imf":
        D0 = IB.simulate_deviation(ctx.imf_errors, years, n, np.random.default_rng(seed), last_observed=ANCHOR)
        return D0, ImfNull(ctx.imf.window_mean(d.base_year, d.window[1]), ctx.imf, ctx.imf_errors, ANCHOR,
                           float(100 * np.log(ctx.wdi.loc[ANCHOR])))
    if d.baseline != "frozen":
        raise ValueError(d.baseline)
    null = B.fit_null(ctx.wdi, d.calib, d.exclude, anchor_year=ANCHOR)
    rng = np.random.default_rng(seed)
    D0 = B.simulate_deviation(null, years, n, rng, d.null_method, param_uncertainty=d.param_uncertainty)
    if d.drift_sd_extra > 0:
        D0 = D0 + rng.normal(0, d.drift_sd_extra, size=(n, 1)) * (np.asarray(years) - ANCHOR)[None, :]
    return D0, null


def simulate(ctx: Context, d: Design, n: int = 50_000, seed: int = 20261017, T26=None, T27=None,
             D0_cache: dict | None = None) -> SimResult:
    """Common random numbers: the same seed gives the same H0 paths, IRF draws and
    temperature draws across designs, so differences between designs are not MC noise."""
    years = np.arange(ANCHOR + 1, max(2035, d.window[1]) + 1)
    key = (d.baseline, d.base_year, d.window, d.calib, d.exclude, d.null_method, d.param_uncertainty,
           d.drift_sd_extra, len(years), n, seed)
    if D0_cache is not None and key in D0_cache:
        D0, null = D0_cache[key]
    else:
        D0, null = null_deviations(ctx, d, years, n, seed)
        if D0_cache is not None:
            D0_cache[key] = (D0, null)
    rng = np.random.default_rng(seed + 1)
    irf = ctx.irfs[d.irf]
    idx = rng.integers(0, irf.draws.shape[0], size=n)
    theta = irf.draws[idx] if d.irf_uncertainty else irf.theta
    z26, z27 = rng.standard_normal(n), rng.standard_normal(n)
    T26v = ctx.T26[0] + ctx.T26[1] * z26 if T26 is None else T26
    T27v = ctx.T27[0] + ctx.T27[1] * z27 if T27 is None else T27
    future = future_raw = None
    if d.future_temps == "simulate":
        rng_t = np.random.default_rng(seed + 2)
        r27 = (float(ctx.djf.loc[2027]) if ctx.roni_djf_2027_observed
               else rng_t.normal(ctx.roni_djf_assumption[0], ctx.roni_djf_assumption[1], size=n))
        fut_years = [int(t) for t in years if t > EVENT_YEARS[-1]]
        future_raw, _ = FT.simulate(ctx.enso_paths, {2025: float(ctx.djf.loc[2025]), 2026: float(ctx.djf.loc[2026]),
                                                      2027: r27}, fut_years, n, rng_t)
        future = remeasure(ctx, d, T26v, T27v, future_raw)
    elif d.future_temps != "none":
        raise ValueError(d.future_temps)
    imp = impulses(ctx, d, T26v, T27v, future)
    eff = I.effect_path(theta, imp, years, anchor=ANCHOR, beyond=d.beyond)
    if eff.shape[0] == 1:
        eff = np.repeat(eff, n, axis=0)
    D1 = D0 + eff
    if d.baseline == "imf" and d.h1_background == "net":
        drag = paper_drag_by_lead(ctx, d)
        D1 = D1 - np.cumsum(drag[np.minimum(years - ANCHOR, len(drag)) - 1])[None, :]
    elif d.h1_background not in ("net", "raw"):
        raise ValueError(d.h1_background)
    m0 = statistic(D0, years, d.window, d.base_year)
    m1 = statistic(D1, years, d.window, d.base_year)
    return SimResult(d, years, null, D0, D1, eff, m0, m1, future,
                     {"idx": idx, "T26": T26v, "T27": T27v, "future_raw": future_raw})


def statistic(D: np.ndarray, years, window: tuple[int, int], base_year: int, anchor: int = ANCHOR) -> np.ndarray:
    """M per path: mean over the window of the deviation from the frozen null, re-based to base_year.

    ``D`` is measured from the last observed year (``anchor``). Re-basing subtracts D at
    base_year, which is exactly what anchoring the frozen baseline at the base-year level
    does: M = mean_t 100*[log y_t - log y_base] - mu*(t - base).
    """
    if base_year < anchor or window[0] <= base_year:
        raise ValueError("need anchor <= base_year < window start")
    m = W.window_mean(D, years, window)
    if base_year == anchor:
        return m
    years = np.asarray(list(years))
    j = np.flatnonzero(years == base_year)
    if len(j) != 1:
        raise ValueError("base year not among simulated years")
    return m - np.atleast_2d(D)[:, j[0]]


def mean_horizon(d: Design) -> float:
    return float(np.mean(np.arange(d.window[0], d.window[1] + 1) - d.base_year))


def growth_equivalent(mu: float, d: Design, c: float) -> float:
    """Constant annual growth (pp) that would put M exactly at c."""
    return mu + c / mean_horizon(d)


def stat_label(d: Design) -> str:
    ref = "IMF baseline" if d.baseline == "imf" else "frozen drift"
    if d.window[0] == d.window[1]:
        return f"M = per-capita growth {d.base_year}-{d.window[1]} minus {ref} (%)"
    return f"M = mean {d.window[0]}-{d.window[1]} deviation from {ref}, vs {d.base_year} (%)"


# ----------------------------------------------------------------------------- end year

def horizon_scan(ctx: Context, d: Design, end_years=SCAN_END_YEARS, n: int = 50_000, seed: int = 20261017,
                 D0_cache: dict | None = None) -> pd.DataFrame:
    """The primary design re-run for each end year: separation, cutoff and the spread of
    average growth from the base year under each hypothesis."""
    rows = []
    for e in end_years:
        de = replace(d, window=(e, e))
        sim = simulate(ctx, de, n, seed, D0_cache=D0_cache)
        oc = sim.oc()
        k = mean_horizon(de)
        r = {"end_year": int(e), "years": k, "baseline_growth_pp": sim.null.mu, "mean_shift": oc.mean_h1 - oc.mean_h0,
             "sd_h0": oc.sd_h0, "sd_h1": oc.sd_h1, "threshold": oc.threshold,
             "growth_bar": growth_equivalent(sim.null.mu, de, oc.threshold), "sensitivity": oc.sensitivity,
             "false_positive": oc.false_positive, "youden_j": oc.youden_j, "auc": oc.auc}
        for lab, m in (("h0", sim.m0), ("h1", sim.m1)):
            for q in (0.10, 0.50, 0.90):
                r[f"growth_{lab}_q{int(q * 100):02d}"] = float(sim.null.mu + np.quantile(m, q) / k)
        rows.append(r)
    return pd.DataFrame(rows)


def select_end_year(scan: pd.DataFrame) -> int:
    j = scan.youden_j.round(2)
    return int(scan.loc[j == j.max(), "end_year"].min())


def primary_design(end_year: int) -> Design:
    return replace(PRIMARY, window=(end_year, end_year))


# ----------------------------------------------------------------------------- variants

def variants(P: Design = PRIMARY) -> list[Design]:
    return [
        P,
        replace(P, name="scope: 2023-27 spikes only", scope="recent"),
        replace(P, name="scope: 2026-27 El Nino only", scope="incremental"),
        replace(P, name="composition: raw shocks (handoff formula)", composition="raw"),
        replace(P, name="2026-27 only + raw shocks (handoff literal)", scope="incremental", composition="raw"),
        replace(P, name="IRF beyond h=10: truncate to 0", beyond="zero"),
        replace(P, name="IRF: point estimate only", irf_uncertainty=False),
        replace(P, name="IRF: Newey-West-scaled draws", irf="PWT_ts_NWscaled"),
        replace(P, name="IRF: draws widened by half", irf="PWT_ts_wide"),
        replace(P, name="IRF: BU time series (NOAA p=6 shocks)", irf="BU_ts"),
        replace(P, name="IRF: PWT panel (paper's 14%)", irf="PWT_panel"),
        replace(P, name="IRF: PWT panel, GDP-weighted (paper App. Fig. B.10)", irf="PWT_panel_gdpw"),
        replace(P, name="IRF: BU panel (paper's 18%)", irf="BU_panel"),
        replace(P, name="IRF: transitory warmth only (Sims)", irf="PWT_ts_transitory"),
        replace(P, name="filter: refit through 2025 (until 30 Oct 2026)", calib_end=2025),
        replace(P, name="paper's world: raw IMF misses (no netting)", h1_background="raw"),
        replace(P, name="IRF: time series re-estimated with NOAA temperature", irf="PWT_ts_noaa"),
        replace(P, name="IRF: time series re-estimated on WDI world GDP at market exchange rates", irf="PWT_ts_wdi"),
        replace(P, name="filter: data from 1880", data_start=1880),
        replace(P, name="filter: p+1 lags (paper eq. 1 literal)", convention="paper_eq1"),
        replace(P, name="post-2027 temperatures: none (until 30 Oct 2026)", future_temps="none"),
        replace(P, name="baseline: frozen 2000-2019 drift (until 30 Oct 2026)", baseline="frozen"),
        replace(P, name="frozen baseline: 1991-2019 drift (handoff)", baseline="frozen", calib=(1991, 2019)),
        replace(P, name="frozen baseline: + structural drift sd 0.5pp", baseline="frozen", drift_sd_extra=0.5),
        replace(P, name="frozen baseline: block bootstrap (3y)", baseline="frozen", null_method="block"),
        replace(P, name=f"statistic: growth 2027-{P.window[1]} (draft until 30 Oct 2026)", base_year=2027),
        replace(P, name="statistic: mean level 2029-33 vs 2025 (earlier)", base_year=2025, window=(2029, 2033)),
        replace(P, name="statistic: mean level 2031-35 vs 2025 (handoff)", base_year=2025, window=(2031, 2035)),
    ]


def trend_design(P: Design, start: int) -> Design:
    """The trend baseline with its average and spread taken from ``start`` through TREND_END."""
    return replace(P, name=f"trend baseline: {start}-{TREND_END} average", baseline="frozen",
                   calib=(start, TREND_END))


def sensitivity_specs(P: Design) -> list[dict]:
    """The Letter's sensitivity rows (its Fig. 4 and Extended Data Table 2), in order.

    Each row changes one thing in the published design. ``bin`` names a conditional contract (the
    run's draws within that range of NOAA's 2027 value). ``settings`` are the page's controls that
    give the same design, over the page's defaults with 2027 drawn from today's forecast, and are
    None where the page has no control for the change.
    """
    est, bg, tp, ct = "The paper’s estimate", "Background growth", "Temperatures", "The contract"

    def row(group, label, design=None, settings=None, bin=None):
        return {"group": group, "label": label, "design": design, "bin": bin,
                "settings": None if settings is None else {"t27": "forecast", **settings}}

    return [
        row("Published", "Published design", P, {}),
        row(est, "Country panel, every country weighted equally (Fig. IV)", replace(P, irf="PWT_panel"),
            {"irf": "PWT_panel"}),
        row(est, "Country panel, weighted by GDP (App. Fig. B.10)", replace(P, irf="PWT_panel_gdpw"),
            {"irf": "PWT_panel_gdpw"}),
        row(est, "Re-estimated with NOAA temperature", replace(P, irf="PWT_ts_noaa"),
            {"irf": "PWT_ts_noaa"}),
        row(est, "Re-estimated on World Bank GDP at market exchange rates", replace(P, irf="PWT_ts_wdi"),
            {"irf": "PWT_ts_wdi"}),
        row(est, "Barro–Ursúa data from 1860, time series", replace(P, irf="BU_ts"), {"irf": "BU_ts"}),
        row(est, "Barro–Ursúa country panel", replace(P, irf="BU_panel"), {"irf": "BU_panel"}),
        row(est, "Transitory part of each shock only (App. B.4)", replace(P, irf="PWT_ts_transitory"),
            {"irf": "PWT_ts_transitory"}),
        row(est, "Central estimate, no uncertainty", replace(P, irf_uncertainty=False), {"uncertainty": "point"}),
        row(est, "Newey–West widths", replace(P, irf="PWT_ts_NWscaled"), {"uncertainty": "nw"}),
        row(est, "Uncertainty widened by half", replace(P, irf="PWT_ts_wide"), {"uncertainty": "wide"}),
        row(bg, "IMF misses not netted in the paper’s world", replace(P, h1_background="raw"), {"netting": False}),
        *[row(bg, f"Trend from {s}", trend_design(P, s), {"baseline": "frozen", "trendStart": s})
          for s in (1991, 2000, 2005)],
        row(tp, "Cool 2027 range", bin="cool", settings={"t27": "bin:cool"}),
        row(tp, "Warm 2027 range", bin="warm", settings={"t27": "bin:warm"}),
        row(tp, "No shocks after 2027", replace(P, future_temps="none"), {"future": "none"}),
        row(tp, "Shocks of 2023–27 only", replace(P, scope="recent"), {"scope": "recent"}),
        row(tp, "Shocks of 2026–27 only", replace(P, scope="incremental"), {"scope": "incremental"}),
        row(ct, "Growth from 2027", replace(P, base_year=2027)),
        row(ct, "End year 2030", replace(P, window=(2030, 2030)), {"endYear": 2030}),
        row(ct, "End year 2032", replace(P, window=(2032, 2032)), {"endYear": 2032}),
    ]


def contract_row(sim: SimResult, d: Design, strike: float) -> dict:
    """A design's contract at its own best cutoff, and each view's chance of Yes at ``strike``."""
    o = sim.oc()
    c = (strike - sim.null.mu) * mean_horizon(d)
    return {"drift_pp": float(sim.null.mu), "threshold_growth_pp": float(growth_equivalent(sim.null.mu, d, o.threshold)),
            "sensitivity": float(o.sensitivity), "false_positive": float(o.false_positive),
            "youden_j": float(o.youden_j), "auc": float(o.auc),
            "p_yes_no_effect_at_strike": float((sim.m0 > c).mean()),
            "p_yes_paper_at_strike": float((sim.m1 > c).mean())}


# ----------------------------------------------------------------------------- summaries

def annual_bands(sim: SimResult, q=(0.05, 0.10, 0.50, 0.90, 0.95)) -> pd.DataFrame:
    """Annual quantiles. ``dev`` is measured from the 2025 anchor; ``devb`` from the
    statistic's base year (the deviation the contract settles on)."""
    base = sim.null.forecast(sim.years)
    b = sim.design.base_year
    jb = int(np.flatnonzero(sim.years == b)[0]) if b > ANCHOR else None
    rows = []
    for k, t in enumerate(sim.years):
        r = {"year": int(t), "baseline_level": float(np.exp(base[k] / 100)),
             "bk_effect_mean_pct": float(sim.effect[:, k].mean())}
        for lab, D in (("H0", sim.D0), ("H1", sim.D1)):
            dev = D[:, k]
            devb = dev - D[:, jb] if jb is not None else dev
            r[f"{lab}_dev_mean"] = float(dev.mean())
            r[f"{lab}_devb_mean"] = float(devb.mean()) if t >= b else np.nan
            for qq in q:
                r[f"{lab}_dev_q{int(qq*100):02d}"] = float(np.quantile(dev, qq))
                r[f"{lab}_devb_q{int(qq*100):02d}"] = float(np.quantile(devb, qq)) if t >= b else np.nan
                r[f"{lab}_level_q{int(qq*100):02d}"] = float(np.exp((base[k] + np.quantile(dev, qq)) / 100))
        rows.append(r)
    return pd.DataFrame(rows).set_index("year")


def decomposition(ctx: Context, d: Design, years=None) -> pd.DataFrame:
    """Mean B&K effect (point IRF, central temperatures) by contributing shock year."""
    years = np.arange(ANCHOR + 1, 2036) if years is None else years
    imp = impulses(ctx, d, ctx.T26[0], ctx.T27[0])
    th = ctx.irfs[d.irf].theta
    rows = {}
    for tau, v in imp.items():
        rows[tau] = I.effect_path(th, {tau: float(np.mean(v))}, years, anchor=ANCHOR, beyond=d.beyond)[0]
    df = pd.DataFrame(rows, index=years).T
    df.index.name = "shock_year"
    df.insert(0, "impulse", [float(np.mean(imp[t])) for t in df.index])
    return df


def threshold_grid(ctx: Context, d: Design, T27_grid, T26_values, n: int, seed: int,
                   D0_cache: dict | None = None) -> pd.DataFrame:
    rows = []
    for t26 in T26_values:
        for t27 in T27_grid:
            sim = simulate(ctx, d, n, seed, T26=t26, T27=t27, D0_cache=D0_cache)
            oc = sim.oc()
            s, ss = event_shocks(ctx, d, t26, t27)
            rows.append({"T2026": t26, "T2027": t27, "s2026": float(s[2026]), "s2027": float(s[2027]),
                         "mean_shift": oc.mean_h1 - oc.mean_h0, "threshold": oc.threshold,
                         "threshold_growth_pp": growth_equivalent(sim.null.mu, d, oc.threshold),
                         "sensitivity": oc.sensitivity, "false_positive": oc.false_positive,
                         "youden_j": oc.youden_j, "auc": oc.auc})
    return pd.DataFrame(rows)


def hindcast_2022(ctx: Context, d: Design) -> dict:
    """Descriptive look at 2023-2025: realized deviation from a 2022-anchored frozen drift
    versus the B&K-implied (point IRF) effect over the same years. Not a test: horizons
    0-2 carry small predicted effects relative to noise."""
    null = B.fit_null(ctx.wdi, d.calib, d.exclude, anchor_year=2022)
    yrs = np.arange(2023, 2026)
    realized = 100 * np.log(ctx.wdi.loc[yrs].values) - null.forecast(yrs)
    s, _ = event_shocks(ctx, d, ctx.T26[0], ctx.T27[0])
    taus = list(range(2022 - I.H_MAX, 2026))
    imp = ctx.filters[IRF_SAMPLE[d.irf]].apply(s, taus) if d.composition == "innovation" else {t: s[t] for t in taus}
    eff = I.effect_path(ctx.irfs[d.irf].theta, imp, yrs, anchor=2022, beyond=d.beyond)[0]
    sd = null.sigma * np.sqrt(yrs - 2022)
    return {"years": yrs.tolist(), "realized_dev_pct": realized.round(3).tolist(),
            "bk_implied_pct": eff.round(3).tolist(), "h0_sd_pct": sd.round(3).tolist(),
            "drift_pp": null.mu}


# ----------------------------------------------------------------------------- conditional contracts

BIN_NAMES = ("cool", "central", "warm")


def conditional_bins(ctx: Context, d: Design, n: int = 50_000, seed: int = 20261017,
                     levels=(0.20, 0.50, 0.80), D0_cache: dict | None = None) -> pd.DataFrame:
    """Cutoffs for contracts conditioned on NOAA's 2027 annual value (decided 30 Oct 2026).

    The three levels are percentiles of the current 2027 forecast; bins split halfway between
    them (cool / central / warm), so each holds about a third of the forecast. Within a bin,
    2027 is drawn from the forecast truncated to the bin; 2026 keeps its own uncertainty.
    """
    from scipy.stats import norm, truncnorm
    m, sd = ctx.T27
    lv = m + sd * norm.ppf(np.asarray(levels))
    edges = np.r_[-np.inf, (lv[:-1] + lv[1:]) / 2, np.inf]
    rows = []
    for k, name in enumerate(BIN_NAMES):
        a, b = (edges[k] - m) / sd, (edges[k + 1] - m) / sd
        T27 = truncnorm.rvs(a, b, loc=m, scale=sd, size=n, random_state=np.random.default_rng(seed + 11 + k))
        sim = simulate(ctx, d, n, seed, T27=T27, D0_cache=D0_cache)
        oc = sim.oc()
        rows.append({"bin": name, "level": lv[k], "lower": edges[k], "upper": edges[k + 1],
                     "prob_now": float(norm.cdf(b) - norm.cdf(a)), "mean_T2027": float(T27.mean()),
                     "mean_shift": float(sim.m1.mean() - sim.m0.mean()), "threshold": oc.threshold,
                     "growth_bar": growth_equivalent(sim.null.mu, d, oc.threshold),
                     "sensitivity": oc.sensitivity, "false_positive": oc.false_positive, "youden_j": oc.youden_j,
                     "sim": sim})
    return pd.DataFrame(rows)


def temperature_levels(ctx: Context, sim: SimResult) -> dict[int, np.ndarray]:
    """Each path's NOAA annual temperature as the run builds it: observed through the anchor year,
    the path's 2026-27 draws, then the forecast filter's prediction plus the path's simulated shock,
    the same arithmetic ``remeasure`` starts from. Years after 2027 are absent without simulated
    shocks."""
    n = len(sim.m0)
    T = {int(t): np.full(n, float(v)) for t, v in ctx.noaa.loc[:ANCHOR].items()}
    T[2026] = np.broadcast_to(np.asarray(sim.inputs["T26"], float), (n,)).copy()
    T[2027] = np.broadcast_to(np.asarray(sim.inputs["T27"], float), (n,)).copy()
    ff = ctx.forecast_filter
    raw = sim.inputs.get("future_raw") or {}
    for t in sorted(raw):
        T[t] = ff.coef[0] + sum(b * T[t - lag] for b, lag in zip(ff.coef[1:], ff.lags)) + np.asarray(raw[t], float)
    return T


def strike_ladder(sim: SimResult, d: Design, bars=np.round(np.arange(1.2, 2.81, 0.2), 1)) -> pd.DataFrame:
    """For 'Will growth average more than X% a year?': P(Yes) under each hypothesis per strike."""
    k = mean_horizon(d)
    rows = []
    for x in bars:
        c = (x - sim.null.mu) * k
        rows.append({"strike_pct_yr": float(x), "M_cut": float(c),
                     "p_yes_no_effect": float((sim.m0 > c).mean()), "p_yes_paper": float((sim.m1 > c).mean())})
    return pd.DataFrame(rows)
