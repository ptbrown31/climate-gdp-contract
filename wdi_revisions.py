"""When the World Bank's first estimate of world GDP per capita appears, and how much it moves after.

The contracts resolve on the WDI vintage current at 10:00 AM CT on 1 October of the year after the end
year. This script reads the World Bank's archive of past WDI vintages (API source 57, one version per
update, named YYYYMM) for the series the contracts use, NY.GDP.PCAP.PP.KD for the World aggregate. For
each year it finds the first vintage with that year and whether the vintage current on 1 October of
the following year had it. For each end year it compares five-year growth read on that date with the
reading a year later and with the current vintage.

    python3 -I wdi_revisions.py      # fetches missing vintages into data/raw/wdi_archive/, writes outputs/wdi_revisions.*

The archive dates each vintage by month only, so a vintage is taken to be current from its month until
the next one: the vintage current on 1 October is the latest one named September or earlier. Growth is
100 x ln(Y_t / Y_t-5) / 5, as in the contracts. The World Bank moved the series to new PPP bases in May
2014, May 2020 and May 2024, and rows whose two readings straddle a move are flagged. The revision
statistics use end years from 2010, the first year whose first estimate appeared by July, as every
year's has since.
"""
from __future__ import annotations

import csv
import json
import math
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw" / "wdi_archive"
OUT = ROOT / "outputs"
API = "https://api.worldbank.org/v2/sources/57"
SERIES, COUNTRY = "NY.GDP.PCAP.PP.KD", "WLD"
PPP_MOVES = ("201405", "202005", "202405")   # 2011, 2017 and 2021 PPPs (datahelpdesk.worldbank.org, article 906522)
REVISION_FROM = 2010


def fetch(url: str, path: Path, refresh: bool = False) -> dict:
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    for k in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                body = r.read()
            path.write_bytes(body)
            return json.loads(body)
        except Exception as e:  # noqa: BLE001 - retried, then the cached copy or a stop
            print(f"retry {url}: {e}", file=sys.stderr)
            time.sleep(2 + 3 * k)
    if path.exists():
        return json.loads(path.read_text())
    sys.exit(f"could not fetch {url}")


def vintages() -> dict[str, dict[int, float]]:
    RAW.mkdir(parents=True, exist_ok=True)
    listing = fetch(f"{API}/version?format=json&per_page=500", RAW / "versions.json", refresh=True)
    out = {}
    for v in sorted(x["id"] for x in listing["source"][0]["concept"][0]["variable"]):
        d = fetch(f"{API}/country/{COUNTRY}/series/{SERIES}/version/{v}/time/all?format=json&per_page=500",
                  RAW / f"{COUNTRY}_{v}.json")
        rows = d.get("source", {}).get("data") or []
        vals = {int(next(c["id"] for c in r["variable"] if c["concept"] == "Time")[2:]): float(r["value"])
                for r in rows if r.get("value") is not None}
        if vals:
            out[v] = vals
    return out


def main():
    S = vintages()
    V = sorted(S)
    today = date.today()

    def current(y: int, m: int) -> str | None:
        """The vintage current on the first day of the month after (y, m)."""
        c = [v for v in V if v <= f"{y}{m:02d}"]
        return c[-1] if c else None

    def passed(y: int, m: int) -> bool:
        return (y, m) < (today.year, today.month)

    def g5(v: str, t: int) -> float | None:
        s = S[v]
        return 100 * math.log(s[t] / s[t - 5]) / 5 if t in s and t - 5 in s else None

    avail = []
    for t in range(max(S[V[0]]) + 1, max(max(s) for s in S.values()) + 1):   # years the archive can date
        if not passed(t + 1, 10):
            break
        first = next(v for v in V if t in S[v])
        a = current(t + 1, 9)
        avail.append({"year": t, "first_vintage": first, "vintage_1oct_next": a, "on_1oct_next": t in S[a]})

    rev = []
    latest = V[-1]
    for t in range(REVISION_FROM, today.year):
        if not passed(t + 2, 10):
            break
        a, b = current(t + 1, 9), current(t + 2, 9)
        ga, gb, gl = g5(a, t), g5(b, t), g5(latest, t)
        if None in (ga, gb, gl):
            continue
        rev.append({"end_year": t, "vintage_1oct_next": a, "vintage_1oct_second": b, "vintage_latest": latest,
                    "g5_1oct_next": round(ga, 4), "g5_1oct_second": round(gb, 4), "g5_latest": round(gl, 4),
                    "ppp_move_between": any(a < m <= b for m in PPP_MOVES)})

    d = [r["g5_1oct_next"] - r["g5_1oct_second"] for r in rev]
    dn = [x for x, r in zip(d, rev) if not r["ppp_move_between"]]
    ea = [r["g5_1oct_next"] - r["g5_latest"] for r in rev]
    eb = [r["g5_1oct_second"] - r["g5_latest"] for r in rev]
    worst = max(range(len(d)), key=lambda i: abs(d[i]))
    since = next(r["year"] + 1 for i, r in enumerate(avail) if all(x["on_1oct_next"] for x in avail[i:]))
    rms = lambda x: math.sqrt(sum(v * v for v in x) / len(x))  # noqa: E731
    summary = {
        "revision_end_years": [rev[0]["end_year"], rev[-1]["end_year"]], "n_end_years": len(rev),
        "mean_abs_diff": round(sum(map(abs, d)) / len(d), 4), "mean_diff": round(sum(d) / len(d), 4),
        "max_abs_diff": round(abs(d[worst]), 4), "max_abs_diff_end_year": rev[worst]["end_year"],
        "max_abs_diff_without_ppp_move": round(max(map(abs, dn)), 4),
        "n_ppp_move_years": len(d) - len(dn),
        "rms_1oct_next_vs_latest": round(rms(ea), 4), "rms_1oct_second_vs_latest": round(rms(eb), 4),
        "mean_1oct_next_vs_latest": round(sum(ea) / len(ea), 4),
        "mean_1oct_second_vs_latest": round(sum(eb) / len(eb), 4),
        "availability_years": [avail[0]["year"], avail[-1]["year"]],
        "missing_on_1oct_next": [r["year"] for r in avail if not r["on_1oct_next"]],
        "found_on_1oct_every_year_since": since,
        "n_found_since": sum(1 for r in avail if r["year"] + 1 >= since),
    }
    res = {"series": SERIES, "country": COUNTRY, "archive": f"{API} (WDI Database Archives)",
           "vintages": len(V), "first_vintage": V[0], "latest_vintage": latest, "retrieved": today.isoformat(),
           "summary": summary, "availability": avail, "revisions": rev}
    OUT.mkdir(exist_ok=True)
    (OUT / "wdi_revisions.json").write_text(json.dumps(res, indent=1) + "\n")
    with (OUT / "wdi_revisions.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rev[0]))
        w.writeheader()
        w.writerows(rev)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
