"""The text of the contract's page on the public site, read from Patrick's Word draft.

The page prints the draft as written. Nothing is reworded here; a change to the text is a change
to the draft, then a re-run.

The draft comes in two forms. The cover article (schema 1, article.json) has headings, paragraphs
with their bold, italics and links, the indented quotations, the lists and two tables, and each
picture becomes a slot for the page's live figure of the same number. The Letter (schema 2,
letter.json, since 5 Nov 2026) adds the summary paragraph, numbered citations, equations, the
Methods, the references, the end notes, the Extended Data and the Supplementary Information. Its
figures and tables are found by their legends ("Fig. 1 |", "Extended Data Fig. 2 |", "Extended
Data Table 1 |", "Supplementary Table 1 |"). The page draws a figure live where it has a drawing
for it, and otherwise shows the draft's own picture, which is written beside letter.json.

Since 6 Nov 2026 the Letter opens with Patrick's article instead of a byline and summary: a
subtitle, then an introduction with indented quotations and lists, up to the first top-level
heading. Each top-level heading starts a section of the page, and lower headings are its
subsections. The Letter's own opening (byline, affiliations, note, bold summary) still reads.
Later the same day every figure and table moved into the text, numbered in reading order ("Fig. 5 |",
"Table 2 |"), and each stays where the draft puts it. The page's live drawings are matched to the
figures by a phrase of each legend (DRAWINGS), so they follow the figures whatever their numbers.

    python3 -I build_site_article.py draft.docx     # or set ELNINO_DRAFT to the draft's path

Writes site_tab/data/elnino/article.json, or for the Letter letter.json and letter/<hash>.png.
The Letter is read with pandoc, which turns Word's equations into TeX for the page's KaTeX.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "site_tab" / "data" / "elnino" / "article.json"
OUT_LETTER = OUT.with_name("letter.json")

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


# ---------------------------------------------------------------------------------------------- the Letter
# Top-level sections of the Letter, in Nature's order. A header with any other text is a subsection.
SECTIONS = ("Methods", "References", "Acknowledgements", "Author contributions", "Competing interests",
            "Additional information", "Figures", "Extended Data", "Supplementary Information")
LEGEND = re.compile(r"^(Extended Data Fig\.|Extended Data Table|Supplementary Table|Fig\.|Table)\s*(\d+)\s*\|")
KINDS = {"Fig.": "fig", "Extended Data Fig.": "ed", "Extended Data Table": "edt", "Supplementary Table": "st",
         "Table": "tab"}
# what the page draws for a figure, found by a phrase of its legend; a figure without one shows the draft's own
# picture. Each phrase must be in exactly one legend, so a reworded legend stops the build instead of losing its
# drawing. Tables get a role the same way, for the method notes that name them.
DRAWINGS = (("main", "indexed to 2026 = 100"), ("timeline", "the contracts resolve on 1 October"),
            ("temperature", "began during a strong El Niño"),
            ("response", "response of world GDP per capita to a 1 °C shock"),
            ("growth", "IMF’s average past error"), ("trendStarts", "depending on the first year of its average"),
            ("afterElNino", "simulated years after 2027"), ("endYear", "last year of the growth period"),
            ("distributions", "Simulated average growth"), ("known2027", "known 2027 value"),
            ("sensitivity", "under the published design and"))
ROLES = (("terms", "Proposed terms"), ("sensitivity", "sensitivity rows"))
CITE = re.compile(r"^[\d\s,–-]+$")
EQNO = re.compile(r"\\quad\s*\\quad\s*\((\d+)\)\s*[.,]?\s*$")


def pandoc_ast(path: Path) -> dict:
    """The draft as pandoc's JSON. A square root that Word saved without a degree element (Google Docs
    does) loses its argument in pandoc, so the empty degree is put back in a scratch copy first."""
    zin = zipfile.ZipFile(path)
    xml = zin.read("word/document.xml").decode("utf-8")
    xml = re.sub(r"(<m:rad>(?:(?!</m:rad>).)*?</m:radPr>)(?!<m:deg)", r"\1<m:deg/>", xml, flags=re.S)
    tmp = OUT.parent / ".letter_pandoc.docx"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for item in zin.infolist():
            z.writestr(item, xml.encode("utf-8") if item.filename == "word/document.xml" else zin.read(item))
    try:
        out = subprocess.run(["pandoc", "-f", "docx", "-t", "json", str(tmp)], capture_output=True, check=True)
    finally:
        tmp.unlink()
    return json.loads(out.stdout)


def fix_tex(s: str) -> str:
    """Word's equations as pandoc reads them, made to print as written: ln as an operator, labels upright."""
    s = re.sub(r"(?<![\\A-Za-z])ln(?=[A-Za-z\\({\s])", r"\\ln ", s)
    s = re.sub(r"\^\{([A-Z]{2,})\}", r"^{\\mathrm{\1}}", s)
    s = re.sub(r"\{?([A-Za-z])‾\}?", r"\\bar{\1}", s)       # Word's overbar, read as a letter and a mark
    return s.strip()


