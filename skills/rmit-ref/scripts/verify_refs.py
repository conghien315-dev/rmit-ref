#!/usr/bin/env python3
"""
verify_refs.py — check whether references are real, and build RMIT Harvard references from DOIs.

Evidence sources (all free, no API key):
  * Crossref REST API         — DOI metadata + bibliographic search
  * doi.org handle registry   — does a non-Crossref DOI exist at all?
  * OpenAlex                  — second independent index + retraction flag
  * Open Library              — books (ISBN and title/author search)
  * Internet Archive Wayback  — snapshots of dead web links

Usage:
  python3 verify_refs.py refs.txt                 # one reference per line, or blank-line separated
  python3 verify_refs.py refs.txt --json          # machine-readable output
  cat refs.txt | python3 verify_refs.py -         # read from stdin
  python3 verify_refs.py --from-doi 10.1080/09650792.2019.1652196 [more DOIs]

Optional: set CROSSREF_MAILTO=you@example.com to use Crossref's "polite" pool.
Only the Python 3 standard library is used.
"""

import argparse
import difflib
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

VERSION = "1.0.0"
UA = f"rmit-ref-verifier/{VERSION} (academic reference checker; +https://github.com/conghien315-dev/rmit-ref)"
MAILTO = os.environ.get("CROSSREF_MAILTO", "").strip()
TIMEOUT = 20
PAUSE = 0.15  # seconds between API calls, to be polite

_cache = {}


# --------------------------------------------------------------------------- HTTP helpers

def http_get(url, accept="application/json", method="GET"):
    """Return (status, body_text_or_None, final_url). status 0 = network error."""
    key = (method, url)
    if key in _cache:
        return _cache[key]
    headers = {"User-Agent": UA, "Accept": accept}
    req = urllib.request.Request(url, headers=headers, method=method)
    result = (0, None, url)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read(2_000_000).decode("utf-8", "replace") if method == "GET" else None
            result = (resp.status, body, resp.geturl())
    except urllib.error.HTTPError as e:
        result = (e.code, None, url)
    except Exception as e:  # DNS failure, timeout, TLS ...
        result = (0, str(e), url)
    time.sleep(PAUSE)
    _cache[key] = result
    return result


def get_json(url):
    status, body, _ = http_get(url)
    if status == 200 and body:
        try:
            return json.loads(body)
        except ValueError:
            return None
    return None


def crossref_url(path, params=None):
    params = dict(params or {})
    if MAILTO:
        params["mailto"] = MAILTO
    q = ("?" + urllib.parse.urlencode(params)) if params else ""
    return "https://api.crossref.org" + path + q


# --------------------------------------------------------------------------- text helpers

def strip_accents(s):
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s):
    s = strip_accents(html.unescape(s or "")).lower()
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def clean_markup(s):
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def title_similarity(cited, registry, full_ref=""):
    """0..1 similarity between the cited title and a registry title (subtitle-tolerant)."""
    r = norm(registry)
    if not r:
        return 0.0
    best = 0.0
    c = norm(cited)
    if c:
        candidates = {r, norm(registry.split(":")[0])}
        for cand in candidates:
            if not cand:
                continue
            best = max(best, difflib.SequenceMatcher(None, c, cand).ratio())
            cw, rw = set(c.split()), set(cand.split())
            if cw and rw:
                best = max(best, len(cw & rw) / max(len(cw), len(rw)))
    # Fallback: how much of the registry title appears inside the whole reference string.
    if full_ref:
        rw = r.split()
        fw = set(norm(full_ref).split())
        if len(rw) >= 4:
            best = max(best, sum(1 for w in rw if w in fw) / len(rw) * 0.95)
    return round(best, 3)


# --------------------------------------------------------------------------- parsing

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.I)
URL_RE = re.compile(r"https?://[^\s<>\"]+", re.I)
ISBN_RE = re.compile(r"(?:ISBN(?:-1[03])?[:\s]*)?\b((?:97[89][\s-]?)?(?:\d[\s-]?){9}[\dXx])\b")
STOP_NAME_WORDS = {"and", "et", "al", "eds", "ed", "the", "of", "n", "d", "nd", "in", "by"}


