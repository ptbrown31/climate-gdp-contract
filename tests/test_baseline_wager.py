import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from bk_elnino import baseline as B
from bk_elnino import wager as W


def levels():
    g = np.r_[np.full(29, 2.0), -4.0, 6.0, np.full(5, 2.0)] / 100  # 1991..2026 with a 2020-21 V
    y = 10000 * np.exp(np.r_[0, np.cumsum(g)])
    return pd.Series(y, index=np.arange(1990, 1990 + len(y)))


def test_growth_computed_before_filtering_years():
    lv = levels()
    with pytest.raises(ValueError):
        B.log_growth(lv.drop([2020, 2021]))  # would fabricate a 2019->2022 "annual" change
    m = B.fit_null(lv, (1991, 2025), exclude=(2020, 2021), anchor_year=2025)
    assert m.mu == pytest.approx(2.0)
    assert 2020 not in m.calib_years and 2022 in m.calib_years


def test_zero_noise_gives_zero_deviation():
    lv = levels().loc[:2019]
    m = B.fit_null(lv, (1991, 2019))
    D = B.simulate_deviation(m, range(2020, 2030), 100, np.random.default_rng(0), param_uncertainty=False)
    np.testing.assert_allclose(D, 0, atol=1e-10)


def test_deviation_variance_grows_with_horizon():
    rng = np.random.default_rng(1)
    g = rng.normal(2.0, 1.4, size=40)
    lv = pd.Series(1e4 * np.exp(np.r_[0, np.cumsum(g / 100)]), index=np.arange(1980, 2021))
    m = B.fit_null(lv, (1981, 2020))
    D = B.simulate_deviation(m, range(2021, 2031), 200_000, np.random.default_rng(2), param_uncertainty=False)
    var = D.var(axis=0)
    expect = m.sigma ** 2 * (len(m.calib_growth) - 1) / len(m.calib_growth) * np.arange(1, 11)
    np.testing.assert_allclose(var, expect, rtol=0.03)
    assert abs(D.mean()) < 0.02


def test_youden_threshold_normals():
    rng = np.random.default_rng(3)
    d = 2.0
    m0, m1 = rng.normal(0, 1, 200_000), rng.normal(-d, 1, 200_000)
    oc = W.youden_threshold(m0, m1)
    assert oc.threshold == pytest.approx(-d / 2, abs=0.05)
    assert oc.youden_j == pytest.approx(2 * norm.cdf(d / 2) - 1, abs=0.01)
    assert oc.auc == pytest.approx(norm.cdf(d / np.sqrt(2)), abs=0.005)
    assert oc.sensitivity + oc.false_negative == pytest.approx(1)


def test_window_mean():
    D = np.arange(20, dtype=float).reshape(2, 10)
    yrs = np.arange(2026, 2036)
    np.testing.assert_allclose(W.window_mean(D, yrs, (2031, 2035)), [7.0, 17.0])
    with pytest.raises(ValueError):
        W.window_mean(D, yrs, (2031, 2036))


def test_statistic_rebases_to_base_year():
    from bk_elnino import analysis as A
    yrs = np.arange(2026, 2036)
    D = np.vstack([np.arange(10.0), 2 * np.arange(10.0)])  # deviations from the 2025 anchor
    np.testing.assert_allclose(A.statistic(D, yrs, (2030, 2030), 2026), [4.0, 8.0])
    # anything already in the 2026 level (e.g. a 2026 shock's impact effect) cancels
    np.testing.assert_allclose(A.statistic(D + 5.0, yrs, (2030, 2030), 2026), [4.0, 8.0])
    # base = anchor reproduces the old level-mean statistic
    np.testing.assert_allclose(A.statistic(D, yrs, (2029, 2033), 2025), D[:, 3:8].mean(1))
    with pytest.raises(ValueError):
        A.statistic(D, yrs, (2026, 2026), 2026)


def test_growth_equivalent_uses_horizon_from_base():
    from dataclasses import replace

    from bk_elnino import analysis as A
    d = replace(A.PRIMARY, base_year=2026, window=(2030, 2030))
    assert A.mean_horizon(d) == 4
    assert A.growth_equivalent(2.0, d, -2.0) == pytest.approx(1.5)
