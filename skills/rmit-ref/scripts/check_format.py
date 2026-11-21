#!/usr/bin/env python3
"""
check_format.py — offline linter for RMIT Harvard reference lists, plus in-text cross-check.

Usage:
  python3 check_format.py refs.txt                  # lint the reference list
  python3 check_format.py refs.txt --text essay.txt # also cross-check in-text citations
  python3 check_format.py refs.txt --json

It catches mechanical mistakes (mostly APA habits). It does not replace reading each entry
against the template for its source type in references/rmit-harvard.md.
Only the Python 3 standard library is used.
"""

import argparse
import json
import re
import sys
import unicodedata

SKIP = re.compile(r"^\s*(references?|reference list|bibliography|works cited|tài liệu tham khảo)\s*:?\s*$", re.I)
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"


def strip_accents(s):
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def split_refs(text):
    text = text.replace("\r\n", "\n")
    blocks = [b for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) > 1 and any("\n" in b.strip() for b in blocks) and all(len(b.strip().split("\n")) <= 4 for b in blocks):
        items = [" ".join(b.split()) for b in blocks]
    else:
        items = [l.strip() for l in text.split("\n") if l.strip()]
    out = []
    for it in items:
        if SKIP.match(it):
            continue
        it = re.sub(r"^\s*(?:\[\d+\]|\d+[.)]|[-•*])\s+", "", it)
        if len(it) > 15:
            out.append(it)
    return out


def author_part(ref):
    m = re.search(r"\((?:[^()]*?\b(?:1[5-9]\d{2}|20\d{2})[a-z]?\b[^()]*|n\.d\.[a-z]?|c\.\s?\d{4})\)", ref)
    return (ref[: m.start()].strip(), m) if m else (None, None)


def sort_key(ref):
    plain = re.sub(r"[*_'‘’\"“”]", "", ref)
    plain = re.sub(r"^(the|a|an)\s+", "", plain, flags=re.I)
    return strip_accents(plain).lower()


def lint_entry(ref):
    issues = []
    plain = re.sub(r"[*_]", "", ref)
    authors, ym = author_part(plain)

    def add(rule, fix):
        issues.append({"rule": rule, "fix": fix})

    if ym is None:
        add("year-missing", "Put the year in parentheses straight after the author: 'Day T (2018) ...'; use (n.d.) if there is no date.")
    if re.search(r"\bet al\b", authors or ""):
        add("et-al-in-list", "List every author in the reference list; 'et al.' is only for in-text citations of 3+ authors.")
    if authors and "&" in authors:
        add("ampersand", "Use 'and' between the last two authors, not '&'.")
    if authors and re.search(r"\b[A-Z]\.\s?(?:[A-Z]\.)?", authors):
        add("initials-full-stops", "Write initials without full stops or spaces: 'Peterson JR', not 'Peterson, J. R.'.")
    if authors and re.search(r"^[A-Z][\w'’\-]+,\s+[A-Z]", authors):
        add("comma-after-family-name", "No comma between family name and initials: 'Deegan C', not 'Deegan, C'.")
    if ym and plain[ym.end(): ym.end() + 2].startswith("."):
        add("full-stop-after-year", "No full stop after the year: '(2019) Title', not '(2019). Title'.")
    if re.search(r"https?://(dx\.)?doi\.org/", plain, re.I):
        add("doi-url", "Write the DOI as 'doi:10.xxxx/...' at the end, not as an https://doi.org/ link.")
    if re.search(r"\bdoi:\s+10\.", plain, re.I) or re.search(r"\bDOI:?\s*10\.", plain):
        add("doi-format", "Use lower-case 'doi:' with no space: 'doi:10.1080/...'.")
    if re.search(r"\b(retrieved|available)\s+(from|at)\b", plain, re.I):
        add("retrieved-from", "Replace 'Retrieved from'/'Available at' with 'accessed Day Month Year. URL'.")
    if re.search(r"https?://", plain) and not re.search(r"https?://(dx\.)?doi\.org/", plain, re.I) and "accessed" not in plain.lower():
        add("accessed-missing", "Online sources need 'accessed Day Month Year.' before the URL.")
    m = re.search(r"accessed\s+([^.]+?)[.,]", plain, re.I)
    if m and not re.fullmatch(rf"\d{{1,2}} ({MONTHS}) \d{{4}}", m.group(1).strip()):
        add("accessed-date-format", f"Accessed date should be Day Month Year (e.g. 'accessed 9 December 2021'), found '{m.group(1).strip()}'.")
    if re.search(r"\bpp?\.\s?\d", plain):
        add("pp-pages", "Journal pages go after the volume/issue with a colon: '28(4):686-699', not 'pp. 686-699'.")
    if re.search(r"\bvol\.?\s?\d|\bno\.\s?\d|\bVolume \d", plain, re.I):
        add("vol-no", "Write volume and issue as 'volume(issue)', e.g. '28(4)', not 'vol. 28, no. 4'.")
    if re.search(r"\(\d{4}[a-z]?\)\.?\s*[\"“]", plain) or re.search(r",\s*[\"“][^\"”]{8,}[\"”]\s*,", plain):
        add("double-quotes-title", "Article/chapter titles take single quotes: 'Title of article'.")
    if re.search(r"\b\d+(st|nd|rd|th) ed\.?(?!n)", plain):
        add("edition-abbrev", "Write editions as '2nd edn', not '2nd ed.'.")
    if re.search(r"\b(google scholar|researchgate|academia\.edu|studocu|coursehero|course hero)\b", plain, re.I):
        add("aggregator-cited", "Google Scholar/ResearchGate/StuDocu are where you found it, not the publisher. Cite the original publication.")
    if re.search(r"wikipedia\.org", plain, re.I):
        add("wikipedia", "Wikipedia is usually not acceptable as an academic source — cite the sources it is based on.")
    if re.search(r"personal communication", plain, re.I):
        add("personal-communication", "Personal communication is cited in-text only; remove it from the reference list.")
    # Title Case heuristic: quoted title with most words capitalised
    tm = re.search(r"[‘'\"“]([^‘’'\"“”]{12,}?)[’'\"”][,.]", plain)
    if tm:
        words = [w for w in re.findall(r"[A-Za-z][\w\-]*", tm.group(1)) if len(w) > 3]
        if len(words) >= 4 and sum(w[0].isupper() for w in words[1:]) / max(1, len(words) - 1) > 0.6:
            add("title-case", "Use sentence case for titles (capitalise only the first word, proper nouns and the first word after a colon).")
    if not ref.rstrip().endswith((".", "/")) and not re.search(r"https?://\S+$", ref.strip()):
        add("ending", "End each entry with a full stop (unless it ends with a URL).")
    return issues


