"""Figures for the general-audience article (docs/article_v2), numbered as in the 30 Oct 2026 draft.

Plain-language labels for readers new to the topic. Same validated palette as
bk_elnino/plots.py: orange = the paper's estimate, blue = no temperature effect,
red/blue diverging pair for warm/cool temperature shocks. Reads only files that
run_analysis.py already wrote, so the numbers match the live proposal page.

    python3 -I docs/article_v2/make_figures.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from bk_elnino import plots as P  # noqa: E402  (sets rcParams and palette)
from bk_elnino import sources as S  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch  # noqa: E402
from scipy.stats import gaussian_kde  # noqa: E402

OUT = Path(__file__).resolve().parent / "figures"
INK, INK2, MUTED, AXIS = P.INK, P.INK2, P.MUTED, P.AXIS
BLUE, ORANGE, RED = P.BLUE, P.ORANGE, P.RED
BLUE_LIGHT, RED_LIGHT = P.BLUE_LIGHT, P.RED_LIGHT
DPI = 220
MINUS = "−"

plt.rcParams.update({
    "font.size": 10.5, "axes.titlesize": 12.5, "legend.fontsize": 9.5,
    "xtick.labelsize": 9.5, "ytick.labelsize": 9.5, "axes.labelsize": 10,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
})


def header(ax, title: str, subtitle: str | None = None):
    ax.set_title(title, loc="left", pad=26 if subtitle else 10, fontsize=12.5, fontweight="semibold", color=INK)
    if subtitle:
        ax.text(0, 1.035, subtitle, transform=ax.transAxes, fontsize=9.6, color=INK2, va="bottom", ha="left")


def save(fig, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=DPI, bbox_inches="tight", pad_inches=0.12, facecolor=fig.get_facecolor())
    plt.close(fig)


def load():
    res = json.loads((ROOT / "outputs/results.json").read_text())
    T = S.read_noaa_cag(ROOT / "data/raw/noaa/noaa_globaltemp_annual.csv")
    oni = S.read_oni(ROOT / "data/raw/oni/oni.ascii.txt")
    djf = oni[oni.season == "DJF"].set_index("year")["anom"]
    shocks = pd.read_csv(ROOT / "outputs/shocks.csv").set_index("year")
    events = pd.read_csv(ROOT / "outputs/event_shocks.csv").set_index("year")
    irf = pd.read_csv(ROOT / "outputs/irf.csv")
    irf = irf[irf.irf == "PWT_ts"].set_index("h")
    scen = pd.read_csv(ROOT / "outputs/scenario_annual.csv").set_index("year")
    draws = np.load(ROOT / "outputs/conditional_M_draws.npz")
    return res, T, djf, shocks, events, irf, scen, draws


def design(res):
    """Numbers every figure shares: base and end year, baseline mean, the central contract."""
    d = res["design_primary"]
    base, end = d["base_year"], d["window"][1]
    bins = {b["bin"]: b for b in res["conditional_contracts"]["bins"]}
    return base, end, res["baseline_primary"]["window_mean_pp"], bins


def fig_temperature(res, T, djf):
    _, _, _, bins = design(res)
    prov = res["provisional"]
    t26, s26 = prov["T2026"]["mean"], prov["T2026"]["sd"]
    t27, s27 = prov["T2027"]["mean"], prov["T2027"]["sd"]
    t = T.loc[1950:2025]
    strong = [y for y, v in djf.items() if v >= 1.5 and 1950 <= y <= 2025]

    fig, ax = plt.subplots(figsize=(7.0, 3.9))
    ax.plot(t.index, t.values, color=INK2, lw=1.7, zorder=2, label="Observed yearly average")
    ax.plot([2025, 2026, 2027], [t.loc[2025], t26, t27], color=INK2, lw=1.2, ls=(0, (2, 2)), zorder=1)
    ax.scatter(strong, t.loc[strong], s=46, color=ORANGE, edgecolor="white", linewidth=1.2, zorder=4,
               label="Year began during a strong El Niño")
    for yr, m, sd, col in [(2026, t26, s26, INK2), (2027, t27, s27, ORANGE)]:
        ax.errorbar([yr], [m], yerr=[[1.645 * sd], [1.645 * sd]], fmt="o", ms=6.5, mfc="white", mec=col, mew=1.8,
                    ecolor=col, elinewidth=1.4, capsize=3, zorder=5,
                    label="Estimate, updated monthly (90% range)" if yr == 2026 else None)
    for yr in (1998, 2016):
        ax.annotate(f"{yr}", (yr, t.loc[yr]), xytext=(0, 9), textcoords="offset points", fontsize=9, color=INK,
                    ha="center")
    ax.annotate("2024\nrecord", (2024, t.loc[2024]), xytext=(-6, 8), textcoords="offset points", fontsize=9,
                color=INK, ha="right", va="bottom")
    ax.annotate("2027\nestimate", (2027, t27), xytext=(-9, 13), textcoords="offset points", fontsize=9,
                color=INK, ha="right", va="bottom")
    # the three ranges of NOAA's 2027 value the contracts are conditioned on
    lo, hi = t27 - 1.645 * s27 - 0.03, t27 + 1.645 * s27 + 0.03
    e1, e2 = bins["central"]["lower"], bins["central"]["upper"]
    x0, w = 2028.1, 0.75
    for (a, b), col, name in (((lo, e1), BLUE_LIGHT, "cool"), ((e1, e2), "#c9c8c0", "central"),
                               ((e2, hi), RED_LIGHT, "warm")):
        ax.add_patch(plt.Rectangle((x0, a), w, b - a, color=col, lw=0, zorder=3))
        lab = bins[name]["condition"].replace(" C", " °C").replace(" to ", "–")
        ax.text(x0 + w + 0.35, (a + b) / 2, f"{name.capitalize()}: {lab}", va="center", ha="left", fontsize=8.3,
                color=INK)
    ax.plot([2027.25, x0 - 0.1], [t27, t27], color=MUTED, lw=0.8, zorder=2)
    ax.annotate("2026\nestimate", (2026, t26), xytext=(9, -14), textcoords="offset points", fontsize=8.6,
                color=INK2, va="top")
    note = "Exceptions: volcanic eruptions\ncooled 1983 and 1992"
    for yr, alpha in ((1992, 1), (1983, 0)):
        ax.annotate(note, (yr, t.loc[yr]), xytext=(1987.5, -0.17), textcoords="data", fontsize=8.6,
                    color=INK2 if alpha else (0, 0, 0, 0), ha="center", va="center",
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=3, shrinkB=4))
    ax.set_xlim(1949, 2042.5)
    ax.set_xticks(range(1950, 2031, 10))
    ax.set_ylim(min(-0.3, float(t.min()) - 0.1), 1.78)
    ax.set_ylabel("°C above the 1901–2000 average")
    ax.legend(loc="upper left", handletextpad=0.5, borderaxespad=0.2)
    header(ax, "Global temperature rises in steps, and strong El Niños set the timing",
           "Global average surface temperature, 1950–2025, estimates for 2026–27, and the three 2027 ranges")
    save(fig, "fig1_temperature.png")


def fig_shocks(shocks, events):
    s = shocks.loc[1953:2025, "shock"]
    fig, ax = plt.subplots(figsize=(7.0, 3.7))
    ax.bar(s.index, s.values, width=0.74, color=[RED if v > 0 else BLUE for v in s.values], linewidth=0, zorder=2)
    for yr in (2026, 2027):
        m, sd = events.loc[yr, "shock"], events.loc[yr, "shock_sd"]
        ax.bar([yr], [m], width=0.74, color=RED_LIGHT if m > 0 else BLUE_LIGHT, linewidth=0, zorder=2)
        ax.errorbar([yr], [m], yerr=[[1.645 * sd], [1.645 * sd]], fmt="none", ecolor=INK2, elinewidth=1.1,
                    capsize=2.5, zorder=3)
    ax.axhline(0, color=AXIS, lw=0.9, zorder=1)
    for yr in (1998, 2016):
        ax.annotate(f"{yr}\nEl Niño", (yr, s.loc[yr]), xytext=(0, 4), textcoords="offset points", ha="center",
                    fontsize=8.4, color=INK)
    ax.annotate(f"2024 El Niño: +{s.loc[2024]:.2f} °C, the largest since at least the 1950s", (2024, s.loc[2024]),
                xytext=(2022.6, 0.425), textcoords="data", ha="right", va="center", fontsize=8.6, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=2, shrinkB=2))
    m27, sd27 = events.loc[2027, "shock"], events.loc[2027, "shock_sd"]
    ax.annotate(f"2027\nestimate\n+{m27:.2f} °C", (2027, m27 + 1.645 * sd27), xytext=(10, -4),
                textcoords="offset points", ha="left", va="center", fontsize=8.4, color=INK)
    ax.text(1990.7, -0.27, "1992: Pinatubo\neruption", ha="right", va="center", fontsize=8.4, color=INK2)
    ax.set_xlim(1951, 2033.5)
    ax.set_ylim(-0.36, 0.48)
    ax.set_ylabel(f"°C warmer (+) or cooler ({MINUS})\nthan expected")
    ax.text(0.01, 0.97, "Warmer than expected", transform=ax.transAxes, color=RED, fontsize=9, va="top",
            fontweight="semibold")
    ax.text(0.01, 0.03, "Cooler than expected", transform=ax.transAxes, color=BLUE, fontsize=9, va="bottom",
            fontweight="semibold")
    header(ax, "Global temperature shocks: how much warmer or cooler each year was than expected",
           "“Expected” is what the temperatures of two and three years earlier predicted (the paper’s method)")
    save(fig, "extra_shocks.png")


def fig_paper(irf):
    h = irf.index.values
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    ax.fill_between(h, irf.q05, irf.q95, color=ORANGE, alpha=0.16, linewidth=0, label="90% range of the estimate")
    ax.plot(h, irf.theta_pct_per_C, color=ORANGE, lw=2.2, marker="o", ms=4.5, mfc=ORANGE, mec="white", mew=1.0,
            label="Central estimate", zorder=3)
    ax.axhline(0, color=INK2, lw=1.0, zorder=1)
    ax.text(2.6, 0.45, "No effect", fontsize=9, color=INK2, va="bottom", ha="left")
    trough = int(irf.theta_pct_per_C.idxmin())
    ax.annotate(f"{MINUS}{abs(irf.theta_pct_per_C.min()):.0f}% after\n{trough} years",
                (trough, irf.theta_pct_per_C.min()), xytext=(0, -30), textcoords="offset points", ha="center",
                va="top", fontsize=9.5, color=INK, fontweight="semibold")
    ax.set_xlim(-0.3, 10.3)
    ax.set_ylim(-21, 4)
    ax.set_xticks(range(0, 11))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}".replace("-", MINUS))
    ax.set_xlabel("Years after a 1 °C global temperature shock")
    ax.set_ylabel("Change in world GDP per person (%)")
    ax.legend(loc="lower left", borderaxespad=0.3)
    header(ax, "The paper’s central finding: a warm shock depresses world output for years",
           "Effect of a 1 °C shock. Real shocks are usually 0.1–0.2 °C, so real effects are proportionally smaller")
    save(fig, "fig2_paper_estimate.png")


def fig_quadrant():
    beige, arrow_grey = "#eae0c3", "#b6af9b"
    fig = plt.figure(figsize=(7.0, 5.25), facecolor=beige)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=beige)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    x0, ya = 0.115, 0.11
    ax.add_patch(FancyArrowPatch((x0, 0.955), (x0, ya + 0.02), arrowstyle="-|>", mutation_scale=22, lw=3.2,
                                 color=INK))
    ax.add_patch(FancyArrowPatch((x0 - 0.006, ya), (0.965, ya), arrowstyle="-|>", mutation_scale=22, lw=3.2,
                                 color=INK))
    ax.text(0.045, 0.55, "How strong is the pull toward a preferred conclusion?", rotation=90, ha="center",
            va="center", fontsize=11.5, fontweight="bold", color=INK)
    ax.text(0.085, 0.94, "Not strong", rotation=90, ha="center", va="top", fontsize=10, color=MUTED)
    ax.text(0.085, 0.14, "Strong", rotation=90, ha="center", va="bottom", fontsize=10, color=MUTED)
    ax.text(0.54, 0.028, "How testable is the relevant real-world conclusion?", ha="center", va="center",
            fontsize=11.5, fontweight="bold", color=INK)
    ax.text(0.14, 0.072, "Not very", ha="left", va="center", fontsize=10, color=MUTED)
    ax.text(0.94, 0.072, "Very", ha="right", va="center", fontsize=10, color=MUTED)
    ax.plot([0.54, 0.54], [0.14, 0.95], color=MUTED, lw=0.9, ls=(0, (4, 4)), alpha=0.6)
    ax.plot([0.14, 0.95], [0.55, 0.55], color=MUTED, lw=0.9, ls=(0, (4, 4)), alpha=0.6)
    for txt, (x, y) in {"II": (0.165, 0.915), "I": (0.935, 0.915), "IV": (0.165, 0.515),
                        "III": (0.935, 0.515)}.items():
        ax.text(x, y, txt, ha="center", va="center", fontsize=10, color="white",
                bbox=dict(boxstyle="square,pad=0.35", fc="#8d8a80", ec="none"))

    dotted = dict(arrowstyle="-|>", mutation_scale=24, lw=5, color=arrow_grey, linestyle=(0, (1.1, 1.5)))
    ax.text(0.305, 0.405, "Headline estimates of\nwhat climate change\ncosts the world economy\n"
            "(e.g., more than $1,200\nper ton of CO$_2$)", ha="center", va="top", fontsize=10, color=INK,
            linespacing=1.22)
    ax.add_patch(FancyArrowPatch((0.47, 0.315), (0.925, 0.315), **dotted))
    ax.text(0.705, 0.285, "Accuracy will actually be assessed:\na dated forecast of world GDP per\nperson, "
            "scored against official data", ha="center", va="top", fontsize=10, color=INK, linespacing=1.22)
    ax.add_patch(FancyArrowPatch((0.305, 0.425), (0.305, 0.9), **dotted))
    ax.text(0.28, 0.69, "Positions are\nrewarded only\nfor accuracy", ha="right", va="center", fontsize=10,
            color=INK, linespacing=1.22)
    ax.add_patch(FancyArrowPatch((0.37, 0.44), (0.86, 0.86), arrowstyle="simple,head_length=1.1,head_width=1.6,"
                                 "tail_width=0.55", mutation_scale=26, color=arrow_grey, lw=0))
    ax.text(0.79, 0.905, "The proposed\nforecast contract", ha="right", va="center", fontsize=11, color=INK,
            fontweight="semibold", linespacing=1.2)
    save(fig, "extra_up_and_to_the_right.png")


def fig_background(res, wdi_growth):
    base, end, mu, _ = design(res)
    scan = {r["end_year"]: r for r in res["end_year"]["scan"]}[end]
    bl = res["baseline_primary"]
    g, miss = bl["growth_pp"], bl["errors"]["mean_by_lead"]          # miss: realized minus forecast, by lead
    h = wdi_growth.loc[1991:2025]
    yrs = range(base + 1, end + 1)
    proj = pd.Series({y: g[str(y)] for y in yrs})
    expect = pd.Series({y: g[str(y)] + miss[min(y - 2025, len(miss)) - 1] for y in yrs})
    paper = res["contract_primary"]["h1_growth_mean_pp"]
    h0 = res["contract_primary"]["h0_growth_mean_pp"]

    fig, ax = plt.subplots(figsize=(7.0, 3.9))
    ax.bar(h.index, h.values, width=0.72, color="#cfcec6", linewidth=0, zorder=2, label="Observed")
    ax.add_patch(plt.Rectangle((base + 0.5, scan["growth_h0_q10"]), end - base, scan["growth_h0_q90"] -
                               scan["growth_h0_q10"], color=BLUE, alpha=0.13, lw=0, zorder=1))
    ax.plot(proj.index, proj.values, color=INK2, lw=1.6, marker="o", ms=3.8, mec="white", mew=1.0, zorder=4,
            label="IMF projection")
    ax.plot(expect.index, expect.values, color=BLUE, lw=2.2, marker="o", ms=4.5, mec="white", mew=1.0, zorder=5,
            label="No temperature effect: IMF projection\nless the IMF’s average past miss")
    ax.hlines(paper, base + 0.5, end + 0.5, color=ORANGE, lw=2.0, ls=(0, (4, 2)), zorder=4,
              label="Paper’s estimate, average")
    ax.axhline(0, color=AXIS, lw=0.9, zorder=1)
    ax.text(end + 0.9, proj.mean() + 0.8, f"IMF projection:\n{proj.mean():.1f}% a year", ha="left", va="bottom",
            fontsize=8.6, color=INK2, linespacing=1.15)
    ax.text(end + 0.9, h0 - 0.05, f"No temperature effect:\n{h0:.1f}% a year, most\nlikely {scan['growth_h0_q10']:.1f}% "
            f"to {scan['growth_h0_q90']:.1f}%\n(shaded, 80% range)", ha="left", va="center", fontsize=8.6,
            color=BLUE, linespacing=1.15)
    ax.text(end + 0.9, paper - 0.35, f"Paper’s estimate:\n{paper:.1f}% a year", ha="left", va="top", fontsize=8.6,
            color=ORANGE, fontweight="semibold", linespacing=1.15)
    ax.annotate("2009: financial crisis", (2009, h.loc[2009]), xytext=(7, 2), textcoords="offset points",
                ha="left", va="center", fontsize=8.2, color=INK2)
    ax.annotate("2020: pandemic", (2020, h.loc[2020]), xytext=(0, -6), textcoords="offset points",
                ha="center", va="top", fontsize=8.2, color=INK2)
    ax.set_xlim(1990, end + 9.5)
    ax.set_xticks(range(1990, end + 1, 5))
    ax.set_ylim(-5.2, 6.2)
    ax.set_ylabel("Growth in world GDP per person (%)")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}".replace("-", MINUS))
    ax.legend(loc="lower left", fontsize=8.4, handlelength=1.8)
    header(ax, "Background growth is the biggest source of uncertainty",
           f"World GDP per person, yearly growth 1991–2025, and the outlook for {base + 1}–{end}")
    save(fig, "fig3_background_growth.png")


def fig_paths(res, scen):
    base, end, mu, bins = design(res)
    strike = bins["central"]["strike"]
    g = res["baseline_primary"]["growth_pp"]
    yrs = np.arange(base, end + 1)
    cum = np.r_[0.0, np.cumsum([g[str(y)] for y in yrs[1:]])]
    idx = lambda dev: 100 * np.exp((cum + dev) / 100)  # noqa: E731
    get = lambda col: scen.loc[yrs, col].fillna(0).values  # noqa: E731
    h0_mean, h1_mean = idx(get("H0_devb_mean")), idx(get("H1_devb_mean"))   # include the IMF's average miss
    h0_lo, h0_hi = idx(get("H0_devb_q10")), idx(get("H0_devb_q90"))
    h1_lo, h1_hi = idx(get("H1_devb_q10")), idx(get("H1_devb_q90"))
    cut = 100 * np.exp(strike * (yrs - base) / 100)

    fig, ax = plt.subplots(figsize=(7.0, 3.9))
    ax.fill_between(yrs, h0_lo, h0_hi, color=BLUE, alpha=0.13, linewidth=0)
    ax.fill_between(yrs, h1_lo, h1_hi, color=ORANGE, alpha=0.15, linewidth=0)
    ax.plot(yrs, h0_mean, color=BLUE, lw=2.2, marker="o", ms=4.5, mec="white", mew=1.0, zorder=3)
    ax.plot(yrs, h1_mean, color=ORANGE, lw=2.2, marker="o", ms=4.5, mec="white", mew=1.0, zorder=3)
    ax.plot(yrs, cut, color=INK, lw=1.4, ls=(0, (4, 3)), zorder=4)
    span = end - base
    rate = lambda path: 100 * np.log(path[-1] / 100) / span  # noqa: E731
    g0, g1 = rate(h0_mean), rate(h1_mean)
    ax.text(end + 0.08, h0_mean[-1], f"No temperature effect\n+{g0:.1f}% a year", color=BLUE, va="center",
            fontsize=9.5, fontweight="semibold")
    ax.text(end + 0.08, cut[-1], f"Cutoff +{strike:.1f}% a year", color=INK, va="center", fontsize=9.5)
    ax.text(end + 0.08, h1_mean[-1], f"Paper’s estimate\n+{g1:.1f}% a year", color=ORANGE, va="center",
            fontsize=9.5, fontweight="semibold")
    ax.set_xlim(base - 0.15, end + 1.05)
    ax.set_xticks(yrs)
    ax.set_ylim(min(h1_lo) - 0.6, max(h0_hi) + 0.6)
    ax.set_ylabel(f"World GDP per person ({base} = 100)")
    header(ax, f"What the paper implies for {base}–{end}",
           "Lines: average projections. Shading: 80% ranges, including normal swings in world growth")
    save(fig, "fig4_paths.png")
    return g0, g1


def fig_after_el_nino(res, shocks):
    base, end, _, _ = design(res)
    ft = res["future_temperatures"]
    analogs = [int(y) for y in re.findall(r"\d{4}", ft["model"].split("[")[1].split("]")[0])]
    s = shocks["shock"]
    fut = pd.read_csv(ROOT / "outputs/future_temperatures.csv").set_index("year")
    sim = [float(s.loc[2027])] + [float(ft["shock_mean_by_year"][str(y)]) for y in (2028, 2029, 2030)]

    fig, (a, b) = plt.subplots(1, 2, figsize=(7.6, 3.7), gridspec_kw={"width_ratios": [1, 1.15], "wspace": 0.32})
    xs = np.arange(4)
    paths = np.array([[s.loc[y + k] for k in xs] for y in analogs])
    for p in paths:
        a.plot(xs, p, color="#c4c3bb", lw=1.0, zorder=1)
    a.plot(xs, paths.mean(axis=0), color=BLUE, lw=2.2, marker="o", ms=4.5, mec="white", mew=1.0, zorder=3,
           label=f"Average after the {len(analogs)} past\nstrong El Niños (gray: each one)")
    a.plot(xs, sim, color=ORANGE, lw=2.0, ls=(0, (4, 2)), marker="o", ms=4.5, mec="white", mew=1.0, zorder=4,
           label="2027 estimate and the\nsimulated years after it")
    a.axhline(0, color=AXIS, lw=0.9, zorder=0)
    a.set_xticks(xs, ["El Niño\nyear", "+1", "+2", "+3"])
    a.set_ylabel("Global temperature shock (°C)")
    a.yaxis.set_major_formatter(lambda v, _: f"{v:.1f}".replace("-", MINUS))
    a.legend(loc="upper right", fontsize=8.0, handlelength=1.6)
    a.set_ylim(-0.42, 0.62)
    a.set_title("Strong El Niños are usually\nfollowed by cooler years", loc="left", fontsize=10.5,
                fontweight="semibold", color=INK)

    w = fut.loc[base:2035, "effect_with_future_pct"]
    wo = fut.loc[base:2035, "effect_without_future_pct"]
    b.axvspan(base, end, color="#eeede8", lw=0, zorder=0)
    b.text(base + 0.15, 1.75, f"Measured\n{base}–{end}", fontsize=8.2, color=INK2, va="top", ha="left")
    b.plot(wo.index, wo.values, color=INK2, lw=1.6, ls=(0, (3, 2)), label="Shocks through 2027 only")
    b.plot(w.index, w.values, color=ORANGE, lw=2.2, label="Plus the simulated years\nafter the El Niño")
    b.axhline(0, color=AXIS, lw=0.9)
    gap = float(w.loc[end] - wo.loc[end])
    lo = float(min(w.min(), wo.min()))
    note = (f"Later years barely change\nthe {base}–{end} gap" if abs(gap) < 0.1 else
            f"Later years change the\n{base}–{end} gap by {gap:+.1f} points".replace("-", MINUS))
    b.annotate(note, (end, (w.loc[end] + wo.loc[end]) / 2), xytext=(base + 2.3, -0.55), textcoords="data",
               fontsize=8.4, color=INK, va="top", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=2,
                                                                 shrinkB=2))
    b.set_xticks(range(base, 2036, 2))
    b.set_ylabel(f"GDP per person vs no-effect path,\n% (from {base})")
    b.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}".replace("-", MINUS))
    b.legend(loc="upper right", fontsize=7.6)
    b.set_ylim(lo - 0.5, 1.95)
    b.set_title("The paper’s prediction, with and\nwithout the years after 2027", loc="left", fontsize=10.5,
                fontweight="semibold", color=INK)
    save(fig, "fig5_after_el_nino.png")
    return gap


def fig_end_year(res):
    _, end, _, _ = design(res)
    sc = pd.DataFrame(res["end_year"]["scan"]).set_index("end_year").loc[:2035]
    p_no = sc.sensitivity                 # paper right -> resolves No
    p_yes = 1 - sc.false_positive         # no effect -> resolves Yes
    avg = (p_no + p_yes) / 2
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    ax.plot(sc.index, 100 * p_no, color=ORANGE, lw=1.8, marker="o", ms=4, mec="white", mew=0.8,
            label="If the paper is right: chance of No")
    ax.plot(sc.index, 100 * p_yes, color=BLUE, lw=1.8, marker="o", ms=4, mec="white", mew=0.8,
            label="If temperature shocks have no effect: chance of Yes")
    ax.plot(sc.index, 100 * avg, color=INK, lw=2.6, zorder=3, label="Average of the two")
    ax.scatter([end], [100 * avg.loc[end]], s=80, color=INK, edgecolor="white", linewidth=1.5, zorder=4)
    ax.annotate(f"Best: {end}\n({100 * avg.loc[end]:.0f}% average)", (end, 100 * avg.loc[end]), xytext=(0, 24),
                textcoords="offset points", ha="center", va="bottom", fontsize=9.2, color=INK, fontweight="semibold")
    ax.axhline(50, color=AXIS, lw=0.9)
    ax.text(sc.index[-1], 50.8, "50% = a coin flip", ha="right", va="bottom", fontsize=8.4, color=INK2)
    ax.set_xticks(sc.index)
    ax.set_ylim(35, 100)
    ax.set_ylabel("Chance the contract resolves\nin line with the true view (%)")
    ax.set_xlabel("Last year of the growth period")
    ax.legend(loc="lower left", fontsize=8.6)
    header(ax, f"Why {end}: the end year where the two views separate best",
           "Each end year gets its own best cutoff; later years add predicted shortfall but also more noise")
    save(fig, "fig6_end_year.png")


def fig_resolution(res, draws):
    base, end, mu, bins = design(res)
    b = bins["central"]
    span = end - base
    g0 = mu + draws["central_m0"] / span
    g1 = mu + draws["central_m1"] / span
    gc = b["strike"]
    p1 = float(np.mean(g1 <= gc))
    p0 = float(np.mean(g0 > gc))
    lo, hi = np.floor(2 * np.quantile(g1, 0.002)) / 2, np.ceil(2 * np.quantile(g0, 0.998)) / 2
    x = np.linspace(lo, hi, 600)
    k0, k1 = gaussian_kde(g0, bw_method=0.18)(x), gaussian_kde(g1, bw_method=0.18)(x)

    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    ax.fill_between(x, 0, k1, where=x <= gc, color=ORANGE, alpha=0.22, linewidth=0)
    ax.fill_between(x, 0, k0, where=x > gc, color=BLUE, alpha=0.2, linewidth=0)
    ax.plot(x, k1, color=ORANGE, lw=2.2)
    ax.plot(x, k0, color=BLUE, lw=2.2)
    top = max(k0.max(), k1.max())
    ax.axvline(gc, color=INK, lw=1.4, ls=(0, (4, 3)))
    ax.text(gc - 0.06, top * 1.2, f"Cutoff: {gc:.1f}% a year", ha="right", va="center", fontsize=9.5, color=INK)
    i1, i0 = x[np.argmax(k1)], x[np.argmax(k0)]
    ax.text(i1 - 0.2, k1.max() * 1.04, f"If the paper is right:\n{p1:.0%} of outcomes fall at\nor below the cutoff",
            ha="right", va="bottom", color=ORANGE, fontsize=9.6, fontweight="semibold", linespacing=1.15)
    ax.text(i0 + 0.2, k0.max() * 0.98, f"If temperature shocks\nhave no effect: {p0:.0%} of\noutcomes fall "
            "above it", ha="left", va="bottom", color=BLUE, fontsize=9.6, fontweight="semibold", linespacing=1.15)
    ax.set_xlim(lo, hi)
    ax.set_ylim(0, top * 1.3)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}".replace("-", MINUS))
    ax.set_xlabel(f"Average yearly growth in world GDP per person, {base} to {end} (%)")
    cond = b["condition"].replace(" C", " °C").replace(" to ", "–")
    header(ax, "The cutoff separates the two predictions",
           f"Simulated outcomes if NOAA’s 2027 temperature is {cond} (the central contract)")
    save(fig, "fig7_resolution.png")
    return p1, p0


def fig_timeline(base, end):
    def d(y, m):
        return y + (m - 1) / 12

    settle = end + 1
    rows = [
        ("Open for comment;\nestimates updated monthly", d(2026, 10), d(2027, 1.5), ORANGE, ""),
        ("Conditional contracts\ntrade", d(2027, 1.5), d(2028, 1.5), P.AQUA, ""),
        ("Growth period measured", d(base + 1, 1), d(end + 1, 1), BLUE, ", ".join(str(y) for y in range(base + 1, end + 1))),
        (f"World Bank publishes\nits {end} estimate", d(end + 1, 7), d(settle, 10), INK2, ""),
    ]
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    for i, (lab, a, b, col, inside) in enumerate(rows):
        ax.barh(i, b - a, left=a, height=0.5, color=col, alpha=0.85, linewidth=0, zorder=2)
        if inside:
            ax.text(a + 0.08, i, inside, va="center", ha="left", fontsize=8.6, color="white", zorder=3,
                    fontweight="semibold")
    ax.barh(1, d(settle, 10) - d(2028, 1.5), left=d(2028, 1.5), height=0.5, color=P.AQUA, alpha=0.35, linewidth=0,
            zorder=2)
    ax.text(d(2028, 3), 1, "converted contract trades until resolution", va="center", ha="left", fontsize=8.3,
            color=INK, zorder=3)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=9.3)
    for x, lab, ytop, ha in [(d(2027, 1.5), "Mid-Jan 2027: NOAA’s 2026 value;\ncontracts list", -2.05, "left"),
                             (d(2028, 1.5), "Mid-Jan 2028: NOAA’s 2027 value;\nthe matching contract converts",
                              -1.2, "left"),
                             (d(settle, 10), f"Oct 1, {settle}:\ncontracts resolve", -2.05, "right")]:
        ax.vlines(x, ytop + 0.05, len(rows) - 0.5, color=INK, lw=1.2, ls=(0, (3, 2)), zorder=1)
        ax.text(x + (0.06 if ha == "left" else -0.06), ytop, lab, ha=ha, va="top", fontsize=8.3, color=INK,
                fontweight="semibold", linespacing=1.15)
    ax.set_xlim(d(2026, 7), d(settle + 1, 3))
    ax.set_ylim(len(rows) - 0.45, -2.15)
    ax.set_xticks(range(2027, settle + 2))
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    save(fig, "fig8_timeline.png")


def main():
    res, T, djf, shocks, events, irf, scen, draws = load()
    base, end, mu, bins = design(res)
    from bk_elnino import baseline as B
    wdi, _ = S.read_wdi_json(ROOT / "data/raw/wdi_gdppc_ppp/WLD_NY.GDP.PCAP.PP.KD.json")
    fig_temperature(res, T, djf)
    fig_paper(irf)
    fig_background(res, B.log_growth(wdi))
    g0, g1 = fig_paths(res, scen)
    gap = fig_after_el_nino(res, shocks)
    fig_end_year(res)
    p1, p0 = fig_resolution(res, draws)
    fig_timeline(base, end)
    fig_shocks(shocks, events)
    fig_quadrant()
    c = res["contract_primary"]
    err = res["baseline_primary"]["errors"]
    contrib = res["effect_contributions_to_M"]
    lvl = scen.loc[2035, "baseline_level"]
    y25 = res["frozen_drift_reference"]["anchor_level"]
    numbers = {
        "base": base, "end": end, "baseline_mean_pct_yr": round(mu, 3),
        "no_effect_expected_pct_yr": round(c["h0_growth_mean_pp"], 3),
        "imf_miss": {"vintages": f"{err['first_vintage']}-{err['last_vintage']}", "n": err["n_forecasts"],
                     "n_below": err["n_below_forecast"], "window_pts": round(err["sum_over_statistic_mean"], 3),
                     "window_sd_pts": round(err["sum_over_statistic_sd"], 3),
                     "per_year_pts": round(err["sum_over_statistic_mean"] / (end - base), 3)},
        "growth_no_effect_pct_yr": round(g0, 3), "growth_paper_pct_yr": round(g1, 3),
        "shortfall_pts": round(c["shortfall_mean"], 3), "shortfall_q05": round(c["shortfall_q05"], 3),
        "shortfall_q95": round(c["shortfall_q95"], 3), "shock_effect_pts": round(c["h1_effect_mean"], 3),
        "background_netting_pts": round(c["background_netting_pts"], 3),
        "share_2026_27": round(contrib["2026-2027"] / contrib["total"], 3),
        "share_2023_25": round(contrib["2023-2025"] / contrib["total"], 3),
        "share_2015_22": round(contrib["2015-2022"] / contrib["total"], 3),
        "cooler_years_pts": round(gap, 3),
        "central_strike": bins["central"]["strike"], "p_no_if_paper_right_central": round(p1, 3),
        "p_yes_if_no_effect_central": round(p0, 3),
        "bins": {k: {"condition": v["condition"], "strike": v["strike"], "prob_now": round(v["prob_now"], 3),
                     "p_yes_no_effect": round(v["p_yes_no_effect_at_strike"], 3),
                     "p_yes_paper": round(v["p_yes_paper_at_strike"], 3), "J": round(v["youden_j"], 3)}
                 for k, v in bins.items()},
        "decade_growth_no_effect_pct": round(100 * (lvl * np.exp(scen.loc[2035, "H0_dev_mean"] / 100) / y25 - 1), 3),
        "decade_growth_paper_pct": round(100 * (lvl * np.exp(scen.loc[2035, "H1_dev_mean"] / 100) / y25 - 1), 3),
        "decade_growth_imf_pct": round(100 * (lvl / y25 - 1), 3),
        "h0_avg_q10": round(next(r for r in res["end_year"]["scan"] if r["end_year"] == end)["growth_h0_q10"], 2),
        "h0_avg_q90": round(next(r for r in res["end_year"]["scan"] if r["end_year"] == end)["growth_h0_q90"], 2),
        "refreshed_utc": res["refreshed_utc"],
        "T2026": res["provisional"]["T2026"]["mean"], "T2027": res["provisional"]["T2027"]["mean"],
    }
    (OUT / "numbers.json").write_text(json.dumps(numbers, indent=1))
    print(json.dumps(numbers, indent=1))


if __name__ == "__main__":
    main()
