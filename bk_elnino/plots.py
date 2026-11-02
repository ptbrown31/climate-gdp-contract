"""Figures (static PNG). Palette: validated reference categorical slots (light mode),
blue<->red diverging pair for warm/cool shocks, hairline solid grids, one y-axis per
panel. Every figure has a CSV twin in outputs/ (the table view)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#e34948"
BLUE_LIGHT, RED_LIGHT = "#9ec5f4", "#f2a8a7"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"], "font.size": 9.5,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titlesize": 10.5, "axes.titleweight": "semibold", "axes.titlelocation": "left",
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "grid.linestyle": "-",
    "axes.spines.top": False, "axes.spines.right": False, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2, "legend.frameon": False, "legend.fontsize": 8.5,
    "lines.linewidth": 1.6, "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
})


def _save(fig, path: Path, note: str | None = None):
    if note:
        fig.text(0.01, -0.01, note, fontsize=7.2, color=MUTED, ha="left", va="top", wrap=True)
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def fig_gmst(T: pd.Series, fitted: dict, T26: tuple, T27: tuple, path: Path, labels: dict | None = None):
    fig, ax = plt.subplots(figsize=(8.2, 3.9))
    t = T.loc[1950:]
    ax.plot(t.index, t.values, color=INK2, lw=1.4, label="NOAA annual mean (observed)")
    for yr, (m, sd) in [(2026, T26), (2027, T27)]:
        ax.errorbar([yr], [m], yerr=[[1.645 * sd], [1.645 * sd]], fmt="o", ms=6, color=ORANGE, ecolor=ORANGE,
                    elinewidth=1.4, capsize=3, mec=SURFACE, mew=1.5, zorder=5,
                    label="Provisional value, 90% range" if yr == 2026 else None)
        ax.annotate(f"{yr}p {m:.2f}", (yr, m), xytext=(7, -3) if yr == 2027 else (7, -14),
                    textcoords="offset points", fontsize=8, color=INK)
    fy = list(fitted)
    ax.scatter(fy, [fitted[y] for y in fy], marker="_", s=120, lw=2.2, color=BLUE, zorder=6,
               label="Hamilton-filter expectation (shock = value minus this)")
    ax.annotate(f"2024 record {t.loc[2024]:.2f}", (2024, t.loc[2024]), xytext=(-92, 6), textcoords="offset points",
                fontsize=7.8, color=INK2)
    ax.set_ylabel("°C vs 1901-2000")
    ax.set_xlim(1949, 2032)
    ax.set_title("Global mean surface temperature, with provisional 2026-2027 values")
    ax.legend(loc="upper left")
    labels = labels or {}
    _save(fig, path, "Source: NOAA NCEI Climate at a Glance (NOAAGlobalTemp, land and ocean). " +
          "; ".join(f"{y}: {labels.get(y, 'placeholder')}" for y in (2026, 2027)) +
          ". Placeholders are replaced as NOAA publishes each annual value.")


def fig_shocks(shocks: pd.Series, prov: dict, bk_pwt: pd.Series, reference: pd.Series, ranks: dict, path: Path,
               fit_years: tuple[int, int] = (1953, 2022)):
    fig, (ax, axr) = plt.subplots(1, 2, figsize=(11.0, 4.0), gridspec_kw={"width_ratios": [3.1, 1]})
    s = shocks.loc[1953:2025]
    cols = [RED if v > 0 else BLUE for v in s.values]
    ax.bar(s.index, s.values, width=0.72, color=cols, linewidth=0, zorder=2)
    for yr, (m, sd) in prov.items():
        ax.bar([yr], [m], width=0.72, color=RED_LIGHT if m > 0 else BLUE_LIGHT, linewidth=0, zorder=2)
        ax.errorbar([yr], [m], yerr=[[1.645 * sd], [1.645 * sd]], fmt="none", ecolor=INK2, elinewidth=1.0, capsize=2.5, zorder=3)
    ax.plot(bk_pwt.index, bk_pwt.values, color=INK, lw=0.9, marker="o", ms=2.2, zorder=4,
            label="Bilal-Kaenzig published PWT shock (Berkeley Earth)")
    ax.axhline(0, color=AXIS, lw=0.8, zorder=1)
    for yr in (2023, 2024):
        v = s.loc[yr]
        ax.annotate(f"{yr}\n{v:+.2f}", (yr, v), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=7.6, color=INK)
    for yr, (m, sd) in prov.items():
        ax.annotate(f"{yr}p\n{m:+.2f}", (yr, m + 1.645 * sd if m > 0 else m - 1.645 * sd),
                    xytext=(0, 4 if m > 0 else -20), textcoords="offset points", ha="center", fontsize=7.6, color=INK)
    from matplotlib.patches import Patch
    handles = [Patch(color=RED, label="Warm shock (NOAA)"), Patch(color=BLUE, label="Cool shock (NOAA)"),
               Patch(color=RED_LIGHT, label="Provisional 2026-27, 90% range")]
    h2, l2 = ax.get_legend_handles_labels()
    ax.legend(handles=handles + h2, loc="upper left", ncol=2, fontsize=7.8)
    ax.set_ylim(-0.33, 0.52)
    ax.set_xlim(1951, 2029.5)
    ax.set_ylabel("°C (innovation vs filter expectation)")
    ax.set_title("Annual global temperature shocks, Hamilton h=2, p=2 (paper Figure II style)")
    # rank panel
    r = np.sort(reference.values)
    axr.hist(r, bins=np.arange(-0.4, 0.45, 0.05), color=AXIS, edgecolor=SURFACE, linewidth=1.5, zorder=2)
    top = axr.get_ylim()[1]
    for k, (lab, (v, pct, color)) in enumerate(sorted(ranks.items(), key=lambda kv: kv[1][0])):
        axr.axvline(v, color=color, lw=1.6, zorder=3)
        axr.annotate(f"{lab}: {pct:.0f}th pct", (v, top * (0.97 - 0.13 * k)), xytext=(-4, 0), textcoords="offset points",
                     fontsize=7.4, color=INK, va="top", ha="right",
                     bbox=dict(boxstyle="round,pad=0.15", fc=SURFACE, ec="none", alpha=0.85))
    axr.set_title(f"Rank vs {fit_years[0]}-{fit_years[1]} shocks")
    axr.set_xlabel("°C")
    axr.set_ylabel("Years")
    _save(fig, path, f"Filter fit on NOAA (dependent years {fit_years[0]}-{fit_years[1]}, the paper's window): T(t) on 1, "
                     "T(t-2), T(t-3); later years are out of sample. 2026p/2027p use provisional temperatures. Black line: "
                     "authors' series (1960-2019) for validation.")


def fig_irf(irfs: dict, path: Path, placeholder=None):
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.0, 4.0), sharey=True)
    h = np.arange(11)
    p = irfs["PWT_ts"]
    lo95, hi95 = p.band(0.05)
    lo90, hi90 = p.band(0.10)
    a.fill_between(h, lo95, hi95, color=BLUE, alpha=0.10, lw=0, label="95% bootstrap band")
    a.fill_between(h, lo90, hi90, color=BLUE, alpha=0.18, lw=0, label="90% bootstrap band")
    a.plot(h, p.theta, color=BLUE, lw=2, marker="o", ms=4, mec=SURFACE, mew=1.2, label="PWT time series (primary)")
    tr = irfs["PWT_ts_transitory"]
    a.plot(h, tr.theta, color=AQUA, lw=1.6, label="Same, one-year warmth only (Sims)")
    a.axhline(0, color=AXIS, lw=0.8)
    a.annotate(f"{p.theta[6]:.1f}% at h=6", (6, p.theta[6]), xytext=(8, -12), textcoords="offset points", fontsize=8, color=INK)
    a.set_title("Primary IRF: world GDP per capita, 1 C global shock")
    a.set_xlabel("Years after shock (h)")
    a.set_ylabel("% (100 x log) vs pre-shock path")
    a.legend(loc="lower left", fontsize=7.8)
    for key, col, lab in [("PWT_ts", BLUE, "PWT time series"), ("BU_ts", ORANGE, "BU time series"),
                          ("PWT_panel", AQUA, "PWT panel"), ("BU_panel", YELLOW, "BU panel")]:
        th = irfs[key].theta
        b.plot(h, th, color=col, lw=1.8, label=lab)
    if placeholder is not None:
        b.plot(h, placeholder, color=MUTED, lw=1.0, label="Handoff placeholder (not used)")
    b.axhline(0, color=AXIS, lw=0.8)
    b.set_xlim(-0.3, 10.3)
    b.set_title("Published IRF variants (paper Figs. III and IV)")
    b.set_xlabel("Years after shock (h)")
    b.legend(loc="lower left", fontsize=7.8)
    _save(fig, path, "Time-series IRFs re-estimated in Python from the authors' replication data (match their Stata output to 1e-6). "
                     "Panel IRFs read from replication files. Units: 100 x log points per 1 C shock.")


def fig_effect(decomp: pd.DataFrame, eff_q: pd.DataFrame, shade, path: Path,
               h1_groups=("2015-2022", "2023-2025", "2026-2027"), shade_label: str = "contract window",
               future: pd.Series | None = None):
    fig, ax = plt.subplots(figsize=(8.2, 3.9))
    yrs = np.array([int(c) for c in decomp.columns if str(c).isdigit()])
    vals = decomp[[c for c in decomp.columns if str(c).isdigit()]]
    groups = [("2015-2022", [t for t in vals.index if t <= 2022], AQUA),
              ("2023-2025", [t for t in vals.index if 2023 <= t <= 2025], ORANGE),
              ("2026-2027", [t for t in vals.index if t >= 2026], MAGENTA)]
    ax.axvspan(shade[0] - 0.5, shade[1] + 0.5, color=GRID, alpha=0.45, lw=0, zorder=0)
    band_col = MAGENTA if tuple(h1_groups) == ("2026-2027",) else BLUE
    ax.fill_between(eff_q.index, eff_q["q05"], eff_q["q95"], color=band_col, alpha=0.12, lw=0,
                    label="Tested prediction, 90% range")
    fut = None if future is None else future.reindex(yrs).fillna(0.0).values
    total = vals.sum().values + (0 if fut is None else fut)
    ax.plot(yrs, total, color=BLUE, lw=2.2,
            label="All shocks" + ("" if fut is None else ", incl. simulated 2028+"))
    for key, rows, col in groups:
        v = vals.loc[rows].sum().values
        inside = key in h1_groups
        lab = f"Shocks {key}" + ("" if inside else " (not tested)")
        ax.plot(yrs, v, color=col, lw=2.0 if inside else 1.3, label=lab)
        ax.annotate(f"{key}{' (H1)' if inside else ''}", (yrs[-1], v[-1]), xytext=(5, 0), textcoords="offset points",
                    fontsize=7.6, color=INK2, va="center")
    if fut is not None:
        ax.plot(yrs, fut, color=YELLOW, lw=2.0, ls=(0, (3, 2)), label="Simulated 2028+ shocks (mean)")
        ax.annotate("2028+ (sim.)", (yrs[-1], fut[-1]), xytext=(5, 0), textcoords="offset points",
                    fontsize=7.6, color=INK2, va="center")
    ax.axhline(0, color=AXIS, lw=0.8)
    ax.text(shade[1] + 0.4, ax.get_ylim()[1] - 0.1, shade_label, fontsize=7.8, color=INK2, ha="right", va="top")
    ax.set_xlim(2025.6, yrs[-1] + 2.6)
    ax.set_xticks(range(2026, int(yrs[-1]) + 1, 2))
    ax.set_ylabel("% vs no-effect path (2025 level)")
    everything = len(h1_groups) == len(groups)
    ax.set_title("What B&K imply for world GDP per capita, by contributing shocks" if everything
                 else "What B&K imply for world GDP per capita, and the part the contract tests", pad=52)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.01), ncol=3, fontsize=7.6, borderaxespad=0.2,
              columnspacing=1.2, handlelength=2.2)
    _save(fig, path, "Innovation composition: theta(h) applied to the part of each shock not predicted by the two prior shocks "
                     "(the variation the LP coefficient measures). Effects already in the 2025 level are removed. "
                     "Simulated 2028+ shocks: mean over ENSO-conditioned paths.")


def fig_paths(hist: pd.Series, bands: pd.DataFrame, base_year: int, window, c: float, path: Path,
              note: str | None = None, ref: str = "no-effect path"):
    """GDP per capita paths under each hypothesis; deviations are measured from ``ref`` (the
    baseline the statistic subtracts: the IMF projection, or a frozen drift)."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.0, 4.0))
    yrs = bands.index.values
    a.plot(hist.loc[2000:].index, hist.loc[2000:].values / 1000, color=INK2, lw=1.6, label="WDI observed")
    for lab, col in (("H0", BLUE), ("H1", ORANGE)):
        a.fill_between(yrs, bands[f"{lab}_level_q10"] / 1000, bands[f"{lab}_level_q90"] / 1000, color=col, alpha=0.13, lw=0)
        a.plot(yrs, bands[f"{lab}_level_q50"] / 1000, color=col, lw=2,
               label={"H0": "H0 no temperature effect: median, 10-90%", "H1": "H1 B&K effect: median, 10-90%"}[lab])
    a.plot(yrs, bands["baseline_level"] / 1000, color=INK2, lw=0.9, alpha=0.9, label=ref[0].upper() + ref[1:])
    a.set_ylabel("Thousand 2021 PPP $ per person")
    a.set_title("World real GDP per capita (WDI NY.GDP.PCAP.PP.KD)")
    a.legend(loc="upper left", fontsize=7.8)
    sel = yrs >= base_year
    yb = yrs[sel]
    bb = bands.loc[sel]
    b.axvspan(window[0] - 0.5, window[1] + 0.5, color=GRID, alpha=0.45, lw=0, zorder=0)
    for lab, col in (("H0", BLUE), ("H1", ORANGE)):
        b.fill_between(yb, bb[f"{lab}_devb_q05"], bb[f"{lab}_devb_q95"], color=col, alpha=0.08, lw=0)
        b.fill_between(yb, bb[f"{lab}_devb_q10"], bb[f"{lab}_devb_q90"], color=col, alpha=0.13, lw=0)
        b.plot(yb, bb[f"{lab}_devb_q50"], color=col, lw=2, label=f"{lab} median (5-95% and 10-90% bands)")
    b.axhline(0, color=AXIS, lw=0.8)
    b.hlines(c, window[0] - 0.5, window[1] + 0.5, color=INK, lw=1.6, zorder=4)
    b.annotate(f"c = {c:.2f}%\nYes above, No at or below", (window[1] + 0.5, c), xytext=(4, 0),
               textcoords="offset points", fontsize=7.8, color=INK, va="center",
               bbox=dict(boxstyle="round,pad=0.25", fc=SURFACE, ec="none", alpha=0.85))
    b.set_ylabel(f"% vs {ref}, re-based to {base_year}")
    b.set_title(f"Deviation from the {ref}, from the {base_year} level")
    b.legend(loc="lower left", fontsize=7.8)
    _save(fig, path, note or "H0: no-effect path with its spread, projected from the last observed year (2025). H1 adds the "
                             "B&K effect with IRF and temperature uncertainty (common random numbers).")


