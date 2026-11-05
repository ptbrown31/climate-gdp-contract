"""The three listing documents in terms/ against the run they are written from.

The flagship must read exactly as the plain ladder does at its threshold, every conditional threshold needs a
plain contract to convert into, the chances must be the run's, and no document may use gambling language.
"""
import json
import re

import pytest

import build_docs as B

pytestmark = pytest.mark.skipif(
    not (B.OUT / "results.json").exists() or not (B.ROOT / "data/raw/imf/NGDP_RPCH.json").exists(),
    reason="needs outputs/results.json and the IMF baseline file")


@pytest.fixture(scope="module")
def x():
    return B.R()


@pytest.fixture(scope="module")
def docs(x):
    return {"plain": B.plain_terms(x), "conditional": B.conditional_terms(x), "flagship": B.flagship_terms(x)}


def test_flagship_states_the_ladders_terms_at_its_threshold(x, docs):
    thr = f"{B.flagship_strike(x):.1f}"
    plain, flag = B.gdp_fields(x, "[##]"), B.gdp_fields(x, thr)
    assert plain.keys() == flag.keys()
    for k in plain:
        assert flag[k] == plain[k].replace("[##]", thr), k
        assert f"**{k}:** {flag[k]}" in docs["flagship"], k
        assert f"**{k}:** {plain[k]}" in docs["plain"], k
    assert B.gdp_question(x, thr) in docs["flagship"]


def test_every_conditional_threshold_has_a_plain_contract(x):
    plain = set(B.plain_ladder(x).strike_pct_yr.round(1))
    for name in ("cool", "central", "warm"):
        cond = set(x.ladder[x.ladder.condition == name].strike_pct_yr.round(1))
        assert cond <= plain, name
        assert round(x.bin(name)["strike"], 1) in cond, name
    assert B.flagship_strike(x) in plain


def test_chances_are_the_runs(x, docs):
    q = B.plain_ladder(x)
    row = q[q.strike_pct_yr.round(1) == B.flagship_strike(x)].iloc[0]
    assert f"If temperature shocks have no effect, the chance of Yes is {B.pc(row.p_yes_no_effect)}." in docs["flagship"]
    assert f"If the paper is right, the chance of Yes is {B.pc(row.p_yes_paper)}." in docs["flagship"]
    for b in x.bins:
        cells = [B.cond_label(b), B.pc(b["prob_now"]), f"{b['strike']:.1f}%", B.pc(b["p_yes_no_effect_at_strike"]),
                 B.pc(b["p_yes_paper_at_strike"]), f"{b['youden_j']:.2f}"]
        assert "| " + " | ".join(cells) + " |" in docs["conditional"], b["bin"]


def test_no_gambling_language(docs):
    for name, text in docs.items():
        words = re.findall(r"\b(bet|bets|betting|odds|win|wins|winning|wager|wagers)\b",
                           text.replace("Simon–Ehrlich wager", ""), re.I)
        assert not words, (name, words)


def test_gt_bounds_give_the_ranges(x):
    """GT resolves Yes above its threshold on NOAA's two-decimal value, so the two bounds must split every
    two-decimal value into the range the run labels it with."""
    lo, hi = B.gt_bounds(x)
    for t in [round(0.01 * k, 2) for k in range(100, 200)]:
        name = "cool" if not t > lo else ("central" if not t > hi else "warm")
        b = x.bin(name)
        assert (b["lower"] is None or t > b["lower"]) and (b["upper"] is None or t <= b["upper"]), (t, name)
    assert B.rng_text(x.bin("cool")).startswith(f"{lo:.2f} ")
    assert B.rng_text(x.bin("central")).endswith(f"{hi:.2f} °C")


def test_resolution_follows_the_first_estimate(x, docs):
    """1 October of the year after the end year, read again each month while the vintage lacks a year."""
    assert x.settle == x.end + 1
    for name, text in docs.items():
        assert f"1 October {x.settle}" in text and f"1 October {x.settle + 1}" not in text, name
        assert "on the first business day of the next month" in text, name


def test_documents_use_the_world_banks_word(x, docs):
    """The World Bank's archive calls each edition of the WDI a version, and the documents use its word."""
    for name, text in {**docs, "CONTRACT_TERMS": B.terms(x)}.items():
        assert not re.search("vintage", text, re.I), name
        assert "WDI version" in text, name


def test_archive_summary_matches_its_rows():
    """The figures CONTRACT_TERMS.md quotes from wdi_revisions.py's summary are those of its own rows."""
    w = json.loads((B.OUT / "wdi_revisions.json").read_text())
    s, rev, av = w["summary"], w["revisions"], w["availability"]
    d = [r["g5_1oct_next"] - r["g5_1oct_second"] for r in rev]
    assert s["n_end_years"] == len(rev) and s["mean_abs_diff"] == pytest.approx(sum(map(abs, d)) / len(d), abs=1e-3)
    assert s["max_abs_diff"] == pytest.approx(max(map(abs, d)), abs=1e-3)
    assert s["missing_on_1oct_next"] == [r["year"] for r in av if not r["on_1oct_next"]]
    since = s["found_on_1oct_every_year_since"]
    assert all(r["on_1oct_next"] for r in av if r["year"] + 1 >= since)
    assert not all(r["on_1oct_next"] for r in av if r["year"] + 1 >= since - 1)
