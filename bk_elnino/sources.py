"""Download and parse primary data sources, recording the vintage of every file.

Each source is saved to its own directory under ``data/raw/<name>/`` together with a
``vintage.json`` holding the URL, retrieval time (UTC), HTTP Last-Modified header and
SHA-256 of the bytes, so a settlement run can show exactly which data it used.
"""
from __future__ import annotations

import hashlib
import io
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

USER_AGENT = "bk-elnino-research/1.0 (python urllib)"


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    filename: str


SOURCES = {
    "gistemp": Source(
        "gistemp",
        "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
        "GLB.Ts+dSST.csv",
    ),
    "berkeley": Source(
        "berkeley",
        "https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com/Global/Land_and_Ocean_summary.txt",
        "Land_and_Ocean_summary.txt",
    ),
    # NOAA Climate at a Glance (NOAAGlobalTemp), deg C vs 1901-2000: the contract's temperature
    # record. Annual = 12-month mean ending December; monthly for the in-year nowcast. The URL
    # names an end year ("{end}"), filled in at download time; see fetch().
    "noaa": Source(
        "noaa",
        "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/"
        "globe/land_ocean/12/12/1850-{end}/data.csv",
        "noaa_globaltemp_annual.csv",
    ),
    "noaa_monthly": Source(
        "noaa_monthly",
        "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/"
        "globe/land_ocean/1/0/1850-{end}/data.csv",
        "noaa_globaltemp_monthly.csv",
    ),
    "oni": Source("oni", "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt", "oni.ascii.txt"),
    "wdi_gdppc_ppp": Source(
        "wdi_gdppc_ppp",
        "https://api.worldbank.org/v2/country/WLD/indicator/NY.GDP.PCAP.PP.KD?format=json&per_page=500",
        "WLD_NY.GDP.PCAP.PP.KD.json",
    ),
    "wdi_gdppc_usd": Source(
        "wdi_gdppc_usd",
        "https://api.worldbank.org/v2/country/WLD/indicator/NY.GDP.PCAP.KD?format=json&per_page=500",
        "WLD_NY.GDP.PCAP.KD.json",
    ),
}


def candidate_urls(url: str) -> list[str]:
    """URLs to try, newest first. Climate-at-a-Glance URLs name an end year and return 404 for a
    year with no data yet (e.g. early January), so try this year and then the previous one."""
    if "{end}" not in url:
        return [url]
    year = datetime.now(timezone.utc).year
    return [url.format(end=year), url.format(end=year - 1)]


def fetch(source: Source, raw_dir: Path, refresh: bool = False) -> Path:
    """Download ``source`` into ``raw_dir/<name>/`` unless already cached."""
    out_dir = raw_dir / source.name
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / source.filename
    if path.exists() and not refresh:
        return path
    body = last_modified = used = None
    misses = []
    for url in candidate_urls(source.url):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
                last_modified = resp.headers.get("Last-Modified")
            used = url
            break
        except urllib.error.HTTPError as err:
            if err.code != 404:
                raise
            misses.append(url)
    if body is None:
        raise RuntimeError(f"{source.name}: no data at {misses}")
    path.write_bytes(body)
    meta = {
        "url": used,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "http_last_modified": last_modified,
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
    }
    (out_dir / "vintage.json").write_text(json.dumps(meta, indent=2))
    return path


def fetch_all(raw_dir: Path, refresh: bool = False) -> dict[str, Path]:
    return {name: fetch(src, raw_dir, refresh) for name, src in SOURCES.items()}


def vintage(raw_dir: Path, name: str) -> dict:
    p = raw_dir / name / "vintage.json"
    return json.loads(p.read_text()) if p.exists() else {}


# --------------------------------------------------------------------------- parsers

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def read_gistemp(path: Path) -> tuple[pd.Series, pd.DataFrame]:
    """Return (annual J-D anomaly for complete years, monthly table Year x Jan..Dec).

    Anomalies are degC relative to 1951-1980. Incomplete years have J-D = '***' and are
    excluded from the annual series (never filled).
    """
    df = pd.read_csv(path, skiprows=1, na_values=["***", "****"])
    df = df.rename(columns=lambda c: c.strip())
    df["Year"] = df["Year"].astype(int)
    df = df.set_index("Year")
    monthly = df[MONTHS].astype(float)
    annual = df["J-D"].astype(float).dropna()
    # guard: J-D must equal the mean of 12 months where all are present
    full = monthly.dropna()
    gap = (full.mean(axis=1).round(2) - annual.reindex(full.index)).abs().max()
    if gap > 0.011:
        raise ValueError(f"GISTEMP J-D does not match monthly means (max gap {gap})")
    if annual.index.duplicated().any():
        raise ValueError("duplicate years in GISTEMP")
    return annual.rename("gistemp"), monthly


