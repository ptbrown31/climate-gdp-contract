"""Write CONTRACT_TERMS.md and MEMO.md from outputs/ (indicative numbers as of the last run).

    python -I run_analysis.py      # outputs/
    python -I build_docs.py        # CONTRACT_TERMS.md, MEMO.md

The design text lives here; every number comes from outputs/results.json and its CSV twins,
so the documents can be regenerated when an input changes (for example a new NOAA value or IMF
vintage).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
sys.path.insert(0, str(ROOT))
from bk_elnino import objections as OB  # noqa: E402


def m(x: float, d: int = 1) -> str:
    """Fixed decimals with a typographic minus (no "−0.0")."""
    x = 0.0 if round(x, d) == 0 else x
    return f"{x:.{d}f}".replace("-", "−")


def sg(x: float, d: int = 2) -> str:
    if round(x, d) == 0:
        return f"{0:.{d}f}"
    return f"{x:+.{d}f}".replace("-", "−")


def op(x: float, d: int = 6) -> str:
    """Signed term inside a formula: '+ 0.36' / '− 0.38'."""
    return ("+ " if x >= 0 else "− ") + f"{abs(x):.{d}f}"


WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}


def pc(p: float) -> str:
    return f"{100 * p:.0f}%"


def table(header: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


class R:
    """Named access to the numbers both documents use."""

    def __init__(self):
        r = json.loads((OUT / "results.json").read_text())
        self.r = r
        d = r["design_primary"]
        self.base, self.end = d["base_year"], d["window"][1]
        self.span = self.end - self.base
        self.settle = self.end + 2
        self.c = r["contract_primary"]
        self.bins = r["conditional_contracts"]["bins"]
        self.ladder = pd.DataFrame(r["conditional_contracts"]["ladder"])
        self.scan = pd.DataFrame(r["end_year"]["scan"]).set_index("end_year")
        self.sel = self.scan.loc[self.end]
        self.ru = int(self.scan.youden_j.drop(self.end).idxmax())      # runner-up end year
        self.peak = int(self.scan.mean_shift.idxmin())                 # where the predicted gap is largest
        self.pck = r["paper_checks"]
        self.bl = r["baseline_primary"]
        self.err = self.bl["errors"]
        self.stand_in = self.err["source"].startswith("stand-in")
        self.miss_c = r.get("imf_miss_if_centred", {})
        self.ft = r["future_temperatures"]
        self.contrib = r["effect_contributions_to_M"]
        self.prov = r["provisional"]
        self.ham = r["hamilton_fit_primary"]
        self.innov = r["innovation_filter"]["PWT"]["coef"]
        self.theta = r["irf_primary"]["theta"]
        self.var = pd.DataFrame(r["contract_variants"]).set_index("variant")
        self.ev = {e["year"]: e for e in r["event_shocks"]}
        self.hind = r["hindcast_2023_2025"]
        self.frozen = r["frozen_drift_reference"]
        self.vint = r["vintages"]
        self.val = r["validation"]
        self.scope = self.c["p_no_at_primary_c_by_scope"]
        self.shocks = pd.read_csv(OUT / "shocks.csv").set_index("year")
        self.bands = pd.read_csv(OUT / "scenario_annual.csv").set_index("year")
        imf = json.loads((ROOT / "data/raw/imf/NGDP_RPCH.json").read_text())
        self.imf_g = {int(k): float(v) for k, v in imf["values"]["NGDP_RPCH"]["WEOWORLD"].items()}
        self.refreshed = r.get("refreshed_utc", "")[:10]

    def v(self, name: str) -> pd.Series:
        return self.var.loc[name]

    def bin(self, name: str) -> dict:
        return next(b for b in self.bins if b["bin"] == name)


def spread_text(x: R) -> str:
    """How the spread of background growth is built, including the IMF's average miss."""
    e = x.err
    if x.stand_in:
        return (f"**Placeholder in use:** until the IMF's historical forecast file is added, the spread uses the errors "
                f"of a 20-year trend forecast of WDI world GDP per capita (constant USD, {e['n_forecasts']} forecasts "
                f"made 1980–2013). Over {x.base + 1}–{x.end} these misses have sd {e['sum_over_statistic_sd']:.1f} "
                f"points and mean {sg(e['sum_over_statistic_mean'], 1)}.")
    return (f"The errors are those of the October World Economic Outlooks of {e['first_vintage']}–{e['last_vintage']} "
            f"({e['n_forecasts']} forecasts, IMF Historical WEO Forecasts Database), measured against the October 2026 "
            f"WEO's estimates of what happened. Years past the IMF's {WORDS.get(e['max_lead'], e['max_lead'])}-year "
            f"horizon are drawn independently from its {WORDS.get(e['max_lead'], e['max_lead'])}-year-ahead errors "
            "(misses in neighbouring years are close to uncorrelated). **The IMF's average miss is kept:** over "
            f"{WORDS.get(x.span, x.span)}-year windows like {x.base + 1}–{x.end}, world growth came in "
            f"{m(abs(e['sum_over_statistic_mean']))} points in total below the IMF's forecast on average (about "
            f"{m(abs(e['sum_over_statistic_mean']) / x.span)} a year; sd {e['sum_over_statistic_sd']:.1f}), and below "
            f"it in {e['n_below_forecast']} of {e['n_forecasts']} windows. "
            f"So with no temperature effect, growth is expected to average {x.c['h0_growth_mean_pp']:.2f}% a year, not "
            f"the IMF's {x.bl['window_mean_pp']:.2f}%. In the paper's world the background leaves out the part of "
            f"those misses that the paper's own estimates put down to temperature shocks "
            f"({m(abs(x.pck['imf_windows']['paper_part_mean']))} of the {m(abs(x.pck['imf_windows']['miss_mean']))} "
            "points on average), because its climate damage enters through the shocks since 2015 instead.")


def runner_up(x: R) -> str:
    j0, j1 = x.sel["youden_j"], x.scan.loc[x.ru, "youden_j"]
    if round(j0, 2) == round(j1, 2):
        return f"{x.ru} ties at two decimals (J {j1:.3f} against {j0:.3f}), and the rule takes the earlier year."
    return f"{x.ru} comes next (J {j1:.2f} against {j0:.2f})."


def objection_lines(x: R) -> list[str]:
    return [f"- **{o['objection']}** *({o['side']}; {o['status']})* {o['answer']}" for o in OB.build(x.r)]


def cond_label(b: dict) -> str:
    return f"{b['bin'].capitalize()}: {b['condition'].replace(' C', ' °C')}"


def question(x: R, strike: float) -> str:
    return (f"Will world real GDP per person grow by more than **{strike:.1f}%** a year, on average, "
            f"from {x.base} to {x.end}?")


def scan_table(x: R, years=None) -> str:
    years = years or [y for y in x.scan.index if y <= 2035]
    rows = [[f"**{y}**" if y == x.end else y, f"{x.scan.loc[y, 'youden_j']:.2f}", m(x.scan.loc[y, "mean_shift"]),
             f"{x.scan.loc[y, 'sd_h0']:.1f}", f"{x.scan.loc[y, 'growth_bar']:.2f}"] for y in years]
    return table(["End year", "J", "Paper's predicted shortfall (points)", "Spread of background growth (sd, points)",
                  "Cutoff (%/yr)"], rows)


