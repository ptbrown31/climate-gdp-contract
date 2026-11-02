# A forecast contract on world GDP after the 2023–27 temperature shocks

The code and data behind a proposed ForecastEx contract,

> Will world GDP per capita grow by more than 1.1% a year, on average, from 2026 to 2031?

built to test Bilal and Känzig's estimate of what global temperature shocks do to world output
([Quarterly Journal of Economics, 2026](https://doi.org/10.1093/qje/qjag011)), and behind the
contract's page on [weather.weatherclimatehumansystems.org](https://weather.weatherclimatehumansystems.org/),
which re-runs this model in the browser as readers change its assumptions.

Patrick T. Brown. Draft for comment.

## What the code does

1. **Re-estimates the paper's responses** from the authors' replication files: the local
   projections, their wild bootstrap, the country panels (`bk_elnino/lp.py`, `irf.py`, `panel.py`).
   The time-series responses match the authors' Stata output to within 1e-6 points.
2. **Measures temperature shocks** the paper's way, the year's temperature less what the
   temperatures two and three years earlier predict, fitted on the paper's window (data through
   2022), on NOAA's global record (`hamilton.py`, `temperature.py`). 2026 and 2027 carry estimates
   until NOAA publishes their annual values.
3. **Simulates 50,000 paths** of world GDP per person, 2026–2035, under two views: no temperature
   effect (the IMF's October 2026 projection less its average past miss, with the spread of its
   record of misses, `imf_baseline.py`), and the paper's estimate applied to every shock since 2015
   and to simulated shocks after 2027 (`future_temps.py`, `analysis.py`).
4. **Sets the terms** from information available before listing: the end year and the cutoff
   that best separate the two views (Youden's J, `wager.py`), and three contracts conditional on
   NOAA's 2027 value.
5. **Writes the page's data** (`build_site_data.py`, `build_site_article.py`). The page's model,
   `site_tab/js/elnino-model.js`, replays the same 50,000 paths; `tests/test_site_model.py` checks
   it against the run, path by path, on twelve designs.

`MEMO.md` explains every choice and lists the objections we expect, with answers.
`CONTRACT_TERMS.md` states the indicative terms.

## Reproduce

Python 3.10 or later with numpy, pandas, scipy, matplotlib and lxml; node for the page-model test.

**1. The inputs this repository does not redistribute.** The authors' replication package and
shock series, and the IMF's files:

    git clone https://github.com/dkaenzig/micc_replication data/external/micc_replication
    git clone https://github.com/dkaenzig/global-temperature-shocks data/external/global-temperature-shocks

| File | Where it goes | Source | SHA-256 of the copy the published run used |
|---|---|---|---|
| `WEOhistorical.xlsx` | `data/raw/imf_hist/` | [IMF Historical WEO Forecasts Database](https://data.imf.org/-/media/iData/External-Storage/Documents/D2AC2BB4C12C4A8CB2B6DAF1159263EB/en/WEOhistorical.xlsx) | `6b15feaec5d77201a496b44bce59138586e3c9fd32531bcdd60d273879691b84` |
| `NGDP_RPCH.json` | `data/raw/imf/` | [IMF DataMapper API, NGDP_RPCH](https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH) (October 2026 WEO) | `5200170b0f19f025e4e0a4e7685d8d5182e11068bff6ef4c92aea400739f0148` |
| `LP.json` | `data/raw/imf/` | [IMF DataMapper API, LP](https://www.imf.org/external/datamapper/api/v1/LP) (October 2026 WEO) | `9ddc36efbd0d0e8166afa9d00e99526425b3c484daf83f5c230af38213410dd0` |

The public-domain and CC BY series (NOAA, NASA GISTEMP, the Oceanic Niño indices, World Bank WDI)
are in `data/raw/` as the published run downloaded them, each with its `vintage.json` (address,
time and SHA-256); anything missing is downloaded on first use.

**2. Run.**

    python -I run_analysis.py            # on the data as committed: reproduces outputs/ (a few minutes)
    python -I run_analysis.py --refresh  # or download every public series again first
    python -I build_site_data.py         # the page's model files, in site_tab/data/elnino/
    python -I -m pytest tests -q

`outputs/` holds the published run's results (`results.json` and the tables) so they can be read
without running anything. To see the page locally with the public site's styles, clone
[the site](https://github.com/ptbrown31/weatherclimatedashboard) beside this repository and run
`python3 -I site_tab/serve_preview.py`.

## Layout

| Path | What |
|---|---|
| `bk_elnino/sources.py` | Downloads with a `vintage.json` per source; parsers with integrity checks |
| `bk_elnino/hamilton.py`, `temperature.py` | The paper's temperature filter; shocks; 2026 nowcast and the ENSO forecast for 2027 |
| `bk_elnino/lp.py`, `irf.py`, `panel.py` | Local projections, the authors' bootstrap, the country panels, the responses used |
| `bk_elnino/imf_baseline.py`, `baseline.py` | The IMF baseline and its record of misses; the 2000–2019 trend alternative |
| `bk_elnino/future_temps.py` | Simulated temperature shocks after 2027 |
| `bk_elnino/analysis.py`, `wager.py` | Every design choice in one `Design`; the simulation; the contract statistic and cutoff |
| `bk_elnino/objections.py` | The objections we expect, with answers built from `results.json` |
| `run_analysis.py`, `build_docs.py` | The run; `MEMO.md` and `CONTRACT_TERMS.md` from its outputs |
| `build_site_data.py`, `build_site_article.py` | The page's model files and text |
| `site_tab/` | The page: HTML, CSS, its model (`js/elnino-model.js`) and figures (`js/climate-gdp.js`) |
| `docs/article_v2/make_figures.py` | The article's static figures |
| `tests/` | Unit tests, the replication checks, and the page-model check |

## Licence

Code: MIT (`LICENSE`). Data keep their sources' terms: NOAA and NASA, US government works; World
Bank WDI, CC BY 4.0; the IMF's and the authors' files are not included here.
