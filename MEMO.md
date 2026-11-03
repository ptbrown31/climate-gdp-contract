# A prospective test of Bilal–Känzig with the 2026–27 El Niño and the design of the forecast contracts

This memo was prepared on 17 October 2026 and revised on 23 October 2026 (NOAA temperature record), **30 October 2026** (conditional contracts, growth from 2026, an end-year rule, the IMF baseline with its own forecast record, simulated post-2027 temperatures, the paper's own filter window) and 31 October 2026 (the paper's GDP-weighted panel and two checks of the paper-side spread, as sensitivities). It is a draft for comment, refreshed monthly. The contracts list right after NOAA's 2026 annual value (mid-Jan 2027). The code is `bk_elnino/` and `run_analysis.py`, and the outputs are in `outputs/`.

Everything below was produced by `python -I run_analysis.py` and written by `build_docs.py`. Every number also appears in a CSV in `outputs/` and under a design label in `outputs/results.json`.

- **Every term is still provisional.** The terms freeze at the refresh that follows NOAA's 2026 annual value, and the conditional contracts list right after.
- **2026 and 2027 temperatures are placeholders** (1.215 ± 0.022 °C for 2026 and 1.495 ± 0.097 °C for 2027). Each monthly refresh replaces them with whatever NOAA has published.

---

## Summary

1. **The handoff's shock formula used the wrong lags.** The authors' shock series is exactly `T_t − (a + b₂T_{t−2} + b₃T_{t−3})`, with two lagged regressors for h=2, p=2 and zero weight on `T_{t−4}`. The paper's Eq. (1) is typeset with p+1 lags, but the data the IRF was estimated on uses p.
2. **The headline −14% / −18% numbers are panel estimates (paper Fig. IV).** The world real GDP per capita IRF (Fig. III), which fits a world-GDP contract, peaks at **−12.1% at h=6 (PWT)** per 1 °C shock. The Python local projections reproduce the authors' Stata estimates to ~1e-7.
3. **The record shock came in 2024.** With NOAA it was +0.35 °C, the largest since at least 1953. 2023 gave +0.22 °C. The 2027 placeholder implies a shock of +0.29 ± 0.10 °C.
4. **The paper predicts a 5.9-point shortfall.** Its published PWT response implies that world per-capita growth from 2026 to 2031 falls that far short of the no-effect path (90% range −10.2 to −2.1). The shortfall is net of the part of the IMF's past misses that the paper itself puts down to temperature. It means growth of about 0.5% a year instead of 1.6%. The 2023–25 and 2026–27 shocks contribute −2.6 and −3.8 points, and the simulated years after 2027 change it by −0.05.
5. **The proposal is three conditional contracts** on NOAA's 2027 temperature, listed right after NOAA's 2026 value. Each asks whether world GDP per person will grow by more than a strike, on average, from 2026 to 2031:
   - cool 2027 (1.45 °C or lower), strike 1.2%/yr, J 0.63;
   - central (1.46 to 1.53 °C), strike 1.1%/yr, J 0.69;
   - warm (1.54 °C or higher), strike 1.0%/yr, J 0.74.
   - The matching contract converts to an unconditional one when NOAA publishes 2027; the others are refunded.
