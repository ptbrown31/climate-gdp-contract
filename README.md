# A forecast contract on world GDP after the 2023–27 temperature shocks

This repository holds the code and data behind a proposed ForecastEx contract that tests Bilal and
Känzig's estimate of what global temperature shocks do to world output
([Quarterly Journal of Economics, 2026](https://doi.org/10.1093/qje/qjag011)). The headline contract
asks whether world GDP per capita will grow by more than 1.1% a year, on average, from 2026 to 2031.
The repository also holds the code behind the contract's page on
[weather.weatherclimatehumansystems.org](https://weather.weatherclimatehumansystems.org/), which
re-runs this model in the browser as readers change its assumptions.

Patrick T. Brown. The design is a draft for comment.

## What the code does

1. **Re-estimates the paper's responses** from the authors' replication files. This covers the local
   projections, their wild bootstrap and the country panels (`bk_elnino/lp.py`, `irf.py`, `panel.py`).
   The time-series responses match the authors' Stata output to within 1e-6 points.
2. **Measures temperature shocks** the paper's way, on NOAA's global record (`hamilton.py`,
   `temperature.py`). A shock is the year's temperature less what the temperatures two and three
   years earlier predict, with the filter fitted on the paper's window (data through 2022). 2026 and
   2027 carry estimates until NOAA publishes their annual values.
3. **Simulates 50,000 paths** of world GDP per person for 2026–2035 under two views. If temperature
   shocks have no effect, growth follows the IMF's October 2026 projection less its average past
   miss, with the spread of its record of misses (`imf_baseline.py`). If the paper is right, its
   response applies to every shock since 2015 and to simulated shocks after 2027 (`future_temps.py`,
   `analysis.py`).
4. **Sets the terms** from information available before listing. It picks the end year and the
   cutoff that best separate the two views (Youden's J, `wager.py`) and defines three contracts
   conditional on NOAA's 2027 value.
5. **Writes the page's data** (`build_site_data.py`, `build_site_article.py`). The page's model,
   `site_tab/js/elnino-model.js`, replays the same 50,000 paths. `tests/test_site_model.py` checks
   it against the run, path by path, on twelve designs.

`MEMO.md` explains every choice and lists the objections we expect, with answers.
`CONTRACT_TERMS.md` states the indicative terms. `terms/` holds the three proposed listing documents
for the plain ladder, the conditional contracts and the flagship contract, in the layout of
ForecastEx's contract terms.

## Reproduction

The code needs Python 3.10 or later with numpy, pandas, scipy, matplotlib and lxml. The page-model
test also needs node.

**1. Inputs fetched separately.** This repository does not redistribute the authors' replication
package, their shock series or the IMF's files. Clone the authors' two repositories from GitHub.

    git clone https://github.com/dkaenzig/micc_replication data/external/micc_replication
    git clone https://github.com/dkaenzig/global-temperature-shocks data/external/global-temperature-shocks

Download each IMF file from its source in the table into the folder shown.

| File | Where it goes | Source | SHA-256 of the copy the published run used |
|---|---|---|---|
| `WEOhistorical.xlsx` | `data/raw/imf_hist/` | [IMF Historical WEO Forecasts Database](https://data.imf.org/-/media/iData/External-Storage/Documents/D2AC2BB4C12C4A8CB2B6DAF1159263EB/en/WEOhistorical.xlsx) | `6b15feaec5d77201a496b44bce59138586e3c9fd32531bcdd60d273879691b84` |
| `NGDP_RPCH.json` | `data/raw/imf/` | [IMF DataMapper API, NGDP_RPCH](https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH) (October 2026 WEO) | `5200170b0f19f025e4e0a4e7685d8d5182e11068bff6ef4c92aea400739f0148` |
| `LP.json` | `data/raw/imf/` | [IMF DataMapper API, LP](https://www.imf.org/external/datamapper/api/v1/LP) (October 2026 WEO) | `9ddc36efbd0d0e8166afa9d00e99526425b3c484daf83f5c230af38213410dd0` |

The public-domain and CC BY series (NOAA, NASA GISTEMP, the Oceanic Niño indices, World Bank WDI)
are in `data/raw/` as the published run downloaded them, each with its `vintage.json` (address,
time and SHA-256). `data/raw/wdi_archive/` holds the World Bank's archived WDI versions of the
world series, which `wdi_revisions.py` reads. Anything missing is downloaded on first use.

**2. Commands.**

    python -I run_analysis.py            # reproduces outputs/ from the data as committed (a few minutes)
    python -I run_analysis.py --refresh  # downloads every public series again, then runs
    python -I build_site_data.py         # the page's model files, in site_tab/data/elnino/
    python -I wdi_revisions.py           # the WDI archive check behind the resolution date
    python -I -m pytest tests -q

`outputs/` holds the published run's results (`results.json` and the tables), so they can be read
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
| `run_analysis.py`, `build_docs.py` | The run; `MEMO.md`, `CONTRACT_TERMS.md` and the listing terms in `terms/` from its outputs |
| `build_site_data.py`, `build_site_article.py` | The page's model files and text |
| `wdi_revisions.py` | When the World Bank's first estimate appears and how much it moves after, from its archive of past WDI versions (`outputs/wdi_revisions.*`) |
| `site_tab/` | The page's HTML, CSS, model (`js/elnino-model.js`) and figures (`js/climate-gdp.js`) |
| `docs/article_v2/make_figures.py` | The article's static figures |
| `tests/` | Unit tests, the replication checks, and the page-model check |

## Licence

The code is under the MIT licence (`LICENSE`). The data keep their sources' terms. NOAA and NASA
data are US government works, World Bank WDI data are CC BY 4.0, and the IMF's and the authors'
files are not included here.
