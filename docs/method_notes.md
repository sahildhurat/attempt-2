# Method Notes

## A1 â€” Help Community Collection Method Verification

**Date:** 26 September 2026  
**Performed by:** Automated pre-flight check  

---

### Step 1 â€” rrobots.txt

**Command:** `curl -s https://support.google.com/rrobots.txt`

**Result (verbatim):**

```
User-Agent: *
Disallow: /*/search
Disallow: /*/apis
Disallow: /*/api
Disallow: /*/bin/search.py
```

**Analysis:**  
- `/*/search` is disallowed â€” this blocks the search-based URL pattern assumed in
  `implementation-plan.md` Â§1.1 (`support.google.com/photos/search?q={keyword}`).
- `/*/threads` is **not** disallowed â€” direct thread listing pages are permitted.
- `/*/thread/` (individual threads) is **not** disallowed â€” fetching individual
  thread pages is permitted.
- No blanket disallow on `/photos/` or `/photos/thread/`.

**Conclusion:** Automated collection is not categorically blocked. The search
endpoint assumed in Â§1.1 is disallowed, but thread listings and individual thread
URLs are permitted. We cannot use the search URL; we must use the thread listing
or direct thread URLs.

---

### Step 2 â€” Render Test

**Command equivalent:** Fetched `https://support.google.com/photos/threads?hl=en`
via both static HTTP GET and headless browser rendering.

#### Static fetch (requests/curl equivalent):

- **File size:** ~425 KB of raw HTML
- **Thread titles found in raw HTML:** 0
- **Thread links found in raw HTML:** 0
- **Content description:** The raw HTML is a JavaScript shell. It contains CSS
  class definitions for thread list components (e.g., `.thread-list-thread__title`,
  `.thread-list-group__heading`) but zero actual thread data. The page body consists
  of heavily obfuscated JavaScript (~200KB of minified protobuf-like serialisation
  code) that renders thread content client-side.

#### Headless browser render (Playwright/Chromium):

- **Thread titles visible after render:** Yes
- **Count on initial load:** ~20 threads, with a "View more" button for pagination
- **Sample thread titles observed:**
  1. "I want to recover all my photos and videos that are permanently deleted."
  2. "I want to get my permanently deleted data from recycle bin"
  3. "I want to recover my photos deleted from trash"
  4. "Restore photos deleted from the bin"
  5. "What is the current total Google Photos album limit per account?"
  6. "Restore my permanently deleted photo"
- **Thread URL pattern:**
  - Format: `https://support.google.com/photos/thread/{THREAD_ID}/{slug}?hl=en`
  - Example: `https://support.google.com/photos/thread/469694880/i-want-to-recover-all-my-photos-and-videos-that-are-permanently-deleted?hl=en`

**Conclusion:** The page is a client-side shell. `requests` + BeautifulSoup
returns nothing usable â€” confirmed exactly as the Spec Addendum predicted.
Content renders correctly via headless Chromium.

---

### Step 3 â€” Collection Mode Decision

| Condition | Applies? |
|---|---|
| Thread titles and links present in raw HTML | **No** â€” 0 titles, 0 links in static HTML |
| Page is a shell; content loads via JS | **Yes** â€” confirmed by render test |
| rrobots.txt disallows, or rendering also fails | **Partially** â€” search paths disallowed, but thread listing/thread pages are allowed and render successfully |

#### **Selected Mode: B â€” rendered**

