# Discovery Engine — Project Context

> Derived from [`ProblemStatement.md`](file:///d:/Attempt%202/docs/ProblemStatement.md)
> Generated: 2026-09-25

---

## 1. Project Overview

| Field | Detail |
|---|---|
| **Project name** | Discovery Engine |
| **Product domain** | Google Photos — retrieval of vaguely remembered photos |
| **Deliverable** | Part 1 of the NextLeap graduation brief (Attempt 2) |
| **Submission deadline** | 7 October 2026, 15:59 IST |
| **Engine findings target** | 29 September 2026 |

### Core Question

> **When someone knows a photo exists but can't pin it down, what do they remember, what have they forgotten, what did they try, and where did it break?**

This is **not** a general "is Google Photos search good?" evaluation. It is a focused investigation into the cognitive and behavioral patterns around photo retrieval with incomplete memory. The brief explicitly rejects the framing *"users find it difficult to search for old photos."*

### Headline Output

The **Memory Map** (Section 6.1 of the spec) — a table showing, for each category of memory cue, how often it is *remembered* vs. *forgotten* across all units. This directly answers the brief's question: *"What information do people actually remember?"*

---

## 2. Governing Principles (Hard Rules)

These four rules are non-negotiable and must be enforced at every stage:

1. **No invented data** — Every number traces to a stored unit. Every quote is a verbatim substring, verified programmatically.
2. **No preset taxonomy** — Categories are *induced* from free-text descriptions, not predefined. Every category must be traceable to the induction step.
3. **Reproducible** — Temperature 0 on every LLM pass. Model strings, prompts, run dates, and counts are saved with every output file.
4. **Honest denominators** — Every stage records units in vs. units out, including losses to errors. Losses are reported, never hidden.

---

## 3. Data Sources

### 3.1 Source Inventory

| # | Source | Type | Collection Method | Priority |
|---|---|---|---|---|
| 1 | **Google Photos Help Community** | Discussion | Web scraping of `support.google.com/photos/` — thread listings + search endpoint | **Primary depth source** |
| 2 | **Google Play Store** | Review | `google-play-scraper` — newest ~10,000 + most-relevant sort, deduplicated | High |
| 3 | **Apple App Store** | Review | Public RSS feed (`itunes.apple.com/.../rss/customerreviews`), storefronts: `in`, `us`, `gb` minimum | Medium (may fail — report if so) |
| 4 | **YouTube** | Discussion | YouTube Data API v3, `commentThreads` — 25–40 videos selected by search query | High |
| 5 | **Hacker News** | Discussion | Algolia HN Search API (public, free, no auth) | Supplementary (low volume, high quality) |
| 6 | **XDA Developers** | Discussion | Public forum pages | Supplementary (collect if time allows) |

### 3.2 Explicitly Excluded

- **Reddit** — API access was not granted in time; scraping would breach terms. This must be stated plainly in method notes and the deck.

### 3.3 Collection Keywords

```
can't find, cannot find, couldn't find, unable to find, looking for,
search for, remember, forgot, don't remember, lost photo, old photo,
that photo, a photo of, find a picture, where is, years ago,
scroll, scrolling, search doesn't, search didn't, search is useless,
search results, no results, nothing comes up, face, people, location,
date, album, screenshot
```

For the Help Community, also walk thread categories: **search**, **organisation**, **albums**, and **"finding photos"** — do not rely on keyword search alone.

### 3.4 Collection Constraints

- Respect `robots.txt`
- Rate-limit to ~1 request/sec
- Set a descriptive user agent
- Deduplicate on normalised text
- Keep **English only** — record count of non-English units set aside
- Never store usernames — use hashed author IDs

---

## 4. Data Schema — Unit Model

Each collected piece of feedback is stored as one "unit" with this schema:

| Field | Description |
|---|---|
| `id` | Stable hash of `source` + `source_id` |
| `source` | `help_community` \| `playstore` \| `appstore` \| `youtube` \| `hn` \| `xda` |
| `source_type` | `review` \| `discussion` |
| `source_id` | Native ID from the platform |
| `url` | Link to the original, where available |
| `text` | Full original text |
| `parent_id` | For replies — the thread/comment being replied to |
| `is_reply` | `true` \| `false` |
| `author_hash` | Hashed author identifier (never raw usernames) |
| `created_at` | ISO date |
| `rating` | Star rating, where applicable |
| `lang` | Detected language |
| `context` | Thread title or video title, where applicable |

**Key design note:** `parent_id` and `is_reply` are critical. Help Community replies often contain *workarounds*, which are a primary analysis output (Section 6.5). Replies must **not** be discarded.

---

## 5. Processing Pipeline

The engine runs a three-pass pipeline, each with a distinct purpose:

```
Collection → Pass 1 (Relevance Gate) → Checkpoint → Pass 2 (Open Extraction) → Pass 3 (Taxonomy Induction) → Analysis Outputs
```

### 5.1 Pass 1 — Relevance Gate

| Aspect | Detail |
|---|---|
| **Model** | Claude Haiku 4.5, temperature 0 |
| **Purpose** | Determine if a unit is about someone trying to find a *specific* photo/video they believe exists |
| **Labels** | `yes` — specific retrieval attempt; `partial` — general search complaint; `no` — unrelated |
| **Keep** | Both `yes` and `partial` |
| **Reply rule** | A reply describing how to find something, in response to a relevant parent, is `yes` even without restating the target |

**Quality gate:** Random sample of 60 decisions (20 per label), human-labelled blind. Agreement must be ≥ 85% or the prompt must be fixed and the pass rerun.

### 5.2 Pass 2 — Open Extraction

| Aspect | Detail |
|---|---|
| **Model** | Claude Sonnet 5, temperature 0 |
| **Purpose** | Describe each relevant unit in free text — no categorisation yet |
| **Context rule** | For replies, pass the parent post's text as context, but extract only from the reply itself |

**Extraction schema fields:**

| Field | What it captures |
|---|---|
| `target` | What the photo/video was, in the user's own terms |
| `remembered` | Each separate thing the person remembered (split into individual items) |
| `forgotten` | Each thing the person couldn't remember or clearly didn't know |
| `attempts` | Actions taken + exact query text if quoted |
| `breakdown` | Where and why the attempt failed, in the user's framing |
| `outcome` | `found` \| `not_found` \| `gave_up` \| `unclear` |
| `workaround` | Anything done outside normal search to find it |
| `stakes` | Why it mattered to them |
| `context_signals` | Library size hint, time since photo, device, use case |
| `evidence_quote` | Exact verbatim substring of the source text |
| `confidence` | 0.0–1.0 |

**Programmatic checks after pass:**
1. **Quote check** — `evidence_quote` must be a substring of `text`. Failures are flagged and excluded from quote displays.
2. **Loss check** — Units in vs. units out. Report any dropped by the batch API.
3. **Confidence floor** — Keep units at confidence ≥ 0.6 (may be lowered to 0.5 per checkpoint 1.4). Report count below threshold.

### 5.3 Pass 3 — Taxonomy Induction

This is the key methodological improvement over Attempt 1 (which used pre-set categories).

**Step 3.1 — Induce** (for each field: `target`, `remembered`, `forgotten`, `breakdown`, `workaround`):
1. Collect all phrases for the field
2. Give the model a shuffled sample of 300–400 phrases → propose 8–15 categories (name + definition + 3 real examples)
3. Repeat with a different shuffled sample
4. Merge: categories in both runs = stable; categories in only one = flagged

**Step 3.2 — Human Review** (HARD STOP):
- Save to `taxonomy_proposed.json`
- Human reviews, merges, renames, splits
- Save result as `taxonomy_final.json`
- Record changes in `taxonomy_changes.md`

**Step 3.3 — Assign:**
- Every unit's phrases are assigned to one category or `other`
- If `other` > 15% for any field → taxonomy is incomplete → return to Step 3.1 with the `other` phrases

**Step 3.4 — Deductive Layer** (the brief's four-stage failure model):

| Stage | Description |
|---|---|
| **Express** | User can't express what they remember |
| **Understand** | Product doesn't understand the clues given |
| **Evaluate** | Results are hard to evaluate |
| **Refine** | User can't refine an unsuccessful search |

Each unit's `breakdown` is mapped onto these four stages as a *separate, labelled layer*. Items fitting none = `other` (potentially the most interesting — failures the brief's own frame didn't anticipate). The dashboard must clearly state this is a deductive frame applied on top of inductive categories.

---

## 6. Analysis Outputs

All files saved to `data/out/` as CSV, plus `summary.json` with counts.

| # | Output | Description |
|---|---|---|
| **6.1** | **Memory Map** (headline) | For each cue category: count of remembered vs. forgotten across units. Shows what memory reliably holds onto and what it drops. |
| **6.2** | **Breakdown Distribution** | Units per inductive breakdown category + units per stage of the four-stage frame, with `other` count. |
| **6.3** | **Query Language** | Every `query_text` collected: word length, whether it names an object/place/person/time/feeling, whether first attempt or reformulation. The gap between what people remember and what they type is where retrieval breaks. |
| **6.4** | **Target Types** | Kinds of photos people hunt for — whatever the taxonomy induction produces (e.g., screenshots, documents, travel, people, pets, receipts, medical). |
| **6.5** | **Workarounds** | What people do instead of search. **Split by origin**: self-discovered workaround vs. recommended-by-someone-else. |
| **6.6** | **Opportunity Ranking** | `opportunity = frequency × mean_severity × specificity × triangulation`. Triangulation is weighted by source *type*, not just source count. |
| **6.7** | **Segment Signals** | Findings broken down by library size, time since photo, use case. Report coverage for every split — if too few units, say so rather than showing numbers. |

### Opportunity Ranking — Triangulation Weights

| Condition | Weight |
|---|---|
| Appears in both a review-type and a discussion-type source | 1.0 |
| Appears in two or more sources of the same type | 0.85 |
| Appears in one source only | 0.7 |

The formula, weights, and source-type mapping must all be visible on the dashboard.

---

## 7. Analysis Questions (Guiding Frame)

These questions guide the analysis — they are questions, not categories:

1. What **kinds of photos** do people struggle to retrieve?
2. What do people actually **remember** about a photo they can't find?
3. What have they **forgotten**?
4. How do they **phrase searches** when memory is incomplete?
5. Where does the attempt **break**?
6. What do they **do instead**?
7. Which patterns are **frequent, severe, and appear across source types**?

---

## 8. Checkpoints & Review Gates

Three hard stops where the engine must pause and wait for human review:

| # | When | What is reviewed |
|---|---|---|
| 1 | After collection + Pass 1 | **Source adequacy checkpoint** — relevant-unit count by source. Need ≥ 400 relevant units with ≥ 80 from discussion-type sources to proceed. |
| 2 | After gate quality check | **Agreement rate** from the 60-unit sample. Must be ≥ 85%. |
| 3 | After Pass 3.1 (taxonomy induction) | `taxonomy_proposed.json` — human reviews before any category assignment happens. |

### Source Adequacy Decision Tree

```
≥ 400 relevant units AND ≥ 80 from discussion sources?
├── YES → Proceed to analysis
└── NO → Widen collection (more Help Community categories, more YouTube videos, more App Store storefronts, then XDA)
    └── Still short?
        └── Report explicitly, lower confidence floor to 0.5 (stated), lean on primary research (Part 3)
```

---

## 9. Per-Stage Reporting

After every stage, report:
- **Counts** in and out
- **Failures** and why they occurred
- **5 randomly sampled units** for sanity-checking

---

## 10. Method Notes (`method_notes.md`)

Must be written as-you-go and rendered verbatim on the dashboard. Required contents:

- Every source attempted + success/failure status
- Reddit exclusion statement (verbatim: *"API access not granted within the project timeline; scraping would breach its terms, so it was excluded rather than worked around"*)
- App Store outcome
- Models and temperatures used, with run dates
- Confidence floor value + whether checkpoint 1.4 forced it lower
- Units in/out at every stage, including batch-API losses
- Gate agreement rate
- Changes between `taxonomy_proposed.json` and `taxonomy_final.json`

---

## 11. Explicitly Out of Scope

| Item | Reason |
|---|---|
| Dashboard | Comes after findings are reviewed |
| Solution / MVP work | Not part of this deliverable |
| Sentiment analysis | Brief explicitly says workflow must go beyond it |

---

## 12. Key Lessons from Attempt 1

The spec references several problems from the first attempt that this design corrects:

| Issue in Attempt 1 | Correction in Attempt 2 |
|---|---|
| Preset taxonomy weakened discovery claims | Taxonomy now *induced* from data (Pass 3) |
| Batch API silently dropped units (910 → 909) | Loss checks are now mandatory at every stage |
| Reddit absence was quietly omitted | Must be stated plainly and openly |
| Triangulation counted sources, not source *types* | Triangulation now weighted by source type |
| App Store returned nothing | Retry with multiple storefronts; if it fails again, report and move on |

---

## 13. Technology & Model Summary

| Purpose | Model | Temperature |
|---|---|---|
| Pass 1 — Relevance gate | Claude Haiku 4.5 | 0 |
| Pass 2 — Open extraction | Claude Sonnet 5 | 0 |
| Pass 3 — Taxonomy induction | (Not explicitly specified — likely Sonnet 5) | 0 |

All model strings must be confirmed before running. Prompts, run dates, and counts must be persisted with every output file.

---

## 14. Directory Structure (Expected)

```
project-root/
├── docs/
│   ├── ProblemStatement.md          # The build specification
│   ├── context.md                   # This file
│   └── method_notes.md              # Written during execution
├── data/
│   ├── raw/                         # Raw collected data per source
│   ├── pass1/                       # Relevance-gated units
│   ├── pass2/                       # Extracted units
│   ├── pass3/                       # Taxonomy-assigned units
│   └── out/                         # Final analysis outputs (CSV + summary.json)
├── taxonomy_proposed.json           # Model-induced categories (pre-review)
├── taxonomy_final.json              # Human-reviewed categories
├── taxonomy_changes.md              # Record of review changes
└── prompts/                         # All prompts used, versioned
```

---

## 15. Success Criteria

The engine succeeds if it can produce:

1. A **Memory Map** showing what people reliably remember vs. forget — grounded in data, not assumption
2. An **opportunity-ranked list** of retrieval breakdowns — triangulated across source types
3. A **transparent method trail** — every number traceable, every loss reported, every category traceable to induction
4. Findings specific enough to guide Part 2 (primary research design) and Part 3 (solution ideation)

The engine fails if it produces only a ranked list of search complaints or relies on categories that weren't derived from the data.
