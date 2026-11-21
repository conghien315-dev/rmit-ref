# Source verification method

How to decide, with evidence, whether a reference is **real**, **real but mis-cited**, or
**likely fabricated** ("hallucinated" — invented by an AI tool, or made up by a person).

The guiding idea: a claim that a source exists is a factual claim, so it needs evidence from
independent registries, not a feeling that it "looks right". Fabricated references are built
to look right — plausible author names, a real journal, a realistic DOI — so surface plausibility
is worth almost nothing.

## Contents
1. Evidence tiers
2. The procedure
3. Verdicts and what they mean
4. Known fabrication patterns
5. Quality / credibility check (real ≠ good)
6. Limits — what "not found" does and does not mean
7. How to report to the student

---

## 1. Evidence tiers

| Tier | Evidence | Strength |
|---|---|---|
| A | DOI resolves **and** registry metadata (title, authors, year, journal) matches the citation | Conclusive: it exists and is this work |
| A | ISBN passes checksum **and** a catalogue record (Open Library / library catalogue) matches title + author | Conclusive for books |
| B | Found by bibliographic search in two independent indexes (e.g. Crossref and OpenAlex) with title similarity ≥ 0.90 and matching first author and year (±1) | Strong |
| C | Found in one index only, or title matches but author/year differ | Moderate — exists, but citation details need correcting |
| D | URL loads (HTTP 200) and the page content matches the title | Moderate for web sources |
| E | No match anywhere, or DOI belongs to a different work | Warning — see §6 before concluding "fake" |

Always triangulate: one strong signal plus one independent confirming signal.

## 2. The procedure

Run `scripts/verify_refs.py` first; it automates steps 1–5 and reports the evidence it found.
Then apply judgement (steps 6–7), which the script cannot do.

1. **Parse** each reference: authors, year, title, container (journal/book/site), DOI, ISBN, URL.
2. **DOI check** (if present): does it resolve (Crossref, then the doi.org handle registry)?
   If it resolves, compare the registered title/authors/year with the citation. A DOI that
   resolves to a *different* paper is one of the strongest fabrication signals.
3. **Bibliographic search**: query Crossref (`query.bibliographic`) and OpenAlex with the
   title (and whole reference). Score the best hit:
   - title similarity (normalised, case/punctuation-insensitive)
   - first-author family name present among the hit's authors
   - year equal or within ±1 (online-first vs print year differ legitimately)
4. **Books**: validate ISBN-10/13 checksum; look up Open Library by ISBN, else by title+author.
5. **Web sources**: request the URL; record HTTP status; if dead, check the Internet Archive
   Wayback Machine for a snapshot (a dead link to a once-real page is "link rot", not fabrication).
6. **Retraction check**: OpenAlex `is_retracted`. A retracted paper is real but generally must
   not be relied on (tell the student; suggest they check the retraction notice).
7. **Human-judgement checks** (you, not the script):
   - Does the journal actually publish on this topic? (A cardiology paper in a marketing journal is a red flag.)
   - Is the volume/issue plausible for that year? Pages plausible for that journal?
   - Does the claimed content match what the student says it supports? If the abstract is
     available (OpenAlex/Crossref), read it — a real paper cited for a claim it doesn't make is
     a different integrity problem ("citation misattribution").
   - Is it a grey-literature or local source (Vietnamese government site, company report,
     lecture notes)? Then registries won't have it — switch to URL/archive/publisher checks.

## 3. Verdicts

| Verdict | Meaning | Action |
|---|---|---|
| `VERIFIED` | Tier A or B evidence, details match | Keep; fix formatting only |
| `FOUND_WITH_ERRORS` | Work exists but year/authors/title/DOI in the citation are wrong | Correct from registry metadata; show diff |
| `DOI_MISMATCH` | The DOI resolves to a different work | Treat as suspicious; search for the cited title separately — maybe the DOI was a typo, maybe the whole reference is invented |
| `DOI_NOT_FOUND` | The DOI is not registered at doi.org at all | Invalid or invented DOI; search the title separately |
| `DOI_EXISTS_UNCOMPARED` | DOI is registered (e.g. DataCite) but metadata couldn't be compared | Open the DOI link and compare by hand |
| `RETRACTED` | Exists but retracted | Advise replacing it |
| `WEB_SOURCE_REACHABLE` | No registry record, but the URL loads (or blocks bots) | Normal for webpages/grey literature; open it and confirm title, author, date |
| `LINK_DEAD` | Web source unreachable; archived copy may exist | Use archived URL or find current location |
| `NOT_FOUND` | No registry evidence | Likely fabricated **if** it claims to be a journal article/book with a DOI/ISBN from a major publisher; otherwise "unverified — manual check needed" |
| `UNVERIFIABLE_TYPE` | Personal communication, lecture notes, print-only local material | Cannot be checked online; that's normal |

## 4. Known fabrication patterns

These are typical of AI-generated reference lists:

- **Chimera**: real author + real journal + invented title (or a real title from a different author).
- **Borrowed DOI**: a well-formed DOI that belongs to an unrelated paper.
- **Phantom DOI**: correct prefix of a real publisher (e.g. `10.1016/`) but suffix not registered.
- **Too-perfect title**: the title restates the student's essay question almost word for word.
- **Impossible metadata**: volume numbers the journal never reached, page ranges beyond an issue,
  publication years before the journal existed or after the cited author's death, a 2026 paper
  "cited" by a 2021 source.
- **Generic authors**: Smith J, Nguyen T, Lee K combinations with no publication record together.
- **Real paper, wrong claim**: the source exists but doesn't say what it's cited for.
- **Dead links to plausible paths** (`/research/2021/impact-of-...`) on real domains that never existed
  (Wayback has no snapshot ever).

One pattern alone is suggestive; two or more together, plus registry absence, is strong.

## 5. Quality check — real is not the same as reliable

After existence, briefly assess suitability (CRAAP-style): Currency (date vs field), Relevance,
Authority (peer-reviewed? who publishes?), Accuracy (evidence, citations), Purpose (commercial
or advocacy bias). Flag predatory-journal warning signs (unknown publisher, aggressive APCs,
no editorial board, wildly broad scope). Wikipedia, essay mills, StuDocu/CourseHero uploads,
and AI chat answers are not citable academic sources — suggest what to cite instead.

## 6. Limits — "not found" is not proof of fabrication

Registries cover most DOI-bearing journal articles, many books and conference papers, but
coverage is weak for: Vietnamese-language publications, local government and company
documents, older print books, newspapers, theses outside repositories, and very new papers
(indexing lag of days to weeks). Spelling variants of Vietnamese names (diacritics, family name
order: "Nguyen Van A" vs "A Nguyen") cause false negatives — retry with variants.

So: report `NOT_FOUND` as **"no evidence found in Crossref / OpenAlex / Open Library"** and give
a likelihood with reasons, never an accusation. Offer the student manual next steps:
RMIT Library Search, Google Scholar (exact title in quotes), the journal's own website
(browse the cited volume/issue), the publisher's catalogue, or asking a librarian.

## 7. Reporting to the student

For each reference give: verdict, the evidence (what matched, what didn't, from which source),
and the corrected RMIT Harvard reference when metadata is available. Summarise at the top:
how many verified / need fixing / suspicious. Be calm and non-judgemental — many students got
fabricated references from an AI tool in good faith. The fix is to find a real source that
supports the claim (and read it), not to "repair" the fake one.
