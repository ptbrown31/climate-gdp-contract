"""The Letter's page text (letter.json) against the Word draft it is read from.

The draft is Patrick's file and stays out of the repository, so these run only when ELNINO_LETTER
names it. Every figure and table must keep its legend, every citation must point at a reference,
every equation must come through whole, and every figure the page draws must be in the draft.
Since 6 Nov 2026 the draft opens with the article's introduction, numbered in reading order, and
the page puts the contract card after its contract question.
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


def block_runs(b, L):
    if b["type"] == "p":
        yield b["runs"]
    elif b["type"] == "list":
        yield from b["items"]
    elif b["type"] == "figure":
        yield L["figures"][b["id"]]["legend"]
    elif b["type"] == "table" and b.get("id"):
        yield L["tables"][b["id"]]["legend"]
        for row in L["tables"][b["id"]]["rows"]:
            yield from row


def all_runs(L):
    """Every run of text the page prints, in the draft's reading order, the reference list aside."""
    if L.get("summary"):
        yield L["summary"]
    for b in L["main"]:
        yield from block_runs(b, L)
    for s in L["sections"]:
        for b in s["blocks"]:
            yield from block_runs(b, L)


def citations(L):
    for runs in all_runs(L):
        for r in runs:
            if r.get("cite"):
                for part in r["t"].split(","):
                    a, _, b = part.strip().partition("–")
                    yield from range(int(a), int(b or a) + 1)


def test_every_figure_and_table_has_its_legend(L):
    assert {f"fig{k}" for k in range(1, 5)} <= set(L["figures"])
    for f in L["figures"].values():
        assert SA.runs_text(f["legend"]).startswith(f["label"] + " |"), f["label"]
    for t in L["tables"].values():
        assert t["rows"] and SA.runs_text(t["legend"]).startswith(t["label"] + " |"), t["label"]


def test_citations_point_at_references(L):
    refs = next(s for s in L["sections"] if s["title"] == "References")["refs"]
    assert [r["n"] for r in refs] == list(range(1, len(refs) + 1))
    cited = set(citations(L))
    assert cited and max(cited) <= len(refs)


def test_references_are_numbered_in_reading_order(L):
    refs = next(s for s in L["sections"] if s["title"] == "References")["refs"]
    first = list(dict.fromkeys(citations(L)))
    assert first == list(range(1, len(refs) + 1)), "a reference is uncited or numbered out of reading order"


def test_the_card_follows_the_contract_question(L):
    if L.get("summary"):
        pytest.skip("the Letter's own opening puts the card after the summary")
    text = [SA.runs_text(b["runs"]) if b["type"] == "p" else "" for b in L["main"]]
    q = [k for k, t in enumerate(text) if t.startswith("Will world GDP per capita grow by more than")]
    assert len(q) == 1 and L["main"][q[0]].get("indent"), "the page places the contract card after this question"
    assert any(b["type"] == "list" for b in L["main"][q[0] + 1:q[0] + 3]), "the list of the two outcomes follows it"
    assert L.get("subtitle")


def test_equations_come_through_whole(L):
    eqs = [b for s in L["sections"] for b in s["blocks"] if b["type"] == "eq"]
    assert eqs and all(b["tex"] and not b["tex"].rstrip().endswith(("/", "=", "+")) for b in eqs)
    numbered = [b["n"] for b in eqs if b["n"]]
    assert numbered == [str(k) for k in range(1, len(numbered) + 1)]


def test_page_draws_only_figures_the_draft_has(L):
    js = (SA.ROOT / "site_tab" / "js" / "climate-gdp.js").read_text()
    drawn = set(re.findall(r"^\s+(fig\d+|ed\d+): \[\[", js, re.M))
    assert drawn and drawn <= set(L["figures"])
