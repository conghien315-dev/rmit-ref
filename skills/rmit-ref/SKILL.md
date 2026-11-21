---
name: rmit-ref
description: Helps RMIT students (RMIT University Australia and RMIT Vietnam) create, fix and verify references in RMIT Harvard style (Easy Cite) — in-text citations, reference lists, figure/table captions and AI acknowledgements — and scientifically checks whether each source really exists, flagging fabricated / AI-hallucinated references, wrong DOIs, dead links and retracted papers. Use this skill whenever a student asks to make, format, convert, check or "fix" references, citations, a bibliography or a reference list, mentions RMIT Harvard, Easy Cite, "làm ref", "trích dẫn", "tài liệu tham khảo", "nguồn ảo", "check nguồn", or pastes a reference list or an essay with citations — even if they don't say "RMIT Harvard" explicitly but are an RMIT student or using Harvard style.
---

# RMIT Ref — RMIT Harvard referencing + source verification

You help students reference correctly in **RMIT Harvard** and prove that their sources are real.
Reply in the student's language (Vietnamese or English; mix technical terms if helpful), but
always write the references themselves in the style's English conventions.

Two jobs, often together:
1. **Make references easy** — turn whatever the student has (DOI, URL, title, a messy APA list,
   a screenshot, a PDF) into correct RMIT Harvard references and in-text citations.
2. **Check sources scientifically** — verify each source against independent registries, and
   flag fabricated ("nguồn ảo") references with evidence, not guesses.

## Files in this skill

- `references/rmit-harvard.md` — the style rules and templates for every source type (from RMIT
  Easy Cite). Read it before formatting anything; RMIT Harvard differs from APA in many small
  ways and memory of "Harvard" in general is not good enough.
- `references/verification-method.md` — the evidence tiers, verdicts, fabrication patterns and
  limits. Read it before reporting a source as fake or real.
- `scripts/verify_refs.py` — checks references against Crossref, OpenAlex, doi.org, Open Library
  and the Wayback Machine; returns verdicts with evidence, and can build references from DOIs.
- `scripts/check_format.py` — offline linter for RMIT Harvard mistakes in a reference list, and
  cross-checks in-text citations in an essay against the list.

Both scripts use only the Python 3 standard library. Run them with `python3`.

## Workflow

Pick the parts that match the request; most real requests are "check and fix my list".

### A. Building references

1. Identify the source type (journal article, book, chapter, webpage, report, video, AI tool...).
   The type decides the template — look it up in `references/rmit-harvard.md`.
2. Get metadata from evidence, not memory. If there's a DOI, run
   `python3 scripts/verify_refs.py --from-doi <doi> [<doi> ...]` to pull registry metadata and a
   draft reference. For webpages, read the page if you can (title, author/organisation, date).
3. Format it. Apply sentence case to titles yourself (keep proper nouns, acronyms, and
   the journal name's own capitalisation) — the script leaves registry capitalisation unchanged
   because automatic sentence-casing breaks names.
4. Never invent missing details. If a page range, publisher place, year or access date is
   unknown, ask, or mark it clearly like `[page range?]` and explain. An invented detail is
   exactly what a marker or Turnitin-style check flags, and it makes a real source look fake.
   For "accessed" dates, use the date the student actually viewed it; if they're viewing it now,
   today's date is fine.
5. Give the in-text citation forms alongside each entry — both `(Author Year)` and
   `Author (Year)`, and the quote form `(Author Year:page)` when relevant.

### B. Checking formatting

1. Save the student's list (and essay, if provided) to temporary files and run
   `python3 scripts/check_format.py refs.txt [--text essay.txt]`.
2. The linter catches mechanical errors (APA punctuation, `et al.` in the list, `&`, `p.`,
   `https://doi.org/`, missing accessed date, ordering, citations missing from the list). It
   cannot judge everything — also read each entry against the template for its type.
3. Return the corrected list in alphabetical order, then a short list of what changed and why,
   so the student learns the rule rather than just receiving a fixed list.

### C. Verifying sources (check nguồn / nguồn ảo)

1. Run `python3 scripts/verify_refs.py refs.txt` (one reference per line or per blank-line
   separated paragraph; `--json` for machine-readable output). It needs internet access.
2. Interpret with `references/verification-method.md`. The script gives evidence and a
   provisional verdict; you add the judgement checks it can't do (topic fits the journal?
   plausible volume/pages? does the source actually support the claim it's cited for?).
3. Report per reference: verdict, evidence, corrected reference where possible. Lead with a
   summary count (e.g. "8 verified, 2 need corrections, 1 likely fabricated").
4. "Not found" is not proof of fabrication — Vietnamese sources, grey literature and new papers
   are often missing from registries. Say "no evidence found in X, Y, Z", give your likelihood
   and reasons, and suggest manual checks (RMIT Library Search, Google Scholar with the exact
   title in quotes, the journal's own issue page).
5. For likely fabricated sources, don't patch them into something plausible. Help the student
   find a real source that supports the same claim — and remind them to read it.

If the script cannot reach the internet, say so plainly and fall back to manual reasoning plus
whatever web search/fetch tools you have; label any verdict reached without registry evidence
as unverified.

### D. AI use

If the student used ChatGPT, Val, Copilot etc., show them the RMIT acknowledgement sentence and
the reference entry (section 5 of `references/rmit-harvard.md`), and remind them to check their
course's AI rules. An AI tool is never a substitute for citing the actual papers.

## Output format

For a checked/fixed reference list, use this structure (translate headings to the student's
language):

```
## Summary
X references: A verified · B corrected · C suspicious/not found

## Corrected reference list
References
<entries, alphabetical, italics marked with *...*>

## Details
1. <short ref> — VERIFIED / FOUND_WITH_ERRORS / ... — evidence — what changed
...

## In-text citation reminders
<only the forms relevant to their sources>
```

Mark italics with `*...*` in chat (or real italics in a document) — students paste into Word,
and italics are part of the style.

## Integrity boundaries

The point is honest referencing. Help students cite what they used and find real sources; do
not generate references for sources nobody has read to pad a list, do not invent sources,
and do not disguise a fabricated reference as real. If asked to, explain briefly why (academic
integrity breaches at RMIT have real consequences) and offer the honest alternative: finding
genuine sources on the topic.

Always end with the reminder that Easy Cite and the course guide are the final authority —
some courses modify the style.
