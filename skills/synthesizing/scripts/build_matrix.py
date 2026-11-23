#!/usr/bin/env python3
"""
build_matrix.py — turn a synthesis matrix (JSON) into Markdown, CSV and colour-coded HTML.

Usage:
  python3 build_matrix.py matrix.json                 # writes files next to the JSON
  python3 build_matrix.py matrix.json --out folder/   # choose output folder
  python3 build_matrix.py matrix.json --print         # also print the Markdown table

JSON format: see references/synthesis-guide.md §6. Only the Python 3 standard library is used.
"""

import argparse
import csv
import html
import json
import os
import sys

STANCES = {
    "agree": ("●", "agrees", "#2e7d32", "#e8f5e9"),
    "partial": ("◐", "partly agrees / different perspective", "#b26a00", "#fff4e0"),
    "disagree": ("⊘", "disagrees", "#c62828", "#fdecea"),
    "alternative": ("✚", "alternative idea", "#1565c0", "#e7f0fb"),
}
PATTERN_HELP = {
    "consensus": "all sources that address this idea agree",
    "majority with dissent": "most agree; at least one differs or adds an alternative",
    "contested": "sources disagree or take different positions",
    "single-source": "only one source addresses this — weak basis",
    "gap": "no source addresses this — possible research gap",
}


def infer_pattern(cells):
    sources = {}
    for c in cells:
        sources.setdefault(c["source"], set()).add(c.get("stance", "agree"))
    if not sources:
        return "gap"
    if len(sources) == 1:
        return "single-source"
    agreeing = [s for s, st in sources.items() if st == {"agree"}]
    if len(agreeing) == len(sources):
        return "consensus"
    supportive = [s for s, st in sources.items() if "agree" in st or ("partial" in st and "disagree" not in st)]
    has_agree = any("agree" in st for st in sources.values())
    if has_agree and len(supportive) * 2 > len(sources):
        return "majority with dissent"
    return "contested"


def validate(data):
    errors = []
    ids = [s.get("id") for s in data.get("sources", [])]
    if not ids:
        errors.append("no sources")
    if len(ids) != len(set(ids)):
        errors.append("duplicate source ids")
    for i, idea in enumerate(data.get("ideas", []), 1):
        if not idea.get("idea"):
            errors.append(f"idea #{i} has no 'idea' text")
        for c in idea.get("cells", []):
            if c.get("source") not in ids:
                errors.append(f"idea #{i}: unknown source id {c.get('source')!r}")
            st = c.get("stance", "agree")
            if st not in STANCES:
                errors.append(f"idea #{i}: stance {st!r} must be one of {', '.join(STANCES)}")
    return errors


def cell_text(c):
    sym = STANCES[c.get("stance", "agree")][0]
    text = (c.get("text") or "").strip()
    return f"{sym} {text}" + (f" [p.{c['page']}]" if c.get("page") else "")


def build(data):
    srcs = data["sources"]
    rows = []
    for idea in data["ideas"]:
        cells = idea.get("cells", [])
        pattern = (idea.get("pattern") or "").strip().lower() or infer_pattern(cells)
        by_src = {s["id"]: [c for c in cells if c["source"] == s["id"]] for s in srcs}
        rows.append({"idea": idea["idea"], "by_src": by_src, "pattern": pattern, "notes": idea.get("notes", "")})
    return rows


def label(s):
    return s.get("label") or s["id"]


def to_markdown(data, rows):
    srcs = data["sources"]
    esc = lambda t: str(t).replace("|", "\\|").replace("\n", " ")
    head = ["Idea / concept / point"] + [label(s) for s in srcs] + ["Notes (pattern · strength · relevance · reliability)"]
    out = []
    if data.get("topic"):
        out.append(f"**Topic:** {esc(data['topic'])}\n")
    out.append("| " + " | ".join(esc(h) for h in head) + " |")
    out.append("|" + "---|" * len(head))
    for r in rows:
        line = [esc(r["idea"])]
        for s in srcs:
            line.append("<br>".join(esc(cell_text(c)) for c in r["by_src"][s["id"]]))
        line.append(esc(f"**{r['pattern'].capitalize()}**" + (f" — {r['notes']}" if r["notes"] else "")))
        out.append("| " + " | ".join(line) + " |")
    out.append("\nLegend: " + " · ".join(f"{v[0]} {v[1]}" for v in STANCES.values()) + " · (empty) not addressed")
    return "\n".join(out) + "\n"


