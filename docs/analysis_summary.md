# Analysis Summary

*This document serves as the single source of truth for figures cited in the final presentation.*

## 1. Corpus and Pre-Processing
*Source: `data/archive/all_units_unfiltered.jsonl`, `data/unified/*.jsonl`, `data/gate_results.jsonl`*
* **Total lines across all collector output files before any dedup:** 41,038 (matches `data/unified/*.jsonl`)
* **Total lines after dedup:** 41,006 (matches `data/archive/all_units_unfiltered.jsonl`)
* **Units processed by Pass 1 Gate:** 7,840
* **Gate Decisions:**
  * **Yes:** 1,015
  * **Partial:** 945
  * **No:** 5,879 (Note: gate output totals 5,879 'no', summing to 7,839 with yes/partial. The missing 1 was dropped during batch processing/retries).

## 2. Gate Validation
*Source: `docs/method_notes.md` (n=59 blind sample)*
* **Overall Agreement:** 64.4%
* **Precision:** 56.0% (Yes), 27.3% (Partial)
* **Recall:** 82.4% (Yes), 50.0% (Partial)
* **Direction of Error:** Systematically over-inclusive.

## 3. Pass 2 Extraction & Grounding
*Source: `data/pass2/extracted_units.jsonl`, `data/pass3/cue_classification.jsonl`*
* **Units Extracted:** 720 (from the 1,015 "Yes" stratum, dropping near-empty units)
* **Remembered Grounding Rate:** 989/998 remembered cues grounded (0.9% dropped).
* **Forgotten Grounding Rate:** 61/61 forgotten cues grounded.
* **Deduplication:** 970 unique phrases across all grounded cues.
* **CUE / SYSTEM Split:** 554 CUE / 416 SYSTEM

## 4. Cue Classification Validation
*Source: `docs/method_notes.md` (n=30 blind sample)*
* **Overall Agreement:** 83.3%
* **CUE Precision:** 78.9%
* **CUE Recall:** 93.8%
* **Bias:** Loose in the CUE direction. 
  *(Caveat: Three labeller rows were internally inconsistent and left uncorrected to prevent post hoc fitting. The 83.3% figure carries roughly ten points of labeller noise).*

## 5. Forgotten Set Taxonomy
*Source: `data/pass3/forgotten_validation.csv`*
* **Distribution (61 items):** 26 MEMORY / 17 NAVIGATION / 9 PRODUCT / 5 NOT_CUE / 4 SYSTEM
* **Attribute Recall Failures:** Of the 26 genuine MEMORY gaps, 14 explicitly name a target attribute. Of those 14, **7** specifically concern **date and time**.

## 6. Final Cue Taxonomy (9 Categories)
*Source: `data/pass3/cue_induction.json`, `data/pass3/taxonomy_assignments.jsonl`, `taxonomy_confirmed.json`*
* **Cue Induction:** 4 shuffled runs returned 12, 13, 17, and 15 categories respectively. Consolidated by hand to 9 categories.
* **Cue Assignment:** 96.4% duplicate consistency; 9.8% unassigned rate (57/580 provenance events).

| Category | Remembered | Forgotten |
| :--- | :--- | :--- |
| **content description** | 140 | 1 |
| **date and time** | 94 | 7 |
| **person identity** | 87 | 1 |
| **UNASSIGNED** | 57 | 12 |
| **search term used** | 41 | 0 |
| **file identity** | 35 | 1 |
| **location** | 32 | 1 |
| **capture source** | 31 | 2 |
| **album or folder name** | 20 | 1 |
| **occasion or event** | 17 | 0 |

## 7. Target Taxonomy
*Source: `data/pass3/target_assignments_v2.jsonl`, `data/pass3/age_assignments.jsonl`, `docs/method_notes.md`*
* **Target taxonomy v1** scored 62.9% duplicate consistency. Rebuilt single-axis.
* **Target taxonomy v2** scored 85.9% duplicate consistency on 71 duplicates.
* **Categories (715 targets):** a specific person 181, not a specific photo 138, one particular photo with content not described 90, an object/scene/subject 66, media of a particular type 56, unassigned 42, unspecified 38, a document/ID/text 31, a place 27, an event 24, a pet or animal 22.
* **Target Age Pass:** 562 unstated (79%), 106 older (15%), 47 recent (7%); 92.9% duplicate consistency. *(Note: "unstated" means the account did not mention age, which may reflect either how users describe photos or what the extraction captured — we cannot distinguish the two).*

