"""Tests for the post-2027 temperature simulation and the IMF baseline."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bk_elnino import future_temps as FT
from bk_elnino import imf_baseline as IB
from bk_elnino import temperature as TM

ROOT = Path(__file__).resolve().parents[1]


def _toy_model():
    years = list(range(1950, 2027))
    rng = np.random.default_rng(0)
    djf = pd.Series(np.clip(rng.normal(0, 1, len(years)), -2.0, 1.4), index=years)
    djf.loc[[1958, 1983, 1998, 2016]] = [1.8, 2.3, 2.2, 2.1]
    shocks = pd.Series(0.07 * djf.values + rng.normal(0, 0.09, len(years)), index=years).loc[1953:2025]
    enso = TM.EnsoShockModel("RONI", "DJF", np.array([0.02, 0.07, 0.01, -0.04]), np.eye(4) * 1e-6, 0.09, 0.5, 70, ())
    return djf, FT.fit(djf, shocks, enso)


def test_strong_el_nino_paths_replay_analog_winters():
    djf, m = _toy_model()
    assert set(m.analog_years) == {1958, 1983, 1998, 2016}
    _, R = FT.simulate(m, {2025: 0.0, 2026: -0.5, 2027: 2.6}, range(2028, 2033), 5000, np.random.default_rng(1))
    allowed = {round(v, 10) for v in m.analog_seqs[:, 0]}
    assert {round(v, 10) for v in np.unique(R[2028])} <= allowed


def test_weak_winter_uses_autoregression_and_shapes():
    djf, m = _toy_model()
    sh, R = FT.simulate(m, {2025: 0.0, 2026: 0.0, 2027: 0.2}, range(2028, 2038), 2000, np.random.default_rng(2))
    assert sorted(sh) == list(range(2028, 2038)) and all(v.shape == (2000,) for v in sh.values())
    with pytest.raises(ValueError):
        FT.simulate(m, {2025: 0.0, 2026: 0.0, 2027: 0.2}, range(2028, 2040), 10, np.random.default_rng(3))


def test_real_enso_paths_turn_cool_after_the_el_nino():
    from bk_elnino import analysis as A
    roni = A.read_roni(ROOT / "data/raw/context/RONI.ascii.txt")
    djf = FT.winter_series(roni)
    shocks = pd.Series(np.zeros(73), index=range(1953, 2026))
    enso = TM.EnsoShockModel("RONI", "DJF", np.array([0.02, 0.07, 0.015, -0.04]), np.eye(4) * 1e-6, 0.09, 0.5, 63, ())
    m = FT.fit(djf, shocks, enso)
    sh, R = FT.simulate(m, {2025: djf[2025], 2026: djf[2026], 2027: 2.6}, range(2028, 2031), 20000,
                        np.random.default_rng(4))
    assert R[2028].mean() < -0.2 and R[2029].mean() < -0.2      # La Niña-leaning winters follow
    assert sh[2029].mean() < sh[2028].mean()                    # the y-2 term lowers 2029's shock


def test_imf_baseline_units_and_extension():
    wdi = pd.Series(np.exp(np.linspace(9.0, 10.0, 41)), index=range(1985, 2026))
    b = IB.load_baseline(ROOT / "data/raw/imf", wdi, 2037, "test vintage")
    assert b.projected_through == 2031
    assert b.growth.loc[2032] == b.growth.loc[2031] == b.growth.loc[2037]
    g = json.loads((ROOT / "data/raw/imf/NGDP_RPCH.json").read_text())["values"]["NGDP_RPCH"]["WEOWORLD"]
    lp = json.loads((ROOT / "data/raw/imf/LP.json").read_text())["values"]["LP"]["WEOWORLD"]
    expect = 100 * np.log1p(g["2028"] / 100) - 100 * np.log(lp["2028"] / lp["2027"])
    assert b.imf_growth.loc[2028] == pytest.approx(expect)
    assert b.growth.loc[2028] == pytest.approx(expect + b.wdi_gap)
    assert b.window_mean(2027, 2030) == pytest.approx(b.growth.loc[2028:2030].mean())


def test_error_paths_keep_mean_and_variance():
    rng = np.random.default_rng(5)
    paths = rng.normal(0.2, 1.0, size=(40, 6)) + rng.normal(0, 0.8, size=(40, 1))   # persistent component
    em = IB.ErrorModel("test", paths, tuple(range(40)))
    D = IB.simulate_deviation(em, range(2026, 2032), 200_000, np.random.default_rng(6), last_observed=2025)
    total = paths.sum(axis=1)
    assert D[:, -1].mean() == pytest.approx(total.mean(), abs=0.05)
    assert D[:, -1].std() == pytest.approx(total.std(ddof=1), rel=0.05)
    assert len(np.unique(np.round(D[:, -1], 6))) > 1000                              # continuous, not 40 points


def test_years_past_the_last_lead_are_independent_draws_of_it():
    rng = np.random.default_rng(7)
    paths = rng.normal(-0.5, 1.5, size=(31, 6))
    em = IB.ErrorModel("test", paths, tuple(range(31)))
    D = IB.simulate_deviation(em, range(2026, 2038), 200_000, np.random.default_rng(8), last_observed=2025)
    e = np.diff(np.c_[np.zeros(len(D)), D], axis=1)
    assert e[:, 6:].mean() == pytest.approx(paths[:, -1].mean(), abs=0.02)        # leads 7-12 centre on lead 6
    assert e[:, 6:].std(axis=0) == pytest.approx(np.full(6, paths[:, -1].std(ddof=1)), rel=0.03)
    assert abs(np.corrcoef(e[:, 7], e[:, 8])[0, 1]) < 0.01                         # not one repeated error
    D6 = IB.simulate_deviation(em, range(2026, 2032), 200_000, np.random.default_rng(8), last_observed=2025)
    assert np.allclose(D6, D[:, :6])                                                # in-horizon draws unchanged


def test_end_year_rule_takes_highest_j_and_breaks_ties_early():
    from bk_elnino import analysis as A
    scan = pd.DataFrame({"end_year": [2029, 2030, 2031, 2032], "youden_j": [0.40, 0.456, 0.454, 0.30]})
    assert A.select_end_year(scan) == 2030
    scan = pd.DataFrame({"end_year": [2030, 2031, 2032], "youden_j": [0.449, 0.451, 0.452]})
    assert A.select_end_year(scan) == 2030          # all round to 0.45: earliest wins


def test_conditions_are_stated_on_noaa_two_decimal_values():
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_analysis", ROOT / "run_analysis.py")
    ra = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ra)
    assert ra.spec_condition(-np.inf, 1.454) == "1.45 C or lower"
    assert ra.spec_condition(1.454, 1.535) == "1.46 to 1.53 C"
    assert ra.spec_condition(1.535, np.inf) == "1.54 C or higher"
    assert ra.spec_condition(1.45, 1.53) == "1.45 to 1.52 C"     # a value exactly on an edge belongs above it


def _write_xlsx(path, sheet: str, rows: list[list]):
    """Smallest valid workbook: one sheet, inline strings, numeric cells."""
    import zipfile
    from xml.sax.saxutils import escape

    def col(j):
        s = ""
        j += 1
        while j:
            j, r = divmod(j - 1, 26)
            s = chr(65 + r) + s
        return s

    body = []
    for i, row in enumerate(rows, 1):
        cells = []
        for j, v in enumerate(row):
            ref = f"{col(j)}{i}"
            if isinstance(v, str):
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(v)}</t></is></c>')
            elif v is not None:
                cells.append(f'<c r="{ref}"><v>{v}</v></c>')
        body.append(f'<row r="{i}">{"".join(cells)}</row>')
    m = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        z.writestr("xl/workbook.xml", f'<?xml version="1.0"?><workbook xmlns="{m}" xmlns:r="{r}"><sheets><sheet name="{sheet}" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", f'<?xml version="1.0"?><worksheet xmlns="{m}"><sheetData>{"".join(body)}</sheetData></worksheet>')


def _toy_weo_history(path, realized: pd.Series, bias=-0.3):
    """A workbook laid out like WEOhistorical.xlsx: sheet ngdp_rpch, one row per country-year,
    one column per vintage (S = April, F = October)."""
    vint = [f"{tag}{V}ngdp_rpch" for V in range(1990, 2026) for tag in ("S", "F")]
    rows = [["country", "WEO_Country_Code", "ISOAlpha_3Code", "year"] + vint]
    for country, code in (("United States", 111), ("World", 1)):
        for y in range(1990, 2032):
            r = [country, code, "WLD" if code == 1 else "USA", y]
            for v in vint:
                lead = y - int(v[1:5]) + 1
                r.append(float(realized[y] - bias * lead) if 1 <= lead <= 6 and y in realized.index else "n/a")
            rows.append(r)
    _write_xlsx(path, "ngdp_rpch", rows)


def test_imf_history_parser_reads_october_vintages(tmp_path):
    realized = pd.Series(np.linspace(2.5, 3.5, 36), index=range(1990, 2026))
    f = tmp_path / "WEOhistorical.xlsx"
    _toy_weo_history(f, realized)
    em = IB.imf_errors(f, realized)
    assert em.max_lead == 6 and em.origins[0] == 1989 and em.origins[-1] == 2019     # Oct 1990 ... Oct 2020
    lg = lambda g: 100 * np.log1p(np.asarray(g) / 100)                                 # noqa: E731
    k, V = 3, 2001
    expect = lg(realized[V + k - 1]) - lg(realized[V + k - 1] + 0.3 * k)
    assert em.paths[em.origins.index(V - 1), k - 1] == pytest.approx(expect)


def test_unreadable_imf_file_falls_back_to_labelled_stand_in(tmp_path):
    hist = tmp_path / "imf_hist"
    hist.mkdir()
    _write_xlsx(hist / "WEOhistorical.xlsx", "other", [["a"], [1], [2]])
    usd = pd.Series(np.exp(np.cumsum(np.full(66, 0.02))), index=range(1960, 2026))
    em = IB.load_errors(hist, ROOT / "data/raw/imf", usd)
    assert em.source.startswith("stand-in") and "not used" in em.source


def _toy_noaa():
    years = np.arange(1950, 2026)
    rng = np.random.default_rng(3)
    T = 0.01 * (years - 1950) + rng.normal(0, 0.1, len(years))
    T[-3:] += 0.25                                                     # a jump at the end, like 2023-25
    return pd.Series(T, index=years)


def test_post_2027_shocks_are_measured_with_the_designs_filter():
    from types import SimpleNamespace
    from dataclasses import replace
    from bk_elnino import analysis as A
    noaa = _toy_noaa()
    ff = TM.build("NOAA", noaa, 1950, 2025).fit
    ctx = SimpleNamespace(noaa=noaa, forecast_filter=ff)
    fut = {2028: np.array([0.1, -0.2]), 2029: np.array([0.0, 0.05]), 2030: np.array([-0.1, 0.0])}
    same = A.remeasure(ctx, replace(A.PRIMARY, calib_end=2025), 1.0, 1.1, fut)
    assert same is fut                                                 # one filter: nothing to convert
    d = replace(A.PRIMARY, calib_end=2022)
    fd = A.shock_set(ctx, d).fit
    out = A.remeasure(ctx, d, 1.0, 1.1, fut)
    T = {int(t): float(v) for t, v in noaa.items()}
    T[2026], T[2027] = 1.0, 1.1
    for t in (2028, 2029, 2030):
        T[t] = ff.coef[0] + ff.coef[1] * T[t - 2] + ff.coef[2] * T[t - 3] + fut[t]
        assert np.allclose(out[t], T[t] - (fd.coef[0] + fd.coef[1] * T[t - 2] + fd.coef[2] * T[t - 3]))


def test_paper_world_background_nets_out_the_papers_own_past_effects(monkeypatch):
    from types import SimpleNamespace
    from bk_elnino import analysis as A
    from bk_elnino import irf as I
    shocks = pd.Series(0.0, index=range(1950, 2026))
    shocks.loc[2000] = 0.1                                             # one shock, a permanent -10% per 1 C
    monkeypatch.setattr(A, "shock_set", lambda ctx, d: SimpleNamespace(shocks=shocks))
    A._PAST.clear()
    em = IB.ErrorModel("test", np.zeros((31, 6)), tuple(range(1989, 2020)))
    ctx = SimpleNamespace(filters={"PWT": I.InnovationFilter(np.zeros(3), {}, 0, "PWT")},
                          irfs={"PWT_ts": SimpleNamespace(theta=np.full(11, -10.0))}, imf_errors=em)
    drag = A.paper_drag_by_lead(ctx, A.PRIMARY)
    assert np.allclose(drag, -1.0 / 31)                                # each lead sees the -1 point once in 31 windows
    A._PAST.clear()
