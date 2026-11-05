"""Bilal-Kaenzig impulse responses and their application to dated temperature shocks.

Units: every IRF here is in *percent* = 100 x log points of world real GDP per capita
per 1 C shock (the authors' dependent variable is 100*[log y_{t+h} - log y_{t-1}]), so
no percent-to-log conversion is needed; theta/100 is already a log-point response.
Each value is a level response at horizon h, never a growth penalty to be compounded.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

from . import hamilton as H
from . import lp
from . import panel as PN
from . import sources as S

H_MAX = 10


@dataclass
class IRF:
    name: str
    theta: np.ndarray            # (H+1,) percent per 1 C
    draws: np.ndarray | None     # (n, H+1) re-centred joint draws, or None
    se: np.ndarray               # (H+1,) as reported (Newey-West or band-implied)
    temp_irf: np.ndarray | None  # temperature response, 1 at h=0 by construction
    shock_definition: str        # which temperature product / filter the IRF is "per unit" of
    note: str

    def band(self, alpha: float) -> tuple[np.ndarray, np.ndarray]:
        if self.draws is not None:
            return (np.quantile(self.draws, alpha / 2, axis=0), np.quantile(self.draws, 1 - alpha / 2, axis=0))
        from scipy.stats import norm
        z = norm.ppf(1 - alpha / 2)
        return self.theta - z * self.se, self.theta + z * self.se


def bk_specs():
    pwt = lp.LPSpec(y="lnrgdppc_world_pwt", shock="gtmp_bkly_aw_dtfe2s", start=1960, end=2019, p=2, ps=2, pr=2)
    bu = lp.LPSpec(y="lnrgdppc_world_bud", shock="gtmp_noaa_aw_dtfe2s", start=1860, end=2019, p=4, ps=4, pr=4,
                   dy_before_restrict=True)
    return pwt, bu


def load_bk_data(bk_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    pwt = S.read_bk_ts(bk_dir / "1_empirics/data/micc_pwt_ts.dta")
    bu = S.read_bk_ts(bk_dir / "1_empirics/data/micc_bu_ts.dta")
    for d in (pwt, bu):
        d["dummyrecession"] = d["recessiondates"]
    return pwt, bu


def replication_check(bk_dir: Path) -> pd.DataFrame:
    """Python LP vs the authors' saved Stata output (point estimates and NW s.e.)."""
    pwt, bu = load_bk_data(bk_dir)
    sp, sb = bk_specs()
    out = []
    for name, df, spec, ref_file, gcol, tcol in [
        ("PWT", pwt, sp, "gshock_tsS.csv", "lnrgdppc_world_pwt", "gtmp_bkly_aw"),
        ("BU", bu, sb, "gshock_tsL.csv", "lnrgdppc_world_bud", "gtmp_noaa_aw")]:
        ref = pd.read_csv(bk_dir / "1_empirics/output" / ref_file).set_index("h")
        g = lp.lp_irf(df, spec)
        t = lp.lp_irf(df, spec, outcome=tcol)
        for h in g.index:
            out.append({"sample": name, "h": h, "gdp_b": g.b[h], "gdp_b_authors": ref.loc[h, "b" + gcol],
                        "gdp_se": g.se[h], "gdp_se_authors": ref.loc[h, "se" + gcol],
                        "temp_b": t.b[h], "temp_b_authors": ref.loc[h, "b" + tcol],
                        "temp_se": t.se[h], "temp_se_authors": ref.loc[h, "seb" + tcol], "n": g.n[h]})
    return pd.DataFrame(out)


def _band_to_se(lo: np.ndarray, hi: np.ndarray, z: float = 1.959964) -> np.ndarray:
    return (np.asarray(hi) - np.asarray(lo)) / (2 * z)


def _mvn_draws(theta, se, corr, n, rng):
    cov = corr * np.outer(se, se)
    return rng.multivariate_normal(theta, cov, size=n, method="eigh")


