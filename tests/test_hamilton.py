import numpy as np
import pandas as pd
import pytest

from bk_elnino import hamilton as H
from bk_elnino import sources as S
from bk_elnino import temperature as TM
from conftest import ROOT

BK = ROOT / "data/external/micc_replication/1_empirics/data"


def ar_series(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    T = np.zeros(n)
    for t in range(3, n):
        T[t] = 0.03 + 0.5 * T[t - 2] + 0.45 * T[t - 3] + rng.normal(0, 0.1)
    return pd.Series(T, index=np.arange(1000, 1000 + n))


def test_lag_sets():
    assert H.lag_set(2, 2) == (2, 3)
    assert H.lag_set(2, 6) == (2, 3, 4, 5, 6, 7)
    assert H.lag_set(2, 2, "paper_eq1") == (2, 3, 4)


def test_design_row_orientation():
    T = pd.Series([10.0, 11, 12, 13, 14, 15], index=range(2000, 2006))
    X = H.design(T, [2005], (2, 3))
    assert X.tolist() == [[1.0, 13.0, 12.0]]  # [1, T(2003), T(2002)]


def test_recovers_known_coefficients():
    f = H.fit(ar_series(), 2, 2)
    assert f.lags == (2, 3)
    np.testing.assert_allclose(f.coef[1:], [0.5, 0.45], atol=0.03)


def test_residuals_mean_zero_and_orthogonal():
    T = ar_series(400, 1)
    f = H.fit(T, 2, 2)
    s = H.shocks(f, T)
    X = H.design(T, list(s.index), f.lags)
    np.testing.assert_allclose(X.T @ s.values, 0, atol=1e-8)


def test_gap_detection():
    T = pd.Series([0.1, 0.2, 0.3, 0.4], index=[2000, 2001, 2003, 2004])
    with pytest.raises(ValueError):
        H.fit(T, 2, 2)


def test_shock_from_value_matches_observed():
    T = ar_series(300, 2)
    f = H.fit(T, 2, 2, end=1250)
    s = H.shocks(f, T)
    yr = 1280
    assert H.shock_from_value(f, T, yr, T.loc[yr]) == pytest.approx(s.loc[yr])


def test_authors_shock_is_two_lag_formula():
    """The published PWT shock is exactly T_t - (a + b2 T_{t-2} + b3 T_{t-3}): weight 1 on
    T_t, zero on T_{t-4} -- i.e. p regressors, not the p+1 printed in eq. (1)."""
    pwt = S.read_bk_ts(BK / "micc_pwt_ts.dta")
    w = TM.exact_linear_weights(pwt["gtmp_bkly_aw_dtfe2"].dropna(), pwt["gtmpanom_bkly_aw"].dropna())
    assert w["max_abs_resid"] < 1e-5
    assert w["T(t-0)"] == pytest.approx(1.0, abs=1e-5)
    assert abs(w["T(t-4)"]) < 1e-5
    assert w["T(t-2)"] == pytest.approx(-0.51959, abs=1e-4)


def test_own_filter_reproduces_authors_shock():
    pwt = S.read_bk_ts(BK / "micc_pwt_ts.dta")
    T = pwt["gtmpanom_bkly_aw"].dropna()
    good = TM.compare(H.shocks(H.fit(T, 2, 2), T), pwt["gtmp_bkly_aw_dtfe2"].dropna())
    bad = TM.compare(H.shocks(H.fit(T, 2, 2, convention="paper_eq1"), T), pwt["gtmp_bkly_aw_dtfe2"].dropna())
    assert good["corr"] > 0.999 and good["max_abs_diff"] < 0.015
    assert bad["corr"] < 0.95


def test_berkeley_public_series_reproduces_authors_coefficients():
    be = S.read_berkeley_summary(ROOT / "data/raw/berkeley/Land_and_Ocean_summary.txt")
    f = H.fit(be.loc[1950:2022], 2, 2)
    np.testing.assert_allclose(f.coef, [0.03873, 0.51959, 0.46080], atol=0.002)


def test_bu_shock_uses_six_lags_from_t_minus_2():
    bu = S.read_bk_ts(BK / "micc_bu_ts.dta")
    assert bu["gtmp_noaa_aw_dtfe2"].first_valid_index() == 1857  # data from 1850 -> lags 2..7
    T = bu["gtmpanom_noaa_aw"].dropna()
    c6 = TM.compare(H.shocks(H.fit(T, 2, 6), T), bu["gtmp_noaa_aw_dtfe2"].dropna())
    assert c6["corr"] > 0.999


def test_placeholders_follow_incoming_data():
    """Nine observed months reproduce the original nowcast; a tenth month narrows it; a
    published annual value replaces it; early in a year the regression fallback is used.
    (Uses the GISTEMP vintage the original nowcast was built on; the logic is product-agnostic.)"""
    gis, mon = S.read_gistemp(ROOT / "data/raw/gistemp/GLB.Ts+dSST.csv")
    oni = S.read_oni(ROOT / "data/raw/oni/oni.ascii.txt")
    m9 = mon.copy()
    m9.loc[2026, ["Oct", "Nov", "Dec"]] = np.nan
    p9 = TM.nowcast_annual(m9, oni, 2026, TM.ONSET)
    assert p9.months_observed == 9
    assert p9.mean == pytest.approx(1.2835, abs=5e-4) and p9.sd == pytest.approx(0.0320, abs=5e-4)
    m10 = m9.copy()
    m10.loc[2026, "Oct"] = 1.45
    p10 = TM.nowcast_annual(m10, oni, 2026, TM.ONSET)
    assert p10.months_observed == 10 and p10.sd < p9.sd
    obs = TM.provisional_temperature(pd.concat([gis, pd.Series({2026: 1.30})]), m10, oni, 2026, TM.ONSET,
                                     label="NOAA annual")
    assert obs.observed and obs.mean == 1.30 and obs.method == "observed (NOAA annual)"
    reg = TM.provisional_temperature(gis, m9, oni, 2027, TM.DECAY, regression=(1.5, 0.1, {}))
    assert reg.method.startswith("ENSO regression") and reg.mean == 1.5