def letter_runs(xs: list, front: bool = False) -> list[dict]:
    """pandoc inlines -> runs of one format each: {"t", "b", "i", "sup", "sub", "href", "math", "cite"}.
    A superscript of numbers is a citation, except in the byline and affiliations (front)."""
    out: list[dict] = []

    def emit(t, style):
        if not t:
            return
        run = dict(style, t=t)
        prev = out[-1] if out else None
        if prev and "math" not in prev and {k: v for k, v in prev.items() if k != "t"} == style:
            prev["t"] += t
        else:
            out.append(run)

    def walk(items, style):
        for x in items:
            t, c = x.get("t"), x.get("c")
            if t == "Str":
                emit(c, style)
            elif t in ("Space", "SoftBreak"):
                emit(" ", style)
            elif t == "LineBreak":
                emit("\n", style)
            elif t == "Strong":
                walk(c, dict(style, b=True))
            elif t == "Emph":
                walk(c, dict(style, i=True))
            elif t == "Subscript":
                walk(c, dict(style, sub=True))
            elif t == "Superscript":
                txt = "".join(r["t"] for r in letter_runs(c))
                walk(c, dict(style, cite=True) if not front and CITE.match(txt) else dict(style, sup=True))
            elif t == "Link":
                walk(c[1], dict(style, href=c[2][0]))
            elif t == "Quoted":
                o, e = ("“", "”") if c[0]["t"] == "DoubleQuote" else ("‘", "’")
                emit(o, style)
                walk(c[1], style)
                emit(e, style)
            elif t == "Math":
                out.append(dict(style, t="", math=fix_tex(c[1])))
            elif t in ("Span", "Underline", "SmallCaps", "Strikeout"):
                walk(c[1] if t == "Span" else c, style)
            elif t == "Code":
                emit(c[1], style)
            # images are slots, handled by the block that holds them; notes and citations do not occur

    walk(xs, {})
    return out


def runs_text(runs: list[dict]) -> str:
    return "".join(r.get("t", "") for r in runs)


def png_size(data: bytes) -> tuple[int, int]:
    return struct.unpack(">II", data[16:24]) if data[:8] == b"\x89PNG\r\n\x1a\n" else (0, 0)


def letter_table(c) -> list[list[list[dict]]]:
    """A pandoc Table -> rows of cells of runs, the header row first."""
    def row(r):
        return [[x for i, b in enumerate(cell[4]) for x in ([{"t": "\n"}] if i else []) + letter_runs(b["c"])]
                for cell in r[1]]
    head, bodies = c[3], c[4]
    rows = [row(r) for r in head[1]]
    for body in bodies:
        rows += [row(r) for r in body[2]] + [row(r) for r in body[3]]
    return rows


