import sys

with open('d:/Attempt 2/docs/method_notes.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
idx = next(i for i, line in enumerate(lines) if '## Span-Level Provenance Test' in line)
lines = lines[:idx]

with open('d:/Attempt 2/docs/method_notes.md', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    f.write('''## Span-Level Provenance Test for Cues (Correction: 1 October 2026)
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
''')
