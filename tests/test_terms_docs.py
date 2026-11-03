"""The three listing documents in terms/ against the run they are written from.

The flagship must read exactly as the plain ladder does at its threshold, every conditional threshold needs a
plain contract to convert into, the chances must be the run's, and no document may use gambling language.
"""
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
    assert f"If temperature shocks have no effect: {B.pc(row.p_yes_no_effect)} chance of Yes." in docs["flagship"]
    assert f"If the paper is right: {B.pc(row.p_yes_paper)} chance of Yes." in docs["flagship"]
    for b in x.bins:
        cells = [B.cond_label(b), B.pc(b["prob_now"]), f"{b['strike']:.1f}%", B.pc(b["p_yes_no_effect_at_strike"]),
                 B.pc(b["p_yes_paper_at_strike"]), f"{b['youden_j']:.2f}"]
        assert "| " + " | ".join(cells) + " |" in docs["conditional"], b["bin"]


def test_no_gambling_language(docs):
    for name, text in docs.items():
        words = re.findall(r"\b(bet|bets|betting|odds|win|wins|winning|wager|wagers)\b",
                           text.replace("Simon–Ehrlich wager", ""), re.I)
        assert not words, (name, words)
