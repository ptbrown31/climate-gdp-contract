"""The site's in-browser model (site_tab/js/elnino-model.js) against the run it replays.

build_site_data.py writes the bundle the page loads and, beside it, the run's own statistic for a
set of designs (tests/fixtures/site_model_reference.npz). Here node runs the page's model on the
bundle for each design and every path's M must land within the bundle's int16 rounding of the
run's, with the same cutoff and error rates.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bk_elnino import wager as W  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "site_model_reference.npz"
BUNDLE = ROOT / "site_tab" / "data" / "elnino" / "model.json"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None or not FIX.exists() or not BUNDLE.exists(),
                                reason="needs node and the output of build_site_data.py")

# (fixture name, the page's settings for that design, end year)
CASES = [
    ("primary", {"t27": "forecast"}, 2031),
    ("cool", {"t27": "bin:cool"}, 2031),
    ("central", {"t27": "bin:central"}, 2031),
    ("warm", {"t27": "bin:warm"}, 2031),
    ("frozen", {"t27": "forecast", "baseline": "frozen"}, 2031),
    ("panel", {"t27": "forecast", "irf": "PWT_panel"}, 2031),
    ("bu", {"t27": "forecast", "irf": "BU_ts"}, 2031),
    ("transitory", {"t27": "forecast", "irf": "PWT_ts_transitory"}, 2031),
    ("recent", {"t27": "forecast", "scope": "recent"}, 2031),
    ("nofuture", {"t27": "forecast", "future": "none"}, 2031),
    ("point", {"t27": "forecast", "uncertainty": "point"}, 2031),
    ("end2029", {"t27": "forecast"}, 2029),
]


def test_page_model_replays_the_run(tmp_path):
    ref = np.load(FIX)
    for name, _, _ in CASES:
        for v in ("m0", "m1"):
            ref[f"{name}_{v}"].astype("<f8").tofile(tmp_path / f"{name}_{v}.bin")
    (tmp_path / "cases.json").write_text(json.dumps([{"name": n, "settings": s, "E": e} for n, s, e in CASES]))
    run = subprocess.run([NODE, str(ROOT / "tests" / "site_model_check.js"), str(tmp_path)],
                         capture_output=True, text=True, timeout=600)
    assert run.returncode == 0, run.stderr
    got = json.loads(run.stdout)
    for name, _, _ in CASES:
        g = got[name]
        assert g["maxdiff0"] < 0.005 and g["maxdiff1"] < 0.005, (name, g["maxdiff0"], g["maxdiff1"])
        oc = W.youden_threshold(ref[f"{name}_m0"], ref[f"{name}_m1"])
        y = g["youden"]
        assert abs(y["threshold"] - oc.threshold) < 0.02, (name, y["threshold"], oc.threshold)
        assert abs(y["sensitivity"] - oc.sensitivity) < 5e-4, (name, y["sensitivity"], oc.sensitivity)
        assert abs(y["falsePositive"] - oc.false_positive) < 5e-4, (name, y["falsePositive"], oc.false_positive)


def test_page_opens_on_the_published_central_contract():
    model = json.loads(BUNDLE.read_text())
    d = model["defaults"]
    central = next(b for b in model["published"]["bins"] if b["bin"] == "central")
    assert d["t27"] == "bin:central" and d["strike"] == central["strike"] and d["endYear"] == model["endYear"]