def clean_doi(doi):
    doi = doi.strip().rstrip(".,;")
    while doi.endswith(")") and doi.count("(") < doi.count(")"):
        doi = doi[:-1]
    return doi.rstrip(".,;")


def isbn_valid(isbn):
    d = re.sub(r"[^0-9Xx]", "", isbn).upper()
    if len(d) == 10:
        if not re.fullmatch(r"\d{9}[\dX]", d):
            return False
        total = sum((10 - i) * (10 if ch == "X" else int(ch)) for i, ch in enumerate(d))
        return total % 11 == 0
    if len(d) == 13 and d.isdigit():
        total = sum(int(ch) * (1 if i % 2 == 0 else 3) for i, ch in enumerate(d))
        return total % 10 == 0
    return False


def parse_reference(ref):
    info = {"raw": ref}
    text = ref.replace("\\[", "[").replace("\\]", "]").replace("\\_", "_")
    plain = re.sub(r"[*_]", "", text)

    m = DOI_RE.search(plain)
    info["doi"] = clean_doi(m.group(0)) if m else None

    urls = [u.rstrip(".,;)") for u in URL_RE.findall(plain)]
    info["url"] = next((u for u in urls if "doi.org/" not in u.lower()), None)

    isbn = None
    if re.search(r"isbn", plain, re.I) or not info["doi"]:
        for cand in ISBN_RE.findall(plain):
            digits = re.sub(r"[^0-9Xx]", "", cand)
            if len(digits) in (10, 13) and (re.search(r"isbn", plain, re.I) or digits.startswith(("978", "979"))):
                isbn = digits
                break
    info["isbn"] = isbn

    # Year: "(2019)", "(2019a)", "(6 December 2021)", "(n.d.)", APA "(2019, May 3)"
    ym = re.search(r"\(([^()]*?)\b(1[5-9]\d{2}|20\d{2})[a-z]?\b[^()]*\)", plain)
    if ym:
        info["year"] = int(ym.group(2))
        author_part = plain[: ym.start()]
        after = plain[ym.end():]
    else:
        y2 = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", plain)
        info["year"] = int(y2.group(1)) if y2 else None
        author_part, after = "", plain

    # Title: quoted title right after the year, else first segment before ", " or ". "
    after = after.lstrip(" .,")
    tm = re.match(r"[‘'\"“](.+?)[’'\"”]\s*(?:[,.]\s|\[|$)", after)
    if tm:
        title = tm.group(1)
        info["title_kind"] = "quoted"
    else:
        seg = re.split(r"(?:,\s|\.\s|\s\[)", after, maxsplit=1)[0]
        title = seg
        info["title_kind"] = "plain"
    info["title"] = title.strip(" .,'\"‘’“”") or None

    # Author family-name candidates (works for RMIT Harvard and APA-ish strings)
    names = []
    for w in re.split(r"[\s,;&]+", strip_accents(author_part)):
        w = w.strip(".()[]")
        if not w or w.lower() in STOP_NAME_WORDS:
            continue
        if re.fullmatch(r"[A-Z]{1,3}", w) or re.fullmatch(r"(?:[A-Z]\.?-?){1,4}", w):
            continue  # initials
        if w[0].isupper() and len(w) >= 2:
            names.append(w.lower())
    info["author_names"] = names

    low = plain.lower()
    if re.search(r"personal communication|\[powerpoint|lecture notes|\[lecture|course material|\[micro-credential|unpublished paper", low):
        info["kind"] = "unverifiable"
    elif "[large language model]" in low or re.search(r"\b(chatgpt|openai|copilot|gemini)\b.*\[", low):
        info["kind"] = "ai_tool"
    elif re.search(r"\bact \d{4}\b", low) and not info["doi"]:
        info["kind"] = "legislation"
    elif info["title_kind"] == "quoted" or info["doi"]:
        info["kind"] = "article_like"
    elif info["url"]:
        info["kind"] = "web"
    else:
        info["kind"] = "book_like"
    return info


