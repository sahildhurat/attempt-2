# Discovery Engine — Build Specification (final)

**Project:** Google Photos — retrieval of vaguely remembered photos
**Deliverable:** Part 1 of the NextLeap graduation brief (attempt 2)
**Submission deadline:** 7 October 2026, 15:59 IST
**Target date for engine findings:** 29 September 2026

---

## 0. Read this first

### What the engine is for

The brief's business goal: *increase the percentage of users who successfully
retrieve a photo they remember but cannot precisely describe.*

The engine does not measure whether Google Photos search is good. It answers a
narrower question:

> **When someone knows a photo exists but can't pin it down, what do they
> remember, what have they forgotten, what did they try, and where did it
> break?**

Everything in this spec serves that question. If a design choice doesn't help
answer it, cut it.

The brief explicitly rejects the framing "users find it difficult to search for
old photos." So the engine must produce something more specific than a ranked
list of search complaints. The headline output is the **memory map** in
section 6.1.

### Four hard rules

1. **No invented data.** Every number traces to a stored unit. Every quote is a
   verbatim substring of the source text, checked programmatically.
2. **No preset taxonomy.** The model describes what it sees in free text first.
   Categories are derived from those descriptions afterwards (section 5). Any
   category in the final output must be traceable to the induction step.
3. **Reproducible.** Temperature 0 on every model pass. Model strings, prompts,
   run dates and counts saved with every output file.
4. **Honest denominators.** Every stage records how many units went in and how
   many came out, including anything lost to errors. Report losses; don't hide
   them.

---

## 1. Sources

**Reddit is out.** API access was not granted in time, and scraping it would
breach its terms. This is stated plainly in the method notes and on the deck —
not quietly omitted. It is the same constraint as last attempt, and honesty
about it is worth more than a workaround.

Reddit would have been the richest source of long-form retrieval stories, so
the collection plan is rebalanced: the **Google Photos Help Community becomes
the primary depth source**, and it needs proportionally more collection effort
than any other source here.

### 1.1 Source table

| Source | Type | What to collect | Method |
|---|---|---|---|
| **Google Photos Help Community** | discussion | Question threads **and all replies**. The primary depth source. | Public pages under `support.google.com/photos/`. Walk the thread listings and the search endpoint using the keyword list in 1.2. Respect robots.txt, rate-limit to ~1 request/sec, set a descriptive user agent. |
| **Google Play Store** | review | Google Photos app reviews | `google-play-scraper`. Pull newest ~10,000 plus the most-relevant sort, deduplicated. |
| **Apple App Store** | review | Google Photos iOS reviews | Public customer-reviews RSS feed (`itunes.apple.com/.../rss/customerreviews`), paginated across available pages and storefronts (at minimum `in`, `us`, `gb`). Last attempt this returned nothing — if it fails again, report it and move on. |
| **YouTube** | discussion | Comments on videos about Google Photos search, finding old photos, photo organisation | YouTube Data API v3, `commentThreads`. Select 25–40 videos by search query; **store the video list and queries used**. |
| **Hacker News** | discussion | Comments mentioning Google Photos search or photo retrieval | Algolia HN Search API (public, free, no auth). Low volume, high quality. |
| **XDA Developers forums** | discussion | Google Photos threads | Public forum pages. Supplementary — collect if time allows after the above are done. |

### 1.2 Collection keywords

Use these to pre-filter at collection time where the source supports search.
They are a net for collection, **not** a taxonomy.

```
can't find, cannot find, couldn't find, unable to find, looking for,
search for, remember, forgot, don't remember, lost photo, old photo,
that photo, a photo of, find a picture, where is, years ago,
scroll, scrolling, search doesn't, search didn't, search is useless,
search results, no results, nothing comes up, face, people, location,
date, album, screenshot
```

For the Help Community specifically, also walk these thread categories rather
than relying on search alone: anything under search, organisation, albums, and
"finding photos".

### 1.3 Unit schema — one row per piece of feedback

```
id              stable hash of source + source_id
source          help_community | playstore | appstore | youtube | hn | xda
source_type     review | discussion
source_id       native ID
url             link to the original, where one exists
text            full original text
parent_id       for replies — the thread or comment being replied to
is_reply        true | false
author_hash     hashed; never store usernames
created_at      ISO date
rating          stars, where applicable
lang            detected language
context         thread title or video title, where applicable
```

`parent_id` and `is_reply` matter more now. In a Help Community thread the
original post states the problem and the **replies often contain the workaround**
— which is section 6.5, and one of the more interesting outputs. Do not discard
replies.

Deduplicate on normalised text. Keep English only for this run; record how many
non-English units were set aside.

### 1.4 Source adequacy checkpoint — do this before Pass 2

After collection and Pass 1, **stop and report the relevant-unit count by
source.**