## 8. Breakdowns and Workarounds
*Source: `data/pass3/bw_assignments.jsonl`, `taxonomy_confirmed_bw.json`*

### Breakdowns (n=164)
* **Duplicate Consistency:** 87.5% (7/8)
* **UNASSIGNED rate:** 10.4% (17/164)

| Category | Count |
| :--- | :--- |
| **text and keyword search fails** | 37 |
| **the capability does not exist** | 21 |
| **display and platform inconsistency** | 18 |
| **UNASSIGNED** | 17 |
| **content not yet indexed or synced** | 17 |
| **user misunderstanding** | 11 |
| **date and time search fails** | 11 |
| **search returns an incomplete subset** | 9 |
| **face and people search fails** | 8 |
| **user-supplied metadata is ignored** | 6 |
| **search terms are blocked or filtered** | 4 *(<5)* |
| **data lost or deleted** | 3 *(<5)* |
| **location search fails or is unavailable** | 2 *(<5)* |

### Workarounds (n=158)
* **Duplicate Consistency:** 71.4% (5/7)
* **UNASSIGNED rate:** 7.6% (12/158)

| Category | Count |
| :--- | :--- |
| **reformulate the query** | 27 |
| **try a different search route** | 25 |
| **no workaround found** | 25 |
| **build your own index** | 16 |
| **troubleshoot the app** | 15 |
| **scroll manually** | 14 |
| **switch interface or device** | 12 |
| **UNASSIGNED** | 12 |
| **leave the app** | 8 |
| **ask someone else** | 4 *(<5)* |

## 9. Search Formulations
*Source: `scripts/clean_search_strings.py`*
* **Literal Verbatim Strings Only:** 124 (after separating out meta-descriptions).
* **Word Counts:** 1 word 74 (60%), 2 words 24, 3 words 11, 4 words 5, 5+ words 10.
* *Caveat:* Short queries are more likely to be quoted verbatim than long ones, so the proportion is biased by the act of quoting and should be read as suggestive. The mechanism — short queries failing after the AI search change, a long query succeeding where a short one failed — is independently evidenced and does not rest on the proportion.

## 10. Opportunity Areas
* **Date and Time Search**: Users strongly rely on date and time, but frequently experience retrieval failure. Supported by: "date and time" is the second most common remembered cue (94), but also represents 7 of the 14 attribute recall failures and 11 breakdowns. Quote: "Sometimes I remember places but not the time when I have taken a photo"
* **Keyword and Subject Searching**: Users try to describe what they are looking for, but the capability often falls short. Supported by: "content description" is the most common cue (140) and "text and keyword search fails" is the most common breakdown (37). Quote: "A long specific query succeeded where a short one failed."
* **Navigation vs. Photo Retrieval**: Many users struggle to navigate the app rather than find a specific photo. Supported by: "not a specific photo" is 19.3% (138) of targets, and "display and platform inconsistency" is 18 breakdowns. Quote: "Where to find videos moved to private"

## 11. Total Pipeline Cost
* **Cumulative Pipeline Spend:** ~$14.86 (about $15)

## 12. Limitations
* Gate over-inclusion at 56% precision so counts are upper bounds.
* The cue field was 43% contaminated and corrected.
* The forgotten set was re-coded AI-proposed and human-reviewed, not independently validated.
* Temperature could not be set to 0 so induction variance conflates shuffle order with sampling.
* Breakdown, workaround and target taxonomies were AI-consolidated without a human checkpoint, unlike cues.
* iOS underrepresented at 2.4% gate yield.
* Public forum text self-selects for people who failed and sought help.
* Source Coverage: The brief names social media and YouTube comments among its example sources and neither was collected. The five source types used (Google Help Community, Stack Exchange, Hacker News, App Store, Play Store) mean the corpus skews toward written help-seeking rather than conversational commentary.
