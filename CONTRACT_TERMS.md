# Draft contract specification (for comment): world GDP per capita after the 2023–27 global temperature shocks

*Status, 2026-10-31: **draft for comment.** Redesigned on 30 Oct 2026; see "What changed on 30 Oct 2026" at the end.*

- Three **conditional contracts**, one for each range of NOAA's 2027 global temperature, are proposed to list right after NOAA publishes its **2026 annual value (expected mid-January 2027)**.
- When NOAA publishes its **2027** annual value (expected mid-January 2028), positions in the contract whose condition was met convert to an unconditional contract at the same cost basis. Positions in the other two are refunded at cost; fees are not refunded. This follows ForecastEx's conditional contracts.
- Every number below is **indicative** and refreshes monthly until the terms freeze at the refresh that follows NOAA's 2026 annual value.

## The contracts

| Condition: NOAA's 2027 global temperature | Chance today | Question | P(Yes) if temperature shocks have no effect | P(Yes) if the paper is right |
|---|---|---|---|---|
| Cool: 1.45 °C or lower | 34% | Will world real GDP per person grow by more than **1.2%** a year, on average, from 2026 to 2031? | 82% | 20% |
| Central: 1.46 to 1.53 °C | 33% | Will world real GDP per person grow by more than **1.1%** a year, on average, from 2026 to 2031? | 87% | 18% |
| Warm: 1.54 °C or higher | 34% | Will world real GDP per person grow by more than **1.0%** a year, on average, from 2026 to 2031? | 90% | 16% |

- **Yes:** growth beats the strike, so the temperature shocks had no large effect.
- **No:** growth at or below the strike, as Bilal and Känzig (QJE 2026) predict.
- A Yes contract pays $1 if the question resolves Yes; a No contract pays $1 if it resolves No. Participants take a financial position on either side, rewarded only for accuracy.
- Each condition also lists a ladder of strikes (term 9). The probabilities are for the headline strike, from 50,000 simulated worlds of each kind (term 8).

## Timeline

| When | What happens |
|---|---|
| Now to mid-Jan 2027 | Proposal circulates for comment. Indicative numbers refresh monthly, after NOAA's monthly release. |
| ~Mid-Jan 2027 | NOAA publishes its 2026 annual value. Final refresh: the end year, conditions, strikes, IMF vintage and code are frozen and archived. |
| Right after | **Conditional contracts list.** |
| ~Mar 2027 | NOAA publishes the winter (DJF) El Niño strength. Prices move; terms do not. |
| ~Mid-Jan 2028 | NOAA publishes its 2027 annual value. **The matching condition converts; the other two are refunded at cost.** |
| Mid-2032 | World Bank publishes the first 2031 figure. |
| **1 Oct 2033** | **Resolve and settle** on the WDI vintage of that date, one revision cycle after the first release. |

## Proposed terms (each open for comment until the freeze)

### 1. Conditioning event: NOAA's 2027 global temperature
- NOAA NCEI Climate at a Glance, global land and ocean surface temperature (NOAAGlobalTemp), January–December mean, °C vs the 1901–2000 average, as published (two decimals): `https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/globe/land_ocean/12/12/1850-2027/data.csv`.
- Read once on 31 January 2028 and archived.
- **Conditions:** cool, 1.45 °C or lower; central, 1.46 to 1.53 °C; warm, 1.54 °C or higher. For scale, the 2024 record is 1.25 °C.
- How the ranges were set: the 20th, 50th and 80th percentiles of the current 2027 forecast (1.41, 1.49 and 1.58 °C), split halfway between neighbours, so each range is about one-third likely today. The forecast is the filter's expectation for 2027 (1.20 °C) plus an ENSO-regression forecast of the 2027 shock (+0.24 ± 0.10 °C), with winter (DJF) RONI assumed ~N(2.6, 0.35). The ranges freeze with the other terms.
- **Fallback:** if NOAA has published no 2027 annual value by 31 March 2028, use NASA GISTEMP v4 (`GLB.Ts+dSST.csv`, column `J-D`) minus the fixed GISTEMP − NOAA offset (2016–2025 mean, +0.007 °C).

### 2. Settlement event: world GDP per capita growth, 2026 to 2031
- World Bank WDI `NY.GDP.PCAP.PP.KD` (GDP per capita, PPP, constant 2021 international $), country `WLD`.
- **Growth = 100 × ln(y2031 / y2026) / 5**, both levels from the single resolution-date vintage, so PPP rebasings and level revisions cancel. Computed to two decimals; **Yes if strictly greater than the strike.**
- This is average log growth. At these rates it is within 0.03 points of the compound annual rate.
- 2026 is the last full year before listing, so none of the growth being measured (2027–2031) is known when the contracts list.

### 3. End year: 2031, chosen by a fixed rule
- **Rule:** among end years 2028–2037, the one with the highest Youden J between simulated "no effect" and "paper right" outcomes, to two decimals; a tie goes to the earlier year.
  - J = P(resolves No | paper right) + P(resolves Yes | no effect) − 1. It rewards a contract that resolves in line with whichever view is true, and favours neither side.
  - It uses only information available before listing: the paper's published response, the IMF projection and its error record, and temperature forecasts. It uses no GDP data after 2025.

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

