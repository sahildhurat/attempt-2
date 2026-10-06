# Spec Addendum 01

**Date:** 26 September 2026
**Applies to:** `ProblemStatement.md`, `context.md`, `implementation-plan.md`, `edge-cases.md`
**Status:** These changes take precedence over the documents above wherever they conflict.

Six changes. Two are blocking — nothing gets built until they are resolved.
One resolves a direct contradiction between two existing documents.

---

## A1 — BLOCKING: verify the Help Community collection method before writing the collector

**Problem.** `implementation-plan.md` §1.1 assumes
`support.google.com/photos/search?q={keyword}` returns server-rendered HTML that
BeautifulSoup can parse. Google help communities are heavily JavaScript-rendered.
If the pages are a client-side shell, `requests` + BS4 returns nothing usable —
and the primary depth source is gone.

No edge case covers this. EC-1.13 covers XDA restructuring; nothing covers the
primary source being uncollectable by the planned method.

**Do this before writing any collector code.**

### Step 1 — robots.txt

```bash
curl -s https://support.google.com/robots.txt
```

Record the result verbatim in `docs/method_notes.md`. If the thread or search
paths are disallowed, automated collection is off the table — go straight to
Mode C below.

### Step 2 — render test

```bash
curl -s "https://support.google.com/photos/threads?hl=en" -o /tmp/gp_test.html
wc -c /tmp/gp_test.html
grep -c -i "thread" /tmp/gp_test.html
```

Then open `/tmp/gp_test.html` and look for actual thread titles and links.

### Step 3 — pick a mode and record the decision

| Condition | Mode | Action |
|---|---|---|
| Thread titles and links present in the raw HTML | **A — static** | Proceed with `implementation-plan.md` §1.1 as written |
| Page is a shell; content loads via JS | **B — rendered** | Add `playwright` to `requirements.txt`, install Chromium, rewrite the collector to render each page before parsing. Keep the 1 req/sec limit. Budget +2 hours. |
| robots.txt disallows, or rendering also fails | **C — manual** | Collect 60–100 thread URLs by hand via Google search (`site:support.google.com/photos` plus keywords), save to `config/manual_thread_urls.txt`, and have the collector fetch only those. Budget +3 hours of manual work. |

**Record the mode, the evidence for it, and the date in `docs/method_notes.md`.**
If Mode C, state plainly in the method notes that Help Community coverage is a
hand-picked sample, not a systematic crawl — that is a corpus limitation to
report, not hide.

### Consequence for the adequacy checkpoint

If Mode C is used, the ≥ 80 discussion-type unit threshold in checkpoint 1 is
likely to be tight. Compensate by widening YouTube (40 videos rather than 25)
and running XDA rather than treating it as optional.

---

## A2 — BLOCKING: per-item grounding for `remembered` and `forgotten`

**Problem.** The memory map (§6.1) is the headline output of the entire project,
and it is built entirely from `remembered` and `forgotten`. Those two fields
currently have the weakest verification in the pipeline.

The schema carries **one** `evidence_quote` for the whole extraction. A unit can
return five remembered cues with a single quote supporting one of them and pass
every automated check. EC-4.4 identifies the hallucination risk but proposes a
manual spot-check of 50 units — that is a sample, not a check.

Hard Rule #1 says no invented data. Right now the most important numbers in the
project are the least protected.

**Fix: every cue carries its own span, and every span is checked.**

### Schema change — replaces the `remembered` and `forgotten` fields in
`prompts/pass2_extraction.md` and `scripts/pass2_extract.py`

```json
"remembered": [
  {
    "cue": "short phrase describing what they remembered",
    "span": "exact verbatim substring of the source text supporting this cue"
  }
],
"forgotten": [
  {
    "cue": "short phrase describing what they could not remember",
    "span": "exact verbatim substring of the source text supporting this cue"
  }
]
```

`evidence_quote` stays as it is — it now covers the extraction overall, while
each cue is independently grounded.

### Prompt additions

Add to the extraction system prompt:

```
For every item in "remembered" and "forgotten", you must supply a "span":
an exact substring copied character-for-character from the source text that
supports that specific cue.

- The span must appear verbatim in the text. Do not paraphrase, correct
  spelling, expand abbreviations, or alter punctuation.
- If you cannot find a verbatim span supporting a cue, do not output that cue
  at all. An omitted cue is correct; an ungrounded cue is a failure.
- Spans may overlap between cues. A single sentence can ground two cues.
```

### New programmatic check — add to `scripts/pass2_checks.py` as Check 4

```python
# Check 4 — Per-cue grounding
for unit in extracted_units:
    for field in ("remembered", "forgotten"):
        kept, dropped = [], []
        for item in unit.get(field, []):
            if item.get("span") and item["span"] in unit["text"]:
                kept.append(item)
            else:
                dropped.append(item)
        unit[field] = kept
        unit.setdefault("dropped_cues", {})[field] = dropped
```

Dropped cues are **removed before analysis** — they never reach the memory map.
They are retained in the unit record for audit.

### Reporting

Add to the Pass 2 report and to `summary.json`:

```
Cue grounding:
  remembered cues returned: X    grounded: Y    dropped: Z (P%)
  forgotten  cues returned: X    grounded: Y    dropped: Z (P%)
```

If the drop rate exceeds 10% for either field, the extraction prompt needs
tightening before proceeding — the model is paraphrasing rather than copying.

**This is the equivalent of the runtime evidence guard from the previous
project.** A fabricated cue becomes structurally unable to reach the headline
output, rather than merely discouraged by prompt instructions. Say so in the
method notes, and on the deck.

---

## A3 — Resolve the contradiction between EC-6.2 and HRV-2

**Problem.** EC-6.2 correctly identifies that the memory map requires
`remembered` and `forgotten` to share one category set, otherwise the table
cannot be built. Its proposed fix is to add to the induction prompt:

> "The categories should be types of memory cues (e.g., people, location, time,
> visual content)"

That seeds categories into the induction prompt, which HRV-2 classifies as a
🔴 critical violation of Hard Rule #2. Following EC-6.2 as written invalidates
the open-tagging claim this whole attempt rests on.

**Fix: induce the two fields jointly, with no examples in the prompt.**

### Replaces `implementation-plan.md` §4.1 for these two fields only

Instead of inducing `remembered` and `forgotten` separately:

1. **Pool** every `cue` value from both fields across all above-floor units into
   one phrase list. Tag each phrase internally with its origin field, but **do
   not show the origin to the model**.
2. Run **Shuffle Run A** and **Shuffle Run B** over the pooled list, using the
   existing induction prompt unchanged — no example categories, no hint that
   cues split into two contexts.
3. Merge the two runs as already specified.
4. The result is a **single shared cue taxonomy**, saved under a `cues` key in
   `taxonomy_proposed.json` rather than separate `remembered` and `forgotten`
   keys.
5. At assignment, each cue is assigned against that shared taxonomy. Its origin
   field determines which column of the memory map it lands in.

`target`, `breakdown` and `workaround` continue to be induced separately, as
already specified.

### Result

The memory map columns align structurally. No category names were suggested to
the model. Zero-count cells — a category appearing only in `remembered` or only
in `forgotten` — are genuine findings and should be shown, not suppressed.

### Update to EC-6.2

Mark the original handling as superseded. The "add example cue types to the
prompt" instruction must not be implemented.

---

## A4 — Batch the Pass 3 assignment calls

**Problem.** `implementation-plan.md` §4.3 sends one API call per phrase, with
the full category list in every prompt. At roughly 500 units averaging eight
phrases across the five fields, that is around 4,000 Sonnet calls. Slow, and the
repeated category list makes it needlessly expensive.

**Fix.** Batch by field: one call assigns up to 40 phrases against that field's
categories.

```
Assign each numbered phrase below to exactly one category, or "other" if it
genuinely does not fit.

Categories for "{field_name}":
{categories with definitions}

Phrases:
1. {phrase}
2. {phrase}
...

Output (JSON): { "assignments": [ {"n": 1, "category": "string"}, ... ] }
```

