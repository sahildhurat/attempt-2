import os
import json

SUMMARY_MD = """# Analysis Summary

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
"""

def generate_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Photos Retrieval Study - Part 1</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #F3F4F6;
            --surface: #FFFFFF;
            --ink: #16181B;
            --secondary: #595F66;
            --muted: #8A9199;
            --rule: #DEE1E5;
            --data: #2A6DAD;
            --emphasis: #C98214;
            --failure: #A6442A;
            color-scheme: light;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --bg: #101113;
                --surface: #17181A;
                --ink: #EDEEF0;
                --secondary: #9AA1A9;
                --muted: #6E757D;
                --rule: #2A2D31;
                --data: #6FA8DC;
                --emphasis: #D9A44A;
                --failure: #C9735A;
                color-scheme: dark;
            }
        }
        
        :root[data-theme="dark"] {
            --bg: #101113;
            --surface: #17181A;
            --ink: #EDEEF0;
            --secondary: #9AA1A9;
            --muted: #6E757D;
            --rule: #2A2D31;
            --data: #6FA8DC;
            --emphasis: #D9A44A;
            --failure: #C9735A;
            color-scheme: dark;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg);
            color: var(--ink);
            font-family: 'IBM Plex Sans', system-ui, -apple-system, sans-serif;
            font-size: 16px;
            line-height: 1.5;
            padding: 16px;
            min-height: 100vh;
            overflow-x: hidden;
        }

        .container {
            max-width: 50rem;
            margin: 0 auto;
            background-color: var(--surface);
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }

        h1, h2, h3 {
            font-family: 'Newsreader', ui-serif, Georgia, serif;
            color: var(--ink);
            margin-bottom: 1rem;
            font-weight: 600;
        }

        h1 {
            font-size: 2.5rem;
            line-height: 1.2;
            margin-bottom: 0.5rem;
        }

        .subtitle {
            font-size: 1.25rem;
            color: var(--secondary);
            margin-bottom: 2rem;
        }

        .metadata-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            padding-bottom: 1.5rem;
            margin-bottom: 2.5rem;
            border-bottom: 1px solid var(--rule);
            font-family: 'IBM Plex Mono', ui-monospace, monospace;
            font-size: 0.875rem;
            color: var(--secondary);
        }

        .metadata-item span {
            color: var(--ink);
            font-weight: 500;
        }

        section {
            margin-bottom: 3.5rem;
        }

        h2 {
            font-size: 1.5rem;
            border-bottom: 1px solid var(--rule);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-family: 'IBM Plex Sans', system-ui, -apple-system, sans-serif;
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--secondary);
        }

        .chart {
            margin-bottom: 1.5rem;
        }

        .bar-container {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
            font-family: 'IBM Plex Mono', ui-monospace, monospace;
            font-size: 0.875rem;
        }

        .bar-label {
            width: 35%;
            padding-right: 1rem;
            text-align: right;
            color: var(--ink);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .bar-wrapper {
            flex-grow: 1;
            display: flex;
            align-items: center;
        }

        .bar {
            display: block;
            height: 1.5rem;
            background-color: var(--data);
            min-width: 2px;
        }

        .bar.emphasis {
            background-color: var(--emphasis);
        }

        .bar.failure {
            background-color: var(--failure);
        }

        .bar-value {
            margin-left: 0.75rem;
            color: var(--secondary);
        }

        .note {
            font-size: 0.875rem;
            color: var(--secondary);
            margin-bottom: 1rem;
            padding-left: 1rem;
            border-left: 2px solid var(--rule);
        }

        .quote {
            font-style: italic;
            font-family: 'Newsreader', ui-serif, Georgia, serif;
            font-size: 1.125rem;
            color: var(--ink);
            margin: 1.5rem 0;
            padding: 1rem 1.5rem;
            background-color: var(--bg);
            border-radius: 4px;
        }

        .big-numbers {
            display: flex;
            justify-content: space-around;
            text-align: center;
            margin: 2rem 0;
        }

        .big-number {
            display: flex;
            flex-direction: column;
        }

        .big-number .val {
            font-family: 'IBM Plex Mono', ui-monospace, monospace;
            font-size: 2.5rem;
            font-weight: 600;
            color: var(--failure);
        }

        .big-number .lbl {
            font-size: 0.875rem;
            color: var(--secondary);
            margin-top: 0.25rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
            margin-bottom: 1.5rem;
        }

        th, td {
            text-align: left;
            padding: 0.75rem;
            border-bottom: 1px solid var(--rule);
        }

        th {
            font-weight: 600;
            color: var(--secondary);
        }

        td.num {
            font-family: 'IBM Plex Mono', ui-monospace, monospace;
        }

        .limitations ul {
            list-style-position: outside;
            padding-left: 1.5rem;
            color: var(--ink);
        }

        .limitations li {
            margin-bottom: 0.5rem;
        }

        @media (max-width: 600px) {
            .container {
                padding: 1rem;
            }
            .bar-label {
                width: 45%;
                font-size: 0.75rem;
            }
            .big-numbers {
                flex-direction: column;
                gap: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Google Photos Retrieval Study</h1>
            <p class="subtitle">Users primarily rely on time and content descriptions to find photos, but the system frequently fails on those exact dimensions.</p>
            
            <div class="metadata-strip">
                <div class="metadata-item">Corpus: <span>41,006 units</span></div>
                <div class="metadata-item">Gate Processed: <span>7,840</span></div>
                <div class="metadata-item">Cost: <span>~$15</span></div>
                <div class="metadata-item">Sources: <span>7 platforms</span></div>
            </div>
        </header>

        <section>
            <h2>What People Were Looking For</h2>
            <div class="chart">
                <div class="bar-container"><div class="bar-label">a specific person</div><div class="bar-wrapper"><div class="bar emphasis" style="width: 100%;"></div><div class="bar-value">181</div></div></div>
                <div class="bar-container"><div class="bar-label">not a specific photo</div><div class="bar-wrapper"><div class="bar" style="width: 76.2%;"></div><div class="bar-value">138</div></div></div>
                <div class="bar-container"><div class="bar-label">particular photo (unstated)</div><div class="bar-wrapper"><div class="bar" style="width: 49.7%;"></div><div class="bar-value">90</div></div></div>
                <div class="bar-container"><div class="bar-label">an object/scene/subject</div><div class="bar-wrapper"><div class="bar" style="width: 36.5%;"></div><div class="bar-value">66</div></div></div>
                <div class="bar-container"><div class="bar-label">media of a particular type</div><div class="bar-wrapper"><div class="bar" style="width: 30.9%;"></div><div class="bar-value">56</div></div></div>
                <div class="bar-container"><div class="bar-label">unassigned</div><div class="bar-wrapper"><div class="bar" style="width: 23.2%;"></div><div class="bar-value">42</div></div></div>
                <div class="bar-container"><div class="bar-label">unspecified</div><div class="bar-wrapper"><div class="bar" style="width: 21.0%;"></div><div class="bar-value">38</div></div></div>
                <div class="bar-container"><div class="bar-label">a document/ID/text</div><div class="bar-wrapper"><div class="bar" style="width: 17.1%;"></div><div class="bar-value">31</div></div></div>
                <div class="bar-container"><div class="bar-label">a place</div><div class="bar-wrapper"><div class="bar" style="width: 14.9%;"></div><div class="bar-value">27</div></div></div>
                <div class="bar-container"><div class="bar-label">an event</div><div class="bar-wrapper"><div class="bar" style="width: 13.3%;"></div><div class="bar-value">24</div></div></div>
                <div class="bar-container"><div class="bar-label">a pet or animal</div><div class="bar-wrapper"><div class="bar" style="width: 12.2%;"></div><div class="bar-value">22</div></div></div>
            </div>
            <p class="note">Rollup (n=715): <strong>57%</strong> a describable kind of photo, <strong>19%</strong> not a photo at all, <strong>13%</strong> a photo the user cannot describe.</p>
        </section>

        <section>
            <h2>What They Remember</h2>
            <div class="chart">
                <div class="bar-container"><div class="bar-label">content description</div><div class="bar-wrapper"><div class="bar" style="width: 100%;"></div><div class="bar-value">140</div></div></div>
                <div class="bar-container"><div class="bar-label">date and time</div><div class="bar-wrapper"><div class="bar emphasis" style="width: 67.1%;"></div><div class="bar-value">94</div></div></div>
                <div class="bar-container"><div class="bar-label">person identity</div><div class="bar-wrapper"><div class="bar" style="width: 62.1%;"></div><div class="bar-value">87</div></div></div>
                <div class="bar-container"><div class="bar-label">search term used</div><div class="bar-wrapper"><div class="bar" style="width: 29.3%;"></div><div class="bar-value">41</div></div></div>
                <div class="bar-container"><div class="bar-label">file identity</div><div class="bar-wrapper"><div class="bar" style="width: 25.0%;"></div><div class="bar-value">35</div></div></div>
                <div class="bar-container"><div class="bar-label">location</div><div class="bar-wrapper"><div class="bar" style="width: 22.9%;"></div><div class="bar-value">32</div></div></div>
                <div class="bar-container"><div class="bar-label">capture source</div><div class="bar-wrapper"><div class="bar" style="width: 22.1%;"></div><div class="bar-value">31</div></div></div>
                <div class="bar-container"><div class="bar-label">album or folder</div><div class="bar-wrapper"><div class="bar" style="width: 14.3%;"></div><div class="bar-value">20</div></div></div>
                <div class="bar-container"><div class="bar-label">occasion</div><div class="bar-wrapper"><div class="bar" style="width: 12.1%;"></div><div class="bar-value">17</div></div></div>
            </div>
            <p class="note">Of 554 extracted cues, 497 were assigned successfully. An additional 57 unassignable items were recorded separately.</p>
            <div class="quote">"I know for a fact I took a photo of my dog sleeping next to a blowtorch. I searched 'blowtorch', I searched 'dog', I scrolled back to August 2021 where I think it was. Nothing."</div>
        </section>

        <section>
            <h2>What They Don't</h2>
            <div class="chart">
                <div class="bar-container"><div class="bar-label">memory</div><div class="bar-wrapper"><div class="bar failure" style="width: 100%;"></div><div class="bar-value">26</div></div></div>
                <div class="bar-container"><div class="bar-label">navigation</div><div class="bar-wrapper"><div class="bar" style="width: 65.4%;"></div><div class="bar-value">17</div></div></div>
                <div class="bar-container"><div class="bar-label">product</div><div class="bar-wrapper"><div class="bar" style="width: 34.6%;"></div><div class="bar-value">9</div></div></div>
                <div class="bar-container"><div class="bar-label">not a cue</div><div class="bar-wrapper"><div class="bar" style="width: 19.2%;"></div><div class="bar-value">5</div></div></div>
                <div class="bar-container"><div class="bar-label">system</div><div class="bar-wrapper"><div class="bar" style="width: 15.4%;"></div><div class="bar-value">4</div></div></div>
            </div>
            <div class="big-numbers">
                <div class="big-number"><span class="val">26</span><span class="lbl">memory gaps</span></div>
                <div class="big-number"><span class="val">14</span><span class="lbl">attribute failures</span></div>
                <div class="big-number"><span class="val">7</span><span class="lbl">date & time failures</span></div>
            </div>
            <div class="quote">"I couldn't remember when I took the photo but I remember where I took it."</div>
            <div class="quote">"Sometimes I remember places but not the time when I have taken a photo."</div>
        </section>

        <section>
            <h2>How They Search</h2>
            <div class="chart">
                <div class="bar-container"><div class="bar-label">1 word</div><div class="bar-wrapper"><div class="bar" style="width: 100%;"></div><div class="bar-value">74 (60%)</div></div></div>
                <div class="bar-container"><div class="bar-label">2 words</div><div class="bar-wrapper"><div class="bar" style="width: 32.4%;"></div><div class="bar-value">24</div></div></div>
                <div class="bar-container"><div class="bar-label">3 words</div><div class="bar-wrapper"><div class="bar" style="width: 14.9%;"></div><div class="bar-value">11</div></div></div>
                <div class="bar-container"><div class="bar-label">5+ words</div><div class="bar-wrapper"><div class="bar" style="width: 13.5%;"></div><div class="bar-value">10</div></div></div>
                <div class="bar-container"><div class="bar-label">4 words</div><div class="bar-wrapper"><div class="bar" style="width: 6.8%;"></div><div class="bar-value">5</div></div></div>
            </div>
            <p class="note">n=124 verbatim search strings. Caveat: short queries are more likely to be quoted verbatim than long ones, so the proportion is biased by the act of quoting; the mechanism is independently evidenced.</p>
            <div class="quote">"The AI search change requires detailed context — a long specific query succeeded where a short one failed."</div>
        </section>

        <section>
            <h2>Where It Breaks</h2>
            <div class="chart">
                <div class="bar-container"><div class="bar-label">text and keyword</div><div class="bar-wrapper"><div class="bar failure" style="width: 100%;"></div><div class="bar-value">37</div></div></div>
                <div class="bar-container"><div class="bar-label">capability does not exist</div><div class="bar-wrapper"><div class="bar" style="width: 56.8%;"></div><div class="bar-value">21</div></div></div>
                <div class="bar-container"><div class="bar-label">display and platform</div><div class="bar-wrapper"><div class="bar" style="width: 48.6%;"></div><div class="bar-value">18</div></div></div>
                <div class="bar-container"><div class="bar-label">not yet indexed</div><div class="bar-wrapper"><div class="bar" style="width: 45.9%;"></div><div class="bar-value">17</div></div></div>
                <div class="bar-container"><div class="bar-label">unassigned</div><div class="bar-wrapper"><div class="bar" style="width: 45.9%;"></div><div class="bar-value">17</div></div></div>
                <div class="bar-container"><div class="bar-label">user misunderstanding</div><div class="bar-wrapper"><div class="bar" style="width: 29.7%;"></div><div class="bar-value">11</div></div></div>
                <div class="bar-container"><div class="bar-label">date and time</div><div class="bar-wrapper"><div class="bar" style="width: 29.7%;"></div><div class="bar-value">11</div></div></div>
                <div class="bar-container"><div class="bar-label">incomplete subset</div><div class="bar-wrapper"><div class="bar" style="width: 24.3%;"></div><div class="bar-value">9</div></div></div>
                <div class="bar-container"><div class="bar-label">face and people</div><div class="bar-wrapper"><div class="bar" style="width: 21.6%;"></div><div class="bar-value">8</div></div></div>
                <div class="bar-container"><div class="bar-label">user metadata ignored</div><div class="bar-wrapper"><div class="bar" style="width: 16.2%;"></div><div class="bar-value">6</div></div></div>
                <div class="bar-container"><div class="bar-label">blocked terms</div><div class="bar-wrapper"><div class="bar" style="width: 10.8%;"></div><div class="bar-value">4</div></div></div>
                <div class="bar-container"><div class="bar-label">data lost</div><div class="bar-wrapper"><div class="bar" style="width: 8.1%;"></div><div class="bar-value">3</div></div></div>
                <div class="bar-container"><div class="bar-label">location</div><div class="bar-wrapper"><div class="bar" style="width: 5.4%;"></div><div class="bar-value">2</div></div></div>
            </div>
            <p class="note">n=164 breakdowns.</p>
            <div class="quote">"I know the exact date I took the photo, I entered it in search, and Photos told me 'No results'."<br><span style="font-size: 0.875rem; color: var(--secondary); font-style: normal; display: block; margin-top: 0.5rem;">Users expect precise dates to act as hard filters, but search treats them as soft keywords.</span></div>
            <div class="quote">"Scrolling back 5 years takes ages because the timeline keeps jumping."<br><span style="font-size: 0.875rem; color: var(--secondary); font-style: normal; display: block; margin-top: 0.5rem;">Visual scanning is heavily penalized by viewport management defects.</span></div>
            <div class="quote">"It sorted all my scanned film photos to the date I scanned them today, not 1995."<br><span style="font-size: 0.875rem; color: var(--secondary); font-style: normal; display: block; margin-top: 0.5rem;">Chronological sorting breaks down entirely on imported or digitized media.</span></div>
        </section>

        <section>
            <h2>What They Do Instead</h2>
            <div class="chart">
                <div class="bar-container"><div class="bar-label">reformulate the query</div><div class="bar-wrapper"><div class="bar" style="width: 100%;"></div><div class="bar-value">27</div></div></div>
                <div class="bar-container"><div class="bar-label">try a different route</div><div class="bar-wrapper"><div class="bar" style="width: 92.6%;"></div><div class="bar-value">25</div></div></div>
                <div class="bar-container"><div class="bar-label">no workaround found</div><div class="bar-wrapper"><div class="bar emphasis" style="width: 92.6%;"></div><div class="bar-value">25</div></div></div>
                <div class="bar-container"><div class="bar-label">build your own index</div><div class="bar-wrapper"><div class="bar failure" style="width: 59.3%;"></div><div class="bar-value">16</div></div></div>
                <div class="bar-container"><div class="bar-label">troubleshoot</div><div class="bar-wrapper"><div class="bar" style="width: 55.6%;"></div><div class="bar-value">15</div></div></div>
                <div class="bar-container"><div class="bar-label">scroll manually</div><div class="bar-wrapper"><div class="bar" style="width: 51.9%;"></div><div class="bar-value">14</div></div></div>
                <div class="bar-container"><div class="bar-label">switch interface</div><div class="bar-wrapper"><div class="bar" style="width: 44.4%;"></div><div class="bar-value">12</div></div></div>
                <div class="bar-container"><div class="bar-label">unassigned</div><div class="bar-wrapper"><div class="bar" style="width: 44.4%;"></div><div class="bar-value">12</div></div></div>
                <div class="bar-container"><div class="bar-label">leave the app</div><div class="bar-wrapper"><div class="bar" style="width: 29.6%;"></div><div class="bar-value">8</div></div></div>
                <div class="bar-container"><div class="bar-label">ask someone</div><div class="bar-wrapper"><div class="bar" style="width: 14.8%;"></div><div class="bar-value">4</div></div></div>
            </div>
            <p class="note">n=158 workarounds. Note the 16% failure rate ("no workaround found") and users performing the product's job by hand ("build your own index").</p>
        </section>

        <section>
            <h2>How This Was Built</h2>
            <table>
                <thead>
                    <tr>
                        <th>Stage</th>
                        <th>Volume</th>
                        <th>Measurement</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Corpus (Raw)</td>
                        <td class="num">41,038</td>
                        <td>Total lines across all collector output files before any dedup</td>
                    </tr>
                    <tr>
                        <td>Corpus (Post-dedup)</td>
                        <td class="num">41,006</td>
                        <td>Total lines after dedup (all_units_unfiltered.jsonl)</td>
                    </tr>
                    <tr>
                        <td>Gate</td>
                        <td class="num">7,840</td>
                        <td>Units processed (1,015 yes / 945 partial)</td>
                    </tr>
                    <tr>
                        <td>Gate Validation</td>
                        <td class="num">59</td>
                        <td>Blind labels; 64.4% agreement; 82.4% recall; 56.0% precision</td>
                    </tr>
                    <tr>
                        <td>Extraction</td>
                        <td class="num">720</td>
                        <td>Units extracted from "yes" stratum</td>
                    </tr>
                    <tr>
                        <td>Grounding</td>
                        <td class="num">998</td>
                        <td>989 grounded remembered cues (0.9% dropped); 61/61 forgotten grounded</td>
                    </tr>
                    <tr>
                        <td>Cue Cleaning</td>
                        <td class="num">970</td>
                        <td>554 CUE / 416 SYSTEM. 83.3% blind agreement; 78.9% precision, 93.8% recall</td>
                    </tr>
                    <tr>
                        <td>Cue Taxonomy</td>
                        <td class="num">4</td>
                        <td>Shuffled runs (12, 13, 17, 15 categories), consolidated by hand to 9</td>
                    </tr>
                    <tr>
                        <td>Cue Assignment</td>
                        <td class="num">580</td>
                        <td>96.4% duplicate consistency; 9.8% unassigned rate</td>
                    </tr>
                    <tr>
                        <td>Target Taxonomy</td>
                        <td class="num">715</td>
                        <td>v1 scored 62.9%; rebuilt single-axis v2 scored 85.9% consistency</td>
                    </tr>
                    <tr>
                        <td>Cost</td>
                        <td class="num">~$15</td>
                        <td>Total pipeline API spend</td>
                    </tr>
                </tbody>
            </table>
        </section>

        <section class="limitations">
            <h2>Limitations</h2>
            <ul>
                <li>Gate over-inclusion at 56% precision so counts are upper bounds.</li>
                <li>The cue field was 43% contaminated and corrected.</li>
                <li>The forgotten set was re-coded AI-proposed and human-reviewed, not independently validated.</li>
                <li>Temperature could not be set to 0 so induction variance conflates shuffle order with sampling.</li>
                <li>Breakdown, workaround and target taxonomies were AI-consolidated without a human checkpoint, unlike cues.</li>
                <li>iOS underrepresented at 2.4% gate yield.</li>
                <li>Public forum text self-selects for people who failed and sought help.</li>
                <li>Source Coverage: The brief names social media and YouTube comments among its example sources and neither was collected. The five source types used (Google Help Community, Stack Exchange, Hacker News, App Store, Play Store) mean the corpus skews toward written help-seeking rather than conversational commentary.</li>
            </ul>
        </section>
    </div>
</body>
</html>"""

def generate_figures_json():
    return json.dumps({
        "corpus_raw": {"value": 41038, "source": "data/unified/*.jsonl"},
        "corpus_post_dedup": {"value": 41006, "source": "data/archive/all_units_unfiltered.jsonl"},
        "gate_processed": {"value": 7840, "source": "data/gate_results.jsonl"},
        "gate_yes": {"value": 1015, "source": "data/gate_results.jsonl"},
        "gate_partial": {"value": 945, "source": "data/gate_results.jsonl"},
        "gate_validation_n": {"value": 59, "source": "docs/method_notes.md"},
        "gate_agreement": {"value": 0.644, "source": "docs/method_notes.md"},
        "gate_recall": {"value": 0.824, "source": "docs/method_notes.md"},
        "gate_precision": {"value": 0.560, "source": "docs/method_notes.md"},
        "units_extracted": {"value": 720, "source": "data/pass2/extracted_units.jsonl"},
        "remembered_cues_extracted": {"value": 998, "source": "data/pass2/extracted_units.jsonl"},
        "remembered_cues_grounded": {"value": 989, "source": "data/pass2/extracted_units.jsonl"},
        "forgotten_cues_extracted": {"value": 61, "source": "data/pass2/extracted_units.jsonl"},
        "forgotten_cues_grounded": {"value": 61, "source": "data/pass2/extracted_units.jsonl"},
        "unique_phrases": {"value": 970, "source": "data/pass3/cue_classification.jsonl"},
        "cue_phrases": {"value": 554, "source": "data/pass3/cue_classification.jsonl"},
        "system_phrases": {"value": 416, "source": "data/pass3/cue_classification.jsonl"},
        "cue_val_agreement": {"value": 0.833, "source": "docs/method_notes.md"},
        "cue_val_precision": {"value": 0.789, "source": "docs/method_notes.md"},
        "cue_val_recall": {"value": 0.938, "source": "docs/method_notes.md"},
        "cue_assignment_consistency": {"value": 0.964, "source": "data/pass3/taxonomy_assignments.jsonl"},
        "cue_unassigned_rate": {"value": 0.098, "source": "data/pass3/taxonomy_assignments_clean.jsonl"},
        "target_v1_consistency": {"value": 0.629, "source": "docs/method_notes.md"},
        "target_v2_consistency": {"value": 0.859, "source": "data/pass3/target_assignments_v2.jsonl"},
        "target_age_older": {"value": 106, "source": "data/pass3/age_assignments.jsonl"},
        "target_age_recent": {"value": 47, "source": "data/pass3/age_assignments.jsonl"},
        "target_age_unstated": {"value": 562, "source": "data/pass3/age_assignments.jsonl"},
        "pipeline_cost": {"value": 15, "source": "docs/analysis_summary.md"}
    }, indent=2)

def main():
    with open('docs/analysis_summary.md', 'w', encoding='utf-8') as f:
        f.write(SUMMARY_MD)
        
    os.makedirs('site', exist_ok=True)
    with open('site/index.html', 'w', encoding='utf-8') as f:
        f.write(generate_html())
        
    with open('site/figures.json', 'w', encoding='utf-8') as f:
        f.write(generate_figures_json())
        
    print("Files successfully compiled and written.")

if __name__ == '__main__':
    main()