def fig_outcome(m0: np.ndarray, m1: np.ndarray, oc, xlabel: str, path: Path):
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.0, 3.9), gridspec_kw={"width_ratios": [1.7, 1]})
    from scipy.stats import gaussian_kde
    lo, hi = np.quantile(np.r_[m0, m1], [0.001, 0.999])
    ctr = np.linspace(lo, hi, 300)
    rs = np.random.default_rng(0)
    for m, col, lab in ((m0, BLUE, "H0: no temperature effect"), (m1, ORANGE, "H1: B&K IRF")):
        dens = gaussian_kde(rs.choice(m, size=min(len(m), 20000), replace=False))(ctr)
        a.plot(ctr, dens, color=col, lw=2, label=lab)
        sel = ctr <= oc.threshold if col == BLUE else ctr > oc.threshold
        a.fill_between(ctr[sel], 0, dens[sel], color=col, alpha=0.18, lw=0)
    a.axvline(oc.threshold, color=INK, lw=1.2)
    a.set_ylim(0, a.get_ylim()[1] * 1.18)
    a.annotate(f"c = {oc.threshold:.2f}%: No if M <= c, Yes above", (oc.threshold, a.get_ylim()[1] * 0.97),
               xytext=(-5, 0), textcoords="offset points", fontsize=8, color=INK, va="top", ha="right")
    a.text(0.99, 0.80, f"Sensitivity {oc.sensitivity:.2f}\nFalse positive {oc.false_positive:.2f}\n"
                       f"Youden J {oc.youden_j:.2f}\nOverlap {oc.overlap:.2f}", transform=a.transAxes, ha="right",
           va="top", fontsize=8, color=INK2)
    a.set_xlabel(xlabel)
    a.set_ylabel("Density")
    a.set_title("Contract statistic under each hypothesis")
    a.legend(loc="center left", fontsize=7.8)
    qs = np.quantile(np.r_[m0, m1], np.linspace(0, 1, 401))
    tpr = [(m1 <= q).mean() for q in qs]
    fpr = [(m0 <= q).mean() for q in qs]
    b.plot(fpr, tpr, color=INK2, lw=1.8)
    b.plot([0, 1], [0, 1], color=AXIS, lw=0.8)
    b.scatter([oc.false_positive], [oc.sensitivity], s=46, color=ORANGE, edgecolor=SURFACE, linewidth=1.5, zorder=4)
    b.annotate("Youden point", (oc.false_positive, oc.sensitivity), xytext=(8, -12), textcoords="offset points", fontsize=8, color=INK)
    b.set_xlabel("False positive rate P_H0(M <= c)")
    b.set_ylabel("Sensitivity P_H1(M <= c)")
    b.set_title(f"ROC (AUC {oc.auc:.2f})")
    b.set_xlim(0, 1); b.set_ylim(0, 1.01)
    _save(fig, path)


