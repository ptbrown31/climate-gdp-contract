# World GDP per Capita Growth (WGDPC): Contract Terms and Conditions

*Draft for comment, 2026-10-31. Proposed by Patrick T. Brown for listing on ForecastEx, in the layout of ForecastEx's published contract terms; ForecastEx sets the final wording, product codes, listings and thresholds. The end year, the thresholds and the chances are indicative and refresh monthly with the analysis until the terms freeze in mid-January 2027.*

## Proposed terms

**Sample Question:** Will world GDP per capita grow by more than [##]% a year, on average, from 2026 to 2031?

**Variables:** [##] is the growth threshold, in percent a year.

**Product Code:** WGDPC (proposed; ForecastEx assigns product codes).

**Instructions:** The World Bank updates its World Development Indicators (WDI) several times a year. Its first estimate of world GDP per capita for 2031 usually appears in mid-2032, and revisions follow. This contract resolves on the vintage current on 1 October 2033, about one revision cycle later, with both years read from that one vintage. This contract is not subject to early Resolution.

**Underlying:** Average annual growth of world GDP per capita from 2026 to 2031, computed as 100 × ln(GDP per capita in 2031 ÷ GDP per capita in 2026) ÷ 5 and rounded to two decimals. GDP per capita is the WDI series NY.GDP.PCAP.PP.KD (GDP per capita, PPP, constant 2021 international $) for the World aggregate (code WLD), available at https://api.worldbank.org/v2/country/WLD/indicator/NY.GDP.PCAP.PP.KD?format=json&per_page=500 (the indicator's page, https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.KD?locations=1W, shows the same series). Both years come from the WDI vintage current at the Resolution Time, so a revision of levels or a new price-comparison (PPP) base that moves both years cancels out. The contract resolves Yes if growth is strictly greater than [##]% a year, and No otherwise. No other GDP series, estimate or projection is used. Links are given for information; the Source Agency may publish the data elsewhere.

**Source Agency:** World Bank, World Development Indicators (compiled by its Development Data Group).

**Minimum Tick:** $0.01.

**Listing Cycle:** One expiration, for growth from 2026 to 2031, proposed to list right after NOAA publishes its 2026 annual global temperature (expected mid-January 2027), alongside the conditional contracts (ZGTWGDPC). ForecastEx lists expirations at its discretion.

**Thresholds:** The proposed thresholds are 0.1, 0.3, 0.5, 0.7, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.7, 1.9 and 2.1% a year. The conditional contracts (ZGTWGDPC) list the same thresholds, so every conditional position has a contract here to convert into. The 1.1% contract is the flagship, also set out in its own terms. ForecastEx lists thresholds at its discretion.

**Position Accountability:** 250,000 contracts in any one Forecast Market (ForecastEx's standard level).

**Last Trading Time:** Same as the Resolution Time.

**Payout Criteria:** Each contract settles at $1.00 or $0.00. If the outcome is Yes, each Yes contract receives $1.00 and each No contract $0.00; if it is No, each No contract receives $1.00 and each Yes contract $0.00.

**Incentive Coupon:** Positions earn ForecastEx's monthly incentive coupon, based on the contract's daily settlement value, at no less than the minimum rate set in ForecastEx Rule 612(c).

**Resolution Time:** 1 October 2033, 10:00 AM CT (proposed). The WDI series is read once at that time; the response, its lastupdated date and the growth computed from it are published with these terms.

**Changes in Resolution Time:** ForecastEx's standard provisions apply. If the Source Agency delays the data, Resolution waits for them; if it changes its release schedule, ForecastEx may move the Resolution Time to match; and ForecastEx may open its event review under Rule 415, which can delay Resolution. ForecastEx posts a public notice in each case. Two more provisions apply to this contract:

1. **Missing years.** If the vintage current at the Resolution Time has no value for 2026 or 2031, the contract resolves on the most recent earlier vintage that has both (the World Bank keeps past WDI vintages in its database archives) or, if none does, on the first later vintage that does. If no vintage has both by 1 October 2034, ForecastEx cancels the contract and refunds every position at cost.
2. **Discontinued series.** If the World Bank discontinues the series, the contract uses its official successor (world GDP per capita, PPP, constant prices). If there is none, ForecastEx cancels the contract and refunds every position at cost.

**Expiration Time:** Same as the Resolution Time.

**Settlement Time:** Under ForecastEx Rule 603(b)(3), settlement takes place at 1:00 PM CT on the day of Resolution if Resolution comes before noon CT, and at 1:00 PM CT the following day otherwise.

**Trading Restrictions:** Under ForecastEx Rule 509(h), no one may trade this contract who has material non-public information about it, is an employee of the Source Agency, or has any direct or indirect influence over its outcome.

## Notes for comment (not part of the exchange terms)

### What the contract tests

Bilal and Känzig (2026) estimate that a 1 °C global temperature shock lowers world GDP per capita by about 12% six years later. Applied to the temperature shocks since 2015, their estimate predicts growth of about 0.5% a year from 2026 to 2031, against 1.6% with no temperature effect (the IMF's projection less its average past miss). Each threshold asks whether growth beats it. Near the headline threshold, Yes means the temperature shocks had no large effect and No is the outcome the paper predicts; the other thresholds let the market show its whole view of growth.

### Chance of Yes at each threshold

| Threshold | Chance of Yes if temperature shocks have no effect | Chance of Yes if the paper is right |
|---|---|---|
| 0.1% | 100% | 70% |
| 0.3% | 99% | 60% |
| 0.5% | 98% | 48% |
| 0.7% | 96% | 37% |
| 0.9% | 92% | 27% |
| 1.0% | 90% | 22% |
| **1.1%** | **87%** | **18%** |
| 1.2% | 82% | 15% |
| 1.3% | 77% | 12% |
| 1.5% | 62% | 7% |
| 1.7% | 45% | 4% |
| 1.9% | 29% | 2% |
| 2.1% | 18% | 1% |

The flagship's threshold is in bold. Each chance comes from one of two sets of 50,000 simulated worlds (common random numbers, seed 20261017), one in which temperature shocks have no effect on GDP and one in which Bilal and Känzig's (2026) estimate holds. These terms never combine the two into one number.

### Growth in each world

With no temperature effect, average growth from 2026 to 2031 has a median of 1.6% a year and an 80% range of 1.0 to 2.3%. If the paper is right, the median is 0.5% a year and the 80% range is −0.5 to 1.4%. At these rates the average log growth in the Underlying is within 0.03 points of the compound annual rate.

### Timeline

| When | What happens |
|---|---|
| Now to mid-January 2027 | Comment period. The indicative numbers refresh monthly. |
| Mid-January 2027 | NOAA publishes its 2026 annual value and the terms freeze. The plain contract (WGDPC) and the conditional contracts (ZGTWGDPC) list. |
| Mid-January 2028 | NOAA publishes its 2027 value, and ForecastEx's GT 2027 contracts resolve on it. Conditional positions in the matching range convert into WGDPC, and the other two ranges are refunded at cost. |
| Mid-2032 | The World Bank publishes its first estimate for 2031. |
| 1 October 2033 | Resolution on the WDI vintage current that day, then settlement. |

### Data and code

Every number here comes from the analysis's latest run (outputs/results.json, 2026-10-31), and build_docs.py rewrites these terms from it at each monthly refresh until the freeze. The code, the published run and its data are at https://github.com/ptbrown31/climate-gdp-contract. The contract's page, https://weather.weatherclimatehumansystems.org/climate-gdp.html, re-runs the model in the browser with its main assumptions on controls. CONTRACT_TERMS.md sets out the full design, the reason for each choice and the objections we expect.