def load_irfs(bk_dir: Path, nboot: int = 4000, seed: int = 123) -> dict[str, IRF]:
    """All IRFs used in the analysis, re-estimated (time series, GDP-weighted panel) or read (panel)."""
    pwt, bu = load_bk_data(bk_dir)
    sp, sb = bk_specs()
    irfs: dict[str, IRF] = {}
    corr_pwt = None
    for key, df, spec, tcol, shockdef in [
        ("PWT_ts", pwt, sp, "gtmp_bkly_aw", "Berkeley Earth GMST, Hamilton h=2 p=2 (1950-2022 fit)"),
        ("BU_ts", bu, sb, "gtmp_noaa_aw", "NOAA GMST, Hamilton h=2 p=6 (1850-2022 fit)")]:
        g = lp.lp_irf(df, spec)
        t = lp.lp_irf(df, spec, outcome=tcol)
        D = lp.recentre(lp.wild_bootstrap_irf(df, spec, nboot=nboot, seed=seed), g.b.values)
        irfs[key] = IRF(key, g.b.values, D, g.se.values, t.b.values, shockdef,
                        "Time-series LP of log world real GDP per capita (paper Fig. III); "
                        "wild-bootstrap ARX draws re-centred on the point estimate.")
        # transitory (Sims) counterfactual: +1 C for one year only
        tr = lp.transitory_irf(g.b.values, t.b.values)
        trD = np.array([lp.transitory_irf(d, t.b.values) for d in D])
        irfs[key + "_transitory"] = IRF(key + "_transitory", tr, trD, trD.std(axis=0), None, shockdef,
                                        "Response to a one-year +1 C temperature deviation (paper App. B.4).")
        if key == "PWT_ts":
            corr_pwt = np.corrcoef(D.T)
    # the data choices the paper checks in its country panel (App. Fig. B.11), applied here to the world time
    # series, which the paper does not report with them: NOAA temperature (h=2 p=2 shocks fitted on 1950-2022,
    # as for Berkeley Earth) and the authors' WDI world GDP (market exchange rates), everything else as in the
    # PWT spec
    noaa = bu["gtmp_noaa_aw"].dropna().loc[1950:]
    alt = pwt.copy()
    alt["gtmp_noaa_aw_h2p2s"] = H.shocks(H.fit(noaa, 2, 2, end=2022), noaa)
    for key, spec, shockdef in [
        ("PWT_ts_noaa", replace(sp, shock="gtmp_noaa_aw_h2p2s"), "NOAA GMST (authors' data), Hamilton h=2 p=2 "
                                                                   "(1950-2022 fit)"),
        ("PWT_ts_wdi", replace(sp, y="lnrgdppc_world_wdi"), "Berkeley Earth GMST, Hamilton h=2 p=2 (1950-2022 fit)")]:
        g = lp.lp_irf(alt, spec)
        D = lp.recentre(lp.wild_bootstrap_irf(alt, spec, nboot=nboot, seed=seed), g.b.values)
        irfs[key] = IRF(key, g.b.values, D, g.se.values, None, shockdef,
                        "PWT time-series LP with one data choice the paper checks in its panel (App. Fig. B.11); "
                        "wild-bootstrap draws re-centred on the point estimate.")
    # Panel (paper Fig. IV, the headline 14% / 18%): point + 95% band only
    rng = np.random.default_rng(seed + 1)
    for key, f, col, shockdef in [
        ("PWT_panel", "irfgs_base_plS.dta", "lnrgdppc_pwtbaseS", "Berkeley Earth GMST, Hamilton h=2 p=2"),
        ("BU_panel", "irfgs_base_plL.dta", "lnrgdppc_budbaseL", "NOAA GMST, Hamilton h=2 p=6")]:
        d = pd.read_stata(bk_dir / "1_empirics/int" / f)
        th = d["b" + col].values.astype(float)
        se = _band_to_se(d["lo1b" + col].values, d["up1b" + col].values)
        D = _mvn_draws(th, se, corr_pwt, nboot, rng)
        irfs[key] = IRF(key, th, D, se, None, shockdef,
                        "Country-panel LP average effect (paper Fig. IV); draws are normal with "
                        "band-implied s.e. and the PWT time-series bootstrap correlation (approximation).")
    # App. Fig. B.10: the PWT panel with each country weighted by its lagged share of world GDP (re-estimated;
    # the authors save only the plot)
    wp = PN.panel_irf(bk_dir, weighted=True)
    th, se = wp.b.values, wp.se.values
    irfs["PWT_panel_gdpw"] = IRF("PWT_panel_gdpw", th, _mvn_draws(th, se, corr_pwt, nboot, rng), se, None,
                                 "Berkeley Earth GMST, Hamilton h=2 p=2",
                                 "GDP-weighted country-panel LP (paper App. Fig. B.10); draws are normal with "
                                 "Driscoll-Kraay s.e. and the PWT time-series bootstrap correlation (approximation).")
    # Newey-West-scaled variant of the primary IRF (wider at long horizons)
    base = irfs["PWT_ts"]
    scale = base.se / base.draws.std(axis=0)
    Dnw = base.theta + (base.draws - base.theta) * scale
    irfs["PWT_ts_NWscaled"] = IRF("PWT_ts_NWscaled", base.theta, Dnw, base.se, base.temp_irf,
                                  base.shock_definition, "Primary IRF with draws rescaled to NW s.e. per horizon.")
    # stress test of the paper-side spread: the primary draws' deviations widened by half
    Dw = base.theta + 1.5 * (base.draws - base.theta)
    irfs["PWT_ts_wide"] = IRF("PWT_ts_wide", base.theta, Dw, 1.5 * base.draws.std(axis=0), base.temp_irf,
                              base.shock_definition, "Primary IRF with its draws' deviations widened by half.")
    return irfs