# ---------------------------------------------------------------- in-text cross-check

NAME = r"[A-ZÀ-Ỹ][\w'’\-À-ỹ]+(?:\s(?:[A-ZÀ-Ỹ][\w'’\-À-ỹ]+|de|van|von|der|da|del|di|le|la))*"
YEAR = r"(?:1[5-9]\d{2}|20\d{2})[a-z]?|n\.d\.[a-z]?|c\.\s?\d{4}"


def intext_citations(text):
    cites = []
    # Parenthetical: (Day 2018; Hill and Martinez-Diez 2020:18; Haslam et al. 2021)
    for paren in re.findall(r"\(([^()]{3,300})\)", text):
        for part in paren.split(";"):
            part = part.strip()
            part = re.sub(r"^.*?cited in\s+", "", part)  # secondary: keep the source actually read
            m = re.match(rf"({NAME}(?:\s(?:and|&)\s{NAME})?(?:\s[A-Z]{{1,3}})?)(\set al\.?)?,?\s((?:{YEAR})(?:,\s?(?:{YEAR}))*)\s*(:|,\s?p{{1,2}}\.)?", part)
            if m:
                cites.append({"text": part, "authors": m.group(1), "etal": bool(m.group(2)),
                              "years": re.findall(YEAR, m.group(3)), "comma": "," in part[: m.start(3)],
                              "page_style": m.group(4)})
    # Narrative: Day (2018:3) / Hill and Martinez-Diez (2020)
    for m in re.finditer(rf"({NAME}(?:\s(?:and|&)\s{NAME})?)(\set al\.?)?\s\(((?:{YEAR})(?:,\s?(?:{YEAR}))*)(:[^)]*|,\s?p{{1,2}}\.[^)]*)?\)", text):
        cites.append({"text": m.group(0), "authors": m.group(1), "etal": bool(m.group(2)),
                      "years": re.findall(YEAR, m.group(3)), "comma": False, "page_style": (m.group(4) or "")[:3] or None})
    return cites


def ref_keys(ref):
    plain = re.sub(r"[*_]", "", ref)
    authors, ym = author_part(plain)
    if ym is None:
        return None
    yr = re.search(YEAR, ym.group(0))
    year = yr.group(0) if yr else None
    a = authors or ""
    org_abbr = re.match(r"^([A-Z]{2,})\s*\(", a)
    a = re.sub(r"\([^)]*\)", "", a)
    a = re.sub(r"\((?:eds?|director|producer|host|presenter)\)", "", a)
    fams = []
    for chunk in re.split(r",\s*|\s+and\s+|\s*&\s*", a):
        chunk = chunk.strip()
        if not chunk:
            continue
        toks = chunk.split()
        while len(toks) > 1 and re.fullmatch(r"(?:[A-Z]\.?-?){1,4}", toks[-1]):
            toks.pop()
        fams.append(" ".join(toks))
    first = org_abbr.group(1) if org_abbr else (fams[0] if fams else "")
    return {"first": strip_accents(first).lower(), "n_authors": len(fams), "year": year,
            "families": [strip_accents(f).lower() for f in fams]}