Validate that the returned `n` values match what was sent. Any phrase missing
from the response is retried individually, and the count is logged — the
honest-denominator rule applies to assignment too.

This cuts the call count by roughly an order of magnitude with no change to
output.

---

## A5 — Smaller corrections

### A5.1 Play Store pagination

`implementation-plan.md` §1.2 specifies `count=10000` in a single `reviews()`
call. The library caps results per call and requires continuation tokens. Use
`reviews_all()`, or loop `reviews()` with the returned token until exhausted or
a cap is reached. Log the actual number retrieved rather than the number
requested.

### A5.2 Confidence proxy must not be named `confidence`

EC-4.5's fallback formula is sound, but if it is used the output field must be
named `confidence_proxy`, and `confidence` must be left as the model returned
it. Record the substitution and the formula in `docs/method_notes.md`. A
computed value presented as a model score is the kind of thing that does not
survive questioning.

### A5.3 Timeline

The plan is dated Sep 25 and assumes four working days. It is now Sep 26.
Revised targets:

```
Sep 26   Pre-flight (A1) + setup + begin collection
Sep 27   Finish collection + Pass 1 + Checkpoints 1 & 2
Sep 28   Pass 2 + Pass 3 induction + Checkpoint 3
Sep 29   Assignment + deductive layer + analysis outputs
Sep 30   Method notes, validation, findings packaged
Oct 1–7  Primary research, MVP, user testing, deck
```

The binding constraint is not the engine. It is **Part 6** — testing the MVP
with at least three users — which needs the MVP working several days before the
deadline. If the engine runs late, compress the engine, not Part 6.

### A5.4 `context.md` §15 part numbering

It refers to "Part 2 (primary research design) and Part 3 (solution ideation)."
In this brief, Part 2 is the metric decomposition, Part 3 is user research,
Part 4 is problem definition and Part 5 is the MVP. Correct it so downstream
work doesn't inherit the error.

---

## A6 — Updated pre-flight checklist

Replaces `implementation-plan.md` §0.5.

- [ ] **A1 Step 1** — fetch and record `support.google.com/robots.txt`
- [ ] **A1 Step 2** — render test on a Help Community thread listing
- [ ] **A1 Step 3** — collection mode chosen and recorded in method notes
- [ ] Confirm the Claude Haiku 4.5 model string against the API; write it to `config/models.json` with `confirmed: true` and the date
- [ ] Confirm the Claude Sonnet 5 model string the same way
- [ ] Set the Pass 3 induction model explicitly in `config/models.json` — `context.md` §13 notes the spec left it unspecified. Use the same Sonnet string as Pass 2.
- [ ] Obtain the YouTube Data API v3 key
- [ ] `.env` populated with `ANTHROPIC_API_KEY` and `YOUTUBE_API_KEY`
- [ ] `pip install -r requirements.txt`
- [ ] Smoke test: one Anthropic call at temperature 0, confirming the model string echoed in the response matches the pinned one
- [ ] `assert config["temperature"] == 0` present in every runner script (HRV-4)
- [ ] Extraction prompt reviewed for seeded categories before first run (HRV-2)

---

## Summary of what changed

| # | Change | Type | Affects |
|---|---|---|---|
| A1 | Verify Help Community collection method before building | Blocking | Phase 0, §1.1 |
| A2 | Per-cue spans + programmatic grounding check | Blocking | Pass 2 schema, prompt, checks |
| A3 | Joint induction for cues; EC-6.2 fix superseded | Correction | Pass 3 §4.1, EC-6.2 |
| A4 | Batch assignment calls | Efficiency | Pass 3 §4.3 |
| A5 | Play Store pagination, confidence naming, timeline, part numbering | Minor | Various |
| A6 | Updated pre-flight checklist | Process | §0.5 |

A1 and A2 are gates. Nothing is built until A1 has a recorded answer, and the
Pass 2 prompt is not written until A2 is in it.