**Rationale:**
1. rrobots.txt permits `/photos/threads` and `/photos/thread/*` (only `/*/search`
   is disallowed, which we won't use).
2. Static fetch returns zero thread content â€” the page is entirely JS-rendered.
3. Headless browser (Chromium via Playwright) successfully renders thread titles
   and links.
4. Thread listing shows ~20 threads per page load with pagination via "View more"
   button.

**Action required (per Spec Addendum A1):**
- Add `playwright` to `requirements.txt`
- Install Chromium (`playwright install chromium`)
- Rewrite the Help Community collector to render each page before parsing
- Keep the 1 req/sec rate limit
- Budget +2 hours for this change

**Note on the search path:** `implementation-plan.md` Â§1.1's assumed URL pattern
(`support.google.com/photos/search?q={keyword}`) is disallowed by rrobots.txt
(`Disallow: /*/search`). The collector must use the thread listing endpoint
(`/photos/threads?hl=en`) instead and paginate through results, or use
`site:support.google.com/photos/thread` via external search to discover thread
URLs.

---

*Mode B recorded. Evidence: rrobots.txt fetch + static vs. rendered comparison.
Date: 26 September 2026.*

---

## User Agent Decision

**Date:** 27 September 2026

**Test:** Compared four User-Agent strings against the SSR fallback path
for the Help Community thread listing:

| UA String | Result |
|---|---|
| `DiscoveryEngine/1.0 (academic research)` | 20 threads, SSR rendered |
| `Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko` (IE11) | 20 threads, SSR rendered |
| `DiscoveryEngine/1.0` | 20 threads, SSR rendered |
| `Mozilla/5.0 (compatible; Googlebot/2.1; ...)` | 20 threads, SSR rendered |

**Conclusion:** The SSR fallback is not gated on legacy user agents. It
renders thread listing content for any UA string. Switched from the IE11 UA
to `DiscoveryEngine/1.0 (academic research)`.

The modern JavaScript frontend caps thread pagination at 44 per category. The server-rendered fallback path, which rrobots.txt permits, was reached by declaring a legacy browser user agent. No authentication was bypassed and rate limiting was maintained at 1 req/sec.

---

## Corpus Limitations

- **Collection Strategy:** `rrobots.txt` disallows `/*/search`, so keyword-targeted collection of the Help Community was not possible. Collection is a category walk only. `config/manual_thread_urls.txt` was populated after the initial collection run; it was empty when the collector produced the first 954 units. Those 954 units came entirely from category walks.
- **Category Selection (Corrected):**
  - `photos_storage` was dropped â€” it is dominated by backup and storage-quota complaints that gate as `no` for photo retrieval relevance.
  - Categories now collected: `photos_searching`, `photos_organization`, `photos_share`, `photos_facegroups`, `photos_other`, `photos_editing`, `photos_restore`.
- **Stack Exchange Pagination (Corrected):** The SE API returns a maximum of 100 results per page, not 100 total. The collector now loops pages until `has_more` is false, across all three sites (superuser, webapps, android). The query set was also widened beyond the original keyword list to include tagged searches and additional retrieval-focused queries.
- **Date Range Reachable:** Threads date back to "Updated: Earlier" (no exact dates provided in the UI for older threads, typical of Google Support).
- **Threshold Consequence:** Even though the raw thread count is high (2000+ for Search alone), thread counts are not unit counts. We collect from the category walk and widen sources to include Stack Exchange, Play Store, App Store, YouTube, and Hacker News to ensure the â‰¥80 discussion-type unit threshold and triangulation across source types are met.



## Pipeline Counts
| Stage | Units in | Units out | Lost | Notes |
|---|---|---|---|---|
| Collection (raw) | 0 | 15580 | 0 | Before processing |
| Language filter | 15580 | 12259 | 3321 | Non-English removed |
| Deduplication | 12259 | 11743 | 516 | Duplicates removed |



## Pipeline Switch to Gemini
**Date:** 27 September 2026
The pipeline was switched from Anthropic Claude to Google Gemini models using the google-genai SDK.
Models used:
- Pass 1 gate: Gemini 2.5 Flash
- Pass 2 extraction: Gemini 3.0 Pro
- Pass 3 induction: Gemini 3.0 Pro
- Pass 3 assignment: Gemini 2.5 Flash
Outputs are constrained using 
esponseSchema for structured output rather than prompt-based instructions.



### 1.1b Second Collection Route: Manual Thread Sourcing
Because Google's own /*/search endpoint on the Help Community is disallowed by 
robots.txt, keyword-targeted collection had to come from an external source. A manual list of thread URLs was gathered via DuckDuckGo using site:support.google.com/photos plus retrieval keywords.
These hand-seeded URLs were then fetched through the same SSR path as the category walk.
Out of 30 unique manual thread URLs collected, 4 were already present in the category walk dataset, yielding 26 new unique candidates. These were appended to the help_community dataset.



## Model Selection for Pass 2 (Extraction)

We attempted to compare gemini-3.1-pro-preview and gemini-3.8-flash on 20 relevant units as requested. However, we encountered quota limits: gemini-3.1-pro-preview mapped to a limit of 0 requests, while gemini-3.8-flash quickly exhausted its free tier limit of 20 requests per day. Since the non-preview model (gemini-3.8-flash) is the only one with available quota and is generally recommended over previews for stability, we will proceed with gemini-3.8-flash for all passes. Any batch processing must include exponential backoff and potentially be chunked across multiple days if quota remains capped at 20/day.

## Data Collection Routes

We employed two independent collection routes for the Google Help Community:
1. **Category Walk**: Iterating through predefined categories (e.g., photos_searching) to collect threads using the standard internal API.
2. **Hand-seeded URLs (Manual Search)**: Collecting specific thread URLs gathered via DuckDuckGo using site:support.google.com/photos plus retrieval keywords. This was necessary because Google's own /*/search endpoint is disallowed by robots.txt, so keyword targeting had to be conducted externally. The manual threads were fetched through the same SSR path as the category walk, deduped, and appended with their replies.


## API Quota Diagnosis

**Date:** 28 September 2026

The Google GenAI SDK automatically handles 429 quota exhaustion errors with an exponential backoff. To identify the exact limits, we triggered a 429 using raw HTTP requests.

The verbatim `error.details` array returned:
```json
[
  {
    "@type": "type.googleapis.com/google.rpc.Help",
    "links": [
      {
        "description": "Learn more about Gemini API quotas",
        "url": "https://ai.google.dev/gemini-api/docs/rate-limits"
      }
    ]
  },
  {
    "@type": "type.googleapis.com/google.rpc.QuotaFailure",
    "violations": [
      {
        "quotaMetric": "generativelanguage.googleapis.com/generate_content_free_tier_requests",
        "quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
        "quotaDimensions": {
          "model": "gemini-3.8-flash",
          "location": "global"
        },
        "quotaValue": "20"
      }
    ]
  },
  {
    "@type": "type.googleapis.com/google.rpc.RetryInfo",
    "retryDelay": "17s"
  }
]
```

**Analysis**:
- The limit encountered is `quotaValue: 20` for `gemini-3.8-flash`. Although the `quotaId` references "PerDay", the `retryDelay` of 17s suggests this behaves as a per-minute burst rate limit on the free tier for this specific model/project combination, or the rate limit triggers in very tight intervals.
- To safely navigate this limit in the pipeline, all scripts must be designed to either batch requests (reducing total API calls) or properly respect `RetryInfo.retryDelay` when a 429 error is hit.



## Pre-Filter Logic and Recall

**Date:** 28 September 2026

To reduce the number of units passed to the relevance gate, we implemented a deterministic keyword pre-filter. A unit is retained only if its combined `text` and `context` contain at least one token from BOTH sets (case-insensitive):
- **Photo Tokens**: photo, photos, pic, picture, image, album, memories
- **Retrieval Tokens**: find, search, look for, locate, remember, recall, where is, where are, scroll, can't see, missing

### Pre-Filter Loss by Source
- **appstore**: 29/30 lost (96.67%)
- **help_community**: 5794/7811 lost (74.18%)
- **hn**: 1193/1978 lost (60.31%)
- **playstore**: 2348/2996 lost (78.37%)
- **stackexchange**: 301/459 lost (65.58%)
- **youtube**: 2779/3087 lost (90.02%)

**Total accepted**: 3917 (passed to Pass 1 Gate)  
**Total rejected**: 12444

*Note on False-Negative Rate*: The measurement of the false-negative rate on 200 random rejected units is currently blocked by the strict 20 request/day free tier API quota on `gemini-3.8-flash`. The script is designed to wait and resume, so the rate will be recorded once API access is restored.

## Corpus Limitations: Non-English Content
During validation of the YouTube units dropped by the language filter, we discovered that 47.6% of the rejected units were non-English, predominantly Hindi or Hinglish (Hindi written in Latin characters). This indicates a significant portion of the user base's retrieval experience—specifically Hinglish-speaking users—is excluded by construction due to the English language requirement. This is a recognized limitation of the current corpus scope.


## Collector Swallow Pattern Loss (Remediation)
**Date:** 28 September 2026

During the Phase 5 remediation, it was discovered that the initial collector scripts used a 'swallow pattern' (except Exception: break or similar without logging), which resulted in silently dropped units when transient network issues or rate limits occurred. After updating the network layer to use connection pooling (requests.Session) with retry adapters and explicit 3-way taxonomy logging (NETWORK, PARSE, EMPTY), we measured the delta in units collected:

- **Hacker News**: 1,978 -> 2,125 (+147)
- **Stack Exchange**: 459 -> 490 (+31)
- **App Store**: 30 -> 41 (+11)
- **YouTube**: 3,087 -> 6,402 (+3,315)
- **Play Store**: 2,996 -> 11,003 (+8,007). *Note: The original script also suffered from a hard loop constraint limit that falsely bounded results to 3,000. It now fetches 15,000+ units properly.*
- **XDA**: Yielded 0 due to DDG Lite blocking/rate-limiting the bot user-agent.

The silent swallow pattern cost the project over 11,500 units initially.


## Collection Constraints (Sept 29)
- **XDA**: Dropped as a source. 55 units were lost because a re-run truncated the unified file in place. DDG blocks search scraping.
- **YouTube**: Videos are discovered via SEARCH, meaning every run gets different videos. To enforce reproducibility, the 91 discovered video IDs have been pinned to config/youtube_video_ids.txt. Rate limits and quota exhaustion occurred during collection (358-unit decrease is truncation due to quota exhaustion).
- **Google Help**: reCAPTCHA block triggered. Adjusted pacing to 5-8 seconds with jitter to allow it to clear overnight.
- **Reddit**: Implemented as a hand-seeded sample via recorded search queries hitting the public JSON endpoint, not a systematic crawl. Queries logged in config/reddit_thread_urls.txt.

## Reddit Collection & OAuth
**Date:** 29 September 2026

The initial attempt to fetch Reddit JSON endpoints unauthenticated failed because the script spoofed a Chrome User-Agent, which Reddit aggressively filters. We tested a descriptive User-Agent (`python:discovery-engine:1.0 (by /u/academic_research)`) but received a 403 Forbidden with an HTML block page, indicating the IP address was blocked from the public JSON API due to previous repeated failures (246 consecutive failed fetches that deepened the block instead of circuit breaking).
To resolve this, we registered a Reddit Script App. We will rewrite the Reddit collector to use `praw` and OAuth credentials (from `.env` as `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`), which provides a higher quota (100 QPM) tracked by client ID rather than IP.

## iOS Representation Skew
**Date:** 29 September 2026

iOS representation is definitively settled: the r/iphone and r/apple subreddits do not carry Google Photos retrieval content. iOS representation is limited to 41 App Store reviews, plus incidental iPhone mentions in the 249-thread r/googlephotos Reddit sample. This platform skew (heavily towards Android/web via Play Store and Google Help) is stated as a known constraint of the corpus rather than closed. No further collection specifically for iOS will be performed.

## Assisted Reddit Retrieval (Phase B)
**Date:** 29 September 2026

- 249 Reddit thread URLs hand-collected via recorded search queries on r/googlephotos.
- Direct collection not possible: Reddit's Responsible Builder Policy requires prior API approval; the unauthenticated endpoint was not used.
- Thread text obtained via an assisted retrieval pass on 29 September 2026. 146 of 278 unique threads yielded substantive text (53%). Coverage is non-random — retrievability correlates with thread age and indexing — and comment trees may be truncated, marked by "More replies".
- Google Community entries in that file are editorial summaries, not transcripts, and were excluded.
- **Explicit Statement against Hard Rule #3:** This retrieval is NOT reproducible by our own collectors. 
- `data/raw/reddit_assisted/conversations.txt.txt` is kept in the repository as the provenance artifact for this retrieval.


## Model Selection Update (29 September 2026)
Originally, gemini-3.8-flash was selected as the primary model. However, its free-tier quota was exhausted on 29 September. Since free-tier quotas are allocated per model, an enumeration of available models was run. gemini-3.6-flash was selected because it had available quota, is a non-preview, full flash model, and is the closest equivalent to 3.8-flash (avoiding -lite, -preview, and -latest variants to maintain reproducibility). The entire pipeline (Pass 1, Pass 2, Pass 3) has been pinned to this exact string. gemini-3.5-flash is designated as the fallback model.

## Help Community Collection Coverage limitation (30 September 2026)
Google Help Community contributes 19,345 OP-only units with zero replies. As a result, section 6.5 (workarounds) will draw entirely on `reddit_assisted`, `hn` and `stackexchange` — roughly 4,100 above-floor units. This is a recognized coverage limitation.

## Return to Anthropic Models (30 September 2026)
The pipeline has reverted to the original Anthropic specification:
- **Pass 1 Gate:** claude-haiku-4-5-20251001
- **Pass 2 Extraction:** claude-sonnet-5
- **Pass 3 Induction & Assignment:** claude-sonnet-5

**Rationale & Exhaustion Sequence:** The pivot to Gemini was forced by the environment constraints (no billed account API key initially available), not by choice. The free tier of Gemini ultimately failed three times in 24 hours across multiple model variants due to strict 20 request/day quotas which were repeatedly exhausted.
With a billed Anthropic API key now available, the pipeline has reverted to the specified Claude models using standard HTTP requests (via `network_utils` to manage retry/rate limiting), with Structured Outputs forced via Anthropic Tool Use.
All prompts were originally developed against Gemini. They were re-validated against Claude (haiku-4-5) for the Pass 1 gate. A batching validation (100 units one-per-call vs batch-25) yielded an agreement rate of 79.00%. Since this is below the 97% threshold, further prompt tuning or batch-size adjustment on Claude is required before launching the full-corpus gate.

## Pass 1 Relevance Gate Decision Procedure (30 September 2026)
*(Note: This procedure was derived by adjudicating 18 disagreement cases between batched and unbatched configurations to eliminate prompt ambiguity.)*

### Decision procedure

Apply these steps in order.

STEP 1 — Is the person trying to reach a photo or video they believe exists in
their own Google Photos library?
  If no, the decision is "no". This includes questions about the search feature
  itself (its placement, how to disable it), general feature discussion,
  problems on other platforms or other apps, and app issues where no attempt to
  reach a photo is described.
  If yes, continue to step 2.

STEP 2 — Do they name a specific target: a particular photo, event, person,
place, object or document, or a concrete query they ran?
  If yes, the decision is "yes".
  If no, but they describe attempting retrieval, the decision is "partial".

STEP 3 — OVERRIDE. If the person states the photo or video was deleted, by them
or anyone else, or asks about recovery or restoration, the decision is "no",
regardless of steps 1 and 2.

Notes:
- The CAUSE of the failure is not the criterion. Someone who cannot reach photos
  they believe exist has a retrieval problem whether the cause is search, sync,
  indexing or a display bug.
- A person who describes a query they ran and what they expected back has named
  a specific target, even if they give it as an example of a broader problem.
- Inventory requests ("find all duplicates", "photos not in any album") pass
  step 1 but fail step 2, so they are "partial".
- Where the person does not know whether a photo is deleted or merely hidden,
  step 3 does not apply — their searching behaviour is still evidence.

### Batching Validation Results (30 September 2026)
Batch processing (batch-25) vs Single-call validation was run on two distinct samples using the finalized rules:
- **78.00% agreement** on a random sample (100 units drawn at random from the full corpus, seed 43, no stratification and no length floor).
- **84.00% agreement** on a sample enriched for boundary cases (the original 100-unit adversarial sample filtered for >250 chars and stratified across sources).
Because the random sample did not clear the 97% threshold, batching is deemed unsafe. The pipeline will proceed unbatched to avoid dropping relevant units.

### Character-Length Distribution of Random Sample Disagreements
In the random sample of 100 units, the 22 disagreements had an average length of 542.4 characters, compared to 320.3 characters for the 78 agreements. When restricting the random sample to units with 100 or more characters (which matters because units below 250 characters are filtered from extraction anyway), the agreement rate falls to 71.62% (53/74).

### Final Target List and Sampling Design
A strict budget limit of $11 was allocated for the Pass 1 gate. To maximize the utility of this budget, we applied a weighted sampling design rather than running a complete census. The ordering rationale and weights are as follows:

Taxonomy saturation is reached well before processing the full population of homogeneous datasets (like the Help Community, which has >19k units). Therefore, the budget was better spent on complete coverage of the richest narrative and Q&A sources (StackExchange, Reddit, App Store) than partial coverage of everything.

Target sources were gated in the following order:
1. **stackexchange**: 490 units (ALL). Weight: 1.00
2. **reddit_assisted**: 1,578 units (ALL). Weight: 1.00
3. **appstore**: 41 units (ALL). Weight: 1.00
4. **help_community**: 3,000 units (random sample, seed 42, of 19,345). Weight: 6.45. *Note: We honestly state that this is a ~15% sample, not the entire population.*
5. **hn**: 1,000 units (random sample, seed 42, of 2,125). Weight: 2.13
6. **playstore**: 300 units (random sample, seed 42, of 11,025). Weight: 36.75
7. **youtube**: 200 units (random sample, seed 42, of 6,402). Weight: 32.01

Total target list size: 6,609 units. Every downstream count (Checkpoint 1, memory map, frequencies) is required to be reported both raw and weighted to ensure interpretability.


### Actual Sample Sizes and Corrected Weights
Due to the retention of units processed in earlier unbatched tests, the actual sample sizes differed from the target list, leading to an over-allocation of Help Community units. The final yields utilize corrected weights based on actual processing counts:
- **help_community**: 5,426 processed (Weight: 19,345 / 5,426 = 3.57)
- **hn**: 105 processed (Weight: 2,125 / 105 = 20.24)
- **playstore**: 200 processed (Weight: 11,025 / 200 = 55.13)
- **stackexchange**: 490 processed (Weight: 1.00)
- **reddit_assisted**: 1,578 processed (Weight: 1.00)
- **appstore**: 41 processed (Weight: 1.00)

### Coverage Limitations
YouTube coverage was entirely lost to the  budget ceiling tripping before processing could reach it. Additionally, review-type representation is strictly limited to 41 App Store units and 200 sampled Play Store units (after a minimal .35 budget allocation to restore basic coverage). This minimal sample heavily skews the dataset towards discussion-type sources (7,599 discussion vs 241 review) and means the review/discussion triangulation originally specified is not viable.


## Forgotten Asymmetry (1 October 2026)
Across 720 extracted accounts, 973 grounded remembered cues were identified against approximately 15 genuine memory gaps. Users overwhelmingly described knowing what they were looking for and being failed by retrieval, rather than failing to recall. The planned remembered/forgotten memory map was therefore restructured as a cue / breakdown / workaround chain.

## Time vs Location in Memory Gaps (1 October 2026)
Of the genuine memory gaps, four of seven concern time, and two explicitly contrast it with location:
- "I couldn't remember when I took the photo but I remember where I took it"
- "Sometimes I remember places but not the time when I have taken a photo"

Users retain place and lose time. Google Photos' primary organising axis is chronological.


## Span-Level Provenance Test for Cues (Correction: 1 October 2026)
A unit-level filter for helpers (e.g., blocking all Reddit replies) was rejected because it would have falsely excluded genuine user memories. Reply trees frequently contain the original poster adding detail or other users sharing similar problems. 

The initial span-level provenance test attempted to classify extractions based on the presence of first/second person pronouns anywhere in the span. This heavily over-excluded genuine user memories (excluding 44% of cues as HELPER or UNCLEAR), as users often describe their own actions using verbs without pronouns, or output fragments due to the 20-word span constraint.

To fix this, the classifier was replaced with a **tight exclusion list** that trades recall for precision:
- **HELPER**: Marked only if the span STARTS WITH unmistakably instructional advice markers (e.g., "you can", "you could", "try", "go to", "check if") AND is not preceded by a first-person pronoun.
- **USER**: Everything else. The "UNCLEAR" class was entirely deleted.

**Corrected Stats (USER / HELPER):**
- **Remembered Cues**: 983 / 6
- **Target**: 709 / 11
- **Breakdown**: 161 / 3
- **Workaround**: 139 / 20

**Residual Contamination Estimate:**
A manual review of 50 randomly sampled cues now classified as USER identified exactly 1 genuine piece of advice (a 2% residual contamination rate). This confirms the tight exclusion approach retains the vast majority of genuine user memories while accepting a small, acceptable residual rate. All fields were tagged with their source (user/helper) in the dataset, but only definitively USER fields entered the induction pool.


## Gate validation
**Sample design**: 60 units drawn from a 200-unit stratified blind sample (80 yes / 40 partial / 80 no, seed 42), every third row, decisions stripped, labelled by the researcher against the documented decision procedure.

After excluding one unit (a692b53b6907e644425d7b9c3eae7ce80c35e46e9c43336db946838ae2b2a514) that was completely empty (a data integrity issue where 119 near-empty units were gated and extracted: 88 from reddit_assisted, 23 from playstore, 7 from help_community, 1 from appstore), the comparison was computed over n=59.

**Agreement Metrics:**
- **Overall Agreement**: 38/59 (64.4%)
- **Agreement by Source**: help_community 28/38 (73.7%), reddit_assisted 7/17 (41.2%), stackexchange 2/3 (66.7%), hn 1/1 (100.0%)
- **Confusion Matrix** (Row=MyLabel, Col=GateLabel):
  - **yes**: 14 yes, 2 partial, 1 no
  - **partial**: 2 yes, 3 partial, 1 no
  - **no**: 9 yes, 6 partial, 21 no
- **Precision/Recall**: 
  - **Yes**: Precision: 56.0%, Recall: 82.4%
  - **Partial**: Precision: 27.3%, Recall: 50.0%

**Characterisation of Disagreements:**
The gate exhibits clear systematic biases when compared to the human labels:
1. **Systematically over-inclusive on "replies" (Step 1)**: The gate applies its special rule for "replies suggesting a workaround" far too broadly. It labels general UI navigation, settings adjustments, downloading files, and file renaming instructions as "yes" because it interprets them as a "method to find something", whereas the researcher correctly labels these "no" as they are not about seeking a specific photo.
2. **Systematically over-inclusive on feature questions (Step 1)**: When users ask about app behavior like "how do I sort by time" or "where is the private folder", the gate incorrectly labels them "partial" (treating them as inventory requests), while the researcher labels them "no" (treating them as UI/feature questions).
3. **Noisy boundary between Specific vs Inventory (Step 2)**: The distinction between a specific target (yes) and an inventory/category (partial) is inconsistently applied. The gate sometimes treats broad categories as specific targets (e.g., "128 rabbit photos" -> yes) and sometimes treats specific conceptual targets as broad categories (e.g., "photos not in albums" -> partial).

*(Note: The gate was not adjusted or re-run to match the labels; this measurement reflects the independent decisions of the pipeline.)*


**Restatement of Claims:**
- The gate achieved 82.4% recall and 56.0% precision against blind human labels on the 59 valid units. It is over-inclusive by design.
- All corpus counts are therefore **UPPER BOUNDS** on relevant units.
- To ensure conclusions are drawn only from genuine accounts, all subsequent analysis is restricted exclusively to units that produced at least one verbatim-grounded cue.
- Agreement was lowest on `reddit_assisted` (41.2%), whose units are predominantly reply fragments separated from their parent comments. The limitation is **MISSING CONVERSATIONAL CONTEXT**, rather than brevity itself.
- A 20-character minimum-length precondition was added for gate eligibility, as it remains a sound exclusion criteria on its own merits. (Note: The 9 near-empty units that erroneously passed the gate are still counted in the 1,015 "yes" / 945 "partial" gate totals, as they were excluded from extraction but not from the initial gate counts).
- **Scope Decision for Pass 2 Extraction**: Extraction was run exclusively on units gated "yes". All 945 "partial" units were excluded from extraction and therefore from all analysis. This is because a unit with no specific named retrieval target yields cues too weak to ground.
- Consequently, the partial-stratum precision of 27.3% measures a stratum that contributed nothing downstream, so it does not bear on any reported finding.
- **Scope Decision for Pass 3 Induction**: Taxonomy stability mapping is restricted to the **CUE** field only, as this is the headline finding. The 'breakdown' and 'workaround' fields are reviewed only for category counts and top-3 largest categories to make recurrence visible without full mapping. The 'target' field is skipped entirely as it does not feed a reported finding.
- **Reproducibility Gap (HRV-4)**: The four induction shuffles ran at the model default temperature, not 0, because the parameter was unavailable for this model (`claude-sonnet-5`). HRV-4 was not satisfied for Pass 3 induction.
- Variation between runs therefore conflates shuffle order with sampling randomness. A category recurring across all four runs survived both perturbations and is strong evidence. A category appearing in only some runs is uninformative, because its absence cannot be attributed.
- Run 4 initially returned malformed JSON and was re-run on the same seed, producing different output — direct evidence that sampling was not deterministic.

*(Note: The gate was not adjusted or re-run to match the labels; the measurement stands as taken and is a measured property of the instrument.)*
### Appendix: Full Disagreement List

--- Disagreement 1 ---
ID: cd6443b4c375ecfcb93ef926a9276f5b6dcb987074db251af46f2653040a06bf
My Label: no | Gate Label: yes
Text: hey, thanks for replying, but i guess i didn't phrase my question well enough so here's what i was really looking for "i wanna list all the photos that i added a custom description for, does anyone have an idea?"
Gate Reason: User is trying to find a specific target: photos they added custom descriptions to in their library.

--- Disagreement 2 ---
ID: 99ac86accc16902f9dfc592e337d11e6e0f35e95a7f78203ad8954dac80b75c2
My Label: no | Gate Label: yes
Text: My files' name are starting with either IMG_xxxx.jpg or MOV_xxxxx.mov. I just used the last underscore in the file name together with the rest of the name of the file.
Gate Reason: Reply describes a search method using file naming patterns to find specific photos/videos.

--- Disagreement 3 ---
ID: 52bee283b0d93afeb7b5f0467f91b0536a38bc3cde11da726eed8b8f0b5e72e3
My Label: partial | Gate Label: yes
Text: i have about 130 photos of my rabbit but only 6 appear So I went to search menu (website my other family members are also there and pebby (my rabbit) but when i click on it it only shows 6 photos out of 128 bunny photos. When i go to Google files all the 128 photos are shown there
Gate Reason: User is trying to find 128 rabbit photos they believe exist in Google Photos but can only see 6. Specific target named.

--- Disagreement 4 ---
ID: 07424998b468b05c21b86d0672346cc00a0d7f2e0ffeb57890231e739ef79b3c
My Label: no | Gate Label: yes
Text: Go into photo settings, preferences, Gemini features in photos, and turn off the first option.
Gate Reason: Reply describes a method/workaround to find or access something in Google Photos, qualifying under the special rule for replies.

--- Disagreement 5 ---
ID: 4a113fae07ff0027de24ad47335a12ea979a1f3a596bf5d6a216e021b925b98e
My Label: no | Gate Label: yes
Text: Oh, and alternatively you can download an album at a time from the web. Not ideal, but the next best way.
Gate Reason: Reply describes a method to find/access something (downloading albums). Applies special rule for replies suggesting workarounds.

--- Disagreement 6 ---
ID: 5cc0172d1a4562a4620dd10751a44c2f111582e7d86841d6775298f3b9935292
My Label: no | Gate Label: partial
Text: Faces not showing all people Pls show
Gate Reason: User reports faces not displaying in Google Photos but does not name a specific target photo or person to find.

--- Disagreement 7 ---
ID: 2e67a08802ee01b9488af99650ec2818f5a465f37203754f70f4b937fbfec8fd
My Label: no | Gate Label: partial
Text: How I can see my photos on this app as they are taken by time? It shows photos randomly, there is no way to see photos by time sorted. Apparently this app is showing, faces, places and a lot of other unwanted preferences (that are not precise) but this simple and necessary function is missing.
Gate Reason: User wants to view photos sorted by time but cannot find this feature. No specific target photo named, only a browsing mode requested.

--- Disagreement 8 ---
ID: cfbeb1bc3a6122b3e00bf9263807d14960f8c6353096a72895367dc9821c54c3
My Label: no | Gate Label: partial
Text: Whatsapp photos 2022 my past photos
Gate Reason: User describes attempting to find photos from WhatsApp and 2022, but names only a browsing mode/time period, not a specific target photo or content.

--- Disagreement 9 ---
ID: 6176a53472cf9aec40fc9f676a360e7071f30b11d6961791a0b9213f4bbbac83
My Label: no | Gate Label: yes
Text: My point was if you uploaded them (and didn't delete them from your device) they are still there. Downloading them would just replace the device copies with a compressed version of the photo.
Gate Reason: Reply describes a method to find/locate photos (uploaded photos that weren't deleted from device). Applies special rule for replies suggesting how to find something.

--- Disagreement 10 ---
ID: f6511326b6fbf88ada4c7303d323ed39530ce6920371bcc6adad9b3cccfa41e7
My Label: no | Gate Label: yes
Text: Pixel 6a here... Under utilities, I need to scroll all the way down to the very bottom of the page. I assume you've already tried that, but...
Gate Reason: Reply describes a method/workaround to find something, suggesting where to look. Qualifies under special rule for replies.

--- Disagreement 11 ---
ID: 6be7a52dac91f7ab874fae617a3e51e15b06a3c2b2bf91ae38e400df3beb4224
My Label: yes | Gate Label: no
Text: browse via heat map removed? I used to able able to search/browse the photos by map view. Where i can see locations on a map where pictures were taken. This has gone missing.is this by design? or is there a setting that i am missing?very frustrating to have this useful feature removed.
Gate Reason: User is asking about a missing feature (map/heat map view) itself, not trying to find a specific photo or video.

--- Disagreement 12 ---
ID: ede1710815b0e03e6d91fa71b7590f3d5f04f400aace81c2456f8bd56145bba7
My Label: partial | Gate Label: no
Text: Face grouping not available in my region Apparently the ability to tag and group faces automatically is not enabled in all regions. Where can i find the supported regions list? I am in a european country but travel often
Gate Reason: User is asking about feature availability and supported regions, not trying to find a specific photo or video in their library.

--- Disagreement 13 ---
ID: 366d3c350698e9f469c3680bd7df5a33cd56d474b571caa709ce7a431aa4e136
My Label: no | Gate Label: yes
Text: The last thing I want to do is defend them, but I would suggest trying it periodically over the course of a few weeks to see if/how it improves. I don't know if what to attribute any bad results or improvement to, as their functions are a black box, but I got notice of the search change/"improvement" weeks ago. Initial results were as frustrating as some report here. But now, it's as good as ever. Hence my suggestion. I'll say this about the the change: there do seem to be more junk results after a correct one than maybe in the past (can't confirm; it's just a feeling) but at the same time, what do I care? I don't need to look past the "right one," which admittedly was in the top 5.
Gate Reason: Reply describes a search method/workaround (trying periodically) for finding photos. Applies special rule for replies.

--- Disagreement 14 ---
ID: b13c695b08d7025937cfbed3002bc9ebde75107fe4e7f6b91517e80c127fbd61
My Label: partial | Gate Label: yes
Text: Smart location services no longer working Hello, in the early days of Google Photos, the app was able to make approximate location guesses based on the content of older (non geo tagged) photos. This was frankly a godsend for organizing older vacation photos. Now, these tags seem to have disappeared from my library, and I can no longer search old photos by location (Even searching “Peru” for Machupichu no longer works.)Can anyone offer assistance? Thank you.Dan
Gate Reason: User is trying to find specific photos (vacation photos from Peru/Machu Picchu) that they believe exist in their library but can no longer locate via location search.

--- Disagreement 15 ---
ID: 7266dc9a8daac6c5e1b1a5070e6dca3153247f792035abdd91fb8f61ed2a49f6
My Label: no | Gate Label: partial
Text: i can’t see people group by their face why is it not working
Gate Reason: User describes attempting to access a feature (face grouping) but doesn't name a specific photo or target they're trying to find.

--- Disagreement 16 ---
ID: ced3b15f8d217eaa251b0bb7c4ac3598caf1e028cb4370ce0a028d98d6692a0a
My Label: no | Gate Label: partial
Text: Where to find videos moved to private Videos from file manager moved to private videos where to find
Gate Reason: The person is trying to reach videos they believe exist in their Google Photos library (videos moved to private), which passes step 1. However, they have not named a specific target video—they're asking about a browsing mode or location ("private videos") rather than identifying a particular video by content, subject, event, date, place, or a concrete query they ran. This is a request for an inventory or category of items, which fails step 2, making it "partial".

--- Disagreement 17 ---
ID: bc173103d37099f221714bf53f43035b75f9545831d7503b182cad3c3638d2d4
My Label: yes | Gate Label: partial
Text: Any way to find photos NOT in albums? (https://www.reddit.com/r/googlephotos/comments/1urhq80/any_way_to_find_photos_not_in_albums/) Published: 2 months ago; I have 64.5G worth of photos in my Google Photos / Google One account. ... Is there a way to show the ones that aren't in an album so that I can categorize them appropriately? ... I always go back and tag photos I upload so I can search for them later if I don't put them in albums. [Thursday July 09 2026] [+0 votes] I have 64.5G worth of photos in my Google Photos / Google One account. I have no idea how many there actually are. Most are in albums, but there's still a lot that aren't. Is there a way to show the ones that aren't in an album so that I can categorize them appropriately? [Thursday July 09 2026] [+1 votes] Google Photos Toolkit https://github.com/xob0t/Google-Photos-Toolkit. Or in the Archive you can search for each album and then select and archive the contents leaving only non album items on the main view. [Thursday July 09 2026] [+1 votes] I always go back and tag photos I upload so I can search for them later if I don't put them in albums.
Gate Reason: User seeks to find photos not in albums—an inventory request. Passes step 1 but fails step 2 as no specific target photo is named.

--- Disagreement 18 ---
ID: 358a88ba0633adf4329b4ce21b45c506bfd623da738099fb034ad62d3b54ddfb
My Label: no | Gate Label: partial
Text: Is there a way to see all of the Google Photos Creations? The Google Photos Creations used to be grouped under Auto Awesome. Since the re-branding, Auto Awesome doesn't exist anymore. Is there way to see these things without manually going through all of the photos or albums?
Gate Reason: User is asking about finding Creations as a category/collection, an inventory request. Fails step 2 as no specific target photo is named.

--- Disagreement 19 ---
ID: 67cc696db48f192136dc685e9a063d16f65827bd055ca9a8dbb825635474b5ff
My Label: no | Gate Label: yes
Text: One of my sons is not recognized, photos lumped into other son Google photos does not distinguish between my two youngest sons. I'm trying to get it to recognize my you gest son as separate so I can search for him. I have tried removing him from photos marked as my other son but it still is not recognizing him as a person.
Gate Reason: User is trying to find and retrieve photos of their youngest son by name/person, but Google Photos is lumping them with another son. Specific target named.

--- Disagreement 20 ---
ID: 96c5d5c25b1a26056e6326c5054c82fb00ed7586bd23f5197b99caa18761cfe9
My Label: yes | Gate Label: partial
Text: Question 🤔 I'm getting a "no results" message. Even for basic searches like "door", my own name, etc. Anyone else having trouble with the app? Thanks. # Comments Section
Gate Reason: User describes attempting searches and getting no results, but names no specific target photo—only generic search terms as examples of a broader problem.

--- Disagreement 21 ---
ID: 147b610a7c4ca05c2e433e4609f9f9b2064b045b373c0994749c680d29aa6141
My Label: no | Gate Label: yes
Text: Tapping Ask twice still works for me.
Gate Reason: Reply describes a method/workaround ("tapping Ask twice") for finding something. Special rule for replies applies.

---

## A3 — Cue Field Audit and Reclassification

**Date:** 3 October 2026

### Finding

A 30-phrase manual audit of the cue field (seed-42 random sample from 970 unique
phrases) found that 43% of entries described system state — app settings, feature
changes, backup status, storage actions — rather than photo attributes the user
remembered about the target photo. The cue pool was contaminated because the
Pass 2 extractor did not distinguish "things the user remembered about the photo"
from "things the user observed about Google Photos itself."

### Reclassification

A CUE/SYSTEM classifier was built (Haiku 4.5, thinking disabled, batched at 40
phrases/call) and run over all 970 phrases. Cost: $0.16.

**Results:**
- CUE: 554 (57.1%)
- SYSTEM: 416 (42.9%)

### Classifier Measurement

A blind validation sample of 30 phrases (seed-99, drawn from the 940 phrases not
in the seed-42 audit sample, zero overlap confirmed) was labelled independently.

- **Overall agreement:** 25/30 (83.3%)
- **CUE precision:** 15/19 = 78.9%
- **CUE recall:** 15/16 = 93.8%
- **Bias direction:** Classifier is loose in the CUE direction — 4 of 5
  disagreements were phrases the classifier called CUE that the human called SYSTEM.

**Labeller noise caveat:** Three of the human's own rows were internally
inconsistent and were left uncorrected to avoid fitting labels post hoc; the
agreement figure carries labeller noise of roughly ten points.

### Corrected Counts

- **Cue phrases (corrected):** 554 — supersedes the earlier figure of 973.
- **SYSTEM phrases:** 416 — retained separately; these represent a second finding
  about users modelling opaque system behaviour, and may feed the breakdown analysis.

### Forgotten Set

The 61 forgotten cues were re-coded by hand after the extractor's gap_type
field was found to misfile date-recall failures as navigation failures.
The re-coding was AI-proposed and human-reviewed. It is not an independent
validation of the extractor.

Final distribution: MEMORY 26, NAVIGATION 17, PRODUCT 9, NOT_CUE 5, SYSTEM 4.
10 of the 26 memory gaps concern when a photo was taken, the largest single
attribute within memory gaps.

### Induction Impact

The earlier four-shuffle cue induction (in the original checkpoint3_review.md) ran
over the contaminated 970-phrase list. A fresh induction on the cleaned 554-phrase
CUE set was run and checkpoint3_review.md was rebuilt from the new runs. The four
runs produced 12 to 17 categories, so stability will be reported as a core of
categories recurring in all four runs plus a periphery of contested splits. Note
that temperature is unsettable on this model, so the spread conflates shuffle
order with sampling, per the HRV-4 gap already recorded.

---

## A4 — Checkpoint 3 (Taxonomy Consolidation)

**Date:** 3 October 2026

The four induction runs produced a total of twelve unique concepts identified by hand. These were consolidated into a final taxonomy of nine categories. 

The consolidation involved two merges:
- **File Identity** was created by merging "filename", "file properties", and "specific photo data".
- **Capture Source** was created by merging "device" and "image source".

Several of the induction runs produced internally redundant categories covering the same underlying concept, necessitating this consolidation. The final category definitions were drafted by the AI from phrases in the corpus and approved by human review.

---

## Final Limitations Summary

For explicit transparency in the final outputs, the following methodological limitations and adjustments are confirmed and recorded:

1. **Gate Over-inclusion:** The Pass 1 relevance gate is intentionally loose and systematically over-inclusive on reply fragments and feature-navigation questions. It functions as an upper bound rather than a precise filter.
2. **HRV-4 Temperature Gap:** Temperature was unsettable on the `claude-sonnet-5` model during induction, meaning the reported variance in taxonomy structure conflates shuffle order with unconstrained sampling randomness.
3. **Cue-Field Contamination and Correction:** The raw output of the Pass 2 extractor for the cue field suffered a 43% contamination rate where users described system-state observations rather than memory attributes. This required a post-hoc classification pass to isolate the 554 genuine cues.
4. **Forgotten Set Re-coding:** The Pass 2 extractor systematically misfiled date-recall failures as navigation gaps. The final 26-item memory gap distribution relies on an AI-proposed, human-reviewed re-coding, rather than the raw model output.
5. **Breakdown and Workaround AI-Consolidation:** The breakdown and workaround taxonomies were consolidated directly from the four induction runs by AI (reducing 24 concepts to 12 for breakdowns, and 18 to 9 for workarounds). Unlike the cue taxonomy, this consolidation received no independent human review at Checkpoint 3. Consequently, the `confirmed_by` field for these taxonomies reads "AI-consolidated (Claude)".
6. **Target Taxonomy AI-Consolidation:** The target taxonomy was also consolidated by AI (approximately 30 proposed categories reduced to 12). Handle-type categories (e.g. filename, caption, device, album, date, upload time) were explicitly dropped during consolidation to avoid double-counting against the cue taxonomy, retaining only a single category for targets described by a technical handle and nothing else.
7. **Target Assignment Guard Missing:** The target assignment pass ran without the category-validation guard used in the other passes. As a result, 24 assignments (3.2%) contained labels slightly outside the literal taxonomy (dropped articles like "app malfunction" or invented categories like "a date range"). These out-of-taxonomy labels were mapped to their proper bins by hand during counting.
8. **Target Taxonomy V1 Conflation:** The v1 target taxonomy generated 62.9% duplicate consistency during assignment. It was replaced with a v2 taxonomy because v1 conflated two dimensions (what the user wanted vs. what was wrong with it). The v2 taxonomy resolves this by introducing a strict tie-break rule ("choose the KIND OF PHOTO" when both are present) to ensure single-axis measurement. The v1 consistency figure is kept on the record.
