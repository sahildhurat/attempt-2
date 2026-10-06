import os

content = """

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

### Appendix: Full Disagreement List
"""

with open(r'd:\Attempt 2\docs\method_notes.md', 'a', encoding='utf-8') as f:
    f.write(content)
    
    # Append the disagreements from the report
    recording = False
    with open(r'd:\Attempt 2\data\comparison_report.txt', 'r', encoding='utf-8') as rep:
        for line in rep:
            if line.strip() == "DISAGREEMENTS:":
                recording = True
                continue
            if recording:
                f.write(line)
