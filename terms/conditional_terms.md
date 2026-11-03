# World GDP per Capita Growth, Conditional on NOAA's 2027 Global Temperature (WGDPCT): Contract Terms and Conditions

*Draft for comment, 2026-10-31. Proposed by Patrick T. Brown for listing on ForecastEx, in the layout of ForecastEx's published contract terms; ForecastEx sets the final wording, product codes, listings and thresholds. The end year, the ranges, the thresholds and the chances are indicative and refresh monthly with the analysis until the terms freeze in mid-January 2027.*

## Proposed terms

**Sample Question:** If NOAA's 2027 global temperature is [range], will world GDP per capita grow by more than [##]% a year, on average, from 2026 to 2031?

**Variables:** [range]: one of three ranges of NOAA's 2027 annual global temperature, in °C above the 1901–2000 average: cool, 1.45 °C or lower; central, 1.46 to 1.53 °C; warm, 1.54 °C or higher. [##]: the growth threshold, in percent a year.

**Product Code:** WGDPCT (proposed; ForecastEx assigns product codes).

**Instructions:** These are conditional contracts and work as ForecastEx's conditional contracts do. Three sets list together, one for each range, each with the thresholds of the plain contract (WGDPC). At the Conversion Time, positions in the range that contains NOAA's 2027 value convert into the WGDPC contract with the same threshold, at the same cost basis; positions in the other two ranges are refunded at cost, and fees are not refunded. Converted positions then resolve as WGDPC contracts. This contract is not subject to early Resolution.

**Conditioning Event:** NOAA's 2027 annual global temperature: NOAA NCEI Climate at a Glance, global land and ocean surface temperature (NOAAGlobalTemp), January–December 2027, in °C above the 1901–2000 average, as published to two decimals, at https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/globe/land_ocean/12/12/1850-2027/data.csv. Each two-decimal value falls in exactly one range. This is the baseline of ForecastEx's Global Temperature contract (GT); its Annual Global Temperature Threshold contract (GTTA) states temperatures against 1850–1900 instead. For scale, NOAA's 2024 value, the record so far, is 1.25 °C.

**Conversion Time:** 31 January 2028, 10:00 AM CT (proposed), when NOAA's 2027 value is read once and archived. If NOAA has not published it by then, Conversion waits for it. If it is still unpublished on 31 March 2028, the conditioning value is NASA GISTEMP v4's 2027 annual value (https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv, column J-D) minus a fixed offset of +0.007 °C (the 2016–2025 mean of GISTEMP minus NOAA), read that day.

**Underlying (after Conversion):** Average annual growth of world GDP per capita from 2026 to 2031: 100 × ln(GDP per capita in 2031 ÷ GDP per capita in 2026) ÷ 5, rounded to two decimals. GDP per capita is the WDI series NY.GDP.PCAP.PP.KD (GDP per capita, PPP, constant 2021 international $) for the World aggregate (code WLD), available at https://api.worldbank.org/v2/country/WLD/indicator/NY.GDP.PCAP.PP.KD?format=json&per_page=500 (the indicator's page, https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.KD?locations=1W, shows the same series). Both years come from the WDI vintage current at the Resolution Time, so a revision of levels or a new price-comparison (PPP) base that moves both years cancels out. The contract resolves Yes if growth is strictly greater than [##]% a year, and No otherwise. No other GDP series, estimate or projection is used. Links are given for information; the Source Agency may publish the data elsewhere.

**Source Agencies:** NOAA National Centers for Environmental Information (the Conditioning Event); World Bank, World Development Indicators (the Underlying).

**Minimum Tick:** $0.01.

**Listing Cycle:** One set of three ranges, proposed to list right after NOAA publishes its 2026 annual global temperature (expected mid-January 2027), alongside the plain contract (WGDPC). ForecastEx lists expirations at its discretion.

**Thresholds:** Proposed for each range: 0.1, 0.3, 0.5, 0.7, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.7, 1.9 and 2.1% a year, the same as WGDPC. The headline thresholds are 1.2% (cool), 1.1% (central) and 1.0% (warm). ForecastEx lists thresholds at its discretion.

