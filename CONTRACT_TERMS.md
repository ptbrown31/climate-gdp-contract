# Draft contract specification for world GDP per capita after the 2023–27 global temperature shocks

*This is a **draft for comment**, refreshed 2026-11-05. The contracts were redesigned on 30 Oct 2026, and on 4 Nov 2026 their conditioning event moved to ForecastEx's Global Temperature contract (see the changes at the end).*

- Three **conditional contracts**, one for each range of NOAA's 2027 global temperature, are proposed to list right after NOAA publishes its **2026 annual value (expected mid-January 2027)**.
- The **plain ladder** asks the same question with no temperature condition and lists at the same time. Its terms are in `terms/plain_ladder_terms.md`.
- When NOAA publishes its **2027** annual value (expected mid-January 2028), positions in the contract whose condition was met convert to an unconditional contract at the same cost basis. Positions in the other two are refunded at cost; fees are not refunded. This follows ForecastEx's conditional contracts.
- Every number below is **indicative** and refreshes monthly until the terms freeze at the refresh that follows NOAA's 2026 annual value.

## The contracts

| Condition on NOAA's 2027 global temperature | Chance today | Question | P(Yes) if temperature shocks have no effect | P(Yes) if the paper is right |
|---|---|---|---|---|
| Cool: 1.45 °C or lower | 34% | Will world real GDP per person grow by more than **1.2%** a year, on average, from 2026 to 2031? | 82% | 20% |
| Central: 1.46 to 1.53 °C | 33% | Will world real GDP per person grow by more than **1.1%** a year, on average, from 2026 to 2031? | 87% | 18% |
| Warm: 1.54 °C or higher | 34% | Will world real GDP per person grow by more than **1.0%** a year, on average, from 2026 to 2031? | 90% | 16% |

- **Yes** means growth is above the strike, so the temperature shocks had no large effect.
- **No** means growth is at or below the strike, as Bilal and Känzig (QJE 2026) predict.
- A Yes contract pays $1 if the question resolves Yes; a No contract pays $1 if it resolves No. Participants take a financial position on either side, rewarded only for accuracy.
- Each condition also lists a ladder of strikes (term 9). The probabilities are for the headline strike, from 50,000 simulated worlds of each kind (term 8).

## Timeline

| When | What happens |
|---|---|
| Now to mid-Jan 2027 | Proposal circulates for comment. Indicative numbers refresh monthly, after NOAA's monthly release. |
| ~Mid-Jan 2027 | NOAA publishes its 2026 annual value. At the final refresh the end year, conditions, strikes, IMF forecast and code are frozen and archived. |
| Right after | **Conditional contracts list.** |
| ~Mar 2027 | NOAA publishes the winter (DJF) El Niño strength. Market prices can move on it, and the terms stay fixed. |
| ~Mid-Jan 2028 | NOAA publishes its 2027 annual value, and ForecastEx's GT 2027 contracts resolve on it (listed for 14 January 2028). **The matching condition converts; the other two are refunded at cost.** |
| Mid-2032 | World Bank publishes the first 2031 figure. |
| **1 Oct 2032** | **Resolve and settle** on the WDI version of that date, about three months after the first release. |

## Proposed terms

Each term is open for comment until the freeze.