def bins_table(x: R) -> str:
    rows = []
    for b in x.bins:
        rows.append([cond_label(b), pc(b["prob_now"]), m(b["mean_shift"]), f"{b['growth_bar']:.2f}",
                     f"**{b['strike']:.1f}**", pc(b["p_yes_no_effect_at_strike"]), pc(b["p_yes_paper_at_strike"]),
                     f"{b['youden_j']:.2f}"])
    c = x.c
    rows.append(["No condition (all 2027 outcomes)", "100%", m(c["shortfall_mean"]),
                 f"{c['threshold_growth_equivalent_pp']:.2f}", "–", pc(c["p_yes_no_effect"]), pc(c["p_yes_paper"]),
                 f"{c['youden_j']:.2f}"])
    return table(["Condition (NOAA 2027)", "Chance today", f"Predicted shortfall {x.base}–{x.end} (points)",
                  "Cutoff (%/yr)", "Strike", "P(Yes) if no effect", "P(Yes) if paper right", "J"], rows)


def ladder_table(x: R) -> str:
    L = x.ladder
    strikes = sorted(L.strike_pct_yr.unique())
    rows = []
    heads = {b["bin"]: b["strike"] for b in x.bins}
    for s in strikes:
        row = [f"{s:.1f}%"]
        for name in ("cool", "central", "warm"):
            q = L[(L.condition == name) & (L.strike_pct_yr.round(2) == round(s, 2))].iloc[0]
            mark = "**" if abs(heads[name] - s) < 1e-9 else ""
            row.append(f"{mark}{pc(q.p_yes_no_effect)} / {pc(q.p_yes_paper)}{mark}")
        rows.append(row)
    return table(["Strike", "Cool: P(Yes) no effect / paper", "Central", "Warm"], rows)


def contrib_rows(x: R) -> list[list]:
    labs = [("2015-2022", "2015–2022"), ("2023-2025", "2023–2025"), ("2026-2027", "2026–2027 (El Niño)"),
            ("2028+ (simulated)", f"2028–{x.end} (simulated, cooler years after the El Niño)")]
    rows = [[lab, sg(x.contrib[k], 1)] for k, lab in labs]
    rows.append(["**Total**", f"**{sg(x.contrib['total'], 1)}**"])
    return rows


# ---------------------------------------------------------------------------------------------- terms

