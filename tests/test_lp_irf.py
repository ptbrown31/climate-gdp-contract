import numpy as np
import pandas as pd
import pytest

from bk_elnino import irf as I
from bk_elnino import lp
from bk_elnino import panel as PN
from conftest import ROOT

BK = ROOT / "data/external/micc_replication"


@pytest.fixture(scope="module")
def rep():
    return I.replication_check(BK)


def test_lp_point_estimates_match_stata(rep):
    assert (rep.gdp_b - rep.gdp_b_authors).abs().max() < 1e-5
    assert (rep.temp_b - rep.temp_b_authors).abs().max() < 1e-5


def test_newey_west_matches_stata(rep):
    assert (rep.gdp_se - rep.gdp_se_authors).abs().max() < 1e-5
    assert (rep.temp_se - rep.temp_se_authors).abs().max() < 1e-5


def test_newey_west_zero_lags_is_scaled_white():
    rng = np.random.default_rng(0)
    X = np.column_stack([np.ones(50), rng.normal(size=50)])
    e = rng.normal(size=50)
    XtXi = np.linalg.inv(X.T @ X)
    white = XtXi @ (X.T * e ** 2) @ X @ XtXi * 50 / 48
    np.testing.assert_allclose(lp.newey_west(X, e, 0), white)


def test_transitory_irf_matches_authors():
    pwt, _ = I.load_bk_data(BK)
    spec, _ = I.bk_specs()
    g = lp.lp_irf(pwt, spec)
    t = lp.lp_irf(pwt, spec, outcome="gtmp_bkly_aw")
    ref = pd.read_csv(BK / "1_empirics/output/bootci_gshock_trans_tsS.csv")
    np.testing.assert_allclose(lp.transitory_irf(g.b.values, t.b.values), ref.b.values, atol=1e-4)


def test_bootstrap_bands_close_to_authors_bu():
    _, bu = I.load_bk_data(BK)
    _, spec = I.bk_specs()
    g = lp.lp_irf(bu, spec)
    D = lp.wild_bootstrap_irf(bu, spec, nboot=1500, seed=7)
    lo, hi = lp.percentile_band(D, g.b.values, 0.05)
    ref = pd.read_csv(BK / "1_empirics/output/bootci_gshock_ts.csv")  # BU (file is overwritten by the L run)
    assert np.abs(lo - ref.lo1b.values).max() < 2.0
    assert np.abs(hi - ref.up1b.values).max() < 2.0


def test_panel_reproduces_authors_fig_iv():
    ours = PN.panel_irf(BK)
    ref = pd.read_stata(BK / "1_empirics/int/irfgs_base_plS.dta")
    col = "lnrgdppc_pwtbaseS"
    se = (ref["up1b" + col] - ref["lo1b" + col]).values / (2 * 1.959964)  # the saved 95% band
    assert np.abs(ours.b.values - ref["b" + col].values).max() < 1e-5
    assert np.abs(ours.se.values / se - 1).max() < 1e-5


# App. Fig. B.10's GDP-weighted response as plotted (read from the vector figure
# 3_output/1_figures/irfgs_lnrgdppc_pwt_plS_weighting.pdf; the authors do not save the numbers)
FIG_B10 = [-1.7766, -2.0814, -4.0257, -5.7531, -8.1227, -9.7353, -9.9365, -8.4715, -7.4837, -4.4783, -3.9044]


def test_gdp_weighted_panel_matches_paper_fig_b10():
    ours = PN.panel_irf(BK, weighted=True)
    assert np.abs(ours.b.values - FIG_B10).max() < 0.003


# ------------------------------------------------------------- applying the IRF

THETA = np.array([-1.0, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11])


def test_single_unit_shock_reproduces_irf_at_calendar_dates():
    yrs = np.arange(2026, 2040)
    e = I.effect_path(THETA, {2027: 1.0}, yrs)[0]
    assert e[0] == 0  # 2026: before the shock
    np.testing.assert_allclose(e[1:12], THETA)  # 2027..2037 = h 0..10
    np.testing.assert_allclose(e[12:], THETA[-1])  # held beyond h=10


def test_level_not_compounded():
    flat = np.full(11, -5.0)
    e = I.effect_path(flat, {2026: 1.0}, np.arange(2026, 2036))[0]
    np.testing.assert_allclose(e, -5.0)  # a level shift, not -5, -10, -15...


def test_additivity_and_scaling():
    yrs = np.arange(2026, 2036)
    a = I.effect_path(THETA, {2026: 0.1}, yrs)
    b = I.effect_path(THETA, {2027: 0.2}, yrs)
    ab = I.effect_path(THETA, {2026: 0.1, 2027: 0.2}, yrs)
    np.testing.assert_allclose(ab, a + b)
    np.testing.assert_allclose(I.effect_path(THETA, {2026: 0.3}, yrs), 3 * a)


def test_anchor_removes_effect_already_in_level():
    yrs = np.arange(2026, 2031)
    e = I.effect_path(THETA, {2024: 1.0, 2026: 1.0}, yrs, anchor=2025)[0]
    # 2024 shock: theta_{t-2024} - theta_1 ; 2026 shock: theta_{t-2026}
    expect = np.array([THETA[t - 2024] - THETA[1] + THETA[t - 2026] for t in yrs])
    np.testing.assert_allclose(e, expect)


def test_truncation_convention():
    e = I.effect_path(THETA, {2020: 1.0}, [2030, 2031], beyond="zero")[0]
    np.testing.assert_allclose(e, [THETA[10], 0.0])


def test_per_path_arrays_broadcast():
    draws = np.vstack([THETA, 2 * THETA])
    e = I.effect_path(draws, {2026: np.array([1.0, 0.5])}, [2026, 2027])
    np.testing.assert_allclose(e, [[THETA[0], THETA[1]], [THETA[0], THETA[1]]])


def test_innovation_filter_removes_predictable_part():
    f = I.InnovationFilter(np.array([0.0, 0.5, -0.2]), {}, 0, "test")
    s = {2020: 0.1, 2021: 0.2, 2022: 0.5 * 0.2 - 0.2 * 0.1}
    u = f.apply(s, [2022])
    assert u[2022] == pytest.approx(0.0)
