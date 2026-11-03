"""Run the full Bilal-Kaenzig x 2026-27 El Nino analysis and write outputs/.

    python -I run_analysis.py            # uses cached downloads in data/raw/
    python -I run_analysis.py --refresh  # re-download every source (records new vintages)

    python -I run_analysis.py --lock 1.29 1.47   # conversion step: cutoff for realised temps

Outputs: outputs/*.csv (table views), outputs/results.json (the Results struct),
outputs/figures/*.png, outputs/primary_M_draws.npz, outputs/irf_draws.npz.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))  # explicit: run with `python -I`, which drops the script dir

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from bk_elnino import analysis as A  # noqa: E402
from bk_elnino import baseline as B  # noqa: E402
from bk_elnino import hamilton as H  # noqa: E402
from bk_elnino import irf as I  # noqa: E402
from bk_elnino import lp  # noqa: E402
from bk_elnino import plots as P  # noqa: E402
from bk_elnino import temperature as TM  # noqa: E402
from bk_elnino import wager as W  # noqa: E402

OUT = ROOT / "outputs"
FIG = OUT / "figures"
N_PATHS = 50_000
SEED = 20261017
HANDOFF_PLACEHOLDER = np.array([-2, -3.5, -5.5, -7.5, -10, -10.5, -10, -9, -8, -7, -6], float)


def jsonable(x):
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, np.ndarray):
        return jsonable(x.tolist())
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    return x


def environment() -> dict:
    import platform

    import matplotlib
    import scipy
    return {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
            "scipy": scipy.__version__, "matplotlib": matplotlib.__version__}


def noaa_through(monthly: pd.DataFrame) -> str:
    """Latest month in the NOAA monthly series, e.g. "2026-09": tells a refresh whether new data arrived."""
    last = monthly.stack().index[-1]
    return f"{last[0]}-{list(monthly.columns).index(last[1]) + 1:02d}"


def lock_threshold(T2026: float, T2027: float):
    """Conversion step (after NOAA publishes 2027, ~mid-Jan 2028): cutoff c for the realised NOAA
    2026/2027 annual anomalies (deg C vs 1901-2000), using only the archived data in data/raw/
    (no downloads). Converted conditional contracts keep their listed strikes; this cutoff is for
    a strike listed on the unconditional contract after conversion."""
    ctx = A.load_context(nboot=4000, seed=123, refresh=False)
    if A.END_YEAR_LOCKED is None:
        print(f"note: END_YEAR_LOCKED is not set; using the default end year {A.PRIMARY.window[1]}")
    D = A.primary_design(A.END_YEAR_LOCKED or A.PRIMARY.window[1])
    sim = A.simulate(ctx, D, N_PATHS, SEED, T26=T2026, T27=T2027)
    oc = sim.oc()
    s, _ = A.event_shocks(ctx, D, T2026, T2027)
    u = ctx.filters["PWT"].apply(s, [2026, 2027])
    out = {"inputs": {"NOAA_2026": T2026, "NOAA_2027": T2027}, "design": asdict(D),
           "shocks": {"2026": float(s[2026]), "2027": float(s[2027])},
           "innovations": {"2026": float(u[2026]), "2027": float(u[2027])},
           "threshold_c_pct": oc.threshold, "threshold_growth_equivalent_pp": A.growth_equivalent(sim.null.mu, D, oc.threshold),
           "operating_characteristics": oc.as_dict(), "vintages": ctx.vintages, "environment": environment()}
    OUT.mkdir(exist_ok=True)
    (OUT / "locked_threshold.json").write_text(json.dumps(jsonable(out), indent=2))
    print(f"s2026={s[2026]:+.3f}  s2027={s[2027]:+.3f}  ->  resolves No if M <= c = {oc.threshold:.3f}% "
          f"(growth {D.base_year}-{D.window[1]} at or below {out['threshold_growth_equivalent_pp']:.2f}% a year), "
          f"Yes above  (sens {oc.sensitivity:.3f}, false positive {oc.false_positive:.3f}, J {oc.youden_j:.3f})")


def spec_condition(lower: float, upper: float) -> str:
    """Bin as stated on NOAA's published value (two decimals), e.g. '1.46 to 1.53 C'."""
    lo = None if not np.isfinite(lower) else np.ceil(lower * 100 - 1e-9) / 100
    hi = None if not np.isfinite(upper) else np.floor(upper * 100 - 1e-9) / 100
    if lo is None:
        return f"{hi:.2f} C or lower"
    if hi is None:
        return f"{lo:.2f} C or higher"
    return f"{lo:.2f} to {hi:.2f} C"


