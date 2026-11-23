# Synthesis guide

## Contents
1. The synthesis matrix
2. Relationship patterns
3. Evaluating sources and arguments (the Notes column)
4. Writing synthesised paragraphs
5. Reporting verbs and transitions
6. JSON format for `build_matrix.py`
7. Worked example
8. Common mistakes

---

## 1. The synthesis matrix

A table with **ideas as rows** and **sources as columns**, plus a final **Notes** column:

| Idea / concept / point | Source A: paraphrase + citation | Source B | Source C | … | Notes on argument strength, relevance, source reliability |
|---|---|---|---|---|---|

Why ideas as rows: an essay paragraph is about one idea. Reading across a row shows every
source's position on that idea at once, which is exactly what a synthesised paragraph needs.
Organising by source (one row per article) produces an annotated bibliography instead.

Cell content: 1–3 sentences of paraphrase in the student's words + citation
(`Nguyen et al. 2021:45`) + stance marker. Keep direct quotes rare and in 'single quotes'
with a page number.

Stance markers (the slide's shapes, given names so the table works in text):

| Marker | Symbol | Use when the source… |
|---|---|---|
| `agree` | ● | supports the idea's main point |
| `partial` | ◐ | agrees on the main aspect but adds a condition, different perspective, context or emphasis |
| `disagree` | ⊘ | contradicts the point or finds the opposite |
| `alternative` | ✚ | proposes another explanation/approach rather than simply agreeing or disagreeing |
| empty | | does not address the idea |

The same source can appear more than once in a row (e.g. ◐ and ✚).

## 2. Relationship patterns

| Pattern | Rule of thumb | What it means for writing |
|---|---|---|
| **Consensus** | all sources addressing the idea `agree` (≥2 sources) | State it confidently; group citations. Still say *how strong* the shared evidence is. |
| **Majority with dissent** | most agree; ≥1 `partial`, `disagree` or `alternative` | Present the majority view, then the qualification/dissent, then evaluate why they differ (method, context, date). |
| **Contested** | sources split, or all take different positions | Present the positions side by side, explain the reasons for the disagreement, give your evaluated view. |
| **Single-source** | only one source addresses it | Weak basis. Find more sources or present cautiously ("one study suggests…"). |
| **Gap** | no source addresses it | Possible research gap — useful in a literature review's conclusion. |

Why sources differ is usually the most valuable thing to write about: different samples,
countries, time periods, methods, definitions, or disciplinary assumptions.

## 3. Evaluating sources and arguments (Notes column)

- **Argument strength** — what kind of evidence? (meta-analysis > RCT > large survey > small
  case study > expert opinion > anecdote); sample size and population; methods appropriate?
  limitations the authors admit?
- **Relevance** — does it address *this* question, population and context (e.g. Vietnam vs
  US; Gen Z vs all consumers)? Is it current enough for the field?
- **Source reliability** — peer-reviewed journal? reputable publisher or government body?
  funding / conflicts of interest? retracted? (verify existence with `rmit-ref`).
- Keep notes short and evaluative: "Large survey (n=1,200) but self-reported intention, not
  actual purchases; US only."

## 4. Writing synthesised paragraphs

**Structure (one paragraph per matrix row):**
1. **Topic sentence about the idea** — not about an author.
   ✗ "Nguyen et al. (2021) studied TikTok ads." ✓ "Short-video advertising appears to raise young consumers' purchase intention."
2. **Evidence of agreement**, grouped: "Several studies report … (Lee 2020; Nguyen et al. 2021; Tran and Pham 2022)."
3. **Qualification / disagreement / alternative**: "However, Smith (2019) found the effect only for low-cost products, …"
4. **Explanation of the difference**: "This difference may reflect …(sample, context, method)."
5. **Your evaluation**: "Taken together, the evidence suggests …, although …"
6. **Link to the question / next paragraph.**

**Templates by pattern**

- Consensus: *"There is broad agreement that X (A 2020; B 2021; C 2022). For example, A (2020) …, while B (2021) similarly …. However, most of this evidence comes from …, so …"*
- Majority with dissent: *"Most studies find X (A 2020; B 2021). B (2021) and C (2022) both show …. In contrast, D (2019) argues …, possibly because …. This suggests X holds mainly when …"*
- Contested: *"Researchers disagree on X. A (2020) argues …, whereas B (2021) contends …, and C (2022) proposes a different explanation: …. These differences appear to stem from …. On balance, …"*
- Single-source / gap: *"Only one study has examined X in Vietnam (A 2021), which found …; further research is needed."* / *"None of the reviewed studies addressed X, which represents a gap …"*

RMIT Harvard in-text reminders: no comma between author and year `(Lee 2020)`; `and` for two
authors; `et al.` for 3+; several sources in one bracket alphabetical, separated by `;`;
quote pages `(Lee 2020:12)`.

## 5. Reporting verbs and transitions

| Purpose | Words |
|---|---|
| Neutral reporting | states, reports, describes, notes, observes, finds |
| Strong claim | argues, contends, asserts, maintains, emphasises |
| Tentative | suggests, proposes, implies, speculates |
| Agreement | similarly, likewise, in line with, consistent with, also, corroborates |
| Contrast | however, in contrast, conversely, whereas, while, on the other hand, challenges, disputes |
| Qualification | although, partly, to some extent, only when, under certain conditions |
| Alternative | alternatively, offers a different explanation, another perspective is |
| Concluding | taken together, overall, on balance, this suggests, therefore |

Vietnamese note (ghi chú): *synthesis* = tổng hợp có phân tích (không phải tóm tắt từng bài);
*paraphrase* = diễn đạt lại bằng lời của mình; *consensus* = đồng thuận; *contested* = còn tranh
cãi; *gap* = khoảng trống nghiên cứu.

## 6. JSON format for `build_matrix.py`

```json
{
  "topic": "Does short-video advertising influence Gen Z purchase intention?",
  "sources": [
    {"id": "S1", "label": "Lee 2020", "reference": "Lee K (2020) 'Title', *Journal*, 1(2):3-4, doi:...", "reliability": "Peer-reviewed; survey n=800"}
  ],
  "ideas": [
    {
      "idea": "Short-video ads raise purchase intention",
      "cells": [
        {"source": "S1", "stance": "agree", "text": "Found intention rose after exposure to TikTok ads.", "page": "45"},
        {"source": "S2", "stance": "partial", "text": "Effect only for low-price items."}
      ],
      "pattern": "",
      "notes": "Mostly self-reported intention; all US/Korea samples."
    }
  ]
}
```

- `stance`: `agree` | `partial` | `disagree` | `alternative`.
- `pattern`: leave empty to let the script infer it (consensus / majority with dissent /
  contested / single-source / gap).
- `page` optional; `reliability` optional (appears under the source header).

## 7. Worked example (the slide)

| Idea | Source 1 (2019) | Source 2 (2019) | Source 3 (2019) | Notes |
|---|---|---|---|---|
| Idea 1 | ● | ● | ● | Consensus — everyone agrees on this point. |
| Idea 2 | ◐ different perspective | ● ✚ agrees, and raises alternative ideas | ● | Majority with dissent — sources 2 and 3 agree on the main aspect; source 1 sees it differently; source 2 adds alternatives. |
| Idea 3 | ⊘ | ⊘ | ⊘ | Contested — all sources take different positions. |

Paragraph for Idea 2 (template): *"Sources 2 and 3 agree that … (Source 2 2019; Source 3 2019).
However, Source 1 (2019) approaches this from a different perspective, arguing …. Source 2 (2019)
also raises an alternative explanation: …. This suggests …."*

## 8. Common mistakes

1. One paragraph per source ("summary stacking") instead of per idea.
2. Topic sentences that start with an author's name.
3. Leaving out disagreement because it's "messy" — debate is what markers reward.
4. Presenting a single-source point as established fact.
5. Copying sentences into the matrix, then into the essay (plagiarism risk).
6. Matrix cells based on titles or guesses, not on reading the source.
7. Describing without evaluating — the Notes column is where marks come from.