def fig_grid(grid: pd.DataFrame, T27: tuple, T26_mean: float, record_2024: float, path: Path,
             t26_label: str = "placeholder"):
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.0, 3.8), sharex=True)
    for ax in (a, b):
        ax.axvspan(T27[0] - T27[1], T27[0] + T27[1], color=GRID, alpha=0.5, lw=0, zorder=0)
        ax.axvline(record_2024, color=AXIS, lw=0.9)
    g = grid[np.isclose(grid.T2026, T26_mean)]
    others = sorted(set(grid.T2026) - {g.T2026.iloc[0]})
    a.plot(g.T2027, g.threshold_growth_pp, color=BLUE, lw=2, label=f"T2026 = {T26_mean:.2f} ({t26_label})")
    b.plot(g.T2027, g.youden_j, color=BLUE, lw=2, label=f"T2026 = {T26_mean:.2f} ({t26_label})")
    for t26, col in zip(others, (AQUA, ORANGE)):
        gg = grid[np.isclose(grid.T2026, t26)]
        a.plot(gg.T2027, gg.threshold_growth_pp, color=col, lw=1.4, label=f"T2026 = {t26:.2f}")
        b.plot(gg.T2027, gg.youden_j, color=col, lw=1.4, label=f"T2026 = {t26:.2f}")
    a.set_ylabel("Cutoff: average growth, % a year")
    a.set_title("Cutoff as a function of the realised 2027 temperature")
    b.set_ylabel("Youden J")
    b.set_title("Discriminating power")
    for ax in (a, b):
        ax.set_xlabel("NOAA 2027 annual anomaly (°C vs 1901-2000)")
        ax.legend(loc="best", fontsize=7.8)
    a.annotate("2024 record", (record_2024, a.get_ylim()[0]), xytext=(3, 4), textcoords="offset points", fontsize=7.6, color=INK2)
    _save(fig, path, "Shaded: provisional 2027 forecast (mean +/- 1 sd). Each point re-runs the primary design with the 2026-27 "
                     "temperatures fixed: the cutoff a contract written after NOAA publishes 2027 would use.")