def paper_checks(ctx, D) -> dict:
    """Numbers behind the anticipated objections in MEMO.md: how the prediction moves with the paper's
    own alternative data and shock choices, and how much of the IMF's past misses the paper's estimates
    would put down to temperature shocks."""
    out = {"theta6": {k: float(ctx.irfs[k].theta[6])
                      for k in ("PWT_ts", "PWT_ts_noaa", "PWT_ts_wdi", "PWT_panel", "PWT_panel_gdpw")}}
    T26, T27 = ctx.T26[0], ctx.T27[0]

    def point(theta, h, end, filt):
        T = ctx.noaa.loc[1950:2025].copy()
        T.loc[2026], T.loc[2027] = T26, T27
        f = H.fit(T.loc[:2025], h, 2, end=end)
        sh = H.shocks(f, T)
        u = {t: sh[t] - (filt[0] + filt[1] * sh[t - 1] + filt[2] * sh[t - 2]) for t in range(A.ANCHOR - 10, 2028)}
        E = I.effect_path(theta, u, [D.base_year, D.window[1]], anchor=A.ANCHOR)[0]
        return {"coef": f.coef, "shocks_2023_2027": [float(sh[t]) for t in range(2023, 2028)],
                "shortfall_point": float(E[1] - E[0])}

    pwt, _ = I.load_bk_data(A.BK)
    sp, _ = I.bk_specs()
    sp1 = replace(sp, shock="gtmp_bkly_aw_dtfe1s")
    th1 = lp.lp_irf(pwt, sp1).b.values
    d1 = lp._restricted(pwt, sp1)
    Z = pd.concat([d1["dy"].rename("dep"), lp.regressors(d1, sp1)], axis=1).dropna()
    filt1 = np.linalg.lstsq(np.column_stack([np.ones(len(Z)), Z["shock_L1"], Z["shock_L2"]]), Z["shock"].values,
                            rcond=None)[0]
    out["theta6"]["PWT_ts_one_step"] = float(th1[6])
    th, filt = ctx.irfs[D.irf].theta, ctx.filters["PWT"].coef
    out["point_predictions"] = {
        "note": f"growth {D.base_year}-{D.window[1]}, point IRF, central 2026-27 temperatures, no post-2027 shocks",
        "two_step_paper_window": point(th, 2, 2022, filt), "two_step_refit_2025": point(th, 2, 2025, filt),
        "one_step_paper_window": point(th1, 1, 2022, filt1), "one_step_refit_2025": point(th1, 1, 2025, filt1)}
    eff = A.paper_effects_on_imf_windows(ctx, D)
    em = ctx.imf_errors
    leads = np.arange(D.base_year + 1, D.window[1] + 1) - A.ANCHOR
    paper_part = eff[:, np.minimum(leads, em.max_lead) - 1].sum(axis=1)
    miss = em.paths[:, np.minimum(leads, em.max_lead) - 1].sum(axis=1)
    out["imf_windows"] = {"paper_part_mean": float(paper_part.mean()), "paper_part_sd": float(paper_part.std(ddof=1)),
                          "miss_mean": float(miss.mean()), "corr": float(np.corrcoef(paper_part, miss)[0, 1]),
                          "slope": float(np.polyfit(paper_part, miss, 1)[0]), "n": int(len(miss))}
    ss = A.shock_set(ctx, D)
    ref = ss.reference
    out["largest_in_sample_shock"] = {"value": float(ref.max()), "year": int(ref.idxmax()),
                                      "fit_years": list(ss.fit.fit_years)}
    return out