# --------------------------------------------------------------------------- registries

def crossref_item_summary(item):
    title = clean_markup((item.get("title") or [""])[0])
    sub = clean_markup((item.get("subtitle") or [""])[0]) if item.get("subtitle") else ""
    if sub and sub.lower() not in title.lower():
        title = f"{title}: {sub}"
    year = None
    for k in ("published-print", "published-online", "issued", "created"):
        dp = (item.get(k) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            year = dp[0][0]
            break
    years = set()
    for k in ("published-print", "published-online", "issued"):
        dp = (item.get(k) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            years.add(dp[0][0])
    authors = []
    for a in item.get("author") or []:
        authors.append(a.get("family") or a.get("name") or "")
    return {
        "source": "Crossref",
        "doi": item.get("DOI"),
        "title": title,
        "year": year,
        "years": sorted(years),
        "authors": authors,
        "container": clean_markup((item.get("container-title") or [""])[0]),
        "type": item.get("type"),
        "raw": item,
    }


def openalex_item_summary(w):
    doi = (w.get("doi") or "").replace("https://doi.org/", "") or None
    loc = (w.get("primary_location") or {}).get("source") or {}
    return {
        "source": "OpenAlex",
        "doi": doi,
        "title": clean_markup(w.get("title") or w.get("display_name") or ""),
        "year": w.get("publication_year"),
        "years": [w.get("publication_year")] if w.get("publication_year") else [],
        "authors": [((a.get("author") or {}).get("display_name") or "").split()[-1:][0]
                    if (a.get("author") or {}).get("display_name") else ""
                    for a in (w.get("authorships") or [])],
        "container": loc.get("display_name") or "",
        "type": w.get("type"),
        "is_retracted": w.get("is_retracted"),
    }


def crossref_by_doi(doi):
    data = get_json(crossref_url("/works/" + urllib.parse.quote(doi, safe="/()")))
    if data and data.get("message"):
        return crossref_item_summary(data["message"])
    return None


def doi_handle_exists(doi):
    """True / False / None(unknown) using the doi.org handle API."""
    data = get_json("https://doi.org/api/handles/" + urllib.parse.quote(doi, safe="/()"))
    if data is None:
        status, _, _ = http_get("https://doi.org/api/handles/" + urllib.parse.quote(doi, safe="/()"))
        return False if status == 404 else None
    return data.get("responseCode") == 1


def crossref_search(query, rows=5):
    data = get_json(crossref_url("/works", {"query.bibliographic": query[:500], "rows": rows}))
    items = ((data or {}).get("message") or {}).get("items") or []
    return [crossref_item_summary(i) for i in items]


def openalex_search(query, rows=5):
    q = re.sub(r"[,:;!?|]", " ", query)[:300]
    data = get_json("https://api.openalex.org/works?" + urllib.parse.urlencode({"search": q, "per-page": rows}))
    return [openalex_item_summary(w) for w in (data or {}).get("results") or []]


def openalex_by_doi(doi):
    data = get_json("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="/()"))
    return openalex_item_summary(data) if data else None


def openlibrary_isbn(isbn):
    data = get_json(f"https://openlibrary.org/isbn/{isbn}.json")
    if not data:
        return None
    years = [int(y) for y in re.findall(r"\b(1[5-9]\d{2}|20\d{2})\b", data.get("publish_date", ""))]
    return {"source": "Open Library", "title": clean_markup(data.get("title", "")),
            "year": years[0] if years else None, "years": years, "authors": [],
            "container": ", ".join(data.get("publishers") or []), "type": "book"}


def openlibrary_search(title, author=None, rows=5):
    params = {"title": title[:200], "limit": rows,
              "fields": "title,subtitle,author_name,first_publish_year,publish_year,publisher"}
    if author:
        params["author"] = author
    data = get_json("https://openlibrary.org/search.json?" + urllib.parse.urlencode(params))
    out = []
    for d in (data or {}).get("docs") or []:
        t = d.get("title", "")
        if d.get("subtitle"):
            t = f"{t}: {d['subtitle']}"
        out.append({"source": "Open Library", "title": t, "year": d.get("first_publish_year"),
                    "years": sorted(set(d.get("publish_year") or [])),
                    "authors": [a.split()[-1] for a in d.get("author_name") or [] if a.split()],
                    "container": ", ".join((d.get("publisher") or [])[:2]), "type": "book"})
    return out


def check_url(url):
    status, body, final = http_get(url, accept="text/html,application/xhtml+xml,*/*")
    res = {"url": url, "status": status, "final_url": final}
    if status == 0:
        res["state"] = "unreachable"
    elif status in (401, 403, 405, 429, 999):
        res["state"] = "blocked_bots"  # site exists but refuses automated checks
    elif 200 <= status < 400:
        res["state"] = "ok"
        m = re.search(r"<title[^>]*>(.*?)</title>", body or "", re.I | re.S)
        res["page_title"] = clean_markup(m.group(1))[:200] if m else None
    else:
        res["state"] = "dead"
    if res["state"] in ("dead", "unreachable"):
        wb = get_json("https://archive.org/wayback/available?" + urllib.parse.urlencode({"url": url}))
        snap = ((wb or {}).get("archived_snapshots") or {}).get("closest")
        res["wayback"] = snap.get("url") if snap and snap.get("available") else None
    return res


# --------------------------------------------------------------------------- scoring

def score_candidate(info, cand):
    tsim = title_similarity(info.get("title") or "", cand.get("title") or "", info["raw"])
    cited_names = set(norm(n) for n in info.get("author_names") or [])
    reg_names = set(norm(a).split()[-1] for a in cand.get("authors") or [] if norm(a))
    author_match = None
    if cited_names and reg_names:
        author_match = bool(cited_names & reg_names) or any(
            difflib.SequenceMatcher(None, c, r).ratio() > 0.85 for c in cited_names for r in reg_names)
    year_ok = None
    if info.get("year") and (cand.get("years") or cand.get("year")):
        ys = cand.get("years") or [cand.get("year")]
        year_ok = any(abs(info["year"] - y) <= 1 for y in ys if y)
    return {"title_sim": tsim, "author_match": author_match, "year_ok": year_ok}


def is_match(s):
    if s["title_sim"] >= 0.9 and s["author_match"] is not False:
        return True
    if s["title_sim"] >= 0.75 and s["author_match"] and s["year_ok"] is not False:
        return True
    return False


def discrepancies(info, cand, s):
    out = []
    if s["title_sim"] < 0.9:
        out.append(f"title differs from registry (similarity {s['title_sim']:.2f}): \"{cand.get('title')}\"")
    if s["author_match"] is False:
        out.append(f"cited author(s) not among registry authors: {', '.join(a for a in cand.get('authors')[:6] if a)}")
    if s["year_ok"] is False:
        out.append(f"year {info.get('year')} vs registry {', '.join(str(y) for y in cand.get('years') or [cand.get('year')])}")
    if info.get("doi") and cand.get("doi") and info["doi"].lower() != cand["doi"].lower():
        out.append(f"DOI in citation ({info['doi']}) differs from registry DOI ({cand['doi']})")
    return out


# --------------------------------------------------------------------------- RMIT Harvard builder

def initials(given):
    parts = re.split(r"[\s.\-]+", given or "")
    return "".join(p[0].upper() for p in parts if p and p[0].isalpha())


def join_names(names):
    names = [n for n in names if n]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def rmit_harvard_from_crossref(item):
    """Draft RMIT Harvard reference from a Crossref work. Titles keep registry capitalisation:
    convert to sentence case by hand (proper nouns stay capitalised)."""
    s = crossref_item_summary(item)
    people = []
    for a in item.get("author") or []:
        if a.get("family"):
            people.append(f"{a['family']} {initials(a.get('given', ''))}".strip())
        elif a.get("name"):
            people.append(a["name"])
    editors = [f"{e.get('family', e.get('name', ''))} {initials(e.get('given', ''))}".strip()
               for e in item.get("editor") or []]
    year = s["year"] or "n.d."
    title = s["title"]
    container = s["container"]
    doi = s["doi"]
    vol, iss = item.get("volume"), item.get("issue")
    page = (item.get("page") or "").replace("–", "-").replace("—", "-")
    artno = item.get("article-number")
    publisher = item.get("publisher") or ""
    place = item.get("publisher-location") or ""
    ed = item.get("edition-number")
    edn = f", {ordinal(ed)} edn" if ed and str(ed).isdigit() and int(ed) > 1 else ""
    typ = item.get("type")
    auth = join_names(people)

    if typ == "journal-article":
        loc = ""
        if vol:
            loc = f"{vol}({iss})" if iss else f"{vol}"
            if page:
                loc += f":{page}"
                if artno:
                    loc += f", Article {artno}"
            elif artno:
                loc += f":Article {artno}"
        author_slot = auth or container
        ref = f"{author_slot} ({year}) '{title}', *{container}*"
        if loc:
            ref += f", {loc}"
        ref += f", doi:{doi}." if doi else "."
    elif typ in ("book", "monograph", "edited-book", "reference-book"):
        if not auth and editors:
            auth = join_names(editors) + (" (eds)" if len(editors) > 1 else " (ed)")
        ref = f"{auth} ({year}) *{title}*{edn}, {publisher}, " + (f"doi:{doi}." if doi else f"{place or '[place?]'}.")
    elif typ in ("book-chapter", "book-section", "book-part"):
        eds = (join_names(editors) + (" (eds) " if len(editors) > 1 else " (ed) ")) if editors else "[editor(s)?] (eds) "
        ref = (f"{auth} ({year}) '{title}', in {eds}*{container}*{edn}, {publisher}, "
               + (f"doi:{doi}." if doi else f"{place or '[place?]'}."))
    elif typ == "proceedings-article":
        ref = (f"{auth} ({year}) '{title}' [conference paper], *{container}*, {publisher}"
               + (f", doi:{doi}." if doi else ".") + "  [check: RMIT gives conference dates and place]")
    else:
        ref = f"{auth} ({year}) '{title}', *{container}*" + (f", doi:{doi}." if doi else ".") + f"  [type: {typ}; check template]"
    return re.sub(r"\s+,", ",", ref).strip()


def ordinal(n):
    n = int(n)
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


# --------------------------------------------------------------------------- verification

def verify(ref):
    info = parse_reference(ref)
    r = {"reference": ref, "parsed": {k: info.get(k) for k in ("kind", "year", "title", "author_names", "doi", "isbn", "url")},
         "verdict": None, "evidence": [], "problems": [], "suggested_reference": None, "sources_confirming": []}

    if info["kind"] == "unverifiable":
        r["verdict"] = "UNVERIFIABLE_TYPE"
        r["evidence"].append("Personal communication / lecture or course material / unpublished work: not in public registries. "
                             "Personal communication belongs in-text only, not in the reference list.")
        return r
    if info["kind"] == "ai_tool":
        r["verdict"] = "UNVERIFIABLE_TYPE"
        r["evidence"].append("Generative AI tool entry. Check the RMIT AI format and that any sources the AI mentioned were found and cited directly.")
        if info.get("url"):
            r["url_check"] = check_url(info["url"])
        return r

    matched = None  # best confirmed registry record
    doi_cand = None

    # 1. DOI
    if info["doi"]:
        doi_cand = crossref_by_doi(info["doi"])
        if doi_cand:
            s = score_candidate(info, doi_cand)
            r["evidence"].append(f"DOI {info['doi']} resolves in Crossref to: \"{doi_cand['title']}\" "
                                 f"({doi_cand['year']}; {', '.join(a for a in doi_cand['authors'][:4] if a)}; {doi_cand['container']}) "
                                 f"[title similarity {s['title_sim']:.2f}, author match {s['author_match']}, year ok {s['year_ok']}]")
            if is_match(s) or (s["title_sim"] >= 0.6 and s["author_match"]):
                matched, mscore = doi_cand, s
                r["sources_confirming"].append("Crossref (DOI)")
            else:
                r["verdict"] = "DOI_MISMATCH"
                r["problems"].append("The DOI belongs to a different work than the one cited — a strong sign of a fabricated "
                                     "or mixed-up reference.")
        else:
            exists = doi_handle_exists(info["doi"])
            if exists:
                r["evidence"].append(f"DOI {info['doi']} is registered at doi.org (not a Crossref DOI, e.g. DataCite); metadata compared via OpenAlex if possible.")
                oa = openalex_by_doi(info["doi"])
                if oa:
                    s = score_candidate(info, oa)
                    if is_match(s):
                        matched, mscore = oa, s
                        r["sources_confirming"].append("doi.org + OpenAlex")
                else:
                    r["sources_confirming"].append("doi.org (existence only)")
            elif exists is False:
                r["problems"].append(f"DOI {info['doi']} is NOT registered at doi.org — the DOI is invalid or invented.")
                r["verdict"] = "DOI_NOT_FOUND"
            else:
                r["evidence"].append("Could not reach doi.org to check the DOI (network problem).")

    # 2. Bibliographic search (Crossref + OpenAlex), unless DOI already confirmed
    search_hits = []
    if not matched and info["kind"] in ("article_like", "book_like", "web"):
        q_title = info.get("title") or ref
        cands = crossref_search(ref) + openalex_search(q_title)
        scored = sorted(((score_candidate(info, c), c) for c in cands),
                        key=lambda sc: (is_match(sc[0]), sc[0]["title_sim"], bool(sc[0]["author_match"])), reverse=True)
        for s, c in scored:
            if is_match(s):
                search_hits.append((s, c))
        if search_hits:
            mscore, matched = search_hits[0]
            srcs = sorted(set(c["source"] for _, c in search_hits))
            r["sources_confirming"].extend(f"{x} (search)" for x in srcs)
            r["evidence"].append(f"Bibliographic search match ({', '.join(srcs)}): \"{matched['title']}\" "
                                 f"({matched['year']}; {', '.join(a for a in matched['authors'][:4] if a)}; {matched['container']}) "
                                 f"[title similarity {mscore['title_sim']:.2f}]")
        elif scored:
            s, c = scored[0]
            r["evidence"].append(f"Closest registry record is NOT a match: \"{c['title']}\" ({c['year']}; "
                                 f"{', '.join(a for a in c['authors'][:3] if a)}) [title similarity {s['title_sim']:.2f}]")

    # 3. Books: ISBN + Open Library
    if not matched and (info["isbn"] or info["kind"] == "book_like"):
        if info["isbn"]:
            if not isbn_valid(info["isbn"]):
                r["problems"].append(f"ISBN {info['isbn']} fails the checksum — it is mistyped or invented.")
            else:
                ol = openlibrary_isbn(info["isbn"])
                if ol:
                    s = score_candidate(info, ol)
                    r["evidence"].append(f"ISBN {info['isbn']} found in Open Library: \"{ol['title']}\" [title similarity {s['title_sim']:.2f}]")
                    if s["title_sim"] >= 0.75:
                        matched, mscore = ol, s
                        r["sources_confirming"].append("Open Library (ISBN)")
                    else:
                        r["problems"].append("ISBN belongs to a different book than the one cited.")
        if not matched and info.get("title"):
            first = (info.get("author_names") or [None])[0]
            hits = openlibrary_search(info["title"], first) or openlibrary_search(info["title"])
            for c in hits:
                s = score_candidate(info, c)
                if is_match(s):
                    matched, mscore = c, s
                    r["sources_confirming"].append("Open Library (search)")
                    r["evidence"].append(f"Open Library match: \"{c['title']}\" ({', '.join(c['authors'][:3])}; first published {c['year']}) "
                                         f"[title similarity {s['title_sim']:.2f}]")
                    break

    # 4. URL
    if info.get("url"):
        u = check_url(info["url"])
        r["url_check"] = u
        if u["state"] == "ok":
            r["evidence"].append(f"URL loads (HTTP {u['status']}); page title: \"{u.get('page_title') or '?'}\"")
            if not matched and info.get("title") and u.get("page_title"):
                sim = title_similarity(info["title"], u["page_title"])
                r["evidence"].append(f"Page title vs cited title similarity: {sim:.2f}")
        elif u["state"] == "blocked_bots":
            r["evidence"].append(f"URL exists but blocks automated checks (HTTP {u['status']}) — open it manually.")
        else:
            msg = f"URL is {u['state']} (HTTP {u['status'] or 'no response'})."
            msg += f" Archived copy: {u['wayback']}" if u.get("wayback") else " No Wayback Machine snapshot found."
            r["problems"].append(msg)

    # 5. Retraction (OpenAlex)
    doi_for_retraction = (matched or {}).get("doi") or (info["doi"] if matched else None)
    if doi_for_retraction:
        oa = matched if matched and matched.get("source") == "OpenAlex" else openalex_by_doi(doi_for_retraction)
        if oa and oa.get("is_retracted"):
            r["problems"].append("This paper is flagged as RETRACTED in OpenAlex. Do not rely on it; check the retraction notice.")
            r["retracted"] = True
        elif oa and matched and matched.get("source") != "OpenAlex":
            r["sources_confirming"].append("OpenAlex (by DOI)")

    # 6. Verdict
    if matched:
        issues = discrepancies(info, matched, mscore)
        r["problems"].extend(issues)
        if not info.get("doi") and matched.get("doi") and matched.get("source") == "Crossref":
            r["evidence"].append(f"Suggestion: the work has a DOI you can add (RMIT: include it when available): doi:{matched['doi']}")
        if matched.get("source") == "Crossref" and matched.get("raw"):
            r["suggested_reference"] = rmit_harvard_from_crossref(matched["raw"])
        if r.get("retracted"):
            r["verdict"] = "RETRACTED"
        elif r["verdict"] == "DOI_MISMATCH":
            r["verdict"] = "DOI_MISMATCH"  # title exists elsewhere, but the cited DOI is wrong
            r["problems"].append("The cited title WAS found under a different record — likely a wrong DOI rather than an invented source.")
        elif issues:
            r["verdict"] = "FOUND_WITH_ERRORS"
        else:
            r["verdict"] = "VERIFIED"
    elif r["verdict"] in ("DOI_MISMATCH", "DOI_NOT_FOUND"):
        r["problems"].append("The cited title was not found in Crossref, OpenAlex or Open Library either.")
    elif "url_check" in r and r["url_check"]["state"] in ("ok", "blocked_bots"):
        r["verdict"] = "WEB_SOURCE_REACHABLE"
    elif "url_check" in r:
        r["verdict"] = "LINK_DEAD"
    elif info["kind"] == "legislation":
        r["verdict"] = "UNVERIFIABLE_TYPE"
        r["evidence"].append("Legislation: check on the official legislation register (e.g. legislation.gov.au, thuvienphapluat.vn).")
    elif "doi.org (existence only)" in r["sources_confirming"]:
        r["verdict"] = "DOI_EXISTS_UNCOMPARED"
    else:
        r["verdict"] = "NOT_FOUND"
        r["problems"].append("No evidence of this work in Crossref, OpenAlex or Open Library. Likely fabricated if it claims to be a "
                             "journal article or book from a major publisher; otherwise check manually (local/grey literature).")

    # Signal strength / tier
    n_indep = len(set(x.split(" ")[0] for x in r["sources_confirming"]))
    r["evidence_tier"] = ("A" if any(x in ("Crossref (DOI)", "doi.org + OpenAlex", "Open Library (ISBN)") for x in r["sources_confirming"]) and r["verdict"] in ("VERIFIED", "FOUND_WITH_ERRORS", "RETRACTED")
                          else "B" if n_indep >= 2 else "C" if n_indep == 1
                          else "D" if r["verdict"] == "WEB_SOURCE_REACHABLE" else "E")
    return r


# --------------------------------------------------------------------------- I/O

SKIP_LINES = re.compile(r"^\s*(references?|reference list|bibliography|works cited|tài liệu tham khảo)\s*:?\s*$", re.I)


def split_refs(text):
    text = text.replace("\r\n", "\n")
    blocks = [b for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) > 1 and any("\n" in b.strip() for b in blocks) and all(len(b.strip().split("\n")) <= 4 for b in blocks):
        items = [" ".join(b.split()) for b in blocks]  # wrapped paragraphs
    else:
        items = [l.strip() for l in text.split("\n") if l.strip()]
    out = []
    for it in items:
        if SKIP_LINES.match(it):
            continue
        it = re.sub(r"^\s*(?:\[\d+\]|\d+[.)]|[-•*])\s+", "", it)
        if len(it) > 15:
            out.append(it)
    return out


ICON = {"VERIFIED": "✅", "FOUND_WITH_ERRORS": "🟡", "WEB_SOURCE_REACHABLE": "🌐", "DOI_EXISTS_UNCOMPARED": "🟡",
        "DOI_MISMATCH": "🔴", "DOI_NOT_FOUND": "🔴", "NOT_FOUND": "🔴", "LINK_DEAD": "🟠",
        "RETRACTED": "⛔", "UNVERIFIABLE_TYPE": "⚪"}


def print_report(results):
    counts = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print(f"Checked {len(results)} reference(s): " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print("=" * 78)
    for i, r in enumerate(results, 1):
        short = r["reference"][:110] + ("…" if len(r["reference"]) > 110 else "")
        print(f"\n[{i}] {ICON.get(r['verdict'], '?')} {r['verdict']}  (evidence tier {r.get('evidence_tier', '-')})")
        print(f"    {short}")
        for e in r["evidence"]:
            print(f"    • {e}")
        for p in r["problems"]:
            print(f"    ⚠ {p}")
        if r.get("suggested_reference"):
            print(f"    → Registry-based RMIT Harvard draft (fix title to sentence case):\n      {r['suggested_reference']}")
    print("\nNote: NOT_FOUND means no registry evidence, not proof of fabrication. See references/verification-method.md.")


def main():
    ap = argparse.ArgumentParser(description="Verify references and build RMIT Harvard drafts from DOIs.")
    ap.add_argument("file", nargs="?", help="text file with references ('-' for stdin)")
    ap.add_argument("--json", action="store_true", help="output JSON")
    ap.add_argument("--from-doi", nargs="+", metavar="DOI", help="build RMIT Harvard drafts from DOIs")
    args = ap.parse_args()

    if args.from_doi:
        out = []
        for d in args.from_doi:
            d = clean_doi(d.replace("https://doi.org/", "").replace("doi:", ""))
            data = get_json(crossref_url("/works/" + urllib.parse.quote(d, safe="/()")))
            if not data:
                out.append({"doi": d, "error": "DOI not found in Crossref (check it, or it may be a DataCite DOI)"})
                continue
            item = data["message"]
            s = crossref_item_summary(item)
            out.append({"doi": d, "type": s["type"], "title": s["title"], "year": s["year"], "authors": s["authors"],
                        "container": s["container"], "rmit_harvard_draft": rmit_harvard_from_crossref(item)})
        if args.json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            for o in out:
                print(o.get("rmit_harvard_draft") or f"{o['doi']}: {o['error']}")
            print("\n(Drafts keep registry capitalisation — convert titles to sentence case; journal names keep their capitals.)")
        return

    if not args.file:
        ap.error("give a file of references, '-' for stdin, or --from-doi")
    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    refs = split_refs(text)
    if not refs:
        print("No references found in input.", file=sys.stderr)
        sys.exit(1)
    results = []
    for ref in refs:
        try:
            results.append(verify(ref))
        except Exception as e:  # keep going; one bad entry shouldn't stop the report
            results.append({"reference": ref, "verdict": "ERROR", "evidence": [], "problems": [f"checker error: {e}"]})
    if args.json:
        for r in results:
            r.pop("raw", None)
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    else:
        print_report(results)


if __name__ == "__main__":
    main()