6. **The test has moderate power.** Unconditionally the cutoff is 1.09% a year. The contract resolves No (the paper's outcome) 81% of the time if the paper is right, and Yes 87% of the time if temperature shocks have no effect (J 0.68, AUC 0.91). A Yes contract would be worth about $0.19 if the paper is right and $0.87 if not, so its price maps onto the credence participants give the paper.
7. **A rule chooses the end year, 2031.** It is the year with the highest separation (J) among 2028–2037, and the rule uses no GDP data after 2025. Separation rises while the paper's response deepens, and falls as background-growth uncertainty accumulates and the earlier shocks recover. 2030 comes next (J 0.67 against 0.68).
8. **Background growth is the biggest uncertainty.** The IMF projection puts per-capita growth at 2.26% a year over 2027–2031. Its forecasts at these horizons have run high. Since 1990 growth has come in 3.1 points below them on average over five-year windows, and below them in 27 of 31 windows. Keeping that miss, the no-effect expectation is 1.65% a year. Over five years, background growth has an sd of 2.6 points, against the paper's predicted shortfall of 5.9.
9. **Growth is measured from 2026**, the last full year before listing, so none of the measured growth is known at listing. Starting at 2027, as in the drafts until 30 Oct, gives J 0.60.
10. **The temperature record changes the prediction.** Under the 23 Oct design, NASA GISTEMP (the proposal until 22 Oct) gave a 4.5-point prediction against NOAA's 3.6. NOAA was chosen because the paper uses it and reports that its Berkeley Earth measure tracks NOAA almost perfectly.

---

## 1. Corrections to the handoff

| # | Handoff said | Evidence | What the code does |
|---|---|---|---|
| 1 | Regress `T_t` on `T_{t−2}, T_{t−3}, T_{t−4}` for h=2, p=2 | Exact regression of the authors' `gtmp_bkly_aw_dtfe2` on `[1, T_t, T_{t−2}, T_{t−3}, T_{t−4}]` returns weights `[−0.0387, 1, −0.5196, −0.4608, 0.0000]` with zero residual. The p+1-lag version correlates only 0.91 with the authors' series. Curtin and Burgess (2026, App. H) independently rebuild the shocks with the same two lags. | `hamilton.lag_set(h, p)` = lags h…h+p−1 (`bk_data`). The literal Eq. (1) reading is kept as `paper_eq1` for sensitivity. |
| 2 | Published IRF peaks at −14% (h=6, PWT) and −18% (h=5, BU) | Those are the country-panel averages (paper Fig. IV). The world-GDP time-series IRF (Fig. III) is −12.1% (h=6) and −16.8% (h=6). | The primary design uses the time-series PWT IRF. Panel IRFs are labelled sensitivities. |
| 3 | Provisional 2023/2024 shocks of +0.174 / +0.269 | Neither convention reproduces them. | NOAA h=2, p=2 gives **+0.215 / +0.353**. |
| 4 | Apply `θ_h` to raw shocks (Σ θ_{t−τ} s_τ) | The authors' LP controls for s_{t−1}, s_{t−2}, so θ_h is the response to the part of s_t not predicted by the two prior shocks, including the predictable follow-on shocks. Applying θ to raw consecutive shocks double counts. | The primary design applies θ to innovations, estimated on the LP's own sample. The raw formula is a labelled variant. |
| 5 | Primary test on the incremental 2026–27 component | The realised outcome will contain the effects of the 2023–25 shocks too (under the paper). A prediction that omits them is mis-specified for the statistic that will be resolved. | The paper's side counts all shocks with effects in the measured years, plus simulated post-2027 shocks. |
| 6 | Null drift from 1991–2019 | 1991–2000 per-capita PPP growth averaged 1.25%/yr (post-Soviet collapse); 2001–10 2.28; 2011–19 2.19; 2022–25 2.44. | Since 30 Oct the no-effect path follows the IMF projection. Frozen 2000–2019 and 1991–2019 drifts are sensitivities. |

## 2. Data

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

The vintages are recorded in `outputs/results.json → vintages`.

## 3. Temperature shocks

The frozen **filter** is `T(t) = 0.0384 + 0.4961 T(t-2) + 0.4850 T(t-3)`, fitted on NOAA over the paper's window (dependent years 1953–2022), with residual sd 0.124 °C. Later years are out of sample.

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

- The **primary** response is the PWT time-series LP (paper Fig. III), re-estimated in Python from the authors' data, with θ = −1.8, −2.5, −4.6, −6.5, −9.1, −11.8, −12.1, −11.3, −10.9, −5.6, −6.9 for h = 0…10 (100×log points per 1 °C).
- The **uncertainty** comes from 4,000 joint draws from the authors' wild-bootstrap procedure, re-centred on the point estimate.
- **Beyond h=10** θ is held at θ₁₀, since the paper reports that responses do not fully mean-revert. Truncation to 0 is a variant.
- The IRF is estimated on PWT world GDP and Berkeley Earth shocks and applied to WDI PPP world GDP and NOAA shocks, a **mismatch** the design accepts. The authors' panel estimate with WDI GDP is close to the PWT one, and the shock series track each other closely.

## 5. The paper's GDP prediction

`E_t = Σ_τ θ_{min(t−τ,10)} · u_τ − Σ_{τ≤2025} θ_{min(2025−τ,10)} · u_τ`. The second sum removes effects already in the observed 2025 level. The contract measures growth from 2026 to 2031, so the paper's prediction is `E_2031 − E_2026`. The table gives each period's contribution at the point IRF, with central placeholders.

| Contributing shocks | Contribution (points) |
|---|---|
| 2015–2022 | −0.5 |
| 2023–2025 | −2.6 |
| 2026–2027 (El Niño) | −3.8 |
| 2028–2031 (simulated, cooler years after the El Niño) | 0.0 |
| **Total** | **−6.9** |

## 6. Temperatures after 2027

Simulated 2028+ shocks are part of the paper's prediction, because under its response any later shock moves GDP too. They enter through their innovations, the part the two prior shocks do not predict, so the typical follow-on path already inside θ is counted only once.

- After a strong El Niño, winter RONI replays the winters that followed one of 7 analog El Niños (1958, 1966, 1973, 1983, 1992, 1998, 2016). Otherwise it follows an AR(2), R_y = +0.088 −0.037 R_(y-1) −0.226 R_(y-2). Each year's shock is the ENSO regression's prediction plus a resampled residual (sd 0.108 °C, n=73, volcanic years included).
- The **mean simulated shocks** are +0.08 °C in 2028, −0.09 °C in 2029, +0.08 °C in 2030 and +0.09 °C in 2031.
- Their **effect** on 2026–2031 growth is −0.05 points (90% range −1.9 to +1.9). Without them the cutoff would be 1.10%/yr and J 0.69.
- The cutoffs are fixed in advance; realised 2028–30 temperatures do not change them.

## 7. The no-effect baseline

- The **path** is IMF WEO October 2026 world real GDP growth minus world population growth, plus the 1991–2025 mean WDI gap (−0.07 points, correlation 0.99). Per-capita growth is 2.42% in 2027, 2.34% in 2028, 2.26% in 2029, 2.15% in 2030 and 2.14% in 2031, a mean of 2.26%/yr. The 2031 rate is held beyond 2031.
- The **spread** comes from whole historical forecast-error paths, shrunk toward their mean and mixed with Gaussian noise of the same covariance (a smoothed bootstrap). Multi-year misses keep their persistence, and the distribution is continuous.
- The errors are those of the October World Economic Outlooks of 1990–2020 (31 forecasts, IMF Historical WEO Forecasts Database), measured against the October 2026 WEO's estimates of what happened. Years past the IMF's six-year horizon are drawn independently from its six-year-ahead errors (misses in neighbouring years are close to uncorrelated). **The IMF's average miss is kept.** Over five-year windows like 2027–2031, world growth came in 3.1 points in total below the IMF's forecast on average (sd 2.7), or about 0.6 a year. It came in below the forecast in 27 of 31 windows. With no temperature effect, growth is therefore expected to average 1.65% a year, against the IMF's 2.26%. In the paper's world the background leaves out the part of those misses that the paper's own estimates put down to temperature shocks (0.9 of the 3.1 points on average), because its climate damage enters through the shocks since 2015 instead.
- With no effect, M has sd 2.62, and average growth over 2026–2031 has a 10–90% range of 1.0–2.3%/yr.
- **Backtests** of a frozen 20-year drift give 8-year misses of about ±4.3 points (WDI USD), ±7.8 (PWT) and ±10.6 (Barro–Ursúa, including wars and the Depression). `outputs/null_backtest.csv` has the contract horizon.

## 8. The end year

The rule picks the end year in 2028–2037 with the highest J, to two decimals, with ties going to the earlier year. It is applied before listing and uses no GDP data after 2025. J rewards a contract that resolves in line with whichever view is true, so choosing the end year this way favours neither side.

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

The strike ladder gives P(Yes) if no effect / if the paper is right, with headline strikes in bold.

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

A participant who puts probability p on the paper being right values a $1 Yes contract at the unconditional cutoff at $0.80 for p = 0.1, $0.70 for p = 0.25, $0.53 for p = 0.5, $0.36 for p = 0.75 and $0.26 for p = 0.9.

## 10. Robustness

Each row changes one choice at a time and has its own cutoff.

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
| Filter with p+1 lags (paper eq. 1 literal) | −5.5 | 1.12 | 0.65 |
| No simulated post-2027 temperatures (until 30 Oct) | −5.9 | 1.10 | 0.69 |
| Frozen 2000–2019 drift baseline (until 30 Oct) | −6.8 | 1.71 | 0.66 |
| Frozen 1991–2019 drift baseline (handoff) | −6.8 | 1.27 | 0.64 |
| Frozen 2000–19 drift + 0.5 pp drift uncertainty | −6.8 | 1.64 | 0.57 |
| Growth 2027→2031 (draft until 30 Oct) | −4.6 | 0.96 | 0.60 |
| Mean level 2029–33 vs 2025 (earlier draft) | −5.3 | 1.36 | 0.59 |
| Mean level 2031–35 vs 2025 (handoff) | −5.7 | 1.36 | 0.51 |

- If the truth were only the 2023–27 or only the 2026–27 shocks, the unconditional contract would resolve No 77% / 51% of the time.
- The predicted size moves most with the IRF family and with how long the warmth persists. What the cutoff means in growth terms moves most with the baseline.

## 11. Interpretation of a result

- **A result tests the paper's prediction for one episode.** Growth at or below the strike is evidence in the direction of the paper's linear world-GDP response, and growth above it is evidence against an effect of that size. Neither outcome identifies causation.
- **The test is relative.** Under the paper, median world GDP per capita still rises, to ≈$23.1k in 2031 against ≈$24.5k with no effect (the 2025 level is $21.9k).
- **The test covers the whole warm sequence.** Both the prediction and the outcome carry the 2023–25 shocks.
- **The test relies on extrapolation.** The 2024 shock (+0.35 °C) is above the largest in the authors' sample (+0.30 °C in 2016).
- **Error rates depend on the baseline being right.** The spread assumes the IMF's average miss continues. If its forecasts had become unbiased, the central contract would resolve No only 51% of the time when the paper is right (instead of 82%). If its misses grew, No would come more often with no effect.
- **The early look is uninformative.** Against a 2022-anchored frozen drift, realised 2023–25 deviations were 0.0 / +0.1 / +0.2%. The paper's point IRF implied +0.2 / +0.6 / +1.3% (sd under no effect 1.3–2.3).

## 12. Objections we expect

These objections come from re-reading the paper and its online appendix against the design. Each entry gives who would raise it, the answer, and whether the design addresses it or it stays a caveat.

- **The contract uses the paper's 12% estimate where its headline is 14%.** *(paper's side; addressed)* The contract is on world GDP per person, and the paper's estimate for world GDP is its time-series result (Fig. III, about 12% six years after a 1 °C shock). The 14% is the country-panel average, which weights every country equally. Weighting countries by their share of world GDP, as the paper does in App. Fig. B.10, gives −9.9% at year 6. Using the 14% moves the gap between the two worlds from 5.9 to 6.3 points and the cutoff from 1.09% to 1.08% a year (J 0.68 vs 0.70). With the GDP-weighted panel they are 4.5 points and 1.20% (J 0.58).
- **The shock filter was fitted on the very years being tested.** *(paper's side; addressed)* Since 30 Oct 2026 the filter has been fitted on the paper's own window (dependent years 1953–2022, data from 1950), so the 2023–27 warmth is measured out of sample. Refitting through 2025 shrinks each tested shock by about 0.04–0.05 °C and the gap to 5.0 points (J 0.62).
- **The no-effect background already contains the paper's damage.** *(paper's side; addressed)* By the paper's own estimates, 0.9 of the IMF's average 3.1-point miss over five-year windows came from temperature shocks (warming ran ahead of its trend after 1990). In the paper's world that part is taken out of the background, because the paper's damage enters through the shocks since 2015 instead. Without this, the gap would be 6.8 points and the contract would overstate its chance of resolving the paper's way.
- **The contract uses NOAA temperatures and World Bank GDP where the paper uses Berkeley Earth and the Penn World Table.** *(paper's side; addressed)* The paper reports similar results with NOAA, NASA and World Bank data (App. Fig. B.11), and says its Berkeley Earth measure tracks NOAA almost perfectly. Re-estimating the paper's world-GDP response with NOAA temperature gives −11.6% at year 6 (the paper's is −12.1%), and with World Bank GDP −12.7%. The cutoffs become 1.10% and 1.06%, against 1.09%. The Penn World Table cannot settle the contract, because its releases lag several years.
- **The growth period ends before the El Niño's full effect.** *(paper's side; caveat)* The paper's response peaks six years after a shock, after 2031 for the 2027 shock. The end year is set by a fixed rule that maximises the separation between the two views. Longer periods add more background noise than predicted damage (see the end-year table).
- **Linear scaling breaks down for shocks this large.** *(paper's side; caveat)* The 2024 shock (0.35 °C) is 31% larger than the largest in the filter's 1953–2022 sample (0.27 °C, 2016). The paper finds no sign that larger shocks have smaller effects, and positive shocks have effects at least as large as negative ones (App. Fig. B.6). Linear scaling is therefore unlikely to overstate the paper's predicted damage.
- **El Niño warmth differs from the global temperature variation the paper studied.** *(paper's side; addressed)* The paper reports almost the same estimate after controlling for the same year's oceanic El Niño index (App. Fig. B.9) and says its results hold across sources of temperature variation. El Niño heat shows up first in the oceans, and the paper finds ocean temperature drives most of the effect (Fig. IX). The years after the El Niño are simulated with the cooling that usually follows a strong one. Measured with the paper's filter, they change the predicted gap by −0.05 points.
- **Adaptation since 2019 has weakened the effect.** *(paper's side; caveat)* The paper reports no sign of adaptation (its estimates are stable across periods) and presents them as the effect absent new adaptation. Curtin and Burgess (2026) dispute this with smaller Penn World Table estimates in later rolling windows, and Kahn (2026) argues the effect fades as people adapt. A Yes could mean the estimate is too high or that adaptation has improved, and the contract cannot tell which.
- **If the IMF has become less optimistic, the strikes are too low.** *(paper's side; caveat)* The no-effect expectation keeps the IMF's average past miss (decided 30 Oct 2026). If the IMF's forecasts are now unbiased, the central contract would resolve No only 51% of the time when the paper is right, instead of 82%.
- **One-step-ahead temperature shocks would change the answer.** *(paper's side; checked)* The paper reports similar responses with one-step shocks (Fig. V, App. Fig. B.13). With one-step shocks and the matching response, the shocks' effect on 2026–2031 growth is 5.9 points, against 6.8 with the paper's two-step shocks (central temperatures, no post-2027 shocks, before the background netting).
- **An unrelated recession would make the contract resolve No.** *(other side; caveat)* The paper's own main identification worry is a severe El Niño coinciding with an unrelated global recession. The spread of background growth includes recessions (the IMF's record covers 2009 and 2020), which is why the contract resolves No 13% of the time even with no temperature effect. A recession clause is not possible, because under the paper temperature shocks themselves cut investment and productivity.
- **The no-effect baseline is a judgment call.** *(other side; caveat)* It is the largest one. A frozen 2000–2019 drift would put the cutoff at 1.71% a year instead of 1.09%. The IMF projection is external and frozen at October 2026, and its spread is the IMF's own forecast record.
- **Part of the 2023–24 warmth had unusual causes (cleaner shipping fuel, the Hunga Tonga eruption, the solar maximum).** *(other side; caveat)* The contract uses NOAA's measured temperature, whatever its cause, and the paper finds similar effects across sources of temperature variation (App. Fig. B.9).
- **Applying the response to raw shocks, or to one-year warmth only, would give a different prediction.** *(other side; checked)* The paper's regression controls for the two previous shocks, so its response applies to the part of each shock they do not predict. Raw shocks would double count and give a gap of 6.6 points. Reading the response as one-year warmth only (App. Fig. B.5) gives 2.8.
- **The paper's estimate is less precise than its bands suggest.** *(both sides; checked)* The paper-side spread comes from bootstrap draws of the paper's response. Rescaled to the paper's Newey–West standard errors, they give a cutoff of 1.10% a year (J 0.66). Widened by half, they give 1.09% (J 0.64), against 1.09% (J 0.68). With the wider draws, the chance of a No if the paper is right falls from 81% to 77%.
- **One episode cannot confirm or refute the paper.** *(both sides; caveat)* Agreed. Separation is moderate (J 0.68), so a result adds to the weight of evidence and leaves the question open. Prices show how much credence participants give the paper.
- **The World Bank may rebase its price comparisons (PPPs) before resolution.** *(both sides; caveat)* Both years come from the same data release, so level revisions cancel. Country weights can still shift growth slightly. The paper's results are similar across GDP sources.
- **The IMF's October 2026 projection may already include some El Niño effects.** *(both sides; caveat)* If so, the no-effect expectation is slightly too low, which tilts the contract toward Yes. IMF projections rarely quantify global temperature effects, and this has not yet been checked against the WEO text.

## 13. Timeline and open questions

The full terms are in `CONTRACT_TERMS.md`.

- The numbers refresh monthly until the freeze.
- NOAA publishes its 2026 annual value ~mid-Jan 2027. The final refresh follows, the terms freeze and the **conditional contracts list**.
- NOAA publishes the DJF 2027 RONI ~Mar 2027. Market prices can move on it, and the terms stay fixed.
- NOAA publishes its 2027 annual value ~mid-Jan 2028. **The matching condition converts and the others are refunded.**
- The first WDI 2031 figure appears mid-2032, and **resolution is 1 Oct 2033**.

**Open questions**
- A low-power clause or no-decision zone for the cool condition (J 0.63)?
- List an unconditional contract from the start as well?

## 14. Reproduction and refresh

```
python -I run_analysis.py --refresh               # monthly refresh of data, placeholders and indicative terms
python -I run_analysis.py                         # re-run on cached data in data/raw/
python -I build_page.py && python -I build_docs.py  # comment page, CONTRACT_TERMS.md, MEMO.md
python -I run_analysis.py --lock <T2026> <T2027>  # after conversion, the cutoff for the realised temperatures
python -I -m pytest tests -q -p no:cacheprovider
```

### Sources

- Bilal & Känzig (2026), *QJE* 141(2), https://doi.org/10.1093/qje/qjag011, with the replication package at https://github.com/dkaenzig/micc_replication and the shocks at https://github.com/dkaenzig/global-temperature-shocks
- NOAA NCEI Climate at a Glance, https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series · NOAA CPC ENSO indices · NASA GISTEMP v4 (comparison and fallback), https://data.giss.nasa.gov/gistemp/
- World Bank WDI `NY.GDP.PCAP.PP.KD`, https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.KD
- IMF World Economic Outlook, October 2026 (DataMapper API), https://www.imf.org/external/datamapper
- The critiques cited in §1 and §12 are Curtin and Burgess, "The empirically inscrutable climate-economy relationship" (University of Wyoming working paper, 31 July 2026), and Kahn, "Real-Time Information Shocks and Climate Change Economic Damage Estimation" (working paper, 30 September 2026).