class Blocks:
    """The draft's blocks as the page prints them: paragraphs, indented quotations, lists, equations, and the figures
    and tables, each where the draft puts it. A picture belongs to the legend after it, and a table to the legend
    before it."""

    def __init__(self, zf: zipfile.ZipFile, media_dir: Path, out: dict):
        self.zf, self.media_dir, self.out = zf, media_dir, out
        self.image, self.table_id = None, None

    def add(self, b: dict, target: list, front: bool = False):
        t = b["t"]
        if t == "Table":
            rows = letter_table(b["c"])
            if self.table_id:
                self.out["tables"][self.table_id]["rows"] = rows
                self.table_id = None
            else:
                target.append({"type": "table", "rows": rows})
        elif t in ("OrderedList", "BulletList"):
            items = b["c"][1] if t == "OrderedList" else b["c"]
            target.append({"type": "list", "ordered": t == "OrderedList",
                           "items": [letter_runs(x for blk in item for x in blk.get("c", []) if isinstance(x, dict))
                                     for item in items]})
        elif t == "BlockQuote":
            inner: list = []
            for x in b["c"]:
                self.add(x, inner, front)
            target += [dict(x, indent=True) if x["type"] == "p" else x for x in inner]
        elif t == "Header" and front:
            text = runs_text(letter_runs(b["c"][2])).strip()
            target.append({"type": "h3", "text": text, "id": slug(text)})
        elif t in ("Para", "Plain") and not self.picture(b):
            self.para(letter_runs(b["c"]), target)

    def picture(self, b: dict) -> bool:
        imgs = [x for x in b["c"] if x.get("t") == "Image"]
        if not imgs:
            return False
        target = imgs[0]["c"][2][0]
        names = self.zf.namelist()
        data = self.zf.read("word/" + target) if "word/" + target in names else self.zf.read(target)
        name = hashlib.sha256(data).hexdigest()[:12] + Path(target).suffix
        self.media_dir.mkdir(parents=True, exist_ok=True)
        (self.media_dir / name).write_bytes(data)
        w, h = png_size(data)
        self.image = {"file": f"{self.media_dir.name}/{name}", "w": w, "h": h}
        return True

    def para(self, runs: list[dict], target: list):
        text = runs_text(runs).strip()
        if not text and not any("math" in r for r in runs):
            return
        m = LEGEND.match(text)
        if m:
            kind = KINDS[m.group(1)]
            fid, label = f"{kind}{m.group(2)}", f"{m.group(1)} {m.group(2)}"
            if kind in ("fig", "ed"):
                self.out["figures"][fid] = {"label": label, "legend": runs, "image": self.image}
                self.image = None
                target.append({"type": "figure", "id": fid})
            else:
                self.out["tables"][fid] = {"label": label, "legend": runs, "rows": []}
                self.table_id = fid
                target.append({"type": "table", "id": fid})
            return
        maths = [r for r in runs if "math" in r]
        if len(maths) == 1 and not text:
            tex = maths[0]["math"]
            n = EQNO.search(tex)
            target.append({"type": "eq", "tex": EQNO.sub("", tex).rstrip(" ,"), "n": n.group(1) if n else None})
            return
        target.append({"type": "p", "runs": runs})


def match_drawings(out: dict):
    """Give each figure the page's drawing for it, and each table its role, by the phrases in DRAWINGS and ROLES.
    A draft that still has Extended Data is older than the phrases, and the page goes by its figures' ids."""
    if any(k.startswith("ed") for k in out["figures"]):
        return
    for items, phrases, field in ((out["figures"], DRAWINGS, "draw"), (out["tables"], ROLES, "role")):
        for key, phrase in phrases:
            hits = [k for k, f in items.items() if phrase in runs_text(f["legend"])]
            if len(hits) != 1:
                sys.exit(f"{field} {key!r}: {len(hits)} legends have {phrase!r}")
            items[hits[0]][field] = key
        for f in items.values():
            f.setdefault(field, None)


