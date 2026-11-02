"""Minimal .xlsx worksheet reader (standard library only).

The pipeline runs under ``python -I``, which leaves out user site-packages such as openpyxl.
An .xlsx file is a zip of XML parts; this reads one worksheet's cell values (shared strings,
inline strings and numbers) into rows, which is all the IMF's historical forecast file needs.
"""
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

M = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"


def sheet_parts(path: Path) -> dict[str, str]:
    """Sheet name -> zip member holding it."""
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels.iter(f"{{{PR}}}Relationship")}
    out = {}
    for s in wb.iter(f"{{{M}}}sheet"):
        t = target[s.get(f"{{{R}}}id")].lstrip("/")
        out[s.get("name")] = t if t.startswith("xl/") else f"xl/{t}"
    return out


def _col(ref: str | None, default: int) -> int:
    if not ref:
        return default
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_sheet(path: Path, name: str) -> list[list]:
    """Rows of one worksheet; numbers as float, text as str, empty cells as None."""
    member = sheet_parts(path)[name]
    rows = []
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(f"{{{M}}}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{M}}}t")))
        with z.open(member) as f:
            for _, el in ET.iterparse(f):
                if el.tag != f"{{{M}}}row":
                    continue
                cells = {}
                for i, c in enumerate(el.iter(f"{{{M}}}c")):
                    kind, v = c.get("t"), c.find(f"{{{M}}}v")
                    text = None if v is None else v.text
                    if kind == "s":
                        val = None if text is None else shared[int(text)]
                    elif kind == "inlineStr":
                        val = "".join(t.text or "" for t in c.iter(f"{{{M}}}t"))
                    elif kind in ("str", "e"):
                        val = text
                    elif kind == "b":
                        val = None if text is None else bool(int(text))
                    else:
                        val = None if text is None else float(text)
                    cells[_col(c.get("r"), i)] = val
                rows.append([cells.get(j) for j in range(max(cells) + 1)] if cells else [])
                el.clear()
    return rows
