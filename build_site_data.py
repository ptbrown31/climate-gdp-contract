"""Data for the contract's page on the public site: the model the browser re-runs, path by path.

The page's sliders recompute the contract from the same 50,000 simulated paths as
run_analysis.py, not from a summary of them. Every random input of the primary run is written
here (the no-effect paths, the IRF draw each path uses, the 2026-27 temperatures, the simulated
post-2027 shocks), together with everything fixed (temperature filters, IRF draws, the IMF
baseline and its average miss), so the browser's arithmetic is the analysis's arithmetic.
``site_tab/js/elnino-model.js`` is that arithmetic; tests/test_site_model.py checks it against
this run, path by path.

    python3 -I build_site_data.py          # after run_analysis.py; writes site_tab/data/elnino/

Path-level arrays are int16, each field at the largest whole-number scale that fits (stored in
model.json); the rounding is under 0.001 points of GDP and 0.0001 C, which moves no published number.
Each binary file is named by its content (paths.<hash>.bin), and model.json names them, so the site
can cache a file for good while model.json itself stays short-lived (the site's DEPLOY.md, 12b).
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))  # explicit: run with `python -I`, which drops the script dir

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from bk_elnino import analysis as A  # noqa: E402
from bk_elnino import baseline as B  # noqa: E402
from bk_elnino import irf as I  # noqa: E402
from bk_elnino import sources as S  # noqa: E402

OUT = ROOT / "site_tab" / "data" / "elnino"
FIXTURE = ROOT / "tests" / "fixtures" / "site_model_reference.npz"
N_PATHS, SEED = 50_000, 20261017
YEARS = list(range(A.ANCHOR + 1, 2036))          # 2026..2035, the primary run's simulated years
END_YEARS = list(range(2028, 2036))              # end years the page offers (the scan's, through 2035)
# The public copy of this code the page links to. Proposed name; the repository does not exist until
# Patrick creates it, so links to it fail until then.
REPO = "https://github.com/ptbrown31/climate-gdp-contract"
# Strikes the page's ladder draws while the contract is unlisted: the article's one contract (Patrick,
# 2 Nov 2026). The exchange's own strikes replace these once it lists.
LADDER = [1.1]
# The robustness rows the page's contract note lists, in plain words, in this order (the rest of the
# published variants are earlier drafts' statistics and are left to MEMO.md).
PAGE_VARIANTS = [
    ("primary", "The article’s design"),
    ("IRF: point estimate only", "The paper’s central estimate, without its statistical uncertainty"),
    ("IRF: Newey-West-scaled draws", "The paper’s uncertainty at Newey–West widths"),
    ("IRF: draws widened by half", "The paper’s uncertainty widened by half"),
    ("IRF: PWT panel (paper's 14%)", "Country panel, every country weighted equally (the paper’s 14%)"),
    ("IRF: PWT panel, GDP-weighted (paper App. Fig. B.10)", "Country panel, countries weighted by GDP (App. Fig. B.10)"),
    ("IRF: re-estimated with NOAA temperature (paper App. B.11)", "Time series with NOAA temperature (App. Fig. B.11)"),
    ("IRF: re-estimated on WDI world GDP (paper App. B.11)", "Time series on World Bank GDP (App. Fig. B.11)"),
    ("IRF: BU time series (NOAA p=6 shocks)", "Barro–Ursúa data from 1860, time series"),
    ("IRF: BU panel (paper's 18%)", "Barro–Ursúa country panel (the paper’s 18%)"),
    ("IRF: transitory warmth only (Sims)", "Only the transitory part of each shock (App. B.4)"),
    ("IRF beyond h=10: truncate to 0", "The paper’s effect ends after year 10"),
    ("composition: raw shocks (handoff formula)", "Each shock applied whole, not only its unpredicted part"),
    ("scope: 2023-27 spikes only", "Only the 2023–27 shocks counted"),
    ("scope: 2026-27 El Nino only", "Only the 2026–27 El Niño counted"),
    ("post-2027 temperatures: none (until 30 Oct 2026)", "No temperature shocks after 2027"),
    ("paper's world: raw IMF misses (no netting)", "The paper’s part of the IMF’s past misses left in"),
    ("filter: refit through 2025 (until 30 Oct 2026)", "Temperature filter refitted through 2025"),
    ("filter: data from 1880", "Temperature filter fitted from 1880"),
    ("filter: p+1 lags (paper eq. 1 literal)", "Temperature filter with three lags (eq. 1 as typeset)"),
    ("baseline: frozen 2000-2019 drift (until 30 Oct 2026)", "No-effect growth: the 2000–2019 average, extended"),
    ("frozen baseline: 1991-2019 drift (handoff)", "No-effect growth: the 1991–2019 average, extended"),
]
SOURCES = [   # (key in results.json vintages, what it is, licence or terms)
    ("noaa", "NOAA NOAAGlobalTemp, global annual mean surface temperature (Climate at a Glance)", "US government, public domain"),
    ("noaa_monthly", "NOAA NOAAGlobalTemp, global monthly mean (Climate at a Glance)", "US government, public domain"),
    ("oni", "NOAA CPC Oceanic Niño Index", "US government, public domain"),
    ("wdi_gdppc_ppp", "World Bank WDI, world GDP per capita, PPP, constant 2021 dollars (NY.GDP.PCAP.PP.KD)", "CC BY 4.0"),
    ("wdi_gdppc_usd", "World Bank WDI, world GDP per capita, constant 2015 dollars (NY.GDP.PCAP.KD)", "CC BY 4.0"),
    ("gistemp", "NASA GISTEMP v4, for comparison", "US government, public domain"),
    ("berkeley", "Berkeley Earth land and ocean summary, for comparison", "Berkeley Earth's terms"),
]

# The paper's estimates the page offers, in the order of the menu. Each is a row of the
# robustness table (MEMO.md section 10) and keeps that row's name in "variant".
IRF_MENU = [
    ("PWT_ts", "World GDP, time series (the paper's Fig. III)", "primary"),
    ("PWT_panel", "Country panel, every country weighted equally (Fig. IV)", "IRF: PWT panel (paper's 14%)"),
    ("PWT_panel_gdpw", "Country panel, countries weighted by GDP (App. Fig. B.10)",
     "IRF: PWT panel, GDP-weighted (paper App. Fig. B.10)"),
    ("PWT_ts_noaa", "Time series re-estimated with NOAA temperature (App. Fig. B.11)",
     "IRF: re-estimated with NOAA temperature (paper App. B.11)"),
    ("PWT_ts_wdi", "Time series re-estimated on World Bank GDP (App. Fig. B.11)",
     "IRF: re-estimated on WDI world GDP (paper App. B.11)"),
    ("BU_ts", "Barro–Ursúa data from 1860, time series", "IRF: BU time series (NOAA p=6 shocks)"),
    ("BU_panel", "Barro–Ursúa country panel", "IRF: BU panel (paper's 18%)"),
    ("PWT_ts_transitory", "Only the transitory part of each shock (App. B.4)",
     "IRF: transitory warmth only (Sims)"),
]


def scale_for(x: np.ndarray, headroom: float = 32000.0) -> int:
    """Largest whole number that keeps round(x * scale) inside int16."""
    m = float(np.nanmax(np.abs(x))) if x.size else 0.0
    return 1 if m == 0 else max(1, int(np.floor(headroom / m)))


def pack(fields: list[tuple], n: int) -> tuple[bytes, list[dict]]:
    """Column blocks of int16: field after field, and within a field year after year (n values each).
    A field is (name, values) or (name, values, scale) for a fixed scale (1 for an integer field)."""
    blobs, meta = [], []
    for name, arr, *fixed in fields:
        a = np.asarray(arr, float).reshape(n, -1)
        sc = fixed[0] if fixed else scale_for(a)
        q = np.round(a * sc)
        if np.abs(q).max() > 32767:
            raise ValueError(f"{name} overflows int16 at scale {sc}")
        blobs.append(q.T.astype("<i2").tobytes())
        meta.append({"name": name, "count": int(a.shape[1]), "scale": sc})
    return b"".join(blobs), meta


def put(stem: str, data: bytes, written: set) -> str:
    """Write ``data`` as <stem>.<content hash>.bin and return the name model.json gives it."""
    name = f"{stem}.{hashlib.sha256(data).hexdigest()[:12]}.bin"
    (OUT / name).write_bytes(data)
    written.add(name)
    return name


def unpack(raw: bytes, meta: list[dict], n: int) -> dict[str, np.ndarray]:
    out, off = {}, 0
    a = np.frombuffer(raw, "<i2")
    for f in meta:
        k = f["count"] * n
        out[f["name"]] = a[off:off + k].reshape(f["count"], n).T / f["scale"]
        off += k
    return out


def plain_source(s: str) -> str:
    """The IMF record's label as page copy: the site's prose check takes no colons."""
    return s.replace("historical forecasts: ", "historical forecasts of ")


def family(ctx, D, key: str) -> dict:
    ss = A.shock_set(ctx, replace(D, irf=key))
    f26, f27 = ss.fitted([2026, 2027]).values
    filt = ctx.filters[A.IRF_SAMPLE[key]]
    return {"coef": [float(c) for c in ss.fit.coef], "lags": list(ss.fit.lags),
            "fitYears": list(ss.fit.fit_years), "dataStart": int(ss.T.index.min()),
            "shocks": {str(int(t)): round(float(v), 6) for t, v in ss.shocks.items()},
            "f26": float(f26), "f27": float(f27),
            "innovation": [float(c) for c in filt.coef], "innovationSample": f"{filt.sample}, n={filt.n}"}


def main():
    res = json.loads((ROOT / "outputs/results.json").read_text())
    end = int(res["end_year"]["selected"])
    D = A.primary_design(end)
    ctx = A.load_context(nboot=4000, seed=123)
    OUT.mkdir(parents=True, exist_ok=True)

    prim = A.simulate(ctx, D, N_PATHS, SEED)
    frozen = A.simulate(ctx, replace(D, baseline="frozen"), N_PATHS, SEED)
    bins = A.conditional_bins(ctx, D, N_PATHS, SEED)
    inp = prim.inputs
    yrs = np.asarray(prim.years)
    if list(yrs) != YEARS:
        raise ValueError(f"simulated years {list(yrs)} differ from {YEARS}")
    jb = YEARS.index(D.base_year)
    rel = lambda X: X[:, jb + 1:] - X[:, [jb]]                    # noqa: E731  (2027..2035, from 2026)
    m27 = float(ctx.T27[0])
    fut_years = sorted(inp["future_raw"])

    fields = [("d0", rel(prim.D0)),
              ("idx", inp["idx"].astype(float), 1),
              ("z26", (np.asarray(inp["T26"]) - ctx.T26[0]) / ctx.T26[1]),
              ("z27", (np.asarray(inp["T27"]) - ctx.T27[0]) / ctx.T27[1]),
              ("future", np.column_stack([inp["future_raw"][t] for t in fut_years])),
              ("t27bins", np.column_stack([np.asarray(r.sim.inputs["T27"]) - m27 for r in bins.itertuples()])),
              ("d0base", prim.D0[:, jb])]                    # the 2025-to-2026 miss, for levels from 2025
    raw, meta = pack(fields, N_PATHS)
    written: set = set()
    paths_file = put("paths", raw, written)
    # the trend baseline for each start year, one file each, fetched when the page asks for that start
    trend, trend_sims = {}, {}
    for s in A.TREND_STARTS:
        sim = frozen if (s, A.TREND_END) == tuple(D.calib) else A.simulate(ctx, A.trend_design(D, s), N_PATHS, SEED)
        raw_t, meta_t = pack([("d0", rel(sim.D0)), ("d0base", sim.D0[:, jb])], N_PATHS)
        trend[str(s)] = {"file": put(f"paths_trend_{s}", raw_t, written), "fields": meta_t, "mu": float(sim.null.mu),
                         "calib": [s, A.TREND_END], "Dbar": [float(v) for v in rel(sim.D0).mean(axis=0)]}
        trend_sims[s] = sim
        back_t = unpack(raw_t, meta_t, N_PATHS)
        sct = {f["name"]: f["scale"] for f in meta_t}
        assert np.abs(back_t["d0"] - rel(sim.D0)).max() <= 0.5 / sct["d0"] + 1e-12, f"trend {s} d0"
    trend_default = trend[str(D.calib[0])]

    # the stored arrays must give back the run's own inputs
    back = unpack(raw, meta, N_PATHS)
    assert np.array_equal(back["idx"].ravel().astype(int), inp["idx"]), "IRF draw index not exact"
    sc = {f["name"]: f["scale"] for f in meta}
    assert np.abs(back["d0"] - rel(prim.D0)).max() <= 0.5 / sc["d0"] + 1e-12
    assert np.abs(back["d0base"].ravel() - prim.D0[:, jb]).max() <= 0.5 / sc["d0base"] + 1e-12

    # the paper's estimates
    irfs = []
    for key, label, variant in IRF_MENU:
        irf = ctx.irfs[key]
        sc = scale_for(irf.draws)
        q = np.round(irf.draws * sc).astype("<i2")
        irf_file = put(f"irf_{key}", q.tobytes(), written)
        drag = A.paper_drag_by_lead(ctx, replace(D, irf=key))
        lo, hi = irf.band(0.10)
        irfs.append({"key": key, "label": label, "variant": variant, "family": A.IRF_SAMPLE[key],
                     "transitory": key.endswith("_transitory"), "theta": [float(v) for v in irf.theta],
                     "q05": [float(v) for v in lo], "q95": [float(v) for v in hi],
                     "draws": {"file": irf_file, "rows": int(irf.draws.shape[0]),
                               "cols": int(irf.draws.shape[1]), "scale": sc},
                     "drag": [float(v) for v in drag], "note": irf.note, "shockDefinition": irf.shock_definition})
    base = ctx.irfs["PWT_ts"]
    nw_scale = (base.se / base.draws.std(axis=0)).tolist()

    em = ctx.imf_errors
    mean_e = em.paths.mean(axis=0)
    leads = np.arange(1, len(YEARS) + 1)
    e_by_lead = np.where(leads <= em.max_lead, mean_e[np.minimum(leads, em.max_lead) - 1], em.paths[:, -1].mean())
    Dbar = np.cumsum(e_by_lead)
    g = ctx.imf.growth
    wdi_g = B.log_growth(ctx.wdi)
    noaa = ctx.noaa.loc[:2025]
    oni = S.read_oni(ROOT / "data/raw/oni/oni.ascii.txt")
    djf_oni = oni[oni.season == "DJF"].set_index("year")["anom"]
    bands = A.annual_bands(prim)
    t26c = min(res["threshold_grid"]["T2026_values"], key=lambda v: abs(v - ctx.T26[0]))
    model = {
        "schema": 1,
        "written": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
        "refreshedUtc": res["refreshed_utc"],
        "n": N_PATHS, "seed": SEED, "years": YEARS, "anchor": A.ANCHOR, "base": D.base_year,
        "endYears": END_YEARS, "endYear": end, "hMax": I.H_MAX, "beyond": D.beyond,
        "paths": {"file": paths_file, "fields": meta, "futureYears": fut_years, "t27center": m27,
                  "binOrder": list(bins.bin)},
        "pathsFrozen": {"file": trend_default["file"], "fields": trend_default["fields"]},
        "trend": {"windowEnd": A.TREND_END, "default": int(D.calib[0]), "starts": trend},
        "noaa": {"first": int(noaa.index.min()), "T": [round(float(v), 4) for v in noaa.values]},
        "forecastFilter": {"coef": [float(c) for c in ctx.forecast_filter.coef],
                           "lags": list(ctx.forecast_filter.lags)},
        "families": {"PWT": family(ctx, D, "PWT_ts"), "BU": family(ctx, D, "BU_ts")},
        "temps": {"T26": {"mean": float(ctx.T26[0]), "sd": float(ctx.T26[1]), "method": ctx.prov26.method},
                  "T27": {"mean": float(ctx.T27[0]), "sd": float(ctx.T27[1]), "method": ctx.prov27.method},
                  "bins": [{"name": r.bin, "lower": None if not np.isfinite(r.lower) else float(r.lower),
                            "upper": None if not np.isfinite(r.upper) else float(r.upper), "level": float(r.level),
                            "probNow": float(r.prob_now)} for r in bins.itertuples()],
                  "strongElNinoYears": [int(y) for y, v in djf_oni.items() if v >= 1.5 and 1950 <= y <= 2025],
                  "analogYears": [int(y) for y in ctx.enso_paths.analog_years]},
        "irfs": irfs, "nwScale": nw_scale,
        "imf": {"vintage": ctx.imf.vintage, "projectedThrough": int(ctx.imf.projected_through),
                "growth": {str(t): float(g.loc[t]) for t in YEARS},
                "meanErrorByLead": [float(v) for v in e_by_lead],
                "Dbar": [float(Dbar[k] - Dbar[jb]) for k in range(jb + 1, len(YEARS))],
                "errorSource": plain_source(em.source), "nForecasts": int(em.paths.shape[0])},
        "frozen": {"mu": float(frozen.null.mu), "calib": list(D.calib),
                   "Dbar": [float(v) for v in rel(frozen.D0).mean(axis=0)]},
        "wdi": {"growth": {str(int(t)): round(float(v), 4) for t, v in wdi_g.loc[1991:2025].items()},
                "levels": {str(int(t)): round(float(v), 3) for t, v in ctx.wdi.loc[:A.ANCHOR].dropna().items()},
                "series": "World Bank WDI NY.GDP.PCAP.PP.KD (world GDP per capita, PPP, constant 2021 dollars)",
                "lastUpdated": ctx.wdi_meta.get("lastupdated")},
        "defaults": {"irf": "PWT_ts", "uncertainty": "boot", "share": 1.0, "baseline": "imf", "missShare": 1.0,
                     "spread": 1.0, "netting": True, "t26": "forecast", "t27": "bin:central", "t26Value": None,
                     "t27Value": None, "future": "simulate", "scope": D.scope, "endYear": end,
                     "trendStart": int(D.calib[0]),
                     "strike": float(next(b for b in res["conditional_contracts"]["bins"]
                                          if b["bin"] == "central")["strike"])},
        "published": {
            "contract": {k: res["contract_primary"][k] for k in ("threshold", "sensitivity", "false_positive",
                                                                 "youden_j", "threshold_growth_equivalent_pp",
                                                                 "h0_growth_mean_pp", "h1_growth_mean_pp")},
            "bins": [{k: b[k] for k in ("bin", "condition", "strike", "threshold", "growth_bar", "sensitivity",
                                        "false_positive", "youden_j", "p_yes_no_effect_at_strike",
                                        "p_yes_paper_at_strike", "prob_now")}
                     for b in res["conditional_contracts"]["bins"]],
            "scan": [{k: r[k] for k in ("end_year", "threshold", "growth_bar", "sensitivity", "false_positive",
                                        "youden_j")} for r in res["end_year"]["scan"]],
            "variants": [dict({k: v[k] for k in ("variant", "threshold_growth_pp", "sensitivity", "false_positive",
                                                 "youden_j")}, label=lab)
                         for key, lab in PAGE_VARIANTS for v in res["contract_variants"] if v["variant"] == key],
            "imfMissIfCentred": res["imf_miss_if_centred"],
            # the Letter's figures at the published settings: GDP levels and temperatures (Fig. 1a), the
            # sensitivity rows (Fig. 4), the trend baseline's start year and a known 2027 value
            "levels": {str(t): {v: [round(float(bands.loc[t, f"{k}_level_q{q:02d}"]), 1) for q in (10, 50, 90)]
                                for v, k in (("h0", "H0"), ("h1", "H1"))} for t in YEARS},
            "futureTemperatures": res["future_temperatures"]["levels"],
            "sensitivity": res["sensitivity_table"],
            "trendStartScan": res["trend_start_scan"],
            "t27Grid": {"T2026": t26c, "rows": [{k: r[k] for k in ("T2027", "s2027", "mean_shift", "threshold_growth_pp",
                                                                 "sensitivity", "false_positive", "youden_j")}
                                                for r in res["threshold_grid"]["rows"] if r["T2026"] == t26c]}},
        "ladder": {"strikes": LADDER, "lists": "mid-January 2027", "symbol": None,
                   "note": "the article's contract; the exchange's own strikes replace it when it lists"},
        "code": {"repo": REPO, "paper": "https://doi.org/10.1093/qje/qjag011",
                 "replication": "https://github.com/dkaenzig/micc_replication",
                 "shocks": "https://github.com/dkaenzig/global-temperature-shocks"},
        "checks": {"irfReplicationMaxAbsDiff": res["irf_replication_max_abs_diff"],
                   "noaaShockVsAuthors": res["validation"]["noaa_p2_vs_authors_pwt_shock"],
                   "hamiltonPrimary": res["hamilton_fit_primary"]["formula"],
                   "imfErrors": {k: res["baseline_primary"]["errors"][k]
                                 for k in ("n_forecasts", "n_below_forecast", "first_vintage", "last_vintage",
                                           "sum_over_statistic_mean", "sum_over_statistic_sd")},
                   "wdiGap": res["baseline_primary"]["wdi_gap_pp"]},
        "sources": [{"what": what, "url": res["vintages"][k]["url"], "retrieved": res["vintages"][k]["retrieved_utc"],
                     "sha256": res["vintages"][k]["sha256"], "terms": terms}
                    for k, what, terms in SOURCES if isinstance(res["vintages"].get(k), dict)],
        "imfSources": {"baseline": res["vintages"]["imf_baseline"], "errors": plain_source(res["vintages"]["imf_errors"])},
    }
    (OUT / "model.json").write_text(json.dumps(model, separators=(",", ":")))
    # last month's files leave this folder (the site keeps its own copies a while; DEPLOY.md, 12b)
    for old in OUT.glob("*.bin"):
        if old.name not in written:
            old.unlink()

    # reference outcomes for the engine test (not published): the run's own statistics, path by path
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    ref = {"primary_m0": prim.m0, "primary_m1": prim.m1, "frozen_m0": frozen.m0, "frozen_m1": frozen.m1}
    for s in (A.TREND_STARTS[0], A.TREND_STARTS[-1]):
        ref[f"trend{s}_m0"], ref[f"trend{s}_m1"] = trend_sims[s].m0, trend_sims[s].m1
    for r in bins.itertuples():
        ref[f"{r.bin}_m0"], ref[f"{r.bin}_m1"] = r.sim.m0, r.sim.m1
    for key, d in [("panel", replace(D, irf="PWT_panel")), ("bu", replace(D, irf="BU_ts")),
                   ("transitory", replace(D, irf="PWT_ts_transitory")), ("recent", replace(D, scope="recent")),
                   ("nofuture", replace(D, future_temps="none")), ("point", replace(D, irf_uncertainty=False)),
                   ("end2029", replace(D, window=(2029, 2029)))]:
        s = A.simulate(ctx, d, N_PATHS, SEED)
        ref[f"{key}_m0"], ref[f"{key}_m1"] = s.m0, s.m1
    np.savez_compressed(FIXTURE, **{k: np.asarray(v, np.float64) for k, v in ref.items()})
    size = sum(p.stat().st_size for p in OUT.iterdir())
    print(f"wrote {OUT} ({size / 1e6:.1f} MB): {len(irfs)} estimates, {N_PATHS} paths, end year {end}")


if __name__ == "__main__":
    main()