- **≥ 400 relevant units, with ≥ 80 from discussion-type sources** — proceed.
- **Below that** — do not proceed straight to analysis. Widen collection first:
  more Help Community categories, more YouTube videos, additional storefronts
  for App Store, then XDA.
- **Still short after widening** — say so explicitly in the findings and in the
  deck, lower the confidence floor to 0.5 with that change stated, and lean
  harder on primary research (Part 3), which is where the depth will have to
  come from.

A smaller corpus that is honestly described beats a padded one. Last attempt
the blind spot in the data *became* a finding; the same discipline applies here.

---

## 2. Pass 1 — relevance gate (cheap model)

**Model:** Claude Haiku 4.5, temperature 0. Confirm the current model string
before running.

**Question the gate answers:** is this unit about someone trying to find a
*specific* photo or video they believe already exists in their library?

### Output

```json
{
  "relevant": "yes | partial | no",
  "reason": "one short sentence"
}
```

### Decision rules, written into the prompt

- **yes** — the person is looking for, or describes trying to find, a specific
  existing photo or video.
- **partial** — search or retrieval discussed in general, with no specific
  target ("search is bad"). Keep these; analysed separately.
- **no** — backup, storage, sync, pricing, editing, sharing, deleted photos,
  app crashes, or anything not about finding.

Keep both `yes` and `partial`. Record counts for all three.

**One addition for replies:** a reply that describes how to find something, in
response to a relevant parent, is `yes` even if it does not restate the target.
Those replies are where workarounds live.

### Quality check on the gate

Pull a random sample of 60 gate decisions (20 per label). A human labels them
blind to the model's answer. Report agreement. If agreement is below 85%, fix
the prompt and rerun before moving on.

---

## 3. Pass 2 — open extraction (stronger model)

**Model:** Claude Sonnet 5, temperature 0. Confirm the current model string.

This pass describes each relevant unit in **free text**. It does not sort
anything into categories. That comes in section 5.

For a reply, pass the parent post's text as context so the model can resolve
what "it" refers to — but extract only from the reply itself.

### Output schema

```json
{
  "target": "what the photo or video was, in the user's terms",

  "remembered": [
    "each separate thing the person remembered about it, as a short phrase"
  ],

  "forgotten": [
    "each thing the person says they could not remember, or clearly did not
     know, as a short phrase"
  ],

  "attempts": [
    {
      "action": "what they did, e.g. typed a query, scrolled, filtered by date",
      "query_text": "the exact words they searched, if quoted, else null"
    }
  ],

  "breakdown": "in one or two sentences, where and why the attempt failed,
                in the user's own framing",

  "outcome": "found | not_found | gave_up | unclear",

  "workaround": "anything they did outside normal search to find it, else null",

  "stakes": "why it mattered to them, if stated, else null",

  "context_signals": {
    "library_size_hint": "any stated size, e.g. '40,000 photos', else null",
    "time_since_photo": "any stated age, e.g. '3 years ago', else null",
    "device": "any stated device, else null",
    "use_case": "any stated purpose, e.g. travel, medical, work, kids"
  },

  "evidence_quote": "an exact verbatim substring of the text supporting the
                     remembered and forgotten fields",

  "confidence": 0.0
}
```

### Prompt rules

- Extract only what the text states. If something isn't there, return null or an
  empty list. Never infer a remembered cue the user didn't state.
- `remembered` and `forgotten` are the most important fields. Split them into
  separate items; don't merge "the beach and my sister" into one.
- `query_text` must be the user's words exactly, or null.
- `evidence_quote` must be copied character for character.

### Programmatic checks after the pass

1. **Quote check** — `evidence_quote` must be a substring of `text`. Units that
   fail are flagged and excluded from quote displays; the count is reported.
2. **Loss check** — units sent versus units returned. Report any dropped by the
   batch API, as happened last attempt (910 in, 909 out).
3. **Confidence floor** — keep units at confidence ≥ 0.6 for the main analysis,
   unless 1.4 forced a change to 0.5. Report how many fall below.

---

## 4. What we are trying to see — the analysis questions

These guide section 6. They are questions, not categories.

1. What kinds of photos do people struggle to retrieve?
2. What do people actually remember about a photo they can't find?
3. What have they forgotten?
4. How do they phrase searches when memory is incomplete?
5. Where does the attempt break?
6. What do they do instead?
7. Which of these patterns are frequent, severe, and appear in more than one
   *kind* of source?

---

## 5. Pass 3 — taxonomy induction

Last attempt the categories were fixed in advance, which weakened the claim that
the engine discovered anything. This time they are derived from the data, and
the derivation is saved so it can be checked.

### 5.1 Induce

Run separately for each free-text field: `target`, `remembered`, `forgotten`,
`breakdown`, `workaround`.

1. Collect all the phrases for that field.
2. Give the model a shuffled sample of 300–400 phrases (or all of them, if
   fewer) and ask it to propose 8–15 categories. Each needs a name, a one-line
   definition, and 3 real example phrases from the sample.