def main(refresh: bool = False):
    OUT.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    ctx = A.load_context(nboot=4000, seed=123, refresh=refresh)

    # ---------------------------------------------------------------- 0. end year (horizon scan)
    cache: dict = {}
    scan = A.horizon_scan(ctx, A.PRIMARY, A.SCAN_END_YEARS, N_PATHS, SEED, D0_cache=cache)
    scan_nf = A.horizon_scan(ctx, replace(A.PRIMARY, future_temps="none"), A.SCAN_END_YEARS, N_PATHS, SEED,
                             D0_cache=cache)
    for col in ("mean_shift", "threshold", "growth_bar", "youden_j"):
        scan[f"{col}_no_future"] = scan_nf[col].values
    scan.to_csv(OUT / "horizon_scan.csv", index=False, float_format="%.4f")
    end = A.END_YEAR_LOCKED or A.select_end_year(scan)
    D = A.primary_design(end)
    res: dict = {"design_primary": asdict(D), "n_paths": N_PATHS, "seed": SEED, "vintages": ctx.vintages,
                 "environment": environment()}
    res["end_year"] = {"selected": end, "locked": A.END_YEAR_LOCKED is not None,
                       "scan_argmax": A.select_end_year(scan),
                       "rule": "highest Youden J to two decimals, ties to the earlier year; frozen at listing",
                       "scan": scan.to_dict(orient="records")}
    np.savez_compressed(OUT / "irf_draws.npz", **{k: v.draws.astype(np.float64) for k, v in ctx.irfs.items()})

    # ---------------------------------------------------------------- 1. replication of the IRF
    rep = I.replication_check(A.BK)
    rep.to_csv(OUT / "replication_check_irf.csv", index=False)
    res["irf_replication_max_abs_diff"] = {
        "gdp_b": float((rep.gdp_b - rep.gdp_b_authors).abs().max()),
        "gdp_se": float((rep.gdp_se - rep.gdp_se_authors).abs().max()),
        "temp_b": float((rep.temp_b - rep.temp_b_authors).abs().max())}

    # ---------------------------------------------------------------- 2. temperature shocks
    ss = A.shock_set(ctx, D)
    res["hamilton_fit_primary"] = {"formula": ss.fit.describe(), "coef": ss.fit.coef, "lags": ss.fit.lags,
                                   "fit_years": ss.fit.fit_years, "resid_sd": ss.fit.resid_sd,
                                   "in_sample_resid_mean": float(ss.reference.mean()),
                                   "resid_acf1": float(ss.reference.autocorr(1)),
                                   "resid_acf2": float(ss.reference.autocorr(2))}
    pwt_ts, bu_ts = I.load_bk_data(A.BK)
    bk_pwt = pwt_ts["gtmp_bkly_aw_dtfe2s"].dropna()
    bk_bu = bu_ts["gtmp_noaa_aw_dtfe2s"].dropna()
    pub = pd.read_csv(A.BK_SHOCKS / "temperatureShocks_pwt.csv").set_index("year")["gtmp_bkly_aw_dtfe2s"]
    berk = TM.build("Berkeley", ctx.berkeley, 1950, 2022)
    noaa6 = TM.build("NOAA", ctx.noaa.loc[:2025], 1850, 2025, 2, 6)
    gis2 = TM.build("GISTEMP", ctx.gistemp.loc[:2025], 1950, 2025)
    own_bk = H.fit(pwt_ts["gtmpanom_bkly_aw"].dropna(), 2, 2)
    res["validation"] = {
        "authors_shock_exact_formula": TM.exact_linear_weights(pwt_ts["gtmp_bkly_aw_dtfe2"].dropna(),
                                                               pwt_ts["gtmpanom_bkly_aw"].dropna()),
        "published_csv_vs_replication_dta": TM.compare(pub, bk_pwt),
        "own_fit_on_authors_temperature_vs_authors_shock": TM.compare(
            H.shocks(own_bk, pwt_ts["gtmpanom_bkly_aw"].dropna()), pwt_ts["gtmp_bkly_aw_dtfe2"].dropna()),
        "berkeley_summary_1950_2022_fit": {"coef": berk.fit.coef, "authors_coef": [0.03873, 0.51959, 0.46080],
                                          "shocks_vs_authors": TM.compare(berk.shocks, bk_pwt)},
        "noaa_p2_vs_authors_pwt_shock": TM.compare(ss.shocks, bk_pwt),
        "gistemp_p2_vs_authors_pwt_shock": TM.compare(gis2.shocks, bk_pwt),
        "noaa_p6_vs_authors_bu_shock": TM.compare(noaa6.shocks, bk_bu),
        "paper_eq1_convention_vs_authors": TM.compare(
            H.shocks(H.fit(pwt_ts["gtmpanom_bkly_aw"].dropna(), 2, 2, convention="paper_eq1"),
                     pwt_ts["gtmpanom_bkly_aw"].dropna()), pwt_ts["gtmp_bkly_aw_dtfe2"].dropna()),
    }

    filt = ctx.filters["PWT"]
    s_all, _ = A.event_shocks(ctx, D, ctx.T26[0], ctx.T27[0])
    innov = filt.apply(s_all, range(1955, 2028))
    f26, f27 = ss.fitted([2026, 2027]).values
    shocks_tab = pd.DataFrame({
        "noaa_T": ctx.noaa.loc[:2025].reindex(range(1950, 2028)),
        "hamilton_fitted": pd.Series({t: float(H.predict(ss.fit, ctx.noaa, [t]).iloc[0]) for t in range(1953, 2026)}
                                     | {2026: f26, 2027: f27}),
        "shock": pd.Series({t: float(np.mean(v)) for t, v in s_all.items()}),
        "innovation": pd.Series({t: float(np.mean(v)) for t, v in innov.items()}),
        "bk_published_pwt_shock": pub,
        "berkeley_summary_shock": berk.shocks,
        "gistemp_shock": gis2.shocks,
        "noaa_p6_shock": noaa6.shocks,
        "bk_published_bu_shock": bk_bu,
    }).loc[1950:2027]
    shocks_tab.loc[2026, "noaa_T"] = ctx.T26[0]
    shocks_tab.loc[2027, "noaa_T"] = ctx.T27[0]
    prov = {2026: ctx.prov26, 2027: ctx.prov27}
    fy = ss.fit.fit_years
    shocks_tab["status"] = ["in-sample" if fy[0] <= t <= fy[1] else (prov[t].method if t >= 2026 else
                            "observed, out of sample" if t > fy[1] else "lag only") for t in shocks_tab.index]
    shocks_tab["pct_rank_vs_fit_sample"] = [ss.rank(v) if np.isfinite(v) else np.nan for v in shocks_tab["shock"]]
    shocks_tab.index.name = "year"
    shocks_tab.to_csv(OUT / "shocks.csv", float_format="%.5f")

    ev = []
    for t in (2023, 2024, 2025, 2026, 2027):
        m = float(np.mean(s_all[t]))
        sd = {2026: ctx.T26[1], 2027: ctx.T27[1]}.get(t, 0.0)
        ev.append({"year": t, "status": prov[t].method if t >= 2026 else "observed",
                   "T_noaa": float(shocks_tab.loc[t, "noaa_T"]), "T_sd": sd,
                   "filter_expectation": float(shocks_tab.loc[t, "hamilton_fitted"]), "shock": m, "shock_sd": sd,
                   "innovation": float(np.mean(innov[t])), "pct_rank": ss.rank(m),
                   "rank_in_fit_sample": int((ss.reference > m).sum() + 1)})
    ev = pd.DataFrame(ev)
    ev.to_csv(OUT / "event_shocks.csv", index=False, float_format="%.4f")
    res["event_shocks"] = ev.to_dict(orient="records")
    res["provisional"] = {
        **{f"T{y}": {"mean": p.mean, "sd": p.sd, "method": p.method, "months_observed": p.months_observed,
                     "detail": p.detail,
                     "analogs": None if p.analogs is None else p.analogs.round(3).reset_index().to_dict(orient="records")}
           for y, p in prov.items()},
        "enso_model": ctx.enso.describe(), "enso_coef": ctx.enso.coef,
        "roni_djf_2027_assumption": ctx.roni_djf_assumption, "roni_djf_2027_observed": ctx.roni_djf_2027_observed,
        "s2027_regression_forecast": ctx.s27_forecast,
        "gistemp_minus_noaa_2016_2025": ctx.noaa_offset,
        "note": "Placeholders until NOAA publishes the annual values (2026: mid-Jan 2027; 2027: mid-Jan 2028). "
                "Terms lock only after the 2027 value is final."}
    res["innovation_filter"] = {k: {"coef": v.coef, "n": v.n, "fwl_other_controls": v.fwl_other}
                                for k, v in ctx.filters.items()}

    # ---------------------------------------------------------------- 3. IRFs table
    rows = []
    for key, irf in ctx.irfs.items():
        lo95, hi95 = irf.band(0.05)
        lo90, hi90 = irf.band(0.10)
        for h in range(11):
            rows.append({"irf": key, "h": h, "theta_pct_per_C": irf.theta[h], "se": irf.se[h],
                         "q025": lo95[h], "q05": lo90[h], "q95": hi90[h], "q975": hi95[h],
                         "temp_irf": None if irf.temp_irf is None else irf.temp_irf[h],
                         "shock_definition": irf.shock_definition})
    pd.DataFrame(rows).to_csv(OUT / "irf.csv", index=False, float_format="%.4f")
    res["irf_primary"] = {"theta": ctx.irfs["PWT_ts"].theta, "se_nw": ctx.irfs["PWT_ts"].se,
                          "peak": float(ctx.irfs["PWT_ts"].theta.min()), "peak_h": int(ctx.irfs["PWT_ts"].theta.argmin())}

    # ---------------------------------------------------------------- 4. null model + backtests
    null = B.fit_null(ctx.wdi, D.calib, D.exclude, anchor_year=A.ANCHOR)
    g = B.log_growth(ctx.wdi)
    res["frozen_drift_reference"] = {
        "note": "the no-effect path until 30 Oct 2026; now a sensitivity variant",
        "anchor_year": null.anchor_year, "anchor_level": float(ctx.wdi.loc[A.ANCHOR]),
        "mu_pp": null.mu, "sigma_pp": null.sigma, "calib_years": null.calib_years,
        "growth_by_period": {f"{a}-{b}": float(g.loc[a:b].mean()) for a, b in
                             [(1991, 2000), (2001, 2010), (2011, 2019), (2000, 2019), (1991, 2019), (2022, 2025)]}}
    imf, em = ctx.imf, ctx.imf_errors
    leads = np.arange(D.base_year + 1, D.window[1] + 1) - A.ANCHOR          # forecast leads the statistic spans
    tot = em.paths[:, np.minimum(leads, em.max_lead) - 1].sum(axis=1)
    res["baseline_primary"] = {
        "vintage": imf.vintage, "projected_through": imf.projected_through, "wdi_gap_pp": imf.wdi_gap,
        "gap_years": list(A.IB.GAP_YEARS),
        "gap_corr": float(np.corrcoef(g.loc[A.IB.GAP_YEARS[0]:A.IB.GAP_YEARS[1]],
                                      imf.imf_growth.reindex(g.loc[A.IB.GAP_YEARS[0]:A.IB.GAP_YEARS[1]].index))[0, 1]),
        "growth_pp": {int(t): float(v) for t, v in imf.growth.loc[2026:2037].items()},
        "imf_implied_pp": {int(t): float(v) for t, v in imf.imf_growth.loc[2026:imf.projected_through].items()},
        "window_mean_pp": imf.window_mean(D.base_year, D.window[1]),
        "errors": {"source": em.source, "n_forecasts": int(em.paths.shape[0]), "max_lead": em.max_lead,
                   "mean_by_lead": em.paths.mean(axis=0), "sd_by_lead": em.paths.std(axis=0, ddof=1),
                   "statistic_leads": leads.tolist(), "sum_over_statistic_mean": float(tot.mean()),
                   "sum_over_statistic_sd": float(tot.std(ddof=1)), "n_below_forecast": int((tot < 0).sum()),
                   "first_vintage": int(em.origins[0]) + 1, "last_vintage": int(em.origins[-1]) + 1,
                   "average_miss": "kept (decided 30 Oct 2026): the no-effect path carries the IMF's historical "
                                   "average miss",
                   "beyond_max_lead": "each later year drawn independently from the last lead's errors"}}
    bts = []
    for name, lv in [("WDI_USD_1960_2025", ctx.wdi_usd), ("PWT_world_1951_2019", pwt_ts["rgdppc_world_pwt"].dropna()),
                     ("BU_world_1850_2019", bu_ts["rgdppc_world_bud"].dropna().loc[:2019])]:
        for L in (29, 20):
            hz = (D.window[0] - D.base_year, D.window[1] - D.base_year)  # same horizons as the statistic
            bt = B.backtest(lv, L, hz)
            bt = bt[[not (o + hz[0] <= 2021 and o + hz[1] >= 2020) for o in bt.index]]
            if len(bt):
                bts.append({"series": name, "calib_len": L, "horizons": f"{hz[0]}-{hz[1]}",
                            "origins": f"{bt.index.min()}-{bt.index.max()}",
                            "n": len(bt), "M_mean": bt.M.mean(), "M_sd": bt.M.std(), "M_rms": float(np.sqrt((bt.M ** 2).mean()))})
    bts = pd.DataFrame(bts)
    bts.to_csv(OUT / "null_backtest.csv", index=False, float_format="%.3f")
    res["null_backtest"] = bts.to_dict(orient="records")

    # ---------------------------------------------------------------- 5. simulations
    prim = A.simulate(ctx, D, N_PATHS, SEED, D0_cache=cache)
    nofut = A.simulate(ctx, replace(D, future_temps="none"), N_PATHS, SEED, D0_cache=cache)
    oc = prim.oc()
    eff_M = A.statistic(prim.effect, prim.years, D.window, D.base_year)
    res["refreshed_utc"] = pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds")
    gap = prim.m1 - prim.m0          # the two worlds, path by path: shock effects less the background netting
    res["contract_primary"] = oc.as_dict() | {
        "h1_effect_mean": float(eff_M.mean()),
        "h1_effect_q05": float(np.quantile(eff_M, 0.05)), "h1_effect_q95": float(np.quantile(eff_M, 0.95)),
        "shortfall_mean": float(gap.mean()),
        "shortfall_q05": float(np.quantile(gap, 0.05)), "shortfall_q95": float(np.quantile(gap, 0.95)),
        "background_netting_pts": float((gap - eff_M).mean()),
        "threshold_growth_equivalent_pp": A.growth_equivalent(prim.null.mu, D, oc.threshold),
        "baseline_growth_pp": prim.null.mu,
        "h0_growth_mean_pp": float(prim.null.mu + prim.m0.mean() / A.mean_horizon(D)),
        "h1_growth_mean_pp": float(prim.null.mu + prim.m1.mean() / A.mean_horizon(D)),
        "p_yes_no_effect": 1 - oc.false_positive, "p_yes_paper": 1 - oc.sensitivity,
        "loss_threshold_equal_costs": W.loss_threshold(prim.m0, prim.m1).as_dict()}
    np.savez_compressed(OUT / "primary_M_draws.npz", m0=prim.m0.astype(np.float32), m1=prim.m1.astype(np.float32))
    qs = np.linspace(0.01, 0.99, 99)
    pd.DataFrame({"quantile": qs, "M_H0": np.quantile(prim.m0, qs), "M_H1": np.quantile(prim.m1, qs)}) \
        .to_csv(OUT / "primary_M_quantiles.csv", index=False, float_format="%.4f")
    bands = A.annual_bands(prim)
    bands.to_csv(OUT / "scenario_annual.csv", float_format="%.4f")
    # full-path decomposition: what B&K imply for every shock, including the ones outside the tested prediction
    decomp = A.decomposition(ctx, replace(D, scope="full"), years=prim.years)
    h1_groups = {"full": ("2015-2022", "2023-2025", "2026-2027"), "recent": ("2023-2025", "2026-2027"),
                 "incremental": ("2026-2027",)}[D.scope]
    decomp.to_csv(OUT / "effect_decomposition.csv", float_format="%.4f")
    # contribution of each shock group to the expected M (point IRF, central temperatures)
    cols = [c for c in decomp.columns if str(c).isdigit()]
    yrs_d = np.array([int(c) for c in cols])
    contrib = {}
    for lab, lo, hi in (("2015-2022", 2015, 2022), ("2023-2025", 2023, 2025), ("2026-2027", 2026, 2027)):
        path_g = decomp.loc[[t for t in decomp.index if lo <= t <= hi], cols].sum().values
        contrib[lab] = float(A.statistic(path_g[None, :], yrs_d, D.window, D.base_year)[0])
    fut_M = A.statistic(prim.effect - nofut.effect, prim.years, D.window, D.base_year)
    contrib["2028+ (simulated)"] = float(fut_M.mean())
    contrib["total"] = float(sum(contrib.values()))
    res["effect_contributions_to_M"] = contrib
    fut_years = sorted(prim.future)
    fut_tab = pd.DataFrame({"shock_mean": [prim.future[t].mean() for t in fut_years],
                            "shock_q10": [np.quantile(prim.future[t], 0.10) for t in fut_years],
                            "shock_q90": [np.quantile(prim.future[t], 0.90) for t in fut_years]}, index=fut_years)
    jb = int(np.flatnonzero(prim.years == D.base_year)[0])
    eff_with = pd.Series(prim.effect.mean(axis=0) - prim.effect[:, jb].mean(), index=prim.years).loc[D.base_year:]
    eff_without = pd.Series(nofut.effect.mean(axis=0) - nofut.effect[:, jb].mean(), index=prim.years).loc[D.base_year:]
    fut_tab = fut_tab.join(pd.DataFrame({"effect_with_future_pct": eff_with, "effect_without_future_pct": eff_without}),
                           how="outer")
    fut_tab.index.name = "year"
    fut_tab.to_csv(OUT / "future_temperatures.csv", float_format="%.4f")
    res["future_temperatures"] = {
        "model": ctx.enso_paths.describe(), "shock_mean_by_year": fut_tab.shock_mean.dropna().to_dict(),
        "effect_on_M_mean": float(fut_M.mean()), "effect_on_M_q05": float(np.quantile(fut_M, 0.05)),
        "effect_on_M_q95": float(np.quantile(fut_M, 0.95)),
        "cutoff_without_pp": A.growth_equivalent(nofut.null.mu, D, nofut.oc().threshold),
        "youden_j_without": nofut.oc().youden_j,
        "note": "simulated post-2027 shocks enter H1 through their innovations (the part the two prior shocks do "
                "not predict); the cutoff is still fixed in advance"}
    eff_q = pd.DataFrame({"q05": np.quantile(prim.effect, 0.05, axis=0), "q50": np.quantile(prim.effect, 0.5, axis=0),
                          "q95": np.quantile(prim.effect, 0.95, axis=0)}, index=prim.years)

    # conditional on the central provisional temperatures (what the contract would compute)
    cond = A.simulate(ctx, D, N_PATHS, SEED, T26=ctx.T26[0], T27=ctx.T27[0], D0_cache=cache).oc()
    res["contract_primary_conditional_on_central_temps"] = cond.as_dict()

    # conditional contracts on NOAA's 2027 value (listed 1 Jan 2027), with strike ladders
    bins = A.conditional_bins(ctx, D, N_PATHS, SEED, D0_cache=cache)
    bins["strike"] = bins.growth_bar.round(1)
    bins["p_yes_no_effect_at_strike"] = [float((r.sim.m0 > (r.strike - r.sim.null.mu) * A.mean_horizon(D)).mean())
                                         for r in bins.itertuples()]
    bins["p_yes_paper_at_strike"] = [float((r.sim.m1 > (r.strike - r.sim.null.mu) * A.mean_horizon(D)).mean())
                                     for r in bins.itertuples()]
    bins["condition"] = [spec_condition(r.lower, r.upper) for r in bins.itertuples()]
    mid = float(bins.loc[bins.bin == "central", "strike"].iloc[0])          # ladder: 0.2 apart around the
    bars = np.unique(np.round(np.r_[mid + 0.2 * np.arange(-5, 6), bins.strike], 1))   # central strike, plus headlines
    ladder = pd.concat([A.strike_ladder(prim, D, bars).assign(condition="none (unconditional)")]
                       + [A.strike_ladder(r.sim, D, bars).assign(condition=r.bin) for r in bins.itertuples()])
    np.savez_compressed(OUT / "conditional_M_draws.npz",
                        **{f"{x.bin}_{h}": getattr(x.sim, h).astype(np.float32) for x in bins.itertuples()
                           for h in ("m0", "m1")})
    # the kept IMF miss, judged against a no-effect path centred on the IMF projection instead (as if the
    # IMF's average miss had stopped): how often each headline strike would then resolve No
    em = ctx.imf_errors
    ctx_c = replace(ctx, imf_errors=A.IB.ErrorModel(em.source + " [centred]", em.paths - em.paths.mean(axis=0),
                                                    em.origins))
    k = A.mean_horizon(D)
    res["imf_miss_if_centred"] = {
        r.bin: {"strike": float(r.strike), "p_no_no_effect": float((s.sim.m0 <= (r.strike - s.sim.null.mu) * k).mean()),
                "p_no_paper": float((s.sim.m1 <= (r.strike - s.sim.null.mu) * k).mean())}
        for r, s in zip(bins.itertuples(), A.conditional_bins(ctx_c, D, N_PATHS, SEED, D0_cache={}).itertuples())}
    bins_tab = bins.drop(columns="sim")
    bins_tab.to_csv(OUT / "conditional_bins.csv", index=False, float_format="%.4f")
    ladder.to_csv(OUT / "strike_ladder.csv", index=False, float_format="%.4f")
    res["conditional_contracts"] = {
        "levels_note": "20th/50th/80th percentiles of the current 2027 forecast; bins split halfway between them",
        "bins": [{k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in r.items()}
                 for r in bins_tab.to_dict(orient="records")],
        "ladder": ladder.to_dict(orient="records")}

    res["paper_checks"] = paper_checks(ctx, D)

    vrows = []

    def same_stat(d):
        return (d.window, d.base_year) == (D.window, D.base_year)

    for d in A.variants(D):
        sim = prim if d.name == "primary" else A.simulate(ctx, d, N_PATHS, SEED, D0_cache=cache)
        o = sim.oc()
        vrows.append({"variant": d.name, "drift_pp": sim.null.mu, "mean_shift": o.mean_h1 - o.mean_h0,
                      "sd_h0": o.sd_h0, "sd_h1": o.sd_h1, "threshold": o.threshold,
                      "threshold_growth_pp": A.growth_equivalent(sim.null.mu, d, o.threshold),
                      "sensitivity": o.sensitivity, "false_positive": o.false_positive, "youden_j": o.youden_j,
                      "auc": o.auc, "overlap": o.overlap,
                      "sens_at_primary_c": float((sim.m1 <= oc.threshold).mean()) if same_stat(d) else np.nan,
                      "fpr_at_primary_c": float((sim.m0 <= oc.threshold).mean()) if same_stat(d) else np.nan})
    vt = pd.DataFrame(vrows)
    vt.to_csv(OUT / "contract_variants.csv", index=False, float_format="%.4f")
    res["contract_primary"]["p_no_at_primary_c_by_scope"] = {
        "note": "P(M <= primary c) when the outcome is generated by each scope's B&K effect",
        **{r.variant: float(r.sens_at_primary_c) for r in vt.itertuples()
           if r.variant == "primary" or r.variant.startswith("scope:")}}
    res["contract_variants"] = vt.to_dict(orient="records")

    t27_grid = np.round(np.arange(1.25, 1.801, 0.025), 3)
    t26_vals = ([round(ctx.T26[0], 3)] if ctx.prov26.observed else
                [round(ctx.T26[0] - 0.03, 3), round(ctx.T26[0], 3), round(ctx.T26[0] + 0.03, 3)])
    grid = A.threshold_grid(ctx, D, t27_grid, t26_vals, N_PATHS, SEED, D0_cache=cache)
    grid.to_csv(OUT / "threshold_grid.csv", index=False, float_format="%.4f")
    alt = "incremental" if D.scope != "incremental" else "full"
    gi = A.threshold_grid(ctx, replace(D, name=alt, scope=alt), t27_grid, [round(ctx.T26[0], 3)],
                          N_PATHS, SEED, D0_cache=cache)
    gi.to_csv(OUT / f"threshold_grid_{alt}.csv", index=False, float_format="%.4f")
    res["hindcast_2023_2025"] = A.hindcast_2022(ctx, D)

    # ---------------------------------------------------------------- 6. figures
    P.fig_gmst(ctx.noaa.loc[:2025], {2026: f26, 2027: f27}, ctx.T26, ctx.T27, FIG / "fig1_gmst.png",
               labels={2026: ctx.prov26.method, 2027: ctx.prov27.method})
    prov = {2026: (float(np.mean(s_all[2026])), ctx.T26[1]), 2027: (float(np.mean(s_all[2027])), ctx.T27[1])}
    ranks = {"2023": (float(s_all[2023]), ss.rank(float(s_all[2023])), P.INK2),
             "2024": (float(s_all[2024]), ss.rank(float(s_all[2024])), P.RED),
             "2027p": (prov[2027][0], ss.rank(prov[2027][0]), P.ORANGE)}
    P.fig_shocks(ss.shocks, prov, bk_pwt, ss.reference, ranks, FIG / "fig2_shocks.png", fit_years=ss.fit.fit_years)
    P.fig_irf(ctx.irfs, FIG / "fig3_irf.png", placeholder=HANDOFF_PLACEHOLDER)
    if D.base_year > A.ANCHOR:
        shade, shade_label = (D.base_year + 1, D.window[1]), f"contract: growth {D.base_year}-{D.window[1]}"
    else:
        shade, shade_label = D.window, "contract window"
    P.fig_effect(decomp, eff_q, shade, FIG / "fig4_effect_decomposition.png", h1_groups=h1_groups,
                 shade_label=shade_label,
                 future=pd.Series((prim.effect - nofut.effect).mean(axis=0), index=prim.years))
    P.fig_paths(ctx.wdi, bands, D.base_year, D.window, oc.threshold, FIG / "fig5_gdp_paths.png",
                note=f"H0: 2025 WDI level grown along the IMF projection ({imf.vintage}), with the IMF's average miss "
                     f"and spread from {em.source}; left panel projected from the last observed year (2025). H1 adds "
                     "the B&K effect with IRF and temperature uncertainty, including simulated post-2027 temperatures "
                     "(common random numbers).", ref="IMF projection" if D.baseline == "imf" else "no-effect path")
    P.fig_outcome(prim.m0, prim.m1, oc, A.stat_label(D), FIG / "fig6_outcome_distribution.png")
    P.fig_grid(grid, ctx.T27, round(ctx.T26[0], 3), float(ctx.noaa.loc[2024]), FIG / "fig7_threshold_vs_T2027.png",
               t26_label="observed" if ctx.prov26.observed else "placeholder")
    P.fig_variants(vt, FIG / "fig8_variants.png")
    P.fig_horizon(scan, end, FIG / "fig9_horizon_scan.png", D.base_year)
    e0 = np.diff(np.c_[np.zeros(len(prim.D0)), prim.D0], axis=1)                 # annual error under H0
    gb = imf.growth.loc[prim.years].values[None, :] + e0
    band = pd.DataFrame({"q10": np.quantile(gb, 0.10, axis=0), "q90": np.quantile(gb, 0.90, axis=0)}, index=prim.years)
    P.fig_baseline(g, imf, null.mu, FIG / "fig10_imf_baseline.png", int(prim.years[-1]), band=band,
                   error_source=em.source,
                   expected=pd.Series(imf.growth.loc[prim.years].values + e0.mean(axis=0), index=prim.years))
    P.fig_future_temps(fut_tab[["shock_mean", "shock_q10", "shock_q90"]].dropna()
                       .rename(columns={"shock_mean": "mean_", "shock_q10": "q10", "shock_q90": "q90"}),
                       eff_with, eff_without, FIG / "fig11_future_temperatures.png", D.base_year)
    P.fig_bins(bins, A.stat_label(D), FIG / "fig12_conditional_bins.png")

    (OUT / "results.json").write_text(json.dumps(jsonable(res), indent=2))
    # one row per full run, so a refresh can report what moved since the previous one
    log_row = {"refreshed_utc": res["refreshed_utc"],
               "noaa_through": noaa_through(ctx.noaa_monthly),
               "gistemp_last_modified": ctx.vintages.get("gistemp", {}).get("http_last_modified"),
               "wdi_lastupdated": ctx.vintages.get("wdi_lastupdated"),
               "T2026": ctx.T26[0], "T2026_sd": ctx.T26[1], "T2026_method": ctx.prov26.method,
               "T2027": ctx.T27[0], "T2027_sd": ctx.T27[1], "T2027_method": ctx.prov27.method,
               "s2026": float(np.mean(s_all[2026])), "s2027": float(np.mean(s_all[2027])),
               "end_year": end, "baseline_growth_pp": prim.null.mu, "error_model": em.source.split(":")[0],
               "threshold_c": oc.threshold, "growth_bar_pp": res["contract_primary"]["threshold_growth_equivalent_pp"],
               "predicted_shift": res["contract_primary"]["h1_effect_mean"], "sensitivity": oc.sensitivity,
               "false_positive": oc.false_positive, "youden_j": oc.youden_j,
               "future_temp_effect": float(fut_M.mean()),
               **{f"bar_{r.bin}": r.growth_bar for r in bins.itertuples()},
               **{f"bin_edge_{k}": v for k, v in (("lo", bins.upper.iloc[0]), ("hi", bins.lower.iloc[2]))}}
    log_path = OUT / "refresh_log.csv"
    pd.concat([pd.read_csv(log_path), pd.DataFrame([log_row])] if log_path.exists() else [pd.DataFrame([log_row])]) \
        .to_csv(log_path, index=False, float_format="%.4f")
    print(json.dumps(jsonable({k: res[k] for k in ("hamilton_fit_primary", "event_shocks", "contract_primary",
                                                   "irf_replication_max_abs_diff")}), indent=1)[:4000])
    print(scan[["end_year", "mean_shift", "sd_h0", "growth_bar", "youden_j", "youden_j_no_future"]].round(3)
          .to_string(index=False))
    print(bins_tab[["bin", "condition", "prob_now", "growth_bar", "strike", "youden_j"]].round(3).to_string(index=False))
    print(vt.round(3).to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download all data sources")
    ap.add_argument("--lock", nargs=2, type=float, metavar=("T2026", "T2027"),
                    help="compute the contractual threshold for realised NOAA 2026 and 2027 annual anomalies")
    args = ap.parse_args()
    if args.lock:
        lock_threshold(*args.lock)
    else:
        main(args.refresh)