**Position Accountability:** 250,000 contracts in any one Forecast Market (ForecastEx's standard level).

**Last Trading Time:** The Conversion Time. Converted positions go on trading as WGDPC contracts.

**Payout Criteria:** Positions refunded at the Conversion Time receive their cost; fees are not refunded. Converted positions settle as WGDPC contracts. Each contract settles at $1.00 or $0.00. If the outcome is Yes, each Yes contract receives $1.00 and each No contract $0.00; if it is No, each No contract receives $1.00 and each Yes contract $0.00.

**Incentive Coupon:** Positions earn ForecastEx's monthly incentive coupon, based on the contract's daily settlement value, at no less than the minimum rate set in ForecastEx Rule 612(c).

**Resolution Time:** For converted positions, the same as WGDPC: 1 October 2033, 10:00 AM CT (proposed). The WDI series is read once at that time; the response, its lastupdated date and the growth computed from it are published with these terms.

**Changes in Resolution Time:** ForecastEx's standard provisions apply to the Conversion Time, with NOAA as the Source Agency, and to the Resolution Time of converted positions, with the World Bank. If the Source Agency delays the data, Conversion or Resolution waits for them; if it changes its release schedule, ForecastEx may move the Conversion Time or Resolution Time to match; and ForecastEx may open its event review under Rule 415, which can delay either. ForecastEx posts a public notice in each case. For converted positions, two more provisions apply:

1. **Missing years.** If the vintage current at the Resolution Time has no value for 2026 or 2031, the contract resolves on the most recent earlier vintage that has both (the World Bank keeps past WDI vintages in its database archives) or, if none does, on the first later vintage that does. If no vintage has both by 1 October 2034, ForecastEx cancels the contract and refunds every position at cost.
2. **Discontinued series.** If the World Bank discontinues the series, the contract uses its official successor (world GDP per capita, PPP, constant prices). If there is none, ForecastEx cancels the contract and refunds every position at cost.

**Expiration Time:** For refunded positions, the Conversion Time; for converted positions, the Resolution Time.

**Settlement Time:** Under ForecastEx Rule 603(b)(3): at 1:00 PM CT on the day of Resolution if Resolution comes before noon CT, otherwise at 1:00 PM CT the following day.

**Trading Restrictions:** Under ForecastEx Rule 509(h), no one may trade this contract who has material non-public information about it, is an employee of either Source Agency, or has any direct or indirect influence over its outcome.

## Notes for comment (not part of the exchange terms)

### What the contracts test

Bilal and Känzig (2026) estimate that a 1 °C global temperature shock lowers world GDP per capita by about 12% six years later. Applied to the temperature shocks since 2015, their estimate predicts growth of about 0.5% a year from 2026 to 2031, against 1.6% with no temperature effect (the IMF's projection less its average past miss). A warmer 2027 means a bigger predicted shortfall, so the threshold that best separates the two views falls as 2027 warms. Conditioning on NOAA's 2027 value lets each range carry its own threshold, set before 2027's temperature is known.

### The three ranges

| Range of NOAA's 2027 value | Chance today | Headline threshold | Chance of Yes if no effect | Chance of Yes if the paper is right | J |
|---|---|---|---|---|---|
| Cool: 1.45 °C or lower | 34% | 1.2% | 82% | 20% | 0.63 |
| Central: 1.46 to 1.53 °C | 33% | 1.1% | 87% | 18% | 0.69 |
| Warm: 1.54 °C or higher | 34% | 1.0% | 90% | 16% | 0.74 |

The ranges are split halfway between the 20th, 50th and 80th percentiles of the current 2027 forecast (1.41, 1.49 and 1.58 °C), so each is about one-third likely today. Within each range, the headline threshold is the growth rate that best separates the two views, rounded to 0.1 point. These are not prices. Each is the chance of Yes in one of two sets of 50,000 simulated worlds (common random numbers, seed 20261017): one in which temperature shocks have no effect on GDP, and one in which Bilal and Känzig's (2026) estimate holds. These terms never combine the two into one number.

For example, if NOAA's 2027 value is 1.49 °C, a central-range position at 1.1% becomes a WGDPC 1.1% position at the same cost, and cool- and warm-range positions are refunded at cost.

### Chance of Yes at every threshold

| Threshold | Cool: P(Yes) no effect / paper | Central | Warm |
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

Each cell gives the chance of Yes if temperature shocks have no effect / if the paper is right; headline thresholds are in bold. With no effect, 2027's temperature does not matter, so the first number is the same in every column.

### Timeline

| When | What happens |
|---|---|
| Now to mid-January 2027 | Comment period. The indicative numbers refresh monthly. |
| Mid-January 2027 | NOAA publishes its 2026 annual value and the terms freeze. The plain contract (WGDPC) and the conditional contracts (WGDPCT) list. |
| 31 January 2028 | NOAA's 2027 value is read. Conditional positions in the matching range convert into WGDPC; the other two ranges are refunded at cost. |
| Mid-2032 | The World Bank publishes its first estimate for 2031. |
| 1 October 2033 | Resolution on the WDI vintage current that day, then settlement. |

### Data and code

Every number here comes from the analysis's latest run (outputs/results.json, 2026-10-31), and build_docs.py rewrites these terms from it at each monthly refresh until the freeze. The code, the published run and its data are at https://github.com/ptbrown31/climate-gdp-contract. The contract's page, https://weather.weatherclimatehumansystems.org/climate-gdp.html, re-runs the model in the browser with its main assumptions on controls. CONTRACT_TERMS.md sets out the full design, the reason for each choice and the objections we expect.