3. Repeat with a second, different shuffled sample.
4. Merge the two proposals. Categories appearing in both runs are stable. Those
   appearing in only one are flagged for review.

### 5.2 Review — human in the loop

Save the proposed categories to `taxonomy_proposed.json`. **Stop here.** A human
reviews, merges, renames or splits categories, and saves the result as
`taxonomy_final.json`. Record what changed and why in `taxonomy_changes.md`.

### 5.3 Assign

Pass every unit's phrases back through the model with `taxonomy_final.json` and
assign each phrase to one category, or `other`.

If `other` exceeds 15% for any field, the taxonomy is missing something. Return
to 5.1 with the `other` phrases.

### 5.4 One deductive layer, labelled as such

The brief suggests four ways retrieval can fail:

- the user can't **express** what they remember
- the product doesn't **understand** the clues it's given
- relevant results are hard to **evaluate**
- the user can't **refine** an unsuccessful search

Map each unit's `breakdown` onto these four as a separate, clearly labelled
layer. It is a deductive frame applied on top of the inductive categories, and
the dashboard must say so.

Where a breakdown fits none of the four, record it as `other` and count it.
Those are potentially the most interesting cases, because they are failures the
brief's own frame didn't anticipate.

---

## 6. Analysis outputs

All files saved to `data/out/` as CSV, plus `summary.json` with the counts.

### 6.1 The memory map — the headline output

For each memory cue category, how often it is **remembered** and how often it is
**forgotten** across units.

| Cue category | Remembered in | Forgotten in | Net |
|---|---|---|---|

This shows what memory reliably holds onto and what it drops. It is the most
important table in the project, because it tells us which clues a retrieval
experience can actually rely on — and it is the direct answer to the brief's
"what information do people actually remember."

### 6.2 Breakdown distribution

Units per inductive breakdown category, and units per stage of the brief's
four-stage frame, with the `other` count shown.

### 6.3 Query language

Every `query_text` collected, plus:

- length in words
- whether it names a concrete object, a place, a person, a time, or a feeling
- whether it was a first attempt or a reformulation

The gap between what people remember (6.1) and what they typed is where
retrieval breaks.

### 6.4 Target types

Which kinds of photos people hunt for: screenshots, documents, travel, people,
pets, receipts, medical — whatever the induction produces.

### 6.5 Workarounds

What people do instead: scroll by year, find an anchor photo and browse nearby,
check WhatsApp, ask someone who was there, give up.

**Split this by whether the workaround came from the person with the problem or
from someone replying to them.** Help Community replies are now a main source,
and a workaround a stranger recommends is different evidence from one the
searcher invented themselves.

### 6.6 Opportunity ranking

For each breakdown category:

```
opportunity = frequency × mean_severity × specificity × triangulation
```

- **frequency** — unit count
- **mean_severity** — from outcome and stakes; `gave_up` or `not_found` with
  stated stakes scores highest
- **specificity** — share of units with a concrete target rather than a general
  complaint
- **triangulation** — see below

**Triangulation is now weighted by source type, not just source count.** Two
app-store reviews are not independent corroboration of each other; a review and
a forum thread are.

| Condition | Weight |
|---|---|
| Appears in both a review-type and a discussion-type source | 1.0 |
| Appears in two or more sources of the same type | 0.85 |
| Appears in one source only | 0.7 |

Save the formula, the weights and the source-type mapping alongside the table.
All three must be visible on the dashboard.

### 6.7 Segment signals

Break the main findings down by library size, time since photo, and use case,
where coverage allows. **Report coverage for every split.** If a split has too
few units to support a claim, say so rather than showing the numbers.

---

## 7. Method notes — write these as you go

A `method_notes.md` that the dashboard renders verbatim. It must state:

- every source attempted, and whether it succeeded
- **Reddit: API access not granted within the project timeline; scraping would
  breach its terms, so it was excluded rather than worked around**
- App Store outcome, whichever way it goes
- models and temperature used, with run dates
- the confidence floor, and whether 1.4 forced it lower
- units in and out at every stage, including the batch-API loss
- the gate agreement rate from section 2
- what changed between `taxonomy_proposed.json` and `taxonomy_final.json`

Last attempt, being open about dropped sources read as rigour rather than
weakness. Keep that.

---

## 8. What to report back after each stage

- counts in and out
- anything that failed, and why
- 5 randomly sampled units so the output can be sanity-checked

**Three hard stops where the agent waits for review:**

1. After collection and Pass 1 — the source adequacy checkpoint (1.4)
2. After the gate quality check (section 2)
3. After Pass 3.1 — send `taxonomy_proposed.json` before anything is assigned

---

## 9. Explicitly out of scope for now

- The dashboard. It comes after the findings are reviewed.
- Any solution or MVP work.
- Sentiment analysis. The brief says the workflow must go beyond it.
