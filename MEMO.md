# Bilal–Känzig × the 2026–27 El Niño: a prospective test and forecast-contract design

**Prepared:** 17 October 2026 · **Revised:** 23 October 2026 (NOAA temperature record), **30 October 2026** (conditional contracts, growth from 2026, an end-year rule, the IMF baseline with its own forecast record, simulated post-2027 temperatures, the paper's own filter window) and 31 October 2026 (the paper's GDP-weighted panel and two checks of the paper-side spread, as sensitivities) · **Status:** draft for comment, refreshed monthly · **Listing:** right after NOAA's 2026 annual value (mid-Jan 2027) · **Code:** `bk_elnino/` + `run_analysis.py` · **Outputs:** `outputs/`

Everything below was produced by `python -I run_analysis.py` and written by `build_docs.py`. Every number has a CSV twin in `outputs/` and a design label in `outputs/results.json`.

- **Nothing is locked yet.** The terms freeze at the refresh that follows NOAA's 2026 annual value, and the conditional contracts list right after.
- **2026 and 2027 temperatures are placeholders** (2026: 1.215 ± 0.022 °C; 2027: 1.495 ± 0.097 °C). Each monthly refresh replaces them with whatever NOAA has published.

---

## Bottom line

1. **The handoff's shock formula was wrong in a way that matters.** The authors' shock series is exactly `T_t − (a + b₂T_{t−2} + b₃T_{t−3})`: two lagged regressors for h=2, p=2, with zero weight on `T_{t−4}`. The paper's Eq. (1) is typeset with p+1 lags, but the data the IRF was estimated on uses p.
2. **The headline −14% / −18% numbers are panel estimates (paper Fig. IV), not the world-GDP time series.** The world real GDP per capita IRF (Fig. III), which fits a world-GDP contract, peaks at **−12.1% at h=6 (PWT)** per 1 °C shock. The Python local projections reproduce the authors' Stata estimates to ~1e-7.
3. **The record shock already happened in 2024:** +0.35 °C with NOAA, the largest since at least 1953. 2023 gave +0.22 °C. The 2027 placeholder implies a shock of +0.29 ± 0.10 °C.
4. **What the paper predicts.** Its published PWT response implies that world per-capita growth from 2026 to 2031 falls **5.9 points** short of the no-effect path (90% range −10.2 to −2.1), net of the part of the IMF's past misses the paper itself puts down to temperature. That is about 0.5% a year instead of 1.6%. The 2023–25 and 2026–27 shocks contribute −2.6 and −3.8 points; the simulated years after 2027 change it by −0.05.
5. **The proposal is three conditional contracts** on NOAA's 2027 temperature, listed right after NOAA's 2026 value. Each asks whether world GDP per person will grow by more than a strike, on average, from 2026 to 2031:
   - cool 2027 (1.45 °C or lower): 1.2%/yr, J 0.63;
   - central (1.46 to 1.53 °C): 1.1%/yr, J 0.69;
   - warm (1.54 °C or higher): 1.0%/yr, J 0.74.
   - The matching contract converts to an unconditional one when NOAA publishes 2027; the others are refunded.
