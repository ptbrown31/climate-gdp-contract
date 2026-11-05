"""The page's data for the Letter's figures (site_tab/data/elnino) against the run it comes from.

build_site_data.py writes one trend-baseline path file per start year, the World Bank levels and
the run's figures at the published settings. These tests rebuild Fig. 1a's numbers from the bundle
the way the page will (GDP levels from the 2025 observation, temperatures after 2027 from each
path's shocks) and check the start years and the sensitivity rows against the run's own tables.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_site_data as SD  # noqa: E402
from bk_elnino import analysis as A  # noqa: E402

DATA = ROOT / "site_tab" / "data" / "elnino"
BUNDLE = DATA / "model.json"
RESULTS = ROOT / "outputs" / "results.json"

pytestmark = pytest.mark.skipif(not BUNDLE.exists() or not RESULTS.exists(),
                                reason="needs the output of run_analysis.py and build_site_data.py")


@pytest.fixture(scope="module")
def model():
    return json.loads(BUNDLE.read_text())


@pytest.fixture(scope="module")
def res():
    return json.loads(RESULTS.read_text())


def paths(model, entry):
    return SD.unpack((DATA / entry["file"]).read_bytes(), entry["fields"], model["n"])


def test_trend_files_cover_the_start_years(model, res):
    t = model["trend"]
    assert t["windowEnd"] == A.TREND_END and [int(s) for s in t["starts"]] == list(A.TREND_STARTS)
    default = t["starts"][str(t["default"])]
    assert default["file"] == model["pathsFrozen"]["file"] and default["mu"] == pytest.approx(model["frozen"]["mu"])
    scan = {r["start"]: r for r in res["trend_start_scan"]["rows"]}
    for s, e in t["starts"].items():
        assert [f["name"] for f in e["fields"]] == ["d0", "d0base"] and (DATA / e["file"]).exists()
        assert e["calib"] == [int(s), A.TREND_END] and e["mu"] == pytest.approx(scan[int(s)]["drift_pp"])
    # the scan's 2000 and 1991 windows are the published trend variants
    var = {v["variant"]: v for v in res["contract_variants"]}
    v2000, v1991 = var["baseline: frozen 2000-2019 drift (until 30 Oct 2026)"], var["frozen baseline: 1991-2019 drift (handoff)"]
    for row, v in ((scan[2000], v2000), (scan[1991], v1991)):
        assert row["threshold_growth_pp"] == pytest.approx(v["threshold_growth_pp"])
        assert row["youden_j"] == pytest.approx(v["youden_j"])


def test_wdi_levels_give_the_growth(model):
    lv = {int(k): v for k, v in model["wdi"]["levels"].items()}
    for t, g in model["wdi"]["growth"].items():
        assert 100 * np.log(lv[int(t)] / lv[int(t) - 1]) == pytest.approx(g, abs=2e-4), t


def test_bundle_rebuilds_the_no_effect_levels(model):
    """Fig. 1a with no temperature effect: each path's level from the 2025 observation, year by year."""
    P = paths(model, model["paths"])
    g, base, pub = model["imf"]["growth"], model["base"], model["published"]["levels"]
    ln26 = 100 * np.log(model["wdi"]["levels"][str(model["anchor"])]) + g[str(base)] + P["d0base"][:, 0]
    assert np.quantile(np.exp(ln26 / 100), [0.1, 0.5, 0.9]) == pytest.approx(pub[str(base)]["h0"], abs=0.5)
    cum = 0.0
    for k, t in enumerate(model["years"][1:]):
        cum += g[str(t)]
        lv = np.exp((ln26 + cum + P["d0"][:, k]) / 100)
        assert np.quantile(lv, [0.1, 0.5, 0.9]) == pytest.approx(pub[str(t)]["h0"], abs=0.5), t


def test_bundle_rebuilds_the_temperature_levels(model):
    """Fig. 1a's temperatures: the 2026-27 draws, then the forecast filter plus each path's shock."""
    P = paths(model, model["paths"])
    tm, ff, n = model["temps"], model["forecastFilter"], model["n"]
    T = {t: np.full(n, v) for t, v in zip(range(model["noaa"]["first"], model["anchor"] + 1), model["noaa"]["T"])}
    T[2026] = tm["T26"]["mean"] + tm["T26"]["sd"] * P["z26"][:, 0]
    T[2027] = tm["T27"]["mean"] + tm["T27"]["sd"] * P["z27"][:, 0]
    for j, t in enumerate(model["paths"]["futureYears"]):
        T[t] = ff["coef"][0] + sum(b * T[t - lag] for b, lag in zip(ff["coef"][1:], ff["lags"])) + P["future"][:, j]
    pub = model["published"]["futureTemperatures"]
    assert sorted(int(t) for t in pub) == list(range(model["base"], model["years"][-1] + 1))
    for t, q in pub.items():
        got = np.quantile(T[int(t)], [0.05, 0.10, 0.50, 0.90, 0.95])
        assert got == pytest.approx([q["q05"], q["q10"], q["q50"], q["q90"], q["q95"]], abs=2e-3), t


def test_published_tables_come_from_the_run(model, res):
    pub = model["published"]
    assert pub["sensitivity"] == res["sensitivity_table"] and pub["trendStartScan"] == res["trend_start_scan"]
    assert len(pub["sensitivity"]["rows"]) == len(A.sensitivity_specs(A.primary_design(model["endYear"])))
    grid = pub["t27Grid"]
    rows = [r for r in res["threshold_grid"]["rows"] if r["T2026"] == grid["T2026"]]
    assert len(grid["rows"]) == len(rows) > 10
    assert [r["threshold_growth_pp"] for r in grid["rows"]] == [r["threshold_growth_pp"] for r in rows]