def to_csv(data, rows, path):
    srcs = data["sources"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:  # BOM so Excel shows Vietnamese correctly
        w = csv.writer(f)
        w.writerow(["Idea / concept / point"] + [label(s) for s in srcs] + ["Pattern", "Notes"])
        for r in rows:
            w.writerow([r["idea"]] + [" / ".join(cell_text(c) for c in r["by_src"][s["id"]]) for s in srcs]
                       + [r["pattern"], r["notes"]])


def to_html(data, rows):
    srcs = data["sources"]
    e = html.escape
    th = "".join(f"<th>{e(label(s))}" + (f"<div class='rel'>{e(s['reliability'])}</div>" if s.get("reliability") else "") + "</th>" for s in srcs)
    body = []
    for r in rows:
        tds = []
        for s in srcs:
            parts = []
            for c in r["by_src"][s["id"]]:
                sym, name, fg, bg = STANCES[c.get("stance", "agree")]
                page = f" <span class='pg'>p.{e(str(c['page']))}</span>" if c.get("page") else ""
                parts.append(f"<div class='cell' style='background:{bg};border-left:4px solid {fg}'>"
                             f"<span class='sym' style='color:{fg}' title='{e(name)}'>{sym}</span> {e(c.get('text', ''))}{page}</div>")
            tds.append(f"<td>{''.join(parts)}</td>")
        pat = r["pattern"]
        body.append(f"<tr><th class='idea'>{e(r['idea'])}</th>{''.join(tds)}"
                    f"<td class='notes'><b class='pat'>{e(pat.capitalize())}</b> <span class='help'>({e(PATTERN_HELP.get(pat, ''))})</span>"
                    f"<div>{e(r['notes'])}</div></td></tr>")
    legend = "".join(f"<span class='lg' style='background:{v[3]};border-left:4px solid {v[2]}'><b style='color:{v[2]}'>{v[0]}</b> {e(v[1])}</span>" for v in STANCES.values())
    refs = "".join(f"<li>{e(s['reference'])}</li>" for s in sorted(srcs, key=lambda s: s.get("reference", label(s)).lower()) if s.get("reference"))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthesis matrix</title>
<style>
:root{{color-scheme:light}} body{{font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;margin:24px;color:#1b1b1b;background:#fff}}
h1{{font-size:22px;margin:0 0 4px}} .topic{{color:#444;margin:0 0 16px}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;min-width:720px;width:100%}}
th,td{{border:1px solid #c9cbe0;padding:8px;vertical-align:top;text-align:left}}
thead th{{background:#dcdcfa}} th.idea{{background:#f4f4fb;width:15%}} td.notes{{width:24%;background:#fafafa}}
.cell{{padding:4px 6px;margin:0 0 4px;border-radius:3px}} .sym{{font-weight:700}} .pg{{color:#666;font-size:12px}}
.rel{{font-weight:400;font-size:12px;color:#555}} .pat{{text-transform:none}} .help{{color:#666;font-size:12px}}
.legend{{margin:12px 0;display:flex;flex-wrap:wrap;gap:8px}} .lg{{padding:3px 8px;border-radius:3px}}
ol{{padding-left:20px}} @media print{{body{{margin:8mm}} .wrap{{overflow:visible}}}}
</style></head><body>
<h1>Synthesis matrix</h1><p class="topic">{e(data.get('topic', ''))}</p>
<div class="legend">{legend}<span class="lg" style="border-left:4px solid #bbb">(empty) not addressed</span></div>
<div class="wrap"><table><thead><tr><th>Idea / concept / point</th>{th}<th>Notes on argument strength, relevance, source reliability</th></tr></thead>
<tbody>{''.join(body)}</tbody></table></div>
{'<h2>References</h2><ol>' + refs + '</ol>' if refs else ''}
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description="Build a synthesis matrix (Markdown, CSV, HTML) from JSON.")
    ap.add_argument("json_file")
    ap.add_argument("--out", help="output folder (default: same folder as the JSON)")
    ap.add_argument("--name", default="synthesis-matrix", help="base file name")
    ap.add_argument("--print", action="store_true", help="print the Markdown table")
    a = ap.parse_args()

    with open(a.json_file, encoding="utf-8") as f:
        data = json.load(f)
    errs = validate(data)
    if errs:
        print("Matrix JSON problems:\n  - " + "\n  - ".join(errs), file=sys.stderr)
        sys.exit(1)
    rows = build(data)
    out = a.out or os.path.dirname(os.path.abspath(a.json_file))
    os.makedirs(out, exist_ok=True)
    base = os.path.join(out, a.name)
    md = to_markdown(data, rows)
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write(md)
    to_csv(data, rows, base + ".csv")
    with open(base + ".html", "w", encoding="utf-8") as f:
        f.write(to_html(data, rows))
    for r in rows:
        print(f"- {r['idea']}: {r['pattern']}")
    print(f"\nWrote {base}.md, {base}.csv, {base}.html")
    if a.print:
        print("\n" + md)


if __name__ == "__main__":
    main()