6. **Moderate, not decisive, power.** Unconditionally the cutoff is 1.09% a year. The contract resolves No (the paper's outcome) 81% of the time if the paper is right, and Yes 87% of the time if temperature shocks have no effect (J 0.68, AUC 0.91). A Yes contract would be worth about $0.19 if the paper is right and $0.87 if not, so its price maps onto the credence participants give the paper.
7. **The end year, 2031, is chosen by a rule:** the highest separation (J) among 2028–2037, using no GDP data after 2025. Separation rises while the paper's response deepens and falls as background-growth uncertainty accumulates and the earlier shocks recover; 2030 comes next (J 0.67 against 0.68).
8. **Background growth is the biggest uncertainty.** The IMF projection puts per-capita growth at 2.26% a year over 2027–2031, but its forecasts at these horizons have run high: since 1990, growth came in 3.1 points below them over five-year windows, on average, and below them in 27 of 31 windows. Keeping that miss, the no-effect expectation is 1.65% a year. Over five years, background growth has an sd of 2.6 points, against the paper's predicted shortfall of 5.9.
9. **Growth is measured from 2026**, the last full year before listing, so none of the measured growth is known at listing. Starting at 2027, as in the drafts until 30 Oct, gives J 0.60.
10. **The temperature record matters.** Under the 23 Oct design, NASA GISTEMP (the proposal until 22 Oct) gave a 4.5-point prediction against NOAA's 3.6. NOAA was chosen because the paper uses it and reports that its Berkeley Earth measure tracks NOAA almost perfectly.

---

## 1. Corrections to the handoff

| # | Handoff said | Evidence | What the code does |
|---|---|---|---|
| 1 | Regress `T_t` on `T_{t−2}, T_{t−3}, T_{t−4}` for h=2, p=2 | Exact regression of the authors' `gtmp_bkly_aw_dtfe2` on `[1, T_t, T_{t−2}, T_{t−3}, T_{t−4}]` returns weights `[−0.0387, 1, −0.5196, −0.4608, 0.0000]` with zero residual. The p+1-lag version correlates only 0.91 with the authors' series. Curtin and Burgess (2026, App. H) independently rebuild the shocks with the same two lags. | `hamilton.lag_set(h, p)` = lags h…h+p−1 (`bk_data`). The literal Eq. (1) reading is kept as `paper_eq1` for sensitivity. |
| 2 | Published IRF peaks at −14% (h=6, PWT) and −18% (h=5, BU) | Those are the country-panel averages (paper Fig. IV). The world-GDP time-series IRF (Fig. III) is −12.1% (h=6) and −16.8% (h=6). | Primary = time-series PWT IRF. Panel IRFs are labelled sensitivities. |
| 3 | Provisional 2023/2024 shocks of +0.174 / +0.269 | Not reproducible from either convention. | NOAA h=2, p=2: **+0.215 / +0.353**. |
| 4 | Apply `θ_h` to raw shocks: Σ θ_{t−τ} s_τ | The authors' LP controls for s_{t−1}, s_{t−2}, so θ_h is the response to the part of s_t not predicted by the two prior shocks, including the predictable follow-on shocks. Applying θ to raw consecutive shocks double counts. | Primary applies θ to innovations, estimated on the LP's own sample. The raw formula is a labelled variant. |
| 5 | Primary test on the incremental 2026–27 component | The realised outcome will contain the effects of the 2023–25 shocks too (under the paper). A prediction that omits them is mis-specified for the statistic that will be resolved. | The paper's side = all shocks with effects in the measured years, plus simulated post-2027 shocks. |
| 6 | Null drift from 1991–2019 | 1991–2000 per-capita PPP growth averaged 1.25%/yr (post-Soviet collapse); 2001–10 2.28; 2011–19 2.19; 2022–25 2.44. | Since 30 Oct the no-effect path follows the IMF projection. Frozen 2000–2019 and 1991–2019 drifts are sensitivities. |

## 2. Data (vintages in `outputs/results.json → vintages`)

| Series | Source | Use |
|---|---|---|
| Global mean temperature (contract record) | NOAA NCEI Climate at a Glance (NOAAGlobalTemp), global land and ocean, °C vs 1901–2000, annual and monthly | Shocks, placeholders, the conditioning event |
| Comparison and fallback | NASA GISTEMP v4 `GLB.Ts+dSST.csv`, J–D | Fallback for the conditioning event |
| Validation temperature | Berkeley Earth Land+Ocean summary (ends 2024) | Reproduces the authors' shocks |
| ENSO | CPC ONI and RONI | 2027 forecast; post-2027 simulation |
| Outcome | World Bank WDI `NY.GDP.PCAP.PP.KD`, WLD (constant 2021 PPP $) | Settlement; 2025 = $21,914 |
| No-effect baseline | IMF WEO October 2026, DataMapper `NGDP_RPCH` and `LP`, WEOWORLD | Baseline per-capita growth |
| Spread of background growth | IMF Historical WEO Forecasts Database (`WEOhistorical.xlsx`, sheet `ngdp_rpch`), October vintages 1990–2020 | Forecast-error paths, including the average miss |
| IRF and shocks | `dkaenzig/micc_replication`; `dkaenzig/global-temperature-shocks` | Response, validation |

## 3. Temperature shocks

**Filter (frozen):** `T(t) = 0.0384 + 0.4961 T(t-2) + 0.4850 T(t-3)`, fitted on NOAA over the paper's window (dependent years 1953–2022), residual sd 0.124 °C. Later years are out of sample.

| Check | Result |
|---|---|
| NOAA shocks (contract) vs authors' published PWT shocks, 1960–2019 | corr 0.990 |
| GISTEMP shocks vs authors' published PWT shocks, 1960–2019 | corr 0.982 |
| NOAA (p=6) vs authors' BU shocks | corr 0.958 |
| p+1-lag (Eq. 1 literal) vs authors' shock | corr 0.908 (rejected) |

| Year | NOAA T (°C) | Filter expectation | Shock s | Innovation u | Rank among 1953–2022 | Status |
|---|---|---|---|---|---|---|
| 2023 | 1.170 | 0.955 | +0.215 | +0.221 | 2 | observed |
| 2024 | 1.250 | 0.897 | +0.353 | +0.217 | 1 | observed |
| 2025 | 1.120 | 1.051 | +0.069 | +0.014 | 25 | observed |
| 2026 | 1.215 ± 0.022 | 1.226 | −0.011 | +0.088 | 36 | nowcast (9 months observed, onset analogs) |
| 2027 | 1.495 ± 0.097 | 1.200 | +0.294 | +0.316 | 1 | ENSO regression (0 months observed) |

Because the h=2 filter predicts 2026 from 2024 and 2023 (both record-warm), the 2026–27 El Niño has to beat an already high expectation to register as a shock. 2024 was predicted from 2022 and 2021 (La Niña years), which is why its shock is the record.

## 4. The impulse response

- **Primary:** the PWT time-series LP (paper Fig. III), re-estimated in Python from the authors' data: θ = −1.8, −2.5, −4.6, −6.5, −9.1, −11.8, −12.1, −11.3, −10.9, −5.6, −6.9 for h = 0…10 (100×log points per 1 °C).
- **Uncertainty:** 4,000 joint draws from the authors' wild-bootstrap procedure, re-centred on the point estimate.
- **Beyond h=10** θ is held at θ₁₀ (the paper: responses do not fully mean-revert). Truncation to 0 is a variant.
- **Mismatches accepted:** the IRF is estimated on PWT world GDP and Berkeley Earth shocks, and applied to WDI PPP world GDP and NOAA shocks. The authors' panel estimate with WDI GDP is close to the PWT one, and the shock series track each other closely.

## 5. From shocks to a GDP prediction

`E_t = Σ_τ θ_{min(t−τ,10)} · u_τ − Σ_{τ≤2025} θ_{min(2025−τ,10)} · u_τ`. The second sum removes effects already in the observed 2025 level. The contract measures growth from 2026 to 2031, so the paper's prediction is `E_2031 − E_2026` (point IRF, central placeholders):

| Contributing shocks | Contribution (points) |
|---|---|
| 2015–2022 | −0.5 |
| 2023–2025 | −2.6 |
| 2026–2027 (El Niño) | −3.8 |
| 2028–2031 (simulated, cooler years after the El Niño) | 0.0 |
| **Total** | **−6.9** |

## 6. Temperatures after 2027

Simulated 2028+ shocks are part of the paper's prediction: under its response, any later shock moves GDP too. They enter through their innovations, the part the two prior shocks do not predict, so the typical follow-on path already inside θ is not counted twice.

- **Model:** winter RONI after a strong El Niño: replay of 7 analogs [1958, 1966, 1973, 1983, 1992, 1998, 2016]; otherwise AR(2) R_y = +0.088 −0.037 R_(y-1) −0.226 R_(y-2); shock = ENSO regression + resampled residual (sd 0.108 °C, n=73, volcanic years included).
- **Mean simulated shocks:** 2028 +0.08, 2029 −0.09, 2030 +0.08, 2031 +0.09 °C.
- **Effect:** −0.05 points on 2026–2031 growth (90% range −1.9 to +1.9). Without them the cutoff would be 1.10%/yr and J 0.69.
- The cutoffs are fixed in advance; realised 2028–30 temperatures do not change them.

## 7. The no-effect baseline

- **Path:** IMF WEO October 2026 world real GDP growth minus world population growth, plus the 1991–2025 mean WDI gap (−0.07 points; correlation 0.99). Per-capita growth 2027 2.42, 2028 2.34, 2029 2.26, 2030 2.15, 2031 2.14; mean 2.26%/yr. The 2031 rate is held beyond 2031.
- **Spread:** whole historical forecast-error paths, shrunk toward their mean and mixed with Gaussian noise of the same covariance (a smoothed bootstrap), so multi-year misses keep their persistence and the distribution is continuous.
- The errors are those of the October World Economic Outlooks of 1990–2020 (31 forecasts, IMF Historical WEO Forecasts Database), measured against the October 2026 WEO's estimates of what happened. Years past the IMF's six-year horizon are drawn independently from its six-year-ahead errors (misses in neighbouring years are close to uncorrelated). **The IMF's average miss is kept:** over five-year windows like 2027–2031, world growth came in 3.1 points in total below the IMF's forecast on average (about 0.6 a year; sd 2.7), and below it in 27 of 31 windows. So with no temperature effect, growth is expected to average 1.65% a year, not the IMF's 2.26%. In the paper's world the background leaves out the part of those misses that the paper's own estimates put down to temperature shocks (0.9 of the 3.1 points on average), because its climate damage enters through the shocks since 2015 instead.
- **Result:** under no effect, M has sd 2.62; average growth 2026–2031 has a 10–90% range of 1.0–2.3%/yr.
- **Backtests of a frozen 20-year drift:** 8-year misses of about ±4.3 points (WDI USD), ±7.8 (PWT) and ±10.6 (Barro–Ursúa, including wars and the Depression). `outputs/null_backtest.csv` has the contract horizon.

## 8. The end year

Rule: the end year in 2028–2037 with the highest J (two decimals; ties to the earlier year), chosen before listing and using no GDP data after 2025. J rewards a contract that resolves in line with whichever view is true, so choosing the end year this way favours neither side.

| End year | J | Paper's predicted shortfall (points) | Spread of background growth (sd, points) | Cutoff (%/yr) |
|---|---|---|---|---|
| 2028 | 0.45 | −2.3 | 2.1 | 1.30 |
| 2029 | 0.54 | −3.5 | 2.3 | 1.22 |
| 2030 | 0.67 | −5.1 | 2.3 | 1.09 |
| **2031** | 0.68 | −5.9 | 2.6 | 1.09 |
| 2032 | 0.57 | −5.6 | 3.1 | 1.17 |
| 2033 | 0.46 | −5.0 | 3.5 | 1.22 |
| 2034 | 0.43 | −5.3 | 3.9 | 1.19 |
| 2035 | 0.41 | −5.3 | 4.3 | 1.21 |
| 2036 | 0.32 | −4.3 | 4.6 | 1.21 |
| 2037 | 0.35 | −5.2 | 4.9 | 1.20 |

## 9. The conditional contracts

| Condition (NOAA 2027) | Chance today | Predicted shortfall 2026–2031 (points) | Cutoff (%/yr) | Strike | P(Yes) if no effect | P(Yes) if paper right | J |
|---|---|---|---|---|---|---|---|
| Cool: 1.45 °C or lower | 34% | −5.1 | 1.16 | **1.2** | 82% | 20% | 0.63 |
| Central: 1.46 to 1.53 °C | 33% | −6.0 | 1.10 | **1.1** | 87% | 18% | 0.69 |
| Warm: 1.54 °C or higher | 34% | −6.9 | 1.04 | **1.0** | 90% | 16% | 0.74 |
| No condition (all 2027 outcomes) | 100% | −5.9 | 1.09 | – | 87% | 19% | 0.68 |

Strike ladder (P(Yes) if no effect / if the paper is right; headline strikes in bold):

| Strike | Cool: P(Yes) no effect / paper | Central | Warm |
|---|---|---|---|
| 0.1% | 100% / 79% | 100% / 70% | 100% / 60% |
| 0.3% | 99% / 70% | 99% / 59% | 99% / 49% |
| 0.5% | 98% / 58% | 98% / 48% | 98% / 38% |
| 0.7% | 96% / 47% | 96% / 37% | 96% / 28% |
| 0.9% | 92% / 35% | 92% / 26% | 92% / 20% |
| 1.0% | 90% / 29% | 90% / 22% | **90% / 16%** |
| 1.1% | 87% / 24% | **87% / 18%** | 87% / 13% |
| 1.2% | **82% / 20%** | 82% / 14% | 82% / 10% |
| 1.3% | 77% / 16% | 77% / 11% | 77% / 8% |
| 1.5% | 62% / 10% | 62% / 7% | 62% / 5% |
| 1.7% | 45% / 6% | 45% / 4% | 45% / 3% |
| 1.9% | 29% / 3% | 29% / 2% | 29% / 1% |
| 2.1% | 18% / 2% | 18% / 1% | 18% / 1% |

Fair price of a $1 Yes contract (unconditional cutoff) for a participant who puts probability p on the paper being right: p = 0.1: $0.80; p = 0.25: $0.70; p = 0.5: $0.53; p = 0.75: $0.36; p = 0.9: $0.26.

## 10. Robustness (one change at a time, each with its own cutoff)

| Variant | Paper's shift (points) | Cutoff (%/yr) | J |
|---|---|---|---|
| **Proposed (conditional design, growth 2026→2031)** | −5.9 | 1.09 | 0.68 |
| 2023–27 spikes only | −5.5 | 1.13 | 0.65 |
| 2026–27 El Niño only | −2.9 | 1.29 | 0.41 |
| Raw-shock composition (handoff formula) | −6.6 | 1.06 | 0.71 |
| 2026–27 only + raw shocks (handoff, literally) | −1.9 | 1.34 | 0.28 |
| BU time-series IRF | −3.5 | 1.19 | 0.43 |
| PWT panel IRF (paper's 14%) | −6.3 | 1.08 | 0.70 |
| PWT panel IRF, GDP-weighted (paper App. Fig. B.10) | −4.5 | 1.20 | 0.58 |
| BU panel IRF (paper's 18%) | −3.5 | 1.15 | 0.43 |
| IRF draws rescaled to Newey–West s.e. | −5.9 | 1.10 | 0.66 |
| IRF draws widened by half | −5.9 | 1.09 | 0.64 |
| Transitory warmth only (Sims) | −2.8 | 1.30 | 0.40 |
| θ truncated to 0 after h=10 | −3.2 | 1.24 | 0.44 |
| Filter: p+1 lags (paper eq. 1 literal) | −5.5 | 1.12 | 0.65 |
| No simulated post-2027 temperatures (until 30 Oct) | −5.9 | 1.10 | 0.69 |
| Baseline: frozen 2000–2019 drift (until 30 Oct) | −6.8 | 1.71 | 0.66 |
| Baseline: frozen 1991–2019 drift (handoff) | −6.8 | 1.27 | 0.64 |
| Frozen 2000–19 drift + 0.5 pp drift uncertainty | −6.8 | 1.64 | 0.57 |
| Growth 2027→2031 (draft until 30 Oct) | −4.6 | 0.96 | 0.60 |
| Mean level 2029–33 vs 2025 (earlier draft) | −5.3 | 1.36 | 0.59 |
| Mean level 2031–35 vs 2025 (handoff) | −5.7 | 1.36 | 0.51 |

- If the truth were only the 2023–27 or only the 2026–27 shocks, the unconditional contract would resolve No 77% / 51% of the time.
- The IRF family and how long the warmth persists matter most for the predicted size; the baseline matters most for what the cutoff means in growth terms.

## 11. What a result would and would not establish

- **It tests a prediction, not the paper.** Growth at or below the strike is evidence in the direction of the paper's linear world-GDP response; growth above it is evidence against an effect of that size. Neither identifies causation for this one episode.
- **The test is relative.** Under the paper, median world GDP per capita still rises, to ≈$23.1k in 2031 against ≈$24.5k with no effect (2025: $21.9k).
- **It tests the warm sequence, not El Niño alone.** Both the prediction and the outcome carry the 2023–25 shocks.
- **Mostly an out-of-sample test of extrapolation.** The 2024 shock (+0.35 °C) is above the largest in the authors' sample (+0.30 °C in 2016).
- **Error rates depend on the baseline being right.** The spread assumes the IMF's average miss continues. If its forecasts had become unbiased, the central contract would resolve No only 51% of the time when the paper is right (instead of 82%); if its misses grew, No would come more often with no effect.
- **The early look is uninformative.** Against a 2022-anchored frozen drift, realised 2023–25 deviations were 0.0 / +0.1 / +0.2%; the paper's point IRF implied +0.2 / +0.6 / +1.3% (sd under no effect 1.3–2.3).

## 12. Objections we expect

Collected after re-reading the paper and its online appendix against the design. Who would raise each, the answer, and whether the design addresses it or it stays a caveat:

- **The contract uses the 12% estimate, not the paper's 14% headline.** *(paper's side; addressed)* The contract is on world GDP per person, and the paper's estimate for world GDP is its time-series result (Fig. III, about 12% six years after a 1 °C shock). The 14% is the country-panel average, which weights every country equally; weighting countries by their share of world GDP instead, as the paper does in App. Fig. B.10, gives −9.9% at year 6. Using the 14% moves the gap between the two worlds from 5.9 to 6.3 points and the cutoff from 1.09% to 1.08% a year (J 0.68 vs 0.70); with the GDP-weighted panel they are 4.5 points and 1.20% (J 0.58).
- **The shock filter was fitted on the very years being tested.** *(paper's side; addressed)* Fixed on 30 Oct 2026: the filter is fitted on the paper's own window (dependent years 1953–2022, data from 1950), so the 2023–27 warmth is measured out of sample. Refitting through 2025 shrinks each tested shock by about 0.04–0.05 °C and the gap to 5.0 points (J 0.62).
- **The no-effect background already contains the paper's damage.** *(paper's side; addressed)* By the paper's own estimates, 0.9 of the IMF's average 3.1-point miss over five-year windows came from temperature shocks (warming ran ahead of its trend after 1990). In the paper's world that part is taken out of the background, because the paper's damage enters through the shocks since 2015 instead. Without this, the gap would be 6.8 points and the contract would overstate its chance of resolving the paper's way.
- **The contract uses NOAA temperatures and World Bank GDP, not Berkeley Earth and the Penn World Table.** *(paper's side; addressed)* The paper reports similar results with NOAA, NASA and World Bank data (App. Fig. B.11), and says its Berkeley Earth measure tracks NOAA almost perfectly. Re-estimating the paper's world-GDP response with NOAA temperature gives −11.6% at year 6 (paper: −12.1%), and with World Bank GDP −12.7%; the cutoffs become 1.10% and 1.06% against 1.09%. The Penn World Table cannot settle the contract: its releases lag several years.
- **The growth period ends before the El Niño's full effect.** *(paper's side; caveat)* The paper's response peaks six years after a shock, after 2031 for the 2027 shock. The end year is set by a fixed rule that maximises the separation between the two views; longer periods add more background noise than predicted damage (see the end-year table).
- **Linear scaling breaks down for shocks this large.** *(paper's side; caveat)* The 2024 shock (0.35 °C) is 31% larger than the largest in the filter's 1953–2022 sample (0.27 °C, 2016). The paper finds no sign that larger shocks have smaller effects, and positive shocks, if anything, hurt more (App. Fig. B.6), so linear scaling is, if anything, conservative for the paper's side.
- **El Niño warmth is not the global temperature the paper studied.** *(paper's side; addressed)* The paper reports almost the same estimate after controlling for the same year's oceanic El Niño index (App. Fig. B.9) and says its results do not depend on particular sources of temperature variation. El Niño heat shows up first in the oceans, and the paper finds ocean temperature drives most of the effect (Fig. IX). The years after the El Niño are simulated with the cooling that usually follows a strong one; measured with the paper's filter, they change the predicted gap by −0.05 points.
- **Adaptation since 2019 has weakened the effect.** *(paper's side; caveat)* The paper reports no sign of adaptation (its estimates are stable across periods) and presents them as the effect absent new adaptation. Others dispute this: Curtin and Burgess (2026) find smaller Penn World Table estimates in later rolling windows, and Kahn (2026) argues the effect fades as people adapt. A Yes could mean the estimate is too high or that adaptation has improved; the contract cannot say which.
- **If the IMF has become less optimistic, the strikes are too low.** *(paper's side; caveat)* The no-effect expectation keeps the IMF's average past miss (decided 30 Oct 2026). If the IMF's forecasts are now unbiased, the central contract would resolve No only 51% of the time when the paper is right, instead of 82%.
- **One-step-ahead temperature shocks would change the answer.** *(paper's side; checked)* The paper reports similar responses with one-step shocks (Fig. V, App. Fig. B.13). With one-step shocks and the matching response, the shocks' effect on 2026–2031 growth is 5.9 points, against 6.8 with the paper's two-step shocks (central temperatures, no post-2027 shocks, before the background netting).
- **An unrelated recession would make the contract resolve No.** *(other side; caveat)* This is the paper's own main identification worry: a severe El Niño coinciding with an unrelated global recession. The spread of background growth includes recessions (the IMF's record covers 2009 and 2020), which is why the contract resolves No 13% of the time even with no temperature effect. A recession clause is not possible: under the paper, temperature shocks themselves cut investment and productivity.
- **The no-effect baseline is a judgment call.** *(other side; caveat)* It is the largest one. A frozen 2000–2019 drift would put the cutoff at 1.71% a year instead of 1.09%. The IMF projection is external and frozen at October 2026, and its spread is the IMF's own forecast record.
- **Part of the 2023–24 warmth had unusual causes (cleaner shipping fuel, the Hunga Tonga eruption, the solar maximum).** *(other side; caveat)* The contract uses NOAA's measured temperature, whatever its cause, and the paper finds similar effects across sources of temperature variation (App. Fig. B.9).
- **Applying the response to raw shocks, or to one-year warmth only, would give a different prediction.** *(other side; checked)* The paper's regression controls for the two previous shocks, so its response applies to the part of each shock they do not predict; raw shocks would double count and give a gap of 6.6 points. Reading the response as one-year warmth only (App. Fig. B.5) gives 2.8.
- **The paper's estimate is less precise than its bands suggest.** *(both sides; checked)* The paper-side spread comes from bootstrap draws of the paper's response. Rescaled to the paper's Newey–West standard errors, they give a cutoff of 1.10% a year (J 0.66); widened by half, 1.09% (J 0.64), against 1.09% (J 0.68). With the wider draws, the chance of a No if the paper is right falls from 81% to 77%.
- **One episode cannot confirm or refute the paper.** *(both sides; caveat)* Agreed. Separation is moderate (J 0.68); a result shifts the weight of evidence rather than settling it, and prices show how much credence participants give the paper.
- **The World Bank may rebase its price comparisons (PPPs) before resolution.** *(both sides; caveat)* Both years come from the same data release, so level revisions cancel; country weights can still shift growth slightly. The paper's results are similar across GDP sources.
- **The IMF's October 2026 projection may already include some El Niño effects.** *(both sides; caveat)* If so, the no-effect expectation is slightly too low, which tilts the contract toward Yes. IMF projections rarely quantify global temperature effects; not yet checked against the WEO text.

## 13. Timeline and open questions (see `CONTRACT_TERMS.md`)

- Monthly refreshes until the freeze.
- NOAA's 2026 annual value ~mid-Jan 2027: final refresh, terms frozen, **conditional contracts list**.
- NOAA's DJF 2027 RONI ~Mar 2027 (prices move; terms do not).
- NOAA's 2027 annual value ~mid-Jan 2028: **the matching condition converts; the others are refunded**.
- WDI 2031 first release mid-2032; **resolution 1 Oct 2033**.

**Open questions:**
- A low-power clause or no-decision zone for the cool condition (J 0.63)?
- List an unconditional contract from the start as well?

## 14. Reproduce and refresh

```
python -I run_analysis.py --refresh               # monthly: re-download data, update placeholders and indicative terms
python -I run_analysis.py                         # re-run on cached data in data/raw/
python -I build_page.py && python -I build_docs.py  # comment page, CONTRACT_TERMS.md, MEMO.md
python -I run_analysis.py --lock <T2026> <T2027>  # after conversion: cutoff for the realised temperatures
python -I -m pytest tests -q -p no:cacheprovider
```

### Sources

- Bilal & Känzig (2026), *QJE* 141(2): https://doi.org/10.1093/qje/qjag011 · replication: https://github.com/dkaenzig/micc_replication · shocks: https://github.com/dkaenzig/global-temperature-shocks
- NOAA NCEI Climate at a Glance: https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series · NOAA CPC ENSO indices · NASA GISTEMP v4 (comparison and fallback): https://data.giss.nasa.gov/gistemp/
- World Bank WDI `NY.GDP.PCAP.PP.KD`: https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.KD
- IMF World Economic Outlook, October 2026 (DataMapper API): https://www.imf.org/external/datamapper
- Critiques cited in §1 and §12: Curtin and Burgess, "The empirically inscrutable climate-economy relationship" (University of Wyoming working paper, 31 July 2026) · Kahn, "Real-Time Information Shocks and Climate Change Economic Damage Estimation" (working paper, 30 September 2026)