# ----------------------------------------------------------------- shock innovations

@dataclass
class InnovationFilter:
    """u_t = s_t - (c + r1 s_{t-1} + r2 s_{t-2}): the variation the LP coefficient responds to.

    The authors' LP controls for s_{t-1}, s_{t-2}, so theta_h is the response to the part of
    s_t not predicted by them; theta_h then also contains the effect of the *expected*
    follow-on shocks. Applying theta to raw consecutive shocks double counts that part.
    """
    coef: np.ndarray  # [c, r1, ..., rk]
    fwl_other: dict   # coefficients on the LP's non-shock controls in the full projection
    n: int
    sample: str

    @property
    def lags(self) -> int:
        return len(self.coef) - 1

    def apply(self, s: dict | pd.Series, years) -> dict:
        """Innovations for ``years``; values of ``s`` may be scalars or per-path arrays."""
        out = {}
        for t in years:
            pred = self.coef[0] + sum(self.coef[j] * np.asarray(s[t - j], float) for j in range(1, self.lags + 1))
            out[t] = np.asarray(s[t], float) - pred
        return out


def fit_innovation_filter(bk_dir: Path, sample: str = "PWT") -> InnovationFilter:
    """Projection of s_t on its own lags, estimated on the LP's h=0 sample.

    PWT uses 2 lags (1963-2019), BU 4 lags (1864-2019), matching the shock lags the
    LP controls for. The full Frisch-Waugh projection on all LP controls is reported
    too; its trend/dummy terms are not used because extrapolating a fitted trend to
    2026-27 would inject an arbitrary drift into the innovations.
    """
    pwt, bu = load_bk_data(bk_dir)
    sp, sb = bk_specs()
    df, spec = (pwt, sp) if sample == "PWT" else (bu, sb)
    d = lp._restricted(df, spec)
    X = lp.regressors(d, spec)
    Z = pd.concat([d["dy"].rename("dep"), X], axis=1).dropna()  # h=0 sample
    s = Z["shock"]
    W = Z.drop(columns=["dep", "shock"])
    b_full, *_ = np.linalg.lstsq(W.values, s.values, rcond=None)
    other = {c: float(v) for c, v in zip(W.columns, b_full) if not c.startswith("shock_")}
    A = np.column_stack([np.ones(len(Z))] + [Z[f"shock_L{j}"] for j in range(1, spec.ps + 1)])
    b, *_ = np.linalg.lstsq(A, s.values, rcond=None)
    return InnovationFilter(b, other, len(Z), sample)


# ----------------------------------------------------------------- applying the IRF

def response(theta: np.ndarray, h, beyond: str = "hold") -> np.ndarray:
    """theta at horizons ``h`` for each IRF row: (m, H+1) x (T,) -> (m, T); h<0 gives 0.

    Beyond the last estimated horizon: 'hold' keeps theta_H (the paper's responses do not
    mean-revert by year 10); 'zero' truncates to 0 (the handoff's literal formula).
    """
    theta = np.atleast_2d(np.asarray(theta, float))
    h = np.atleast_1d(np.asarray(h))
    H = theta.shape[1] - 1
    val = theta[:, np.clip(h, 0, H)]
    val[:, h < 0] = 0.0
    if beyond == "zero":
        val[:, h > H] = 0.0
    elif beyond != "hold":
        raise ValueError(beyond)
    return val


def effect_path(theta: np.ndarray, impulses: dict[int, np.ndarray | float], years, anchor: int | None = None,
                beyond: str = "hold") -> np.ndarray:
    """sum_tau theta_{t-tau} * impulse_tau for each calendar year t, in percent (100 x log).

    ``theta`` is (H+1,) or (m, H+1) (one IRF draw per Monte Carlo path); each impulse is a
    scalar or an (n,) array (one shock draw per path). With ``anchor`` A the path is
    expressed relative to year A: for shocks dated tau <= A the part of their effect
    already embedded in the observed anchor level, theta_{A-tau} * impulse_tau, is removed.
    Returns a 2-D array (max(m, n), len(years)).
    """
    years = np.asarray(list(years))
    out = 0.0
    for tau, imp in impulses.items():
        imp = np.asarray(imp, float).reshape(-1, 1)            # (k, 1)
        resp = response(theta, years - tau, beyond)             # (m, T)
        if anchor is not None and tau <= anchor:
            resp = resp - response(theta, [anchor - tau], beyond)  # (m, 1) broadcast
        out = out + imp * resp
    return np.atleast_2d(out)
