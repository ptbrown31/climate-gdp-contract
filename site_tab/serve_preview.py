"""Preview the contract's page inside the public site, locally.

Serves site_tab/ first, then the site's built standalone pages (its CSS, scripts, header and
config), then the site's local snapshots under /data/. The page reads its model from
data/snapshots/elnino/, which here is site_tab/data/elnino/, the files build_site_data.py just
wrote. Reads the site's checkout; writes nothing.

    python3 -I site_tab/serve_preview.py [port] [path to weather-tools-site]
    open http://localhost:8791/climate-gdp.html
"""
from __future__ import annotations

import http.server
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", 8791))
SITE = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / "weather-tools-site"
ROOTS = [HERE, SITE / "dist" / "standalone", SITE / "site"]
DATA = SITE / "data"
MODEL = ("data/snapshots/elnino/", HERE / "data" / "elnino")


class Overlay(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        rel = path.split("?", 1)[0].split("#", 1)[0].lstrip("/") or "index.html"
        if ".." in Path(rel).parts:
            return str(HERE / "__nope__")
        if rel.startswith(MODEL[0]):
            return str(MODEL[1] / rel[len(MODEL[0]):])
        for root in ROOTS:
            p = root / rel
            if p.is_file():
                return str(p)
        if rel.startswith("data/"):
            p = DATA / rel[len("data/"):]
            if p.is_file():
                return str(p)
        return str(HERE / rel)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        if args and str(args[1]).startswith(("4", "5")):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Overlay).serve_forever()