def read_berkeley_summary(path: Path) -> pd.Series:
    """Berkeley Earth Land+Ocean annual anomaly (air temperature over sea ice version).

    The summary file holds two tables (sea ice as air temperature, then as water
    temperature); we take the first, which is Berkeley's headline series.
    """
    rows, tables = [], []
    for line in path.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("%"):
            if rows:
                tables.append(rows)
                rows = []
            continue
        parts = s.split()
        try:
            rows.append((int(parts[0]), float(parts[1])))
        except (ValueError, IndexError):
            continue
    if rows:
        tables.append(rows)
    first = max(tables[:1], key=len)
    ser = pd.Series({y: v for y, v in first}, name="berkeley").sort_index()
    return ser


def read_noaa_cag(path: Path) -> pd.Series:
    """NOAA Climate-at-a-Glance global land-ocean annual (12-month ending Dec) anomaly."""
    text = path.read_text()
    lines = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    # header lines are descriptive; data lines are YYYY12,value or YYYY,value
    recs = []
    for ln in lines:
        parts = ln.split(",")
        if len(parts) < 2:
            continue
        key = parts[0].strip()
        try:
            year = int(key[:4])
            val = float(parts[1])
        except ValueError:
            continue
        recs.append((year, val))
    ser = pd.Series(dict(recs), name="noaa").sort_index()
    return ser


def read_noaa_monthly(path: Path) -> pd.DataFrame:
    """NOAA Climate-at-a-Glance monthly global anomalies -> Year x Jan..Dec (NaN where missing)."""
    recs = {}
    for ln in path.read_text().splitlines():
        parts = ln.split(",")
        key = parts[0].strip()
        if len(parts) < 2 or len(key) != 6 or not key.isdigit():
            continue  # comment lines and the "Date,..." header
        recs[(int(key[:4]), int(key[4:]))] = float(parts[1])
    if not recs:
        raise ValueError(f"no monthly values in {path}")
    years = range(min(y for y, _ in recs), max(y for y, _ in recs) + 1)
    tab = pd.DataFrame(np.nan, index=pd.Index(years, name="Year"), columns=MONTHS)
    for (y, m), v in recs.items():
        tab.loc[y, MONTHS[m - 1]] = v
    return tab


def read_oni(path: Path) -> pd.DataFrame:
    """CPC ONI table: columns season (e.g. 'DJF'), year, total, anom."""
    df = pd.read_csv(path, sep=r"\s+")
    df.columns = ["season", "year", "total", "anom"]
    df["year"] = df["year"].astype(int)
    return df


def read_wdi_json(path: Path) -> tuple[pd.Series, dict]:
    """World Bank API JSON -> (Series by year, header metadata incl. lastupdated)."""
    payload = json.loads(path.read_text())
    header, data = payload[0], payload[1]
    recs = {}
    for d in data:
        if d.get("value") is None:
            continue
        recs[int(d["date"])] = float(d["value"])
    ser = pd.Series(recs).sort_index()
    if (ser <= 0).any():
        raise ValueError("non-positive GDP per capita in WDI data")
    if ser.index.duplicated().any():
        raise ValueError("duplicate WDI years")
    years = np.arange(ser.index.min(), ser.index.max() + 1)
    if len(years) != len(ser):
        raise ValueError(f"WDI series has interior gaps: {sorted(set(years) - set(ser.index))}")
    meta = {"lastupdated": header.get("lastupdated"), "sourceid": header.get("sourceid"),
            "indicator": data[0]["indicator"] if data else None}
    return ser, meta


def read_bk_ts(path: Path) -> pd.DataFrame:
    """Authors' Stata time-series file (micc_pwt_ts.dta / micc_bu_ts.dta), indexed by year."""
    df = pd.read_stata(path, convert_categoricals=False)
    df["year"] = df["year"].astype(int)
    return df.set_index("year")


def read_bk_vardata(path: Path) -> pd.DataFrame:
    """Authors' intermediate VAR/bootstrap input (int/vardataS.csv or vardataL.csv)."""
    df = pd.read_csv(io.StringIO(path.read_text()))
    df["year"] = df["year"].astype(int)
    return df.set_index("year")