def cross_check(refs, text):
    keys = [(r, ref_keys(r)) for r in refs]
    keys = [(r, k) for r, k in keys if k]
    cites = intext_citations(text)
    used = set()
    problems = []
    for c in cites:
        first = strip_accents(re.split(r"\s(?:and|&)\s", c["authors"])[0]).lower()
        first = re.sub(r"\s[a-z]{1,3}$", "", first)  # drop initials used to disambiguate
        n_named = 2 if re.search(r"\s(?:and|&)\s", c["authors"]) else 1
        for y in c["years"]:
            hit = [i for i, (r, k) in enumerate(keys) if k["year"] == y and (k["first"] == first or first.endswith(k["first"]) or k["first"].endswith(first))]
            if not hit:
                problems.append({"rule": "citation-not-in-list", "detail": f"In-text '{c['text']}' has no matching reference-list entry ({first} {y})."})
                continue
            used.update(hit)
            k = keys[hit[0]][1]
            if k["n_authors"] >= 3 and not c["etal"]:
                problems.append({"rule": "et-al-needed", "detail": f"'{c['text']}': 3+ authors → first author + et al."})
            if k["n_authors"] == 2 and n_named == 1 and not c["etal"]:
                problems.append({"rule": "two-authors", "detail": f"'{c['text']}': two authors → name both, joined by 'and'."})
            if k["n_authors"] <= 2 and c["etal"]:
                problems.append({"rule": "et-al-misused", "detail": f"'{c['text']}': only {k['n_authors']} author(s) → no 'et al.'."})
        if "&" in c["authors"]:
            problems.append({"rule": "ampersand-intext", "detail": f"'{c['text']}': use 'and', not '&'."})
        if c.get("comma"):
            problems.append({"rule": "comma-intext", "detail": f"'{c['text']}': no comma between author and year in RMIT Harvard."})
        if c.get("page_style") and "p" in c["page_style"]:
            problems.append({"rule": "page-style", "detail": f"'{c['text']}': quote pages use a colon, e.g. (Day 2018:3), not 'p.'."})
    for i, (r, k) in enumerate(keys):
        if i not in used:
            problems.append({"rule": "never-cited", "detail": f"Reference-list entry never cited in the text: {r[:90]}"})
    return {"n_citations_found": len(cites), "problems": problems}


def main():
    ap = argparse.ArgumentParser(description="Lint an RMIT Harvard reference list.")
    ap.add_argument("refs", help="file containing the reference list ('-' for stdin)")
    ap.add_argument("--text", help="essay/assignment text file to cross-check in-text citations")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    raw = sys.stdin.read() if a.refs == "-" else open(a.refs, encoding="utf-8").read()
    refs = split_refs(raw)
    report = {"entries": [{"reference": r, "issues": lint_entry(r)} for r in refs], "list_issues": []}

    ordered = sorted(refs, key=sort_key)
    if refs != ordered:
        report["list_issues"].append({"rule": "alphabetical-order", "fix": "Sort entries alphabetically by first author's family name (or title if no author)."})
    seen = {}
    for r in refs:
        k = re.sub(r"\W+", "", r.lower())
        if k in seen:
            report["list_issues"].append({"rule": "duplicate", "fix": f"Duplicate entry: {r[:80]}"})
        seen[k] = 1
    # same author + same year without a/b suffix
    ky = {}
    for r in refs:
        k = ref_keys(r)
        if k and k["year"] and re.fullmatch(r"\d{4}", k["year"]):
            ky.setdefault((tuple(k["families"]), k["year"]), []).append(r)
    for (fam, y), rs in ky.items():
        if len(rs) > 1:
            report["list_issues"].append({"rule": "same-author-year", "fix": f"{len(rs)} works by {', '.join(fam)} in {y}: label them {y}a, {y}b (in-text too)."})

    if a.text:
        report["cross_check"] = cross_check(refs, open(a.text, encoding="utf-8").read())

    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    n_bad = sum(1 for e in report["entries"] if e["issues"])
    print(f"{len(refs)} entries, {n_bad} with formatting issues.")
    for i, e in enumerate(report["entries"], 1):
        if e["issues"]:
            print(f"\n[{i}] {e['reference'][:110]}")
            for iss in e["issues"]:
                print(f"    ✗ {iss['rule']}: {iss['fix']}")
    for li in report["list_issues"]:
        print(f"\nLIST ✗ {li['rule']}: {li['fix']}")
    if "cross_check" in report:
        cc = report["cross_check"]
        print(f"\nIn-text cross-check: {cc['n_citations_found']} citations found.")
        for p in cc["problems"]:
            print(f"    ✗ {p['rule']}: {p['detail']}")
    print("\nSuggested sorted order:")
    for r in ordered:
        print(f"  {r}")


if __name__ == "__main__":
    main()