### 1. Conditioning event
- The conditioning event is the resolution of ForecastEx's Global Temperature contracts (GT) for 2027 at two thresholds, the range bounds of 1.45 and 1.53 °C. ForecastEx's live conditional contracts (ZSENMFES, ZSENMUSR) use its Senate majority contract the same way.
- GT resolves on NOAA's 2027 global temperature, the January–December mean of global land and ocean surface temperature (NOAAGlobalTemp) in NOAA's annual global climate report. It is in °C relative to the 1901–2000 average, as first published to two decimals (https://data.forecastex.com/regulatory/GTTermsandConditions.pdf).
- The conditions are cool (1.45 °C or lower), central (1.46 to 1.53 °C) and warm (1.54 °C or higher). Cool occurs if GT 2027 at 1.45 resolves No, central if GT 2027 at 1.45 resolves Yes and GT 2027 at 1.53 resolves No, and warm if GT 2027 at 1.53 resolves Yes. For scale, the 2024 record is 1.25 °C.
- Each boundary between ranges lies halfway between neighbouring percentiles of the current 2027 forecast. The percentiles are the 20th, 50th and 80th (1.41, 1.49 and 1.58 °C), so each range is about one-third likely today. The forecast is the filter's expectation for 2027 (1.20 °C) plus an ENSO-regression forecast of the 2027 shock (+0.24 ± 0.10 °C), with winter (DJF) RONI assumed ~N(2.6, 0.35). The ranges freeze with the other terms.
- ForecastEx lists GT 2027 to resolve at 10:00 AM CT on 14 January 2028 and would list both bounds before the conditional contracts list. If NOAA is late, the GT resolution and the conversion wait for it. No other dataset stands in. NASA's GISTEMP takes its land and ocean data from NOAA and was delayed with it in 2019.

### 2. Settlement event
- The settlement event is world GDP per capita growth from 2026 to 2031, measured with World Bank WDI `NY.GDP.PCAP.PP.KD` (GDP per capita, PPP, constant 2021 international $) for country `WLD`.
- The contract settles on the series that most closely follows the paper's GDP data among those published in time to settle it. The paper's estimate is fitted on the Penn World Table's world GDP per capita, whose releases lag several years. Of the World Bank's series, the PPP series tracks it most closely, with five-year average growth 0.20 points a year apart (root mean square over windows ending 1995–2019). The World Bank's published growth rate, `NY.GDP.PCAP.KD.ZG`, measures growth in constant 2015 dollars at market exchange rates and sits 0.37 points apart. The paper's country panel gives very similar estimates with World Bank data (its App. Fig. B.11).
- **Growth = 100 × ln(y2031 / y2026) / 5**, with both levels from the single resolution-date version, so PPP rebasings and level revisions cancel. Growth is used unrounded, and the contract resolves **Yes if growth is strictly greater than the strike.**
- This is average log growth. At these rates it is within 0.03 points of the compound annual rate.
- 2026 is the last full year before listing, so none of the growth being measured (2027–2031) is known when the contracts list.

### 3. End year
- The end year is 2031, chosen by a fixed rule. Among end years 2028–2037, the rule picks the one with the highest Youden J between simulated "no effect" and "paper right" outcomes, to two decimals. A tie goes to the earlier year.
  - J = P(resolves No | paper right) + P(resolves Yes | no effect) − 1. It rewards a contract that resolves in line with whichever view is true, and favours neither side.
  - The rule uses only the paper's published response, the IMF projection and its error record, and temperature forecasts, all available before listing. It uses no GDP data after 2025.

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

- Separation peaks at 2031. The paper's response deepens for six years after a shock, so the predicted gap grows through 2031. After 2031 the 2023–24 shocks start to recover in the paper's response. Uncertainty about background growth grows with every added year.
- 2030 comes next (J 0.67 against 0.68). The end year freezes with the other terms.

### 4. Shock definition
- `s_t = T_t − (0.038438 + 0.496114·T_(t−2) + 0.485010·T_(t−3))`.
  - These are the Hamilton h=2, p=2 coefficients fitted on NOAA over the paper's own window (dependent years 1953–2022, data from 1950; paper footnote 2), on the annual series archived on 17 Oct 2026. The coefficients are frozen, so the 2023–27 warmth is measured out of sample, against a trend fitted without it.
  - Refitting through 2025 would shrink each 2023–27 shock by about 0.04–0.05 °C (gap 5.0 points, J 0.62).
- The **innovations** are `u_t = s_t − (0.008832 + 0.362637·s_(t−1) − 0.377483·s_(t−2))`.
  - This matches how the paper's regression defines its response and avoids double counting back-to-back warm years.
  - The alternative, raw shocks, gives a predicted shortfall of −6.6 points (J 0.71).

### 5. The paper's prediction
- The prediction uses the frozen Bilal–Känzig time-series local projection of log world real GDP per capita, PWT sample 1960–2019 (paper Fig. III), in 100×log points per 1 °C shock.
  - For h = 0…10 the response is `−1.7946, −2.4754, −4.5536, −6.4967, −9.1359, −11.7698, −12.1094, −11.2642, −10.9062, −5.6482, −6.8999`.
- Beyond h=10 the response is held at its h=10 value. Its uncertainty comes from the archived 4,000 wild-bootstrap draws (seed 123).
- The **shocks that count** are all shocks since 2015 whose effects change after 2026, plus simulated shocks for 2028–2031 (term 7). The table gives the contribution of each period's shocks to the predicted 2026–2031 shortfall at the point estimate, with central temperatures.

| Shocks | Points |
|---|---|
| 2015–2022 | −0.5 |
| 2023–2025 | −2.6 |
| 2026–2027 (El Niño) | −3.8 |
| 2028–2031 (simulated, cooler years after the El Niño) | 0.0 |
| **Total** | **−6.9** |

- These shocks lower 2026–2031 growth by 6.8 points (90% range −11.0 to −2.9; response and temperature uncertainty). In the paper's world the background is also 0.9 points better than the IMF's raw record (term 6), so the two worlds differ by **5.9 points** on average.

### 6. No-effect baseline
- The no-effect baseline is the IMF projection in the October 2026 World Economic Outlook (DataMapper, retrieved 17 Oct 2026). It puts world real GDP growth at 3.4% in 2027, 3.3% in 2028, 3.2% in 2029, 3.1% in 2030 and 3.1% in 2031. World population comes from the same release.
- Per-capita growth = 100·ln(1 + g/100) − 100·Δln(population), plus the 1991–2025 mean gap between WDI and IMF-implied per-capita growth (−0.07 points, correlation 0.99).
- Baseline per-capita growth is 2.42% in 2027, 2.34% in 2028, 2.26% in 2029, 2.15% in 2030 and 2.14% in 2031, a **mean of 2.26% a year** (the 2000–2019 average was 2.29%). Beyond 2031 the 2031 rate is held.
- The baseline stays frozen at the October 2026 WEO, because the January 2027 WEO Update usually appears after mid-January and projects only two years.
- The **spread** comes from the IMF's own historical forecast errors for world real GDP growth by years ahead. They are resampled as whole forecast paths so that multi-year misses (recessions, slowdowns) keep their persistence, then smoothed so the distribution is continuous. The errors are those of the October World Economic Outlooks of 1990–2020 (31 forecasts, IMF Historical WEO Forecasts Database), measured against the October 2026 WEO's estimates of what happened. Years past the IMF's six-year horizon are drawn independently from its six-year-ahead errors (misses in neighbouring years are close to uncorrelated). **The IMF's average miss is kept.** Over five-year windows like 2027–2031, world growth came in 3.1 points in total below the IMF's forecast on average (sd 2.7), or about 0.6 a year. It came in below the forecast in 27 of 31 windows. With no temperature effect, growth is therefore expected to average 1.65% a year, against the IMF's 2.26%. In the paper's world the background leaves out the part of those misses that the paper's own estimates put down to temperature shocks (0.9 of the 3.1 points on average), because its climate damage enters through the shocks since 2015 instead.
- With no temperature effect, average growth 2026–2031 has a 10–90% range of 1.0% to 2.3% a year. This spread is the largest uncertainty in the contract, larger than the uncertainty in the temperature record.

### 7. Temperatures after 2027
- These temperatures are simulated and form part of the paper's prediction.
- Strong El Niños are usually followed by cooler years. After a strong El Niño winter (RONI ≥ 1.5, true in virtually every simulated 2027), each simulated path replays the winters that followed one of the seven strong El Niños since 1950 (1958, 1966, 1973, 1983, 1992, 1998, 2016). Otherwise winter RONI follows an AR(2).
- Each year's shock is the ENSO regression's prediction plus a resampled residual; volcanic years stay in the residual pool.
- The mean simulated shocks are +0.08 °C in 2028, −0.09 °C in 2029 and +0.08 °C in 2030.
- They are measured with the same frozen filter (term 4). That filter was fitted before the 2023–24 jump, so it still counts a lasting warmer level as positive shocks, as the paper's method would. This partly or fully offsets the cooling that usually follows a strong El Niño.
- Under the paper's estimate, the simulated years change 2026–2031 growth by −0.05 points (90% range −1.9 to +1.9). Without them the cutoff would be 1.10% a year and J 0.69.
- The strikes are fixed in advance, so actual 2028–2031 temperatures do not change them.

### 8. Strikes
- Each condition has 50,000 simulated worlds with no temperature effect and 50,000 with the paper's effect (common random numbers, seed 20261017). NOAA's 2027 value is drawn from the forecast within the condition's range.
- The cutoff within each condition is the growth rate that maximises J (tolerance 0.0025). The **headline strike** is the cutoff rounded to 0.1 point.

| Condition (NOAA 2027) | Chance today | Predicted shortfall 2026–2031 (points) | Cutoff (%/yr) | Strike | P(Yes) if no effect | P(Yes) if paper right | J |
|---|---|---|---|---|---|---|---|
| Cool: 1.45 °C or lower | 34% | −5.1 | 1.16 | **1.2** | 82% | 20% | 0.63 |
| Central: 1.46 to 1.53 °C | 33% | −6.0 | 1.10 | **1.1** | 87% | 18% | 0.69 |
| Warm: 1.54 °C or higher | 34% | −6.9 | 1.04 | **1.0** | 90% | 16% | 0.74 |
| No condition (all 2027 outcomes) | 100% | −5.9 | 1.09 | – | 87% | 19% | 0.68 |

- A warmer 2027 means a bigger predicted shortfall, so the warm condition has the lowest cutoff and the most power.

### 9. Strike ladder
- Each condition lists strikes from 0.1% to 2.1% a year, 0.2 points apart around the central strike, plus every headline strike (in bold). Each cell gives P(Yes) if temperature shocks have no effect / if the paper is right. With no effect, 2027's temperature does not matter, so the first number is the same in every column.

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

### 10. Conversion and refunds
- When the GT 2027 contracts resolve on NOAA's 2027 annual value, positions in the contracts whose condition was met convert to the unconditional contract with the same question and strike, at the same cost basis.
- Positions in the other conditions' contracts are refunded at cost; fees are not refunded.
- More strikes may be listed after conversion. The cutoff for the realised 2026 and 2027 values comes from `python -I run_analysis.py --lock <T2026> <T2027>` on the archived data (`outputs/threshold_grid.csv` shows how it moves).

### 11. Resolution and settlement
- **1 Oct 2032.** Retrieve the WDI series once, archive the response and its `lastupdated` field, and compute growth with the archived code.
- If 2026 or 2031 is missing from that version, read the series again at the same time on the first business day of each following month, and resolve on the first version that has both years.
- If the indicator is discontinued, ForecastEx resolves the contracts under its event review (Rule 415).

### 12. Acknowledged limits
- One outcome cannot confirm or refute the paper. A global recession year can move five-year growth by several points; 2020 alone was −3.9%.
- Under the paper's estimate, GDP per capita still grows (about 0.5% a year, against 1.6% with no effect). The test is the shortfall against the baseline.
- The 2024 shock (+0.35 °C with NOAA) already exceeds the largest in the filter's sample (+0.27 °C, 2016), so the test relies on the paper's linear scaling.
- The contract tests the paper's response to the whole 2023–27 warm sequence. If only the 2026–27 shocks mattered, the unconditional contract would resolve No only 51% of the time.
- The response was estimated with Berkeley Earth shocks and is applied to NOAA shocks; the two track each other closely (corr 0.990, 1960–2019).

### 13. Objections we expect
Each entry gives who would raise it, the answer, and whether the design addresses it or it stays a caveat.

- **The contract uses the paper's 12% estimate where its headline is 14%.** *(paper's side; addressed)* The contract is on world GDP per person, and the paper's estimate for world GDP is its time-series result (Fig. III, about 12% six years after a 1 °C shock). The 14% is the country-panel average, which weights every country equally. Weighting countries by their share of world GDP, as the paper does in App. Fig. B.10, gives −9.9% at year 6. Using the 14% moves the gap between the two worlds from 5.9 to 6.3 points and the cutoff from 1.09% to 1.08% a year (J 0.68 vs 0.70). With the GDP-weighted panel they are 4.5 points and 1.20% (J 0.58).
- **The shock filter was fitted on the very years being tested.** *(paper's side; addressed)* Since 30 Oct 2026 the filter has been fitted on the paper's own window (dependent years 1953–2022, data from 1950), so the 2023–27 warmth is measured out of sample. Refitting through 2025 shrinks each tested shock by about 0.04–0.05 °C and the gap to 5.0 points (J 0.62).
- **The no-effect background already contains the paper's damage.** *(paper's side; addressed)* By the paper's own estimates, 0.9 of the IMF's average 3.1-point miss over five-year windows came from temperature shocks (warming ran ahead of its trend after 1990). In the paper's world that part is taken out of the background, because the paper's damage enters through the shocks since 2015 instead. Without this, the gap would be 6.8 points and the contract would overstate its chance of resolving the paper's way.
- **The contract uses NOAA temperatures and World Bank GDP where the estimate it tests uses Berkeley Earth and the Penn World Table.** *(paper's side; addressed)* The paper reports similar results with NOAA, NASA and World Bank data in its country panel (App. Fig. B.11), and says its Berkeley Earth measure tracks NOAA almost perfectly. It does not report its world time series with these data. Re-estimating that series with the authors' NOAA data gives −11.6% at year 6 (the paper's is −12.1%), and with their World Bank data, at market exchange rates, −12.7%. The cutoffs become 1.10% and 1.06%, against 1.09%. ForecastEx's GT contracts resolve on NOAA. The Penn World Table cannot settle the contract, because its releases lag several years. Its version 11.0, of October 2025, ends in 2023.
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

### Open questions for comment
- A low-power clause or no-decision zone for the cool condition (J 0.63)?

## Changes on 30 Oct 2026
- Three conditional contracts on NOAA's 2027 value replace a single contract whose cutoff was to be computed from the final 2027 value on 1 March 2028.
- Growth is now measured from 2026 instead of 2027, because the contracts list right after NOAA's 2026 value, before any 2027 growth is known. J is 0.68, against 0.60 from 2027.
- The end year (2031) is chosen by a fixed rule, explained in term 3.
- The no-effect baseline is the IMF projection. The previous frozen 2000–2019 drift (2.29%/yr) is kept as a sensitivity (J 0.66).
- Simulated temperatures after 2027 enter the paper's prediction; they change the gap by −0.05 points (J 0.69 without them).
- The spread of background growth comes from the IMF's own forecast record (October WEOs 1990–2020), which replaced a stand-in. It keeps the IMF's average miss, so the no-effect expectation is below the IMF's projection.
- The design was checked against the paper and its online appendix. The temperature-shock filter is now fitted on the paper's own window (data 1950–2022) and frozen, so the 2023–27 warmth is measured out of sample. In the paper's world the background leaves out the part of the IMF's past misses that the paper puts down to temperature shocks (0.9 points). Simulated post-2027 temperatures are measured with the same filter. Term 13 lists the objections these changes answer.
- With these changes the end-year rule picks 2031 (J 0.68). 2030 comes next (J 0.67 against 0.68). The strikes are 1.2 / 1.1 / 1.0% (cool / central / warm). They were 2.0 / 1.9 / 1.8% for growth to 2030 before the IMF record was added.
- The question asks whether growth will be **more than** the strike, so Yes means no large effect and No is the outcome the paper predicts.

## Changes on 31 Oct 2026
- Term 13 now cites the paper's own GDP-weighted panel (App. Fig. B.10, −9.9% at year 6) and checks the paper-side spread with wider draws (cutoff 1.09% a year, J 0.64). The contracts and strikes are unchanged.

## Changes on 4 Nov 2026
- The conditional contracts' proposed code is ZGTWGDPC, following ForecastEx's pattern of Z, the conditioning contract's code and the settlement contract's code (ZSENMFES, ZSENMUSR). It was WGDPCT.
- The conditioning event is the resolution of ForecastEx's GT contracts for 2027 at the two range bounds (term 1). Conversion moves from a reading of NOAA's value on 31 January 2028 to GT's resolution, expected in mid-January 2028.
- The GISTEMP fallback is dropped. If NOAA is late, conversion waits under GT's terms. GISTEMP takes its land and ocean data from NOAA and was delayed with it in 2019, so it would not cover a NOAA outage.
- Growth is used unrounded. It was rounded to two decimals.
- A missing year or a discontinued series goes to ForecastEx's event review (Rule 415). The contracts used to fall back on archived versions or an official successor and were cancelled at cost otherwise.
- The ranges, strikes and chances are unchanged.

## Changes on 5 Nov 2026
- The contracts resolve on 1 October 2032, about three months after the World Bank's first estimate for 2031. They were to resolve a year later, on 1 October 2033, after the first round of revisions.
- In the World Bank's archive of past WDI versions, five-year growth for end years 2010–2024 read on 1 October of the following year differs from the reading a year later by 0.08 points a year on average. The earlier reading is 0.12 points a year from the current version (root mean square) and the later one 0.11 (`wdi_revisions.py`, `outputs/wdi_revisions.csv`).
- The version current on 1 October of the following year has had the end year every year since 2011. It lacked the end year for 2003, 2008 and 2009, when the World Bank published later. A version that lacks either year now moves the reading to the first business day of each following month until a version has both. A discontinued series still goes to ForecastEx's event review (Rule 415).
- The ranges, strikes and chances are unchanged.