- **Why separation peaks at 2031:**
  - The paper's response deepens for six years after a shock, so the predicted gap grows through 2031.
  - Uncertainty about background growth grows with every added year.
  - After 2031 the 2023–24 shocks start to recover in the paper's response.
- 2030 comes next (J 0.67 against 0.68). The end year freezes with the other terms.

### 4. Shock definition (frozen coefficients)
- `s_t = T_t − (0.038438 + 0.496114·T_(t−2) + 0.485010·T_(t−3))`.
  - These are the Hamilton h=2, p=2 coefficients fitted on NOAA over the paper's own window (dependent years 1953–2022, data from 1950; paper footnote 2), on the archived 17 Oct 2026 annual vintage. They are not re-estimated, so the 2023–27 warmth is measured out of sample instead of helping to fit the trend it is measured against.
  - Refitting through 2025 would shrink each 2023–27 shock by about 0.04–0.05 °C (gap 5.0 points, J 0.62).
- **Innovations** `u_t = s_t − (0.008832 + 0.362637·s_(t−1) − 0.377483·s_(t−2))`.
  - This matches how the paper's regression defines its response and avoids double counting back-to-back warm years.
  - The alternative, raw shocks, gives a predicted shortfall of −6.6 points (J 0.71).

### 5. The paper's prediction (frozen)
- Bilal–Känzig time-series local projection of log world real GDP per capita, PWT sample 1960–2019 (paper Fig. III), in 100×log points per 1 °C shock:
  - `−1.7946, −2.4754, −4.5536, −6.4967, −9.1359, −11.7698, −12.1094, −11.2642, −10.9062, −5.6482, −6.8999` (h = 0…10).
- Held at its h=10 value beyond h=10. Uncertainty from the archived 4,000 wild-bootstrap draws (seed 123).
- **Shocks that count:** all shocks since 2015 whose effects change after 2026, plus simulated shocks for 2028–2031 (term 7). Contribution to the predicted 2026–2031 shortfall (point estimate, central temperatures):

| Shocks | Points |
|---|---|
| 2015–2022 | −0.5 |
| 2023–2025 | −2.6 |
| 2026–2027 (El Niño) | −3.8 |
| 2028–2031 (simulated, cooler years after the El Niño) | 0.0 |
| **Total** | **−6.9** |

- These shocks lower 2026–2031 growth by 6.8 points (90% range −11.0 to −2.9; response and temperature uncertainty). In the paper's world the background is also 0.9 points better than the IMF's raw record (term 6), so the two worlds differ by **5.9 points** on average.

### 6. No-effect baseline: the IMF projection
- IMF World Economic Outlook, October 2026 (DataMapper, retrieved 17 Oct 2026): world real GDP growth 2027 3.4%, 2028 3.3%, 2029 3.2%, 2030 3.1%, 2031 3.1%; world population from the same release.
- Per-capita growth = 100·ln(1 + g/100) − 100·Δln(population), plus the 1991–2025 mean gap between WDI and IMF-implied per-capita growth (−0.07 points; correlation 0.99).
- Baseline per-capita growth: 2027 2.42%, 2028 2.34%, 2029 2.26%, 2030 2.15%, 2031 2.14%; **mean 2.26% a year** (the 2000–2019 average was 2.29%). Beyond 2031 the 2031 rate is held.
- Frozen at the October 2026 vintage: the January 2027 WEO Update usually appears after mid-January and projects only two years.
- **Spread:** the IMF's own historical forecast errors for world real GDP growth, by years ahead, resampled as whole forecast paths so that multi-year misses (recessions, slowdowns) keep their persistence, then smoothed so the distribution is continuous. The errors are those of the October World Economic Outlooks of 1990–2020 (31 forecasts, IMF Historical WEO Forecasts Database), measured against the October 2026 WEO's estimates of what happened. Years past the IMF's six-year horizon are drawn independently from its six-year-ahead errors (misses in neighbouring years are close to uncorrelated). **The IMF's average miss is kept:** over five-year windows like 2027–2031, world growth came in 3.1 points in total below the IMF's forecast on average (about 0.6 a year; sd 2.7), and below it in 27 of 31 windows. So with no temperature effect, growth is expected to average 1.65% a year, not the IMF's 2.26%. In the paper's world the background leaves out the part of those misses that the paper's own estimates put down to temperature shocks (0.9 of the 3.1 points on average), because its climate damage enters through the shocks since 2015 instead.
- With no temperature effect, average growth 2026–2031 has a 10–90% range of 1.0% to 2.3% a year. This spread, not the temperature record, is the largest uncertainty in the contract.