def convert_letter(path: Path, media_dir: Path) -> dict:
    doc = pandoc_ast(path)
    zf = zipfile.ZipFile(path)
    title = runs_text(letter_runs(doc["meta"].get("title", {}).get("c", []))).strip()
    subtitle = runs_text(letter_runs(doc["meta"].get("subtitle", {}).get("c", []))).strip()
    blocks = doc["blocks"]
    paras = lambda b: b["t"] in ("Para", "Plain")  # noqa: E731
    head_text = lambda b: runs_text(letter_runs(b["c"][2])).strip()  # noqa: E731
    top = lambda b: b["t"] == "Header" and (b["c"][0] == 1 or head_text(b) in SECTIONS)  # noqa: E731

    # everything before the first top-level heading: the Letter's byline, affiliations, note, bold summary and
    # main text, or the article's introduction
    i = next((k for k, b in enumerate(blocks) if top(b)), len(blocks))
    front = blocks[:i]
    fr = [letter_runs(b["c"], front=True) for b in front if paras(b)]
    bold = [k for k, r in enumerate(fr) if r and all(x.get("b") or not x.get("t", "x").strip() for x in r)]
    if all(paras(b) for b in front) and bold and bold[0] >= 2:
        s = bold[0]
        out = {"title": title, "byline": fr[0], "affiliations": fr[1], "note": [x for r in fr[2:s] for x in r],
               "summary": letter_runs([x for x in front if paras(x)][s]["c"]),
               "main": [{"type": "p", "runs": letter_runs(b["c"])} for b in [x for x in front if paras(x)][s + 1:]],
               "sections": [], "figures": {}, "tables": {}}
        read = Blocks(zf, media_dir, out)
    else:
        out = {"title": title, "main": [], "sections": [], "figures": {}, "tables": {}}
        read = Blocks(zf, media_dir, out)
        for b in front:
            read.add(b, out["main"], front=True)
    if subtitle:
        out["subtitle"] = subtitle
    if not out["main"]:
        sys.exit("the draft has no text before its first top-level heading")

    sec = None
    for b in blocks[i:]:
        if b["t"] == "Header":
            text = head_text(b)
            if top(b):
                sec = {"id": slug(text), "title": text, "blocks": []}
                out["sections"].append(sec)
            else:
                m = re.match(r"Supplementary Section (\d+)", text)
                sec["blocks"].append({"type": "h3", "text": text, "id": f"ss{m.group(1)}" if m else slug(text)})
            continue
        if b["t"] == "OrderedList" and sec["title"] == "References":
            items = [letter_runs(x for blk in item for x in blk.get("c", []) if isinstance(x, dict))
                     for item in b["c"][1]]
            sec["refs"] = [{"n": b["c"][0][0] + k, "runs": r} for k, r in enumerate(items)]
            continue
        read.add(b, sec["blocks"])
    match_drawings(out)
    return out


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.environ.get("ELNINO_DRAFT", ""))
    if not src.is_file():
        sys.exit("give the draft's path, or set ELNINO_DRAFT")
    mtime = datetime.fromtimestamp(src.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    source = {"file": src.name, "modified": mtime, "read": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = etree.fromstring(zipfile.ZipFile(src).read("word/document.xml"))
    # the Letter has figure legends ("Fig. 1 |"); the cover article has captions ("Figure 1.")
    if any(LEGEND.match("".join(t.text or "" for t in p.iter(q("t")))) for p in body.iter(q("p"))):
        media = OUT.parent / "letter"
        art = {"schema": 2, "source": source} | convert_letter(src, media)
        keep = {f["image"]["file"].split("/")[-1] for f in art["figures"].values() if f.get("image")}
        for p in media.glob("*"):
            if p.name not in keep:
                p.unlink()
        OUT_LETTER.write_text(json.dumps(art, ensure_ascii=False, separators=(",", ":")))
        refs = next((len(s.get("refs", [])) for s in art["sections"] if s["title"] == "References"), 0)
        print(f"wrote {OUT_LETTER}: {len(art['main'])} main paragraphs, {len(art['sections'])} sections, "
              f"figures {sorted(art['figures'])}, tables {sorted(art['tables'])}, {refs} references, "
              f"draft modified {mtime}")
        return
    art = {"schema": 1, "source": source} | convert(src)
    figs = sorted(b["n"] for b in art["blocks"] if b["type"] == "figure")
    OUT.write_text(json.dumps(art, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {OUT}: {len(art['blocks'])} blocks, figures {figs}, draft modified {mtime}")


if __name__ == "__main__":
    main()