def fig_variants(tab: pd.DataFrame, path: Path):
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.0, 0.32 * len(tab) + 1.4), sharey=True)
    y = np.arange(len(tab))[::-1]
    prim = tab.variant == "primary"
    for ax, col, xlab in ((a, "mean_shift", "H1 minus H0 mean of M (%)"), (b, "youden_j", "Youden J")):
        ax.hlines(y, 0, tab[col], color=AXIS, lw=0.8)
        ax.scatter(tab[col], y, s=34, color=np.where(prim, ORANGE, BLUE), edgecolor=SURFACE, linewidth=1.2, zorder=3)
        ax.axvline(tab.loc[prim, col].iloc[0], color=ORANGE, lw=0.8, alpha=0.6)
        ax.set_xlabel(xlab)
        ax.grid(axis="y", visible=False)
    a.set_yticks(y)
    a.set_yticklabels(tab.variant, fontsize=7.8)
    a.set_title("Predicted effect by design variant")
    b.set_title("Contract power by design variant")
    _save(fig, path, "One-at-a-time changes from the primary design (orange). Each variant re-optimises its own Youden threshold.")


def fig_horizon(scan: pd.DataFrame, selected: int, path: Path, base_year: int):
    """Average growth from the base year under each hypothesis, the cutoff and the separation, by end year."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.0, 3.9))
    x = scan.end_year.values
    for lab, col, name in (("h0", BLUE, "No temperature effect"), ("h1", ORANGE, "Paper's estimate")):
        a.fill_between(x, scan[f"growth_{lab}_q10"], scan[f"growth_{lab}_q90"], color=col, alpha=0.13, lw=0)
        a.plot(x, scan[f"growth_{lab}_q50"], color=col, lw=2, marker="o", ms=4.5, mec=SURFACE, mew=1.0,
               label=f"{name}: median and 10-90%")
    a.plot(x, scan.growth_bar, color=INK, lw=1.4, ls=(0, (3, 2)), label="Cutoff that best separates them")
    a.axvline(selected, color=AXIS, lw=0.9, zorder=0)
    a.set_title(f"Average growth from {base_year} to the end year")
    a.set_ylabel("World GDP per capita growth, % a year")
    a.legend(loc="lower right", fontsize=7.6)
    b.plot(x, scan.youden_j, color=BLUE, lw=2, marker="o", ms=5, mec=SURFACE, mew=1.2, label="Primary design")
    if "youden_j_no_future" in scan:
        b.plot(x, scan.youden_j_no_future, color=INK2, lw=1.3, ls=(0, (3, 2)),
               label="Without simulated 2028+ temperatures")
    j = scan.set_index("end_year").youden_j
    b.scatter([selected], [j.loc[selected]], s=90, color=ORANGE, edgecolor=SURFACE, linewidth=1.5, zorder=4)
    b.annotate(f"selected: {selected}", (selected, j.loc[selected]), xytext=(0, 9), textcoords="offset points",
               ha="center", va="bottom", fontsize=8.2, color=INK)
    b.set_ylim(top=max(b.get_ylim()[1], float(j.max()) + 0.06))
    b.set_title("Separation between the two predictions")
    b.set_ylabel("Youden J (0 = none, 1 = perfect)")
    b.legend(loc="lower left", fontsize=7.6)
    for ax in (a, b):
        ax.set_xticks(x)
        ax.set_xlabel(f"End year (growth measured from {base_year})")
    _save(fig, path, f"Each end year re-runs the primary design (base {base_year}; IMF baseline with its error spread, simulated post-2027 "
                     "temperatures, the paper's world-GDP response). Rule: the end year with the highest J, chosen before "
                     "listing and using no GDP data after 2025.")


def fig_baseline(wdi_growth: pd.Series, baseline, drift_2000_2019: float, path: Path, last_year: int,
                 band: pd.DataFrame | None = None, error_source: str = "", expected: pd.Series | None = None):
    """Observed world GDP per capita growth, the IMF projection, and the no-effect path built on it
    (``expected``: the projection plus the IMF's average historical miss at each lead)."""
    fig, ax = plt.subplots(figsize=(8.2, 3.6))
    if band is not None:
        bb = band.loc[:last_year]
        ax.fill_between(bb.index, bb.q10, bb.q90, color=BLUE, alpha=0.12, lw=0, zorder=1,
                        label="10-90% range of a single year (forecast-error spread)")
    h = wdi_growth.loc[1991:]
    ax.bar(h.index, h.values, width=0.72, color=AXIS, linewidth=0, zorder=2, label="Observed (WDI, PPP per capita)")
    g = baseline.growth.loc[2026:last_year]
    proj = g.loc[:baseline.projected_through]
    held = g.loc[baseline.projected_through:]
    imf_col = INK2 if expected is not None else BLUE
    ax.plot(proj.index, proj.values, color=imf_col, lw=1.8, marker="o", ms=4.0, mec=SURFACE, mew=1.0, zorder=3,
            label="IMF projection (WEO, WDI units)")
    ax.plot(held.index, held.values, color=imf_col, lw=1.6, ls=(0, (3, 2)), zorder=3,
            label="Held at the last projected rate")
    if expected is not None:
        ex = expected.loc[2026:last_year]
        ax.plot(ex.index, ex.values, color=BLUE, lw=2.2, marker="o", ms=4.5, mec=SURFACE, mew=1.0, zorder=4,
                label="No-effect path: IMF projection plus its average past miss")
    ax.axhline(drift_2000_2019, color=MUTED, lw=0.9, ls=(0, (1, 2)), zorder=1,
               label=f"2000-2019 average ({drift_2000_2019:.2f}%)")
    ax.axhline(0, color=AXIS, lw=0.8)
    ax.set_ylabel("Growth, % a year (100 x log)")
    ax.set_title("World GDP per capita growth: history, the IMF projection and the no-effect path")
    ax.set_ylim(-7.4, max(6.2, ax.get_ylim()[1]))
    ax.legend(loc="lower left", fontsize=7.6, ncol=2, columnspacing=1.4)
    _save(fig, path, f"{baseline.vintage}. IMF world real GDP growth minus IMF world population growth, plus the "
                     f"1991-2025 mean gap to the WDI series ({baseline.wdi_gap:+.2f} pp). Spread: {error_source}.")


def fig_future_temps(shock_q: pd.DataFrame, eff_with: pd.Series, eff_without: pd.Series, path: Path,
                     base_year: int = 2026):
    """Simulated post-2027 temperature shocks and what they do to the paper's prediction."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.0, 3.8))
    yr = shock_q.index.values
    a.fill_between(yr, shock_q.q10, shock_q.q90, color=BLUE_LIGHT, alpha=0.6, lw=0, label="10-90% range")
    a.plot(yr, shock_q.mean_, color=BLUE, lw=2, marker="o", ms=4.5, mec=SURFACE, mew=1.0, label="Mean")
    a.axhline(0, color=AXIS, lw=0.8)
    a.set_title("Simulated global temperature shocks after 2027")
    a.set_ylabel("°C (shock, NOAA)")
    a.legend(loc="lower right", fontsize=7.8)
    b.plot(eff_without.index, eff_without.values, color=INK2, lw=1.6, ls=(0, (3, 2)),
           label="Shocks through 2027 only")
    b.plot(eff_with.index, eff_with.values, color=ORANGE, lw=2.2, label="Plus simulated 2028+ shocks")
    b.axhline(0, color=AXIS, lw=0.8)
    b.set_title("Paper's predicted effect on world GDP per capita")
    b.set_ylabel(f"% vs no-effect path, re-based to {base_year}")
    b.legend(loc="lower left", fontsize=7.8)
    _save(fig, path, "Strong El Niños are usually followed by cooler years: after a strong 2027 winter each path replays "
                     "the winters that followed one of the seven strong El Niños since 1950. Shocks are measured with "
                     "the paper's filter (fitted through 2022), which still counts a lasting warmer level as above "
                     "trend, so the usual cooling is partly or fully offset.")


def fig_bins(bins: pd.DataFrame, xlabel: str, path: Path):
    """The three conditional contracts: outcome distributions and cutoff by 2027 temperature bin."""
    from scipy.stats import gaussian_kde
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.5), sharey=True)
    rs = np.random.default_rng(0)
    lo = min(np.quantile(r.sim.m1, 0.002) for r in bins.itertuples())
    hi = max(np.quantile(r.sim.m0, 0.998) for r in bins.itertuples())
    ctr = np.linspace(lo, hi, 300)
    dens = [[gaussian_kde(rs.choice(m, size=min(len(m), 20000), replace=False))(ctr) for m in (r.sim.m0, r.sim.m1)]
            for r in bins.itertuples()]
    top = 1.3 * max(d.max() for pair in dens for d in pair)
    for ax, r, (d0, d1) in zip(axes, bins.itertuples(), dens):
        ax.plot(ctr, d0, color=BLUE, lw=1.8, label="No temperature effect")
        ax.plot(ctr, d1, color=ORANGE, lw=1.8, label="Paper's estimate")
        ax.axvline(r.threshold, color=INK, lw=1.1)
        cond = getattr(r, "condition", None)
        if cond is None:
            cond = (f"below {r.upper:.2f} C" if not np.isfinite(r.lower) else
                    f"{r.lower:.2f}-{r.upper:.2f} C" if np.isfinite(r.upper) else f"above {r.lower:.2f} C")
        ax.set_title(f"{r.bin.capitalize()} 2027: {cond.replace(' C', ' °C')}", fontsize=9.6)
        ax.set_ylim(0, top)
        ax.text(r.threshold - 0.35, top * 0.97, f"cutoff {r.growth_bar:.2f}%/yr\nJ {r.youden_j:.2f}",
                ha="right", va="top", fontsize=7.8, color=INK2)
    axes[0].set_ylabel("Density")
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower right", bbox_to_anchor=(1.0, 0.985), ncol=2, fontsize=8)
    axes[1].set_xlabel(xlabel)
    _save(fig, path, "One conditional contract per 2027 bin (bins split halfway between the 20th, 50th and 80th "
                     "percentiles of the 2027 forecast; stated on NOAA's two-decimal value). In each, 2027 is drawn within "
                     "the bin; the vertical line is the bin's cutoff on growth minus the IMF baseline.")
