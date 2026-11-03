"""Objections we expect to the contract as a test of Bilal and Känzig (QJE 2026), with the answers.

One list, built from outputs/results.json, rendered by build_docs.py (MEMO.md, CONTRACT_TERMS.md)
and build_page.py, so the documents and the comment page give the same numbers. Each entry says
who would raise it, the answer, and whether the design addresses it or it stays a caveat.
"""
from __future__ import annotations

PAPER, OTHER, BOTH = "paper's side", "other side", "both sides"
ADDRESSED, CHECKED, CAVEAT = "addressed", "checked", "caveat"
WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}


def _m(x: float, d: int = 1) -> str:
    x = 0.0 if round(x, d) == 0 else x
    return f"{x:.{d}f}".replace("-", "−")


def _pc(p: float) -> str:
    return f"{100 * p:.0f}%"


def build(r: dict) -> list[dict]:
    d = r["design_primary"]
    base, end = d["base_year"], d["window"][1]
    span = end - base
    c = r["contract_primary"]
    var = {v["variant"]: v for v in r["contract_variants"]}
    pcx = r["paper_checks"]
    ev = {e["year"]: e for e in r["event_shocks"]}
    err = r["baseline_primary"]["errors"]
    imfw = pcx["imf_windows"]
    big = pcx["largest_in_sample_shock"]
    bins = {b["bin"]: b for b in r["conditional_contracts"]["bins"]}
    miss_c = r.get("imf_miss_if_centred", {}).get("central")
    pts = pcx["point_predictions"]
    gap, cut, J = c["shortfall_mean"], c["threshold_growth_equivalent_pp"], c["youden_j"]

    def v(name):
        x = var[name]
        return x["mean_shift"], x["threshold_growth_pp"], x["youden_j"]

    panel = v("IRF: PWT panel (paper's 14%)")
    gdpw = v("IRF: PWT panel, GDP-weighted (paper App. Fig. B.10)")
    nw = v("IRF: Newey-West-scaled draws")
    wide = v("IRF: draws widened by half")
    sens, sens_w = var["primary"]["sensitivity"], var["IRF: draws widened by half"]["sensitivity"]
    refit = v("filter: refit through 2025 (until 30 Oct 2026)")
    raw_bg = v("paper's world: raw IMF misses (no netting)")
    noaa = v("IRF: re-estimated with NOAA temperature (paper App. B.11)")
    wdi = v("IRF: re-estimated on WDI world GDP (paper App. B.11)")
    frozen = v("baseline: frozen 2000-2019 drift (until 30 Oct 2026)")
    rawsh = v("composition: raw shocks (handoff formula)")
    trans = v("IRF: transitory warmth only (Sims)")
    th = pcx["theta6"]
    s24 = ev[2024]["shock"]
    fy = big["fit_years"]
    cen_no = 1 - bins["central"]["p_yes_paper_at_strike"]

    out = [
        {"side": PAPER, "status": ADDRESSED,
         "objection": "The contract uses the paper's 12% estimate where its headline is 14%.",
         "answer": f"The contract is on world GDP per person, and the paper's estimate for world GDP is its time-series "
                   f"result (Fig. III, about 12% six years after a 1 °C shock). The 14% is the country-panel average, which "
                   f"weights every country equally. Weighting countries by their share of world GDP, as the paper "
                   f"does in App. Fig. B.10, gives {_m(th['PWT_panel_gdpw'])}% at year 6. Using the 14% moves the gap "
                   f"between the two worlds from {_m(abs(gap))} to {_m(abs(panel[0]))} points and the cutoff from "
                   f"{cut:.2f}% to {panel[1]:.2f}% a year (J {J:.2f} vs {panel[2]:.2f}). With the GDP-weighted panel "
                   f"they are {_m(abs(gdpw[0]))} points and {gdpw[1]:.2f}% (J {gdpw[2]:.2f})."},
        {"side": PAPER, "status": ADDRESSED,
         "objection": "The shock filter was fitted on the very years being tested.",
         "answer": f"Since 30 Oct 2026 the filter has been fitted on the paper's own window (dependent years {fy[0]}–{fy[1]}, "
                   f"data from 1950), so the 2023–27 warmth is measured out of sample. Refitting through 2025 shrinks "
                   f"each tested shock by about 0.04–0.05 °C and the gap to {_m(abs(refit[0]))} points (J {refit[2]:.2f})."},
        {"side": PAPER, "status": ADDRESSED,
         "objection": "The no-effect background already contains the paper's damage.",
         "answer": f"By the paper's own estimates, {_m(abs(imfw['paper_part_mean']))} of the IMF's average "
                   f"{_m(abs(imfw['miss_mean']))}-point miss over {WORDS.get(span, span)}-year windows came from temperature shocks "
                   f"(warming ran ahead of its trend after 1990). In the paper's world that part is taken out of the "
                   f"background, because the paper's damage enters through the shocks since 2015 instead. Without this, "
                   f"the gap would be {_m(abs(raw_bg[0]))} points and the contract would overstate its chance of resolving "
                   f"the paper's way."},
        {"side": PAPER, "status": ADDRESSED,
         "objection": "The contract uses NOAA temperatures and World Bank GDP where the paper uses Berkeley Earth and "
                      "the Penn World Table.",
         "answer": f"The paper reports similar results with NOAA, NASA and World Bank data (App. Fig. B.11), and says its "
                   f"Berkeley Earth measure tracks NOAA almost perfectly. Re-estimating the paper's world-GDP response "
                   f"with NOAA temperature gives {_m(th['PWT_ts_noaa'])}% at year 6 (the paper's is {_m(th['PWT_ts'])}%), "
                   f"and with World Bank GDP {_m(th['PWT_ts_wdi'])}%. The cutoffs become {noaa[1]:.2f}% and "
                   f"{wdi[1]:.2f}%, against {cut:.2f}%. The Penn World Table cannot settle the contract, because its "
                   "releases lag several years."},
        {"side": PAPER, "status": CAVEAT,
         "objection": "The growth period ends before the El Niño's full effect.",
         "answer": f"The paper's response peaks six years after a shock, after {end} for the 2027 shock. The end year is "
                   f"set by a fixed rule that maximises the separation between the two views. Longer periods add more "
                   f"background noise than predicted damage (see the end-year table)."},
        {"side": PAPER, "status": CAVEAT,
         "objection": "Linear scaling breaks down for shocks this large.",
         "answer": f"The 2024 shock ({_m(s24, 2)} °C) is {100 * (s24 / big['value'] - 1):.0f}% larger than the largest in "
                   f"the filter's {fy[0]}–{fy[1]} sample ({_m(big['value'], 2)} °C, {big['year']}). The paper finds no "
                   f"sign that larger shocks have smaller effects, and positive shocks have effects at least as large as "
                   f"negative ones (App. Fig. B.6). Linear scaling is therefore unlikely to overstate the paper's "
                   "predicted damage."},
        {"side": PAPER, "status": ADDRESSED,
         "objection": "El Niño warmth differs from the global temperature variation the paper studied.",
         "answer": f"The paper reports almost the same estimate after controlling for the same year's oceanic El Niño "
                   f"index (App. Fig. B.9) and says its results hold across sources of temperature variation. El "
                   f"Niño heat shows up first in the oceans, and the paper finds ocean temperature drives most of the "
                   f"effect (Fig. IX). The years after the El Niño are simulated with the cooling that usually follows "
                   f"a strong one. Measured with the paper's filter, they change the predicted gap by "
                   f"{_m(r['future_temperatures']['effect_on_M_mean'], 2)} points."},
        {"side": PAPER, "status": CAVEAT,
         "objection": "Adaptation since 2019 has weakened the effect.",
         "answer": "The paper reports no sign of adaptation (its estimates are stable across periods) and presents them as "
                   "the effect absent new adaptation. Curtin and Burgess (2026) dispute this with smaller Penn World "
                   "Table estimates in later rolling windows, and Kahn (2026) argues the effect fades as people adapt. "
                   "A Yes could mean the estimate is too high or that adaptation has improved, and the contract cannot "
                   "tell which."},
        {"side": PAPER, "status": CAVEAT,
         "objection": "If the IMF has become less optimistic, the strikes are too low.",
         "answer": "The no-effect expectation keeps the IMF's average past miss (decided 30 Oct 2026). "
                   + (f"If the IMF's forecasts are now unbiased, the central contract would resolve No only "
                      f"{_pc(miss_c['p_no_paper'])} of the time when the paper is right, instead of {_pc(cen_no)}."
                      if miss_c else "")},
        {"side": PAPER, "status": CHECKED,
         "objection": "One-step-ahead temperature shocks would change the answer.",
         "answer": f"The paper reports similar responses with one-step shocks (Fig. V, App. Fig. B.13). With one-step "
                   f"shocks and the matching response, the shocks' effect on {base}–{end} growth is "
                   f"{_m(abs(pts['one_step_paper_window']['shortfall_point']))} points, against "
                   f"{_m(abs(pts['two_step_paper_window']['shortfall_point']))} with the paper's two-step shocks (central "
                   f"temperatures, no post-2027 shocks, before the background netting)."},
        {"side": OTHER, "status": CAVEAT,
         "objection": "An unrelated recession would make the contract resolve No.",
         "answer": f"The paper's own main identification worry is a severe El Niño coinciding with an unrelated "
                   f"global recession. The spread of background growth includes recessions (the IMF's record covers 2009 "
                   f"and 2020), which is why the contract resolves No {_pc(c['false_positive'])} of the time even with no "
                   f"temperature effect. A recession clause is not possible, because under the paper temperature shocks "
                   f"themselves cut investment and productivity."},
        {"side": OTHER, "status": CAVEAT,
         "objection": "The no-effect baseline is a judgment call.",
         "answer": f"It is the largest one. A frozen 2000–2019 drift would put the cutoff at {frozen[1]:.2f}% a year "
                   f"instead of {cut:.2f}%. The IMF projection is external and frozen at October 2026, and its spread "
                   f"is the IMF's own forecast record."},
        {"side": OTHER, "status": CAVEAT,
         "objection": "Part of the 2023–24 warmth had unusual causes (cleaner shipping fuel, the Hunga Tonga eruption, the "
                      "solar maximum).",
         "answer": "The contract uses NOAA's measured temperature, whatever its cause, and the paper finds similar effects "
                   "across sources of temperature variation (App. Fig. B.9)."},
        {"side": OTHER, "status": CHECKED,
         "objection": "Applying the response to raw shocks, or to one-year warmth only, would give a different prediction.",
         "answer": f"The paper's regression controls for the two previous shocks, so its response applies to the part of "
                   f"each shock they do not predict. Raw shocks would double count and give a gap of {_m(abs(rawsh[0]))} "
                   f"points. Reading the response as one-year warmth only (App. Fig. B.5) gives {_m(abs(trans[0]))}."},
        {"side": BOTH, "status": CHECKED,
         "objection": "The paper's estimate is less precise than its bands suggest.",
         "answer": f"The paper-side spread comes from bootstrap draws of the paper's response. Rescaled to the paper's "
                   f"Newey–West standard errors, they give a cutoff of {nw[1]:.2f}% a year (J {nw[2]:.2f}). Widened by "
                   f"half, they give {wide[1]:.2f}% (J {wide[2]:.2f}), against {cut:.2f}% (J {J:.2f}). With the wider "
                   f"draws, the chance of a No if the paper is right falls from {_pc(sens)} to {_pc(sens_w)}."},
        {"side": BOTH, "status": CAVEAT,
         "objection": "One episode cannot confirm or refute the paper.",
         "answer": f"Agreed. Separation is moderate (J {J:.2f}), so a result adds to the weight of evidence and leaves "
                   f"the question open. Prices show how much credence participants give the paper."},
        {"side": BOTH, "status": CAVEAT,
         "objection": "The World Bank may rebase its price comparisons (PPPs) before resolution.",
         "answer": "Both years come from the same data release, so level revisions cancel. Country weights can still "
                   "shift growth slightly. The paper's results are similar across GDP sources."},
        {"side": BOTH, "status": CAVEAT,
         "objection": "The IMF's October 2026 projection may already include some El Niño effects.",
         "answer": "If so, the no-effect expectation is slightly too low, which tilts the contract toward Yes. IMF "
                   "projections rarely quantify global temperature effects, and this has not yet been checked against "
                   "the WEO text."},
    ]
    return out
