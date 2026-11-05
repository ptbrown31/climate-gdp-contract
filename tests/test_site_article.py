"""The Letter's page text (letter.json) against the Word draft it is read from.

The draft is Patrick's file and stays out of the repository, so these run only when ELNINO_LETTER
names it. Every figure and table must keep its legend, every citation must point at a reference,
every equation must come through whole, and every figure the page draws must be in the draft.
"""
import os
import re
from pathlib import Path

import pytest

import build_site_article as SA

LETTER = Path(os.environ.get("ELNINO_LETTER", ""))
pytestmark = pytest.mark.skipif(not LETTER.is_file(), reason="set ELNINO_LETTER to the Letter draft (.docx)")


@pytest.fixture(scope="module")
def L(tmp_path_factory):
    return SA.convert_letter(LETTER, tmp_path_factory.mktemp("letter"))


def all_runs(L):
    yield L["summary"]
    for p in L["main"]:
        yield p["runs"]
    for s in L["sections"]:
        for b in s["blocks"]:
            if b["type"] == "p":
                yield b["runs"]
    for f in list(L["figures"].values()) + list(L["tables"].values()):
        yield f["legend"]


def test_every_figure_and_table_has_its_legend(L):
    assert {f"fig{k}" for k in range(1, 5)} <= set(L["figures"])
    for f in L["figures"].values():
        assert SA.runs_text(f["legend"]).startswith(f["label"] + " |"), f["label"]
    for t in L["tables"].values():
        assert t["rows"] and SA.runs_text(t["legend"]).startswith(t["label"] + " |"), t["label"]


def test_citations_point_at_references(L):
    refs = next(s for s in L["sections"] if s["title"] == "References")["refs"]
    assert [r["n"] for r in refs] == list(range(1, len(refs) + 1))
    cited = {int(n) for runs in all_runs(L) for r in runs if r.get("cite") for n in re.findall(r"\d+", r["t"])}
    assert cited and max(cited) <= len(refs)


def test_equations_come_through_whole(L):
    eqs = [b for s in L["sections"] for b in s["blocks"] if b["type"] == "eq"]
    assert eqs and all(b["tex"] and not b["tex"].rstrip().endswith(("/", "=", "+")) for b in eqs)
    numbered = [b["n"] for b in eqs if b["n"]]
    assert numbered == [str(k) for k in range(1, len(numbered) + 1)]


def test_page_draws_only_figures_the_draft_has(L):
    js = (SA.ROOT / "site_tab" / "js" / "climate-gdp.js").read_text()
    drawn = set(re.findall(r"^\s+(fig\d+|ed\d+): \[\[", js, re.M))
    assert drawn and drawn <= set(L["figures"])
