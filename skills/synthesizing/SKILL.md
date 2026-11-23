---
name: synthesizing
description: Helps students synthesise sources for essays, literature reviews and reports using a synthesis matrix — organising notes by idea (not by source), marking where sources agree, partly agree, disagree or add alternative ideas, evaluating argument strength, relevance and reliability, and turning the matrix into synthesised paragraphs with correct in-text citations (RMIT Harvard by default). Use this skill whenever a student wants to synthesise or compare sources, build a synthesis matrix / synthesis grid / literature review table, organise research notes, find themes or gaps across articles, "tổng hợp nguồn", "synthesis", "so sánh các bài báo", "viết literature review", or pastes several summaries/articles and asks how they fit together — even if they don't say "synthesis".
---

# Synthesizing — from notes to synthesis

Synthesis means organising what you read **by idea, not by source**, then showing how the
sources relate on each idea: where they agree, where they partly agree or see it differently,
where they disagree, and what is missing. A list of summaries ("Smith says… Lee says…") is not
synthesis — markers at RMIT call that "describing, not analysing".

Reply in the student's language (Vietnamese or English). Write citations in **RMIT Harvard**
unless the student says their course uses another style. If the `rmit-ref` skill is available,
use it to verify sources and format the reference list.

## Files

- `references/synthesis-guide.md` — the matrix method, the relationship patterns, how to judge
  argument strength / relevance / reliability, paragraph templates, reporting verbs and
  transition words (English, with Vietnamese notes), and a worked example. Read it before
  building a matrix or writing paragraphs.
- `scripts/build_matrix.py` — turns the matrix (JSON) into a Markdown table, a CSV for
  Excel/Google Sheets, and a colour-coded HTML page the student can print. Python 3 stdlib only.

## Workflow

### 1. Collect sources and the question
- Ask for (or identify) the essay question / topic, because "relevance" is judged against it.
- Get the actual content: pasted text, PDFs, abstracts, or the student's own notes. Work from
  what the sources really say. If the student gives only titles, say you need the text (or
  fetch the abstract and label any cell based on it "abstract only") — a matrix built from
  guesses about papers produces confident-sounding nonsense and misrepresents authors.
- Give each source a short in-text label, e.g. `(Nguyen et al. 2021)`, plus its full reference.

### 2. Find the ideas (rows)
Read across all sources and list the 3–7 ideas, concepts or claims relevant to the question.
Ideas come from the overlap between sources, not from one source's headings. Phrase each idea
neutrally (e.g. "Effect of TikTok ads on Gen Z purchase intention"), not as one author's
conclusion.

### 3. Fill the cells
For each idea × source: a short **paraphrase in the student's own words** (not copied
sentences), the citation with page/section if there is one, and a **stance marker**:

| Marker | Meaning (from the synthesis-matrix convention) |
|---|---|
| `agree` ● | supports the main point |
| `partial` ◐ | agrees with the main aspect but with a different perspective, condition or emphasis |
| `disagree` ⊘ | contradicts the point |
| `alternative` ✚ | raises an alternative idea or explanation |
| *(empty)* | source doesn't address this idea — leave it empty; gaps are information |

A source may appear twice in one row (e.g. it partly agrees *and* raises an alternative).

### 4. Notes column — evaluate, don't just describe
For every idea, state the **relationship pattern** and evaluate:
- Pattern: *consensus* (all agree), *majority with dissent*, *contested* (sources disagree),
  *single-source* (only one source — weak basis), *gap* (no source — possible research gap).
- Argument strength: evidence type (RCT, survey n=?, case study, opinion), methods, sample, context.
- Relevance to the question, and currency.
- Source reliability: peer-reviewed? publisher? conflicts of interest? (Use `rmit-ref` to verify existence.)

### 5. Produce the matrix
Write the matrix as JSON (format in `references/synthesis-guide.md`, §6) and run:

```
python3 scripts/build_matrix.py matrix.json --out <folder>
```

It writes `synthesis-matrix.md`, `.csv` and `.html`, and fills in the pattern automatically
when the notes don't state one. Show the Markdown table in chat; give the student the CSV/HTML
paths. If Python isn't available, write the Markdown table directly.

### 6. From matrix to paragraphs
For each row, help the student write one synthesised paragraph using the templates in
`references/synthesis-guide.md` §4: topic sentence about the **idea**; grouped citations for
agreement `(Lee 2020; Tran and Pham 2022)`; contrast with transitions ("However, …",
"In contrast, …"); the student's evaluation ("This suggests…", "evidence is limited because…");
link back to the question.

Prefer scaffolding over ghost-writing: give the structure, sentence starters and one model
paragraph, then let the student write the rest. Remind them to check whether their course
allows AI help and to acknowledge it (RMIT format: "I used [tool] (Creator year) to …").

### 7. Check
Before finishing: every claim in a paragraph traces to a matrix cell; no cell paraphrase is a
copied sentence; every in-text citation has a reference-list entry; single-source and gap rows
are flagged, not presented as consensus.

## Output format

```
## Topic / question
## Synthesis matrix   (Markdown table: Idea | Source A | Source B | … | Notes)
## What the matrix shows   (2–4 bullets: strongest consensus, main debate, gaps)
## Paragraph plan   (one line per idea: topic sentence + order of evidence)
## Model paragraph   (one idea only, if asked)
## Files   (paths to CSV / HTML)
```