### 7. Temperatures after 2027 (simulated, part of the paper's prediction)
- Strong El Niños are usually followed by cooler years. After a strong El Niño winter (RONI ≥ 1.5, true in virtually every simulated 2027), each simulated path replays the winters that followed one of the seven strong El Niños since 1950 (1958, 1966, 1973, 1983, 1992, 1998, 2016). Otherwise winter RONI follows an AR(2).
- Each year's shock is the ENSO regression's prediction plus a resampled residual; volcanic years stay in the residual pool.
- Mean simulated shocks: 2028 +0.08 °C, 2029 −0.09 °C, 2030 +0.08 °C.
- They are measured with the same frozen filter (term 4). The cooling that usually follows a strong El Niño is then partly or fully offset, because the paper's filter, fitted before the 2023–24 jump, still counts a lasting warmer level as positive shocks, as the paper's method would.
- Under the paper's estimate, the simulated years change 2026–2031 growth by −0.05 points (90% range −1.9 to +1.9). Without them the cutoff would be 1.10% a year and J 0.69.
- The strikes are fixed in advance: actual 2028–2031 temperatures do not change them.

### 8. Strikes: the cutoff within each condition
- For each condition: 50,000 simulated worlds with no temperature effect and 50,000 with the paper's effect (common random numbers, seed 20261017), with NOAA's 2027 value drawn from the forecast within the condition's range.
- The cutoff is the growth rate that maximises J (tolerance 0.0025); the **headline strike** is the cutoff rounded to 0.1 point.

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
- When NOAA publishes its 2027 annual value, positions in the contracts whose condition was met convert to the unconditional contract with the same question and strike, at the same cost basis.
- Positions in the other conditions' contracts are refunded at cost; fees are not refunded.
- More strikes may be listed after conversion. The cutoff for the realised 2026 and 2027 values comes from `python -I run_analysis.py --lock <T2026> <T2027>` on the archived data (`outputs/threshold_grid.csv` shows how it moves).

### 11. Resolution and settlement
- **1 Oct 2033.** Retrieve the WDI series once, archive the response and its `lastupdated` field, and compute growth with the archived code.
- If 2026 or 2031 is missing from that vintage, use the latest vintage that has both. If none exists by 1 Oct 2034, the contracts are void.
- If the indicator is discontinued, use its official successor (world GDP per capita, PPP, constant prices). Otherwise void.

### 12. Acknowledged limits
- One outcome cannot confirm or refute the paper. A global recession year can move five-year growth by several points; 2020 alone was −3.9%.
- Under the paper's estimate, GDP per capita still grows (about 0.5% a year, against 1.6% with no effect). The test is the shortfall against the baseline.
- The 2024 shock (+0.35 °C with NOAA) already exceeds the largest in the filter's sample (+0.27 °C, 2016), so the test relies on the paper's linear scaling.
- It tests the paper's response to the whole 2023–27 warm sequence, not the El Niño alone. If only the 2026–27 shocks mattered, the unconditional contract would resolve No only 51% of the time.
- The response was estimated with Berkeley Earth shocks and is applied to NOAA shocks; the two track each other closely (corr 0.990, 1960–2019).

### 13. Objections we expect
Who would raise each, the answer, and whether the design addresses it or it stays a caveat:

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

### Open questions for comment
- A low-power clause or no-decision zone for the cool condition (J 0.63)?
- Should an unconditional contract also list from the start, alongside the three conditional ones?

## What changed on 30 Oct 2026
- Three conditional contracts on NOAA's 2027 value replace a single contract whose cutoff was to be computed from the final 2027 value on 1 March 2028.
- Growth is measured from 2026 (was 2027): the contracts list right after NOAA's 2026 value, before any 2027 growth is known. J 0.68, against 0.60 from 2027.
- The end year (2031) is chosen by a fixed rule, explained in term 3.
- The no-effect baseline is the IMF projection. The previous frozen 2000–2019 drift (2.29%/yr) is kept as a sensitivity (J 0.66).
- Simulated temperatures after 2027 enter the paper's prediction; they change the gap by −0.05 points (J 0.69 without them).
- The spread of background growth comes from the IMF's own forecast record (October WEOs 1990–2020), replacing a stand-in, and keeps the IMF's average miss, so the no-effect expectation is below the IMF's projection.
- After checking the design against the paper and its online appendix: the temperature-shock filter is fitted on the paper's own window (data 1950–2022) and frozen, so the 2023–27 warmth is measured out of sample; in the paper's world the background leaves out the part of the IMF's past misses that the paper puts down to temperature shocks (0.9 points); and simulated post-2027 temperatures are measured with the same filter. See term 13 for the objections these answer.
- With these changes the end-year rule picks 2031 (J 0.68); 2030 comes next (J 0.67 against 0.68). The strikes are 1.2 / 1.1 / 1.0% (cool / central / warm); they were 2.0 / 1.9 / 1.8% for growth to 2030 before the IMF record was added.
- The question asks whether growth will be **more than** the strike: Yes means no large effect, No is the outcome the paper predicts.

## What changed on 31 Oct 2026
- Term 13 now cites the paper's own GDP-weighted panel (App. Fig. B.10, −9.9% at year 6) and checks the paper-side spread with wider draws (cutoff 1.09% a year, J 0.64). The contracts and strikes are unchanged.