def terms(x: R) -> str:
    c, b0, b1, b2 = x.c, x.bin("cool"), x.bin("central"), x.bin("warm")
    t24 = float(x.shocks.loc[2024, "noaa_T"])
    offset = x.prov.get("gistemp_minus_noaa_2016_2025", 0.007)
    imf_years = [y for y in range(x.base + 1, 2032) if y in x.imf_g]
    stand = " " + spread_text(x)
    q_h0 = (x.sel["growth_h0_q10"], x.sel["growth_h0_q90"])
    raw = x.v("composition: raw shocks (handoff formula)")
    lines = [
        "# Draft contract specification (for comment): world GDP per capita after the 2023–27 global temperature shocks",
        "",
        f"*Status, {x.refreshed}: **draft for comment.** Redesigned on 30 Oct 2026; see \"What changed on 30 Oct 2026\" at the end.*",
        "",
        "- Three **conditional contracts**, one for each range of NOAA's 2027 global temperature, are proposed to list "
        f"right after NOAA publishes its **2026 annual value (expected mid-January 2027)**.",
        "- When NOAA publishes its **2027** annual value (expected mid-January 2028), positions in the contract whose "
        "condition was met convert to an unconditional contract at the same cost basis. Positions in the other two are "
        "refunded at cost; fees are not refunded. This follows ForecastEx's conditional contracts.",
        "- Every number below is **indicative** and refreshes monthly until the terms freeze at the refresh that follows "
        "NOAA's 2026 annual value.",
    ]
    if x.stand_in:
        lines.append("- **Placeholder in use:** the spread of background growth is a labelled stand-in until the IMF's "
                     "historical forecast file is added (term 6).")
    lines += [
        "",
        "## The contracts",
        "",
        table(["Condition: NOAA's 2027 global temperature", "Chance today", "Question",
               "P(Yes) if temperature shocks have no effect", "P(Yes) if the paper is right"],
              [[cond_label(b), pc(b["prob_now"]), question(x, b["strike"]), pc(b["p_yes_no_effect_at_strike"]),
                pc(b["p_yes_paper_at_strike"])] for b in x.bins]),
        "",
        "- **Yes:** growth beats the strike, so the temperature shocks had no large effect.",
        "- **No:** growth at or below the strike, as Bilal and Känzig (QJE 2026) predict.",
        "- A Yes contract pays $1 if the question resolves Yes; a No contract pays $1 if it resolves No. Participants "
        "take a financial position on either side, rewarded only for accuracy.",
        "- Each condition also lists a ladder of strikes (term 9). The probabilities are for the headline strike, "
        "from 50,000 simulated worlds of each kind (term 8).",
        "",
        "## Timeline",
        "",
        table(["When", "What happens"], [
            ["Now to mid-Jan 2027", "Proposal circulates for comment. Indicative numbers refresh monthly, after NOAA's "
                                    "monthly release."],
            ["~Mid-Jan 2027", "NOAA publishes its 2026 annual value. Final refresh: the end year, conditions, strikes, "
                              "IMF vintage and code are frozen and archived."],
            ["Right after", "**Conditional contracts list.**"],
            ["~Mar 2027", "NOAA publishes the winter (DJF) El Niño strength. Prices move; terms do not."],
            ["~Mid-Jan 2028", "NOAA publishes its 2027 annual value. **The matching condition converts; the other two "
                              "are refunded at cost.**"],
            [f"Mid-{x.end + 1}", f"World Bank publishes the first {x.end} figure."],
            [f"**1 Oct {x.settle}**", "**Resolve and settle** on the WDI vintage of that date, one revision cycle after "
                                      "the first release."],
        ]),
        "",
        "## Proposed terms (each open for comment until the freeze)",
        "",
        "### 1. Conditioning event: NOAA's 2027 global temperature",
        "- NOAA NCEI Climate at a Glance, global land and ocean surface temperature (NOAAGlobalTemp), January–December "
        "mean, °C vs the 1901–2000 average, as published (two decimals): "
        "`https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/globe/land_ocean/12/12/1850-2027/data.csv`.",
        "- Read once on 31 January 2028 and archived.",
        f"- **Conditions:** cool, {b0['condition'].replace(' C', ' °C')}; central, "
        f"{b1['condition'].replace(' C', ' °C')}; warm, {b2['condition'].replace(' C', ' °C')}. "
        f"For scale, the 2024 record is {t24:.2f} °C.",
        f"- How the ranges were set: the 20th, 50th and 80th percentiles of the current 2027 forecast "
        f"({b0['level']:.2f}, {b1['level']:.2f} and {b2['level']:.2f} °C), split halfway between neighbours, so each "
        f"range is about one-third likely today. The forecast is the filter's expectation for 2027 "
        f"({x.ev[2027]['filter_expectation']:.2f} °C) plus an ENSO-regression forecast of the 2027 shock "
        f"({sg(x.prov['s2027_regression_forecast'][0])} ± {x.prov['s2027_regression_forecast'][1]:.2f} °C), with winter "
        f"(DJF) RONI assumed ~N({x.prov['roni_djf_2027_assumption'][0]}, {x.prov['roni_djf_2027_assumption'][1]}). "
        "The ranges freeze with the other terms.",
        f"- **Fallback:** if NOAA has published no 2027 annual value by 31 March 2028, use NASA GISTEMP v4 "
        f"(`GLB.Ts+dSST.csv`, column `J-D`) minus the fixed GISTEMP − NOAA offset (2016–2025 mean, {sg(offset, 3)} °C).",
        "",
        f"### 2. Settlement event: world GDP per capita growth, {x.base} to {x.end}",
        "- World Bank WDI `NY.GDP.PCAP.PP.KD` (GDP per capita, PPP, constant 2021 international $), country `WLD`.",
        f"- **Growth = 100 × ln(y{x.end} / y{x.base}) / {x.span}**, both levels from the single resolution-date vintage, "
        "so PPP rebasings and level revisions cancel. Computed to two decimals; **Yes if strictly greater than the "
        "strike.**",
        f"- This is average log growth. At these rates it is within 0.03 points of the compound annual rate.",
        f"- {x.base} is the last full year before listing, so none of the growth being measured ({x.base + 1}–{x.end}) "
        "is known when the contracts list.",
        "",
        f"### 3. End year: {x.end}, chosen by a fixed rule",
        "- **Rule:** among end years 2028–2037, the one with the highest Youden J between simulated \"no effect\" and "
        "\"paper right\" outcomes, to two decimals; a tie goes to the earlier year.",
        "  - J = P(resolves No | paper right) + P(resolves Yes | no effect) − 1. It rewards a contract that resolves in "
        "line with whichever view is true, and favours neither side.",
        "  - It uses only information available before listing: the paper's published response, the IMF projection and "
        "its error record, and temperature forecasts. It uses no GDP data after 2025.",
        "",
        scan_table(x),
        "",
        f"- **Why separation peaks at {x.end}:**",
        f"  - The paper's response deepens for six years after a shock, so the predicted gap grows through {x.peak}.",
        "  - Uncertainty about background growth grows with every added year.",
        f"  - After {x.peak} the 2023–24 shocks start to recover in the paper's response.",
        f"- {runner_up(x)} The end year freezes with the other terms.",
        "",
        "### 4. Shock definition (frozen coefficients)",
        f"- `s_t = T_t − ({x.ham['coef'][0]:.6f} + {x.ham['coef'][1]:.6f}·T_(t−2) + {x.ham['coef'][2]:.6f}·T_(t−3))`.",
        f"  - These are the Hamilton h=2, p=2 coefficients fitted on NOAA over the paper's own window (dependent years "
        f"{x.ham['fit_years'][0]}–{x.ham['fit_years'][1]}, data from 1950; paper footnote 2), on the archived 17 Oct "
        "2026 annual vintage. They are not re-estimated, so the 2023–27 warmth is measured out of sample instead of "
        "helping to fit the trend it is measured against.",
        f"  - Refitting through 2025 would shrink each 2023–27 shock by about 0.04–0.05 °C (gap "
        f"{m(abs(x.v('filter: refit through 2025 (until 30 Oct 2026)').mean_shift))} points, J "
        f"{x.v('filter: refit through 2025 (until 30 Oct 2026)').youden_j:.2f}).",
        f"- **Innovations** `u_t = s_t − ({x.innov[0]:.6f} {op(x.innov[1])}·s_(t−1) {op(x.innov[2])}·s_(t−2))`.",
        "  - This matches how the paper's regression defines its response and avoids double counting back-to-back warm "
        "years.",
        f"  - The alternative, raw shocks, gives a predicted shortfall of {m(raw.mean_shift)} points (J {raw.youden_j:.2f}).",
        "",
        "### 5. The paper's prediction (frozen)",
        "- Bilal–Känzig time-series local projection of log world real GDP per capita, PWT sample 1960–2019 (paper "
        "Fig. III), in 100×log points per 1 °C shock:",
        "  - `" + ", ".join(m(t, 4) for t in x.theta) + "` (h = 0…10).",
        "- Held at its h=10 value beyond h=10. Uncertainty from the archived 4,000 wild-bootstrap draws (seed 123).",
        f"- **Shocks that count:** all shocks since 2015 whose effects change after {x.base}, plus simulated shocks for "
        f"2028–{x.end} (term 7). Contribution to the predicted {x.base}–{x.end} shortfall (point estimate, central "
        "temperatures):",
        "",
        table(["Shocks", "Points"], contrib_rows(x)),
        "",
        f"- These shocks lower {x.base}–{x.end} growth by {m(abs(c['h1_effect_mean']))} points (90% range "
        f"{m(c['h1_effect_q05'])} to {m(c['h1_effect_q95'])}; response and temperature uncertainty). In the paper's "
        f"world the background is also {m(c['background_netting_pts'])} points better than the IMF's raw record "
        f"(term 6), so the two worlds differ by **{m(abs(c['shortfall_mean']))} points** on average.",
        "",
        "### 6. No-effect baseline: the IMF projection",
        "- IMF World Economic Outlook, October 2026 (DataMapper, retrieved 17 Oct 2026): world real GDP growth "
        + ", ".join(f"{y} {x.imf_g[y]:.1f}%" for y in imf_years) + "; world population from the same release.",
        f"- Per-capita growth = 100·ln(1 + g/100) − 100·Δln(population), plus the {x.bl['gap_years'][0]}–"
        f"{x.bl['gap_years'][1]} mean gap between WDI and IMF-implied per-capita growth ({sg(x.bl['wdi_gap_pp'])} points; "
        f"correlation {x.bl['gap_corr']:.2f}).",
        "- Baseline per-capita growth: " + ", ".join(f"{y} {x.bl['growth_pp'][str(y)]:.2f}%"
                                                     for y in range(x.base + 1, x.end + 1))
        + f"; **mean {x.bl['window_mean_pp']:.2f}% a year** (the 2000–2019 average was {x.frozen['mu_pp']:.2f}%). "
        "Beyond 2031 the 2031 rate is held.",
        "- Frozen at the October 2026 vintage: the January 2027 WEO Update usually appears after mid-January and "
        "projects only two years.",
        "- **Spread:** the IMF's own historical forecast errors for world real GDP growth, by years ahead, resampled as "
        "whole forecast paths so that multi-year misses (recessions, slowdowns) keep their persistence, then smoothed so "
        f"the distribution is continuous.{stand}",
        f"- With no temperature effect, average growth {x.base}–{x.end} has a 10–90% range of {q_h0[0]:.1f}% to "
        f"{q_h0[1]:.1f}% a year. This spread, not the temperature record, is the largest uncertainty in the contract.",
        "",
        "### 7. Temperatures after 2027 (simulated, part of the paper's prediction)",
        "- Strong El Niños are usually followed by cooler years. After a strong El Niño winter (RONI ≥ 1.5, true in "
        "virtually every simulated 2027), each simulated path replays the winters that followed one of the seven strong "
        "El Niños since 1950 (1958, 1966, 1973, 1983, 1992, 1998, 2016). Otherwise winter RONI follows an AR(2).",
        "- Each year's shock is the ENSO regression's prediction plus a resampled residual; volcanic years stay in the "
        "residual pool.",
        "- Mean simulated shocks: " + ", ".join(f"{y} {sg(float(v))} °C" for y, v in
                                               list(x.ft["shock_mean_by_year"].items())[:3]) + ".",
        "- They are measured with the same frozen filter (term 4). The cooling that usually follows a strong El Niño "
        "is then partly or fully offset, because the paper's filter, fitted before the 2023–24 jump, still counts a "
        "lasting warmer level as positive shocks, as the paper's method would.",
        f"- Under the paper's estimate, the simulated years change {x.base}–{x.end} growth by "
        f"{sg(x.ft['effect_on_M_mean'], 2)} points (90% range {sg(x.ft['effect_on_M_q05'], 1)} to "
        f"{sg(x.ft['effect_on_M_q95'], 1)}). Without them the cutoff would be {x.ft['cutoff_without_pp']:.2f}% a year "
        f"and J {x.ft['youden_j_without']:.2f}.",
        f"- The strikes are fixed in advance: actual 2028–{x.end} temperatures do not change them.",
        "",
        "### 8. Strikes: the cutoff within each condition",
        "- For each condition: 50,000 simulated worlds with no temperature effect and 50,000 with the paper's effect "
        "(common random numbers, seed 20261017), with NOAA's 2027 value drawn from the forecast within the condition's "
        "range.",
        "- The cutoff is the growth rate that maximises J (tolerance 0.0025); the **headline strike** is the cutoff "
        "rounded to 0.1 point.",
        "",
        bins_table(x),
        "",
        "- A warmer 2027 means a bigger predicted shortfall, so the warm condition has the lowest cutoff and the most "
        "power." + (f" After rounding, the central and warm conditions share the {b2['strike']:.1f}% strike."
                    if b1["strike"] == b2["strike"] else ""),
        "",
        "### 9. Strike ladder",
        f"- Each condition lists strikes from {x.ladder.strike_pct_yr.min():.1f}% to {x.ladder.strike_pct_yr.max():.1f}% "
        "a year, 0.2 points apart around the central strike, plus every headline strike (in bold). "
        "Each cell gives P(Yes) if temperature shocks have no effect / if the paper is right. With no effect, "
        "2027's temperature does not matter, so the first number is the same in every column.",
        "",
        ladder_table(x),
        "",
        "### 10. Conversion and refunds",
        "- When NOAA publishes its 2027 annual value, positions in the contracts whose condition was met convert to the "
        "unconditional contract with the same question and strike, at the same cost basis.",
        "- Positions in the other conditions' contracts are refunded at cost; fees are not refunded.",
        "- More strikes may be listed after conversion. The cutoff for the realised 2026 and 2027 values comes from "
        "`python -I run_analysis.py --lock <T2026> <T2027>` on the archived data (`outputs/threshold_grid.csv` shows "
        "how it moves).",
        "",
        "### 11. Resolution and settlement",
        f"- **1 Oct {x.settle}.** Retrieve the WDI series once, archive the response and its `lastupdated` field, and "
        "compute growth with the archived code.",
        f"- If {x.base} or {x.end} is missing from that vintage, use the latest vintage that has both. If none exists by "
        f"1 Oct {x.settle + 1}, the contracts are void.",
        "- If the indicator is discontinued, use its official successor (world GDP per capita, PPP, constant prices). "
        "Otherwise void.",
        "",
        "### 12. Acknowledged limits",
        f"- One outcome cannot confirm or refute the paper. A global recession year can move "
        f"{WORDS.get(x.span, x.span)}-year growth by "
        "several points; 2020 alone was −3.9%.",
        f"- Under the paper's estimate, GDP per capita still grows (about {c['h1_growth_mean_pp']:.1f}% a year, against "
        f"{c['h0_growth_mean_pp']:.1f}% with no effect). The test is the shortfall against the baseline.",
        f"- The 2024 shock ({sg(x.ev[2024]['shock'])} °C with NOAA) already exceeds the largest in the filter's "
        f"sample ({sg(x.pck['largest_in_sample_shock']['value'])} °C, {x.pck['largest_in_sample_shock']['year']}), so "
        "the test relies on the paper's linear scaling.",
        "- It tests the paper's response to the whole 2023–27 warm sequence, not the El Niño alone. If only the 2026–27 "
        f"shocks mattered, the unconditional contract would resolve No only "
        f"{pc(x.scope['scope: 2026-27 El Nino only'])} of the time.",
        "- The response was estimated with Berkeley Earth shocks and is applied to NOAA shocks; the two track each other "
        f"closely (corr {x.val['noaa_p2_vs_authors_pwt_shock']['corr']:.3f}, 1960–2019).",
    ]
    if x.stand_in:
        lines.append("- The spread of background growth is a stand-in until the IMF's historical forecast file is added.")
    lines += [
        "",
        "### 13. Objections we expect",
        "Who would raise each, the answer, and whether the design addresses it or it stays a caveat:",
        "",
        *objection_lines(x),
        "",
        "### Open questions for comment",
        f"- A low-power clause or no-decision zone for the cool condition (J {b0['youden_j']:.2f})?",
        "- Should an unconditional contract also list from the start, alongside the three conditional ones?",
        "",
        "## What changed on 30 Oct 2026",
        "- Three conditional contracts on NOAA's 2027 value replace a single contract whose cutoff was to be computed "
        "from the final 2027 value on 1 March 2028.",
        f"- Growth is measured from 2026 (was 2027): the contracts list right after NOAA's 2026 value, before any 2027 "
        f"growth is known. J {x.c['youden_j']:.2f}, against "
        f"{x.v('statistic: growth 2027-' + str(x.end) + ' (draft until 30 Oct 2026)').youden_j:.2f} from 2027.",
        f"- The end year ({x.end}) is chosen by a fixed rule, explained in term 3.",
        f"- The no-effect baseline is the IMF projection. The previous frozen 2000–2019 drift "
        f"({x.frozen['mu_pp']:.2f}%/yr) is kept as a sensitivity (J "
        f"{x.v('baseline: frozen 2000-2019 drift (until 30 Oct 2026)').youden_j:.2f}).",
        f"- Simulated temperatures after 2027 enter the paper's prediction; they change the gap by "
        f"{sg(x.ft['effect_on_M_mean'], 2)} points (J {x.ft['youden_j_without']:.2f} without them).",
        *([f"- The spread of background growth comes from the IMF's own forecast record (October WEOs "
           f"{x.err['first_vintage']}–{x.err['last_vintage']}), replacing a stand-in, and keeps the IMF's average "
           "miss, so the no-effect expectation is below the IMF's projection."] if not x.stand_in else []),
        f"- After checking the design against the paper and its online appendix: the temperature-shock filter is fitted "
        f"on the paper's own window (data 1950–2022) and frozen, so the 2023–27 warmth is measured out of sample; in the "
        f"paper's world the background leaves out the part of the IMF's past misses that the paper puts down to "
        f"temperature shocks ({m(abs(x.pck['imf_windows']['paper_part_mean']))} points); and simulated post-2027 "
        "temperatures are measured with the same filter. See term 13 for the objections these answer.",
        f"- With these changes the end-year rule picks {x.end} (J {x.c['youden_j']:.2f}); {runner_up(x)} The strikes "
        f"are {b0['strike']:.1f} / {b1['strike']:.1f} / {b2['strike']:.1f}% (cool / central / warm); they were 2.0 / "
        "1.9 / 1.8% for growth to 2030 before the IMF record was added.",
        "- The question asks whether growth will be **more than** the strike: Yes means no large effect, No is the "
        "outcome the paper predicts.",
        "",
        "## What changed on 31 Oct 2026",
        f"- Term 13 now cites the paper's own GDP-weighted panel (App. Fig. B.10, "
        f"{m(x.pck['theta6']['PWT_panel_gdpw'])}% at year 6) and checks the paper-side spread with wider draws (cutoff "
        f"{x.v('IRF: draws widened by half').threshold_growth_pp:.2f}% a year, J "
        f"{x.v('IRF: draws widened by half').youden_j:.2f}). The contracts and strikes are unchanged.",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------- memo

VARIANT_LABELS = [
    ("primary", "**Proposed (conditional design, growth {base}→{end})**"),
    ("scope: 2023-27 spikes only", "2023–27 spikes only"),
    ("scope: 2026-27 El Nino only", "2026–27 El Niño only"),
    ("composition: raw shocks (handoff formula)", "Raw-shock composition (handoff formula)"),
    ("2026-27 only + raw shocks (handoff literal)", "2026–27 only + raw shocks (handoff, literally)"),
    ("IRF: BU time series (NOAA p=6 shocks)", "BU time-series IRF"),
    ("IRF: PWT panel (paper's 14%)", "PWT panel IRF (paper's 14%)"),
    ("IRF: PWT panel, GDP-weighted (paper App. Fig. B.10)", "PWT panel IRF, GDP-weighted (paper App. Fig. B.10)"),
    ("IRF: BU panel (paper's 18%)", "BU panel IRF (paper's 18%)"),
    ("IRF: Newey-West-scaled draws", "IRF draws rescaled to Newey–West s.e."),
    ("IRF: draws widened by half", "IRF draws widened by half"),
    ("IRF: transitory warmth only (Sims)", "Transitory warmth only (Sims)"),
    ("IRF beyond h=10: truncate to 0", "θ truncated to 0 after h=10"),
    ("filter: p+1 lags (paper eq. 1 literal)", "Filter: p+1 lags (paper eq. 1 literal)"),
    ("post-2027 temperatures: none (until 30 Oct 2026)", "No simulated post-2027 temperatures (until 30 Oct)"),
    ("baseline: frozen 2000-2019 drift (until 30 Oct 2026)", "Baseline: frozen 2000–2019 drift (until 30 Oct)"),
    ("frozen baseline: 1991-2019 drift (handoff)", "Baseline: frozen 1991–2019 drift (handoff)"),
    ("frozen baseline: + structural drift sd 0.5pp", "Frozen 2000–19 drift + 0.5 pp drift uncertainty"),
    ("statistic: growth 2027-{end} (draft until 30 Oct 2026)", "Growth 2027→{end} (draft until 30 Oct)"),
    ("statistic: mean level 2029-33 vs 2025 (earlier)", "Mean level 2029–33 vs 2025 (earlier draft)"),
    ("statistic: mean level 2031-35 vs 2025 (handoff)", "Mean level 2031–35 vs 2025 (handoff)"),
]


def memo(x: R) -> str:
    c, ev = x.c, x.ev
    b0, b1, b2 = x.bin("cool"), x.bin("central"), x.bin("warm")
    var_rows = []
    for key, lab in VARIANT_LABELS:
        key = key.format(end=x.end)
        if key not in x.var.index:
            continue
        v = x.var.loc[key]
        var_rows.append([lab.format(base=x.base, end=x.end), m(v.mean_shift), f"{v.threshold_growth_pp:.2f}",
                         f"{v.youden_j:.2f}"])
    h0_lv, h1_lv = x.bands.loc[x.end, "H0_level_q50"], x.bands.loc[x.end, "H1_level_q50"]
    y25 = x.frozen["anchor_level"]
    gp = x.frozen["growth_by_period"]
    hind = x.hind
    stand_note = spread_text(x)
    t26, t27 = x.prov["T2026"], x.prov["T2027"]
    lines = [
        "# Bilal–Känzig × the 2026–27 El Niño: a prospective test and forecast-contract design",
        "",
        "**Prepared:** 17 October 2026 · **Revised:** 23 October 2026 (NOAA temperature record), **30 October 2026** "
        "(conditional contracts, growth from 2026, an end-year rule, the IMF baseline with its own forecast record, "
        "simulated post-2027 temperatures, the paper's own filter window) and 31 October 2026 (the paper's GDP-weighted "
        "panel and two checks of the paper-side spread, as sensitivities) · "
        "**Status:** draft for comment, refreshed monthly · **Listing:** right after NOAA's 2026 annual value (mid-Jan "
        "2027) · **Code:** `bk_elnino/` + `run_analysis.py` · **Outputs:** `outputs/`",
        "",
        "Everything below was produced by `python -I run_analysis.py` and written by `build_docs.py`. Every number has a "
        "CSV twin in `outputs/` and a design label in `outputs/results.json`.",
        "",
        "- **Nothing is locked yet.** The terms freeze at the refresh that follows NOAA's 2026 annual value, and the "
        "conditional contracts list right after.",
        f"- **2026 and 2027 temperatures are placeholders** (2026: {t26['mean']:.3f} ± {t26['sd']:.3f} °C; 2027: "
        f"{t27['mean']:.3f} ± {t27['sd']:.3f} °C). Each monthly refresh replaces them with whatever NOAA has published.",
    ]
    if x.stand_in:
        lines.append("- **The spread of background growth is a labelled stand-in** until the IMF's historical forecast "
                     "file is added (section 7).")
    lines += [
        "",
        "---",
        "",
        "## Bottom line",
        "",
        "1. **The handoff's shock formula was wrong in a way that matters.** The authors' shock series is exactly "
        "`T_t − (a + b₂T_{t−2} + b₃T_{t−3})`: two lagged regressors for h=2, p=2, with zero weight on `T_{t−4}`. The "
        "paper's Eq. (1) is typeset with p+1 lags, but the data the IRF was estimated on uses p.",
        "2. **The headline −14% / −18% numbers are panel estimates (paper Fig. IV), not the world-GDP time series.** The "
        "world real GDP per capita IRF (Fig. III), which fits a world-GDP contract, peaks at **−12.1% at h=6 (PWT)** per "
        "1 °C shock. The Python local projections reproduce the authors' Stata estimates to ~1e-7.",
        f"3. **The record shock already happened in 2024:** {sg(ev[2024]['shock'])} °C with NOAA, the largest since at "
        f"least 1953. 2023 gave {sg(ev[2023]['shock'])} °C. The 2027 placeholder implies a shock of "
        f"{sg(ev[2027]['shock'])} ± {ev[2027]['shock_sd']:.2f} °C.",
        f"4. **What the paper predicts.** Its published PWT response implies that world per-capita growth from {x.base} "
        f"to {x.end} falls **{m(abs(c['shortfall_mean']))} points** short of the no-effect path (90% range "
        f"{m(c['shortfall_q05'])} to {m(c['shortfall_q95'])}), net of the part of the IMF's past misses the paper "
        f"itself puts down to temperature. That is about {c['h1_growth_mean_pp']:.1f}% a year "
        f"instead of {c['h0_growth_mean_pp']:.1f}%. The 2023–25 and 2026–27 shocks contribute "
        + (f"{sg(x.contrib['2023-2025'], 1)} points each"
           if sg(x.contrib['2023-2025'], 1) == sg(x.contrib['2026-2027'], 1) else
           f"{sg(x.contrib['2023-2025'], 1)} and {sg(x.contrib['2026-2027'], 1)} points")
        + f"; the simulated years after 2027 change it by {sg(x.contrib['2028+ (simulated)'], 2)}.",
        "5. **The proposal is three conditional contracts** on NOAA's 2027 temperature, listed right after NOAA's 2026 "
        f"value. Each asks whether world GDP per person will grow by more than a strike, on average, from {x.base} to "
        f"{x.end}:",
        f"   - cool 2027 ({b0['condition'].replace(' C', ' °C')}): {b0['strike']:.1f}%/yr, J {b0['youden_j']:.2f};",
        f"   - central ({b1['condition'].replace(' C', ' °C')}): {b1['strike']:.1f}%/yr, J {b1['youden_j']:.2f};",
        f"   - warm ({b2['condition'].replace(' C', ' °C')}): {b2['strike']:.1f}%/yr, J {b2['youden_j']:.2f}.",
        "   - The matching contract converts to an unconditional one when NOAA publishes 2027; the others are refunded.",
        f"6. **Moderate, not decisive, power.** Unconditionally the cutoff is {c['threshold_growth_equivalent_pp']:.2f}% a "
        f"year. The contract resolves No (the paper's outcome) {pc(c['sensitivity'])} of the time if the paper is right, "
        f"and Yes {pc(c['p_yes_no_effect'])} of the time if temperature shocks have no effect (J {c['youden_j']:.2f}, "
        f"AUC {c['auc']:.2f}). A Yes contract would be worth about ${c['p_yes_paper']:.2f} if the paper is right and "
        f"${c['p_yes_no_effect']:.2f} if not, so its price maps onto the credence participants give the paper.",
        f"7. **The end year, {x.end}, is chosen by a rule:** the highest separation (J) among 2028–2037, using no GDP "
        f"data after 2025. Separation rises while the paper's response deepens and falls as background-growth "
        f"uncertainty accumulates and the earlier shocks recover; {runner_up(x)}",
        f"8. **Background growth is the biggest uncertainty.** The IMF projection puts per-capita growth at "
        f"{x.bl['window_mean_pp']:.2f}% a year over {x.base + 1}–{x.end}"
        + (". The spread is a stand-in until the IMF's own forecast-error record is added." if x.stand_in else
           f", but its forecasts at these horizons have run high: since {x.err['first_vintage']}, growth came in "
           f"{m(abs(x.err['sum_over_statistic_mean']))} points below them over {WORDS.get(x.span, x.span)}-year windows, "
           f"on average, and below them in {x.err['n_below_forecast']} of {x.err['n_forecasts']} windows. Keeping "
           f"that miss, the no-effect expectation is {c['h0_growth_mean_pp']:.2f}% a year.")
        + f" Over {WORDS.get(x.span, x.span)} years, background growth has an sd of {x.sel['sd_h0']:.1f} points, "
        f"against the paper's predicted shortfall of {m(abs(c['shortfall_mean']))}.",
        f"9. **Growth is measured from 2026**, the last full year before listing, so none of the measured growth is "
        f"known at listing. Starting at 2027, as in the drafts until 30 Oct, gives J "
        f"{x.v('statistic: growth 2027-' + str(x.end) + ' (draft until 30 Oct 2026)').youden_j:.2f}.",
        "10. **The temperature record matters.** Under the 23 Oct design, NASA GISTEMP (the proposal until 22 Oct) "
        "gave a 4.5-point prediction against NOAA's 3.6. NOAA was chosen because the paper uses it and reports that its "
        "Berkeley Earth measure tracks NOAA almost perfectly.",
        "",
        "---",
        "",
        "## 1. Corrections to the handoff",
        "",
        table(["#", "Handoff said", "Evidence", "What the code does"], [
            [1, "Regress `T_t` on `T_{t−2}, T_{t−3}, T_{t−4}` for h=2, p=2",
             "Exact regression of the authors' `gtmp_bkly_aw_dtfe2` on `[1, T_t, T_{t−2}, T_{t−3}, T_{t−4}]` returns "
             "weights `[−0.0387, 1, −0.5196, −0.4608, 0.0000]` with zero residual. The p+1-lag version correlates only "
             "0.91 with the authors' series. Curtin and Burgess (2026, App. H) independently rebuild the shocks with the "
             "same two lags.",
             "`hamilton.lag_set(h, p)` = lags h…h+p−1 (`bk_data`). The literal Eq. (1) reading is kept as `paper_eq1` "
             "for sensitivity."],
            [2, "Published IRF peaks at −14% (h=6, PWT) and −18% (h=5, BU)",
             "Those are the country-panel averages (paper Fig. IV). The world-GDP time-series IRF (Fig. III) is −12.1% "
             "(h=6) and −16.8% (h=6).", "Primary = time-series PWT IRF. Panel IRFs are labelled sensitivities."],
            [3, "Provisional 2023/2024 shocks of +0.174 / +0.269", "Not reproducible from either convention.",
             f"NOAA h=2, p=2: **{sg(ev[2023]['shock'], 3)} / {sg(ev[2024]['shock'], 3)}**."],
            [4, "Apply `θ_h` to raw shocks: Σ θ_{t−τ} s_τ",
             "The authors' LP controls for s_{t−1}, s_{t−2}, so θ_h is the response to the part of s_t not predicted by "
             "the two prior shocks, including the predictable follow-on shocks. Applying θ to raw consecutive shocks "
             "double counts.",
             "Primary applies θ to innovations, estimated on the LP's own sample. The raw formula is a labelled variant."],
            [5, "Primary test on the incremental 2026–27 component",
             "The realised outcome will contain the effects of the 2023–25 shocks too (under the paper). A prediction "
             "that omits them is mis-specified for the statistic that will be resolved.",
             "The paper's side = all shocks with effects in the measured years, plus simulated post-2027 shocks."],
            [6, "Null drift from 1991–2019",
             f"1991–2000 per-capita PPP growth averaged {gp['1991-2000']:.2f}%/yr (post-Soviet collapse); 2001–10 "
             f"{gp['2001-2010']:.2f}; 2011–19 {gp['2011-2019']:.2f}; 2022–25 {gp['2022-2025']:.2f}.",
             "Since 30 Oct the no-effect path follows the IMF projection. Frozen 2000–2019 and 1991–2019 drifts are "
             "sensitivities."],
        ]),
        "",
        "## 2. Data (vintages in `outputs/results.json → vintages`)",
        "",
        table(["Series", "Source", "Use"], [
            ["Global mean temperature (contract record)", "NOAA NCEI Climate at a Glance (NOAAGlobalTemp), global land and "
             "ocean, °C vs 1901–2000, annual and monthly", "Shocks, placeholders, the conditioning event"],
            ["Comparison and fallback", "NASA GISTEMP v4 `GLB.Ts+dSST.csv`, J–D", "Fallback for the conditioning event"],
            ["Validation temperature", "Berkeley Earth Land+Ocean summary (ends 2024)", "Reproduces the authors' shocks"],
            ["ENSO", "CPC ONI and RONI", "2027 forecast; post-2027 simulation"],
            ["Outcome", "World Bank WDI `NY.GDP.PCAP.PP.KD`, WLD (constant 2021 PPP $)",
             f"Settlement; 2025 = ${y25:,.0f}"],
            ["No-effect baseline", "IMF WEO October 2026, DataMapper `NGDP_RPCH` and `LP`, WEOWORLD",
             "Baseline per-capita growth"],
            ["Spread of background growth", "IMF historical WEO forecasts (pending); stand-in: WDI `NY.GDP.PCAP.KD`, "
             "1960–2025" if x.stand_in else "IMF Historical WEO Forecasts Database (`WEOhistorical.xlsx`, sheet "
             f"`ngdp_rpch`), October vintages {x.err['first_vintage']}–{x.err['last_vintage']}",
             "Forecast-error paths, including the average miss"],
            ["IRF and shocks", "`dkaenzig/micc_replication`; `dkaenzig/global-temperature-shocks`", "Response, validation"],
        ]),
        "",
        "## 3. Temperature shocks",
        "",
        f"**Filter (frozen):** `{x.ham['formula'].split(';')[0]}`, fitted on NOAA over the paper's window (dependent years "
        f"{x.ham['fit_years'][0]}–{x.ham['fit_years'][1]}), residual sd {x.ham['resid_sd']:.3f} °C. Later years are out of "
        "sample.",
        "",
        table(["Check", "Result"], [
            ["NOAA shocks (contract) vs authors' published PWT shocks, 1960–2019",
             f"corr {x.val['noaa_p2_vs_authors_pwt_shock']['corr']:.3f}"],
            ["GISTEMP shocks vs authors' published PWT shocks, 1960–2019",
             f"corr {x.val['gistemp_p2_vs_authors_pwt_shock']['corr']:.3f}"],
            ["NOAA (p=6) vs authors' BU shocks", f"corr {x.val['noaa_p6_vs_authors_bu_shock']['corr']:.3f}"],
            ["p+1-lag (Eq. 1 literal) vs authors' shock",
             f"corr {x.val['paper_eq1_convention_vs_authors']['corr']:.3f} (rejected)"],
        ]),
        "",
        table(["Year", "NOAA T (°C)", "Filter expectation", "Shock s", "Innovation u",
               f"Rank among {x.ham['fit_years'][0]}–{x.ham['fit_years'][1]}", "Status"],
              [[e["year"], f"{e['T_noaa']:.3f}" + (f" ± {e['T_sd']:.3f}" if e["T_sd"] else ""),
                f"{e['filter_expectation']:.3f}", sg(e["shock"], 3), sg(e["innovation"], 3),
                e["rank_in_fit_sample"], e["status"]] for e in x.r["event_shocks"]]),
        "",
        "Because the h=2 filter predicts 2026 from 2024 and 2023 (both record-warm), the 2026–27 El Niño has to beat an "
        "already high expectation to register as a shock. 2024 was predicted from 2022 and 2021 (La Niña years), which "
        "is why its shock is the record.",
        "",
        "## 4. The impulse response",
        "",
        "- **Primary:** the PWT time-series LP (paper Fig. III), re-estimated in Python from the authors' data: θ = "
        + ", ".join(m(t) for t in x.theta) + " for h = 0…10 (100×log points per 1 °C).",
        "- **Uncertainty:** 4,000 joint draws from the authors' wild-bootstrap procedure, re-centred on the point estimate.",
        "- **Beyond h=10** θ is held at θ₁₀ (the paper: responses do not fully mean-revert). Truncation to 0 is a variant.",
        "- **Mismatches accepted:** the IRF is estimated on PWT world GDP and Berkeley Earth shocks, and applied to WDI "
        "PPP world GDP and NOAA shocks. The authors' panel estimate with WDI GDP is close to the PWT one, and the shock "
        "series track each other closely.",
        "",
        "## 5. From shocks to a GDP prediction",
        "",
        "`E_t = Σ_τ θ_{min(t−τ,10)} · u_τ − Σ_{τ≤2025} θ_{min(2025−τ,10)} · u_τ`. The second sum removes effects "
        f"already in the observed 2025 level. The contract measures growth from {x.base} to {x.end}, so the paper's "
        f"prediction is `E_{x.end} − E_{x.base}` (point IRF, central placeholders):",
        "",
        table(["Contributing shocks", "Contribution (points)"], contrib_rows(x)),
        "",
        "## 6. Temperatures after 2027",
        "",
        "Simulated 2028+ shocks are part of the paper's prediction: under its response, any later shock moves GDP too. "
        "They enter through their innovations, the part the two prior shocks do not predict, so the typical follow-on "
        "path already inside θ is not counted twice.",
        "",
        f"- **Model:** " + x.ft["model"].replace(" C,", " °C,").replace(" -0.", " −0.") + ".",
        "- **Mean simulated shocks:** " + ", ".join(f"{y} {sg(float(v))}" for y, v in
                                                    list(x.ft["shock_mean_by_year"].items())[:4]) + " °C.",
        f"- **Effect:** {sg(x.ft['effect_on_M_mean'], 2)} points on {x.base}–{x.end} growth (90% range "
        f"{sg(x.ft['effect_on_M_q05'], 1)} to {sg(x.ft['effect_on_M_q95'], 1)}). Without them the cutoff would be "
        f"{x.ft['cutoff_without_pp']:.2f}%/yr and J {x.ft['youden_j_without']:.2f}.",
        "- The cutoffs are fixed in advance; realised 2028–30 temperatures do not change them.",
        "",
        "## 7. The no-effect baseline",
        "",
        f"- **Path:** IMF WEO October 2026 world real GDP growth minus world population growth, plus the "
        f"{x.bl['gap_years'][0]}–{x.bl['gap_years'][1]} mean WDI gap ({sg(x.bl['wdi_gap_pp'])} points; correlation "
        f"{x.bl['gap_corr']:.2f}). Per-capita growth "
        + ", ".join(f"{y} {x.bl['growth_pp'][str(y)]:.2f}" for y in range(x.base + 1, x.end + 1))
        + f"; mean {x.bl['window_mean_pp']:.2f}%/yr. The 2031 rate is held beyond 2031.",
        "- **Spread:** whole historical forecast-error paths, shrunk toward their mean and mixed with Gaussian noise "
        "of the same covariance (a smoothed bootstrap), so multi-year misses keep their persistence and the distribution "
        "is continuous.",
        f"- {stand_note}",
        f"- **Result:** under no effect, M has sd {c['sd_h0']:.2f}; average growth {x.base}–{x.end} has a 10–90% range "
        f"of {x.sel['growth_h0_q10']:.1f}–{x.sel['growth_h0_q90']:.1f}%/yr.",
        "- **Backtests of a frozen 20-year drift:** 8-year misses of about ±4.3 points (WDI USD), ±7.8 (PWT) and "
        "±10.6 (Barro–Ursúa, including wars and the Depression). `outputs/null_backtest.csv` has the contract horizon.",
        "",
        "## 8. The end year",
        "",
        "Rule: the end year in 2028–2037 with the highest J (two decimals; ties to the earlier year), chosen before "
        "listing and using no GDP data after 2025. J rewards a contract that resolves in line with whichever view is "
        "true, so choosing the end year this way favours neither side.",
        "",
        scan_table(x, [y for y in x.scan.index]),
        "",
        "## 9. The conditional contracts",
        "",
        bins_table(x),
        "",
        "Strike ladder (P(Yes) if no effect / if the paper is right; headline strikes in bold):",
        "",
        ladder_table(x),
        "",
        "Fair price of a $1 Yes contract (unconditional cutoff) for a participant who puts probability p on the paper "
        "being right: " + "; ".join(f"p = {k.split('=')[1]}: ${v['yes']:.2f}" for k, v in x.r["prices_by_prior"].items())
        + ".",
        "",
        "## 10. Robustness (one change at a time, each with its own cutoff)",
        "",
        table(["Variant", "Paper's shift (points)", "Cutoff (%/yr)", "J"], var_rows),
        "",
        f"- If the truth were only the 2023–27 or only the 2026–27 shocks, the unconditional contract would resolve No "
        f"{pc(x.scope['scope: 2023-27 spikes only'])} / {pc(x.scope['scope: 2026-27 El Nino only'])} of the time.",
        "- The IRF family and how long the warmth persists matter most for the predicted size; the baseline matters "
        "most for what the cutoff means in growth terms.",
        "",
        "## 11. What a result would and would not establish",
        "",
        "- **It tests a prediction, not the paper.** Growth at or below the strike is evidence in the direction of the "
        "paper's linear world-GDP response; growth above it is evidence against an effect of that size. Neither "
        "identifies causation for this one episode.",
        f"- **The test is relative.** Under the paper, median world GDP per capita still rises, to ≈${h1_lv / 1000:.1f}k "
        f"in {x.end} against ≈${h0_lv / 1000:.1f}k with no effect (2025: ${y25 / 1000:.1f}k).",
        "- **It tests the warm sequence, not El Niño alone.** Both the prediction and the outcome carry the 2023–25 "
        "shocks.",
        f"- **Mostly an out-of-sample test of extrapolation.** The 2024 shock ({sg(ev[2024]['shock'])} °C) is above the "
        "largest in the authors' sample (+0.30 °C in 2016).",
        "- **Error rates depend on the baseline being right.** "
        + (f"The spread assumes the IMF's average miss continues. If its forecasts had become unbiased, the central "
           f"contract would resolve No only {pc(x.miss_c['central']['p_no_paper'])} of the time when the paper is "
           f"right (instead of {pc(1 - b1['p_yes_paper_at_strike'])}); if its misses grew, No would come more often "
           "with no effect." if x.miss_c and not x.stand_in else
           "If the IMF's errors are wider or more biased than the spread assumes, the error rates are worse."),
        "- **The early look is uninformative.** Against a 2022-anchored frozen drift, realised 2023–25 deviations were "
        + " / ".join(sg(v, 1) for v in hind["realized_dev_pct"]) + "%; the paper's point IRF implied "
        + " / ".join(sg(v, 1) for v in hind["bk_implied_pct"]) + "% (sd under no effect "
        + "–".join(f"{v:.1f}" for v in hind["h0_sd_pct"][::2]) + ").",
        "",
        "## 12. Objections we expect",
        "",
        "Collected after re-reading the paper and its online appendix against the design. Who would raise each, the "
        "answer, and whether the design addresses it or it stays a caveat:",
        "",
        *objection_lines(x),
        "",
        "## 13. Timeline and open questions (see `CONTRACT_TERMS.md`)",
        "",
        "- Monthly refreshes until the freeze.",
        "- NOAA's 2026 annual value ~mid-Jan 2027: final refresh, terms frozen, **conditional contracts list**.",
        "- NOAA's DJF 2027 RONI ~Mar 2027 (prices move; terms do not).",
        "- NOAA's 2027 annual value ~mid-Jan 2028: **the matching condition converts; the others are refunded**.",
        f"- WDI {x.end} first release mid-{x.end + 1}; **resolution 1 Oct {x.settle}**.",
        "",
        "**Open questions:**",
        *(["- Replace the stand-in spread with the IMF's historical forecast errors "
           "(`data/raw/imf_hist/WEOhistorical.xlsx`)."] if x.stand_in else []),
        f"- A low-power clause or no-decision zone for the cool condition (J {b0['youden_j']:.2f})?",
        "- List an unconditional contract from the start as well?",
        "",
        "## 14. Reproduce and refresh",
        "",
        "```",
        "python -I run_analysis.py --refresh               # monthly: re-download data, update placeholders and indicative terms",
        "python -I run_analysis.py                         # re-run on cached data in data/raw/",
        "python -I build_page.py && python -I build_docs.py  # comment page, CONTRACT_TERMS.md, MEMO.md",
        "python -I run_analysis.py --lock <T2026> <T2027>  # after conversion: cutoff for the realised temperatures",
        "python -I -m pytest tests -q -p no:cacheprovider",
        "```",
        "",
        "### Sources",
        "",
        "- Bilal & Känzig (2026), *QJE* 141(2): https://doi.org/10.1093/qje/qjag011 · replication: "
        "https://github.com/dkaenzig/micc_replication · shocks: https://github.com/dkaenzig/global-temperature-shocks",
        "- NOAA NCEI Climate at a Glance: https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series"
        " · NOAA CPC ENSO indices · NASA GISTEMP v4 (comparison and fallback): https://data.giss.nasa.gov/gistemp/",
        "- World Bank WDI `NY.GDP.PCAP.PP.KD`: https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.KD",
        "- IMF World Economic Outlook, October 2026 (DataMapper API): https://www.imf.org/external/datamapper",
        "- Critiques cited in §1 and §12: Curtin and Burgess, \"The empirically inscrutable climate-economy "
        "relationship\" (University of Wyoming working paper, 31 July 2026) · Kahn, \"Real-Time Information Shocks and "
        "Climate Change Economic Damage Estimation\" (working paper, 30 September 2026)",
        "",
    ]
    return "\n".join(lines)


def main():
    x = R()
    (ROOT / "CONTRACT_TERMS.md").write_text(terms(x))
    (ROOT / "MEMO.md").write_text(memo(x))
    print(f"wrote CONTRACT_TERMS.md and MEMO.md (base {x.base}, end {x.end}, refreshed {x.refreshed})")


if __name__ == "__main__":
    main()
