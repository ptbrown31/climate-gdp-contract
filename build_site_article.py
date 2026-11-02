"""The article's text for the contract's page on the public site, read from Patrick's draft.

The page prints the draft as written: headings, paragraphs with their bold, italics and links,
the indented quotations, the lists and the two tables. Each picture in the draft becomes a slot
for the page's live figure of the same number, and the caption under it stays the draft's. Nothing
is reworded here; a change to the text is a change to the draft, then a re-run.

    python3 -I build_site_article.py draft.docx     # or set ELNINO_DRAFT to the draft's path

Writes site_tab/data/elnino/article.json.
"""
from __future__ import annotations

import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "site_tab" / "data" / "elnino" / "article.json"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
BLIP = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
STYLES = {"Title": "title", "Subtitle": "subtitle", "Heading1": "h1", "Heading2": "h2", "Heading3": "h3"}
FIGURE = re.compile(r"^Figure (\d+)\.")


def q(tag: str) -> str:
    return f"{{{W}}}{tag}"


def on(rpr, tag: str) -> bool:
    e = rpr.find(q(tag)) if rpr is not None else None
    return e is not None and e.get(q("val")) not in ("0", "false", "none")


def runs_of(p, links: dict) -> list[dict]:
    """The paragraph's text as runs of one format each: {"t", "b", "i", "href"}, adjacent alike runs merged."""
    out = []

    def add(r, href):
        t = "".join((x.text or "") if x.tag == q("t") else ("\t" if x.tag == q("tab") else "\n")
                    for x in r if x.tag in (q("t"), q("tab"), q("br")))
        if not t:
            return
        rpr = r.find(q("rPr"))
        run = {"t": t}
        if on(rpr, "b"):
            run["b"] = True
        if on(rpr, "i"):
            run["i"] = True
        if href:
            run["href"] = href
        prev = out[-1] if out else None
        if prev and {k: v for k, v in prev.items() if k != "t"} == {k: v for k, v in run.items() if k != "t"}:
            prev["t"] += t
        else:
            out.append(run)

    for child in p:
        if child.tag == q("r"):
            add(child, None)
        elif child.tag == q("hyperlink"):
            href = links.get(child.get(f"{{{R}}}id"))
            for r in child.iter(q("r")):
                add(r, href)
    return out


def plain(runs: list[dict]) -> str:
    return "".join(r["t"] for r in runs)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def list_kind(zf: zipfile.ZipFile) -> dict[str, str]:
    """numId -> 'ol' or 'ul' from the first level of its abstract numbering."""
    try:
        num = etree.fromstring(zf.read("word/numbering.xml"))
    except KeyError:
        return {}
    fmt = {}
    for a in num.findall(q("abstractNum")):
        lvl = a.find(q("lvl"))
        f = lvl.find(q("numFmt")).get(q("val")) if lvl is not None and lvl.find(q("numFmt")) is not None else "bullet"
        fmt[a.get(q("abstractNumId"))] = "ul" if f == "bullet" else "ol"
    return {n.get(q("numId")): fmt.get(n.find(q("abstractNumId")).get(q("val")), "ul") for n in num.findall(q("num"))}


def convert(path: Path) -> dict:
    zf = zipfile.ZipFile(path)
    doc = etree.fromstring(zf.read("word/document.xml"))
    rels = etree.fromstring(zf.read("word/_rels/document.xml.rels"))
    links = {r.get("Id"): r.get("Target") for r in rels if r.get("TargetMode") == "External"}
    kinds = list_kind(zf)
    blocks, pending_fig = [], False
    for el in doc.find(q("body")):
        if el.tag == q("tbl"):
            rows = []
            for tr in el.findall(q("tr")):
                rows.append([[r for p in tc.findall(q("p")) for r in (runs_of(p, links) + [{"t": "\n"}])][:-1]
                             for tc in tr.findall(q("tc"))])
            blocks.append({"type": "table", "rows": rows})
            continue
        if el.tag != q("p"):
            continue
        ppr = el.find(q("pPr"))
        style = ppr.find(q("pStyle")).get(q("val")) if ppr is not None and ppr.find(q("pStyle")) is not None else ""
        if list(el.iter(BLIP)):
            pending_fig = True
            continue
        runs = runs_of(el, links)
        text = plain(runs).strip()
        if not text:
            continue
        m = FIGURE.match(text)
        if m:
            blocks.append({"type": "figure", "n": int(m.group(1)), "caption": runs, "image": pending_fig})
            pending_fig = False
            continue
        kind = STYLES.get(style, "p")
        if kind in ("h1", "h2", "h3"):
            blocks.append({"type": kind, "text": text, "id": slug(text)})
            continue
        if kind in ("title", "subtitle"):
            blocks.append({"type": kind, "text": text})
            continue
        b = {"type": "p", "runs": runs}
        num = ppr.find(q("numPr")) if ppr is not None else None
        ind = ppr.find(q("ind")) if ppr is not None else None
        if num is not None and num.find(q("numId")) is not None:
            b["list"] = kinds.get(num.find(q("numId")).get(q("val")), "ul")
        elif ind is not None and int(ind.get(q("left")) or 0) > 0:
            b["indent"] = True
        blocks.append(b)
    return {"blocks": blocks}


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.environ.get("ELNINO_DRAFT", ""))
    if not src.is_file():
        sys.exit("give the draft's path, or set ELNINO_DRAFT")
    art = convert(src)
    mtime = datetime.fromtimestamp(src.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    art = {"schema": 1, "source": {"file": src.name, "modified": mtime,
                                   "read": datetime.now(timezone.utc).isoformat(timespec="seconds")}} | art
    figs = sorted(b["n"] for b in art["blocks"] if b["type"] == "figure")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(art, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {OUT}: {len(art['blocks'])} blocks, figures {figs}, draft modified {mtime}")


if __name__ == "__main__":
    main()
