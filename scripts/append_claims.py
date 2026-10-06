content = """
**Restatement of Claims:**
- The gate achieved 82.4% recall and 56.0% precision against blind human labels on the 59 valid units. It is over-inclusive by design.
- All corpus counts are therefore **UPPER BOUNDS** on relevant units.
- To ensure conclusions are drawn only from genuine accounts, all subsequent analysis is restricted exclusively to units that produced at least one verbatim-grounded cue.
- Gate reliability scaled directly with unit length and completeness; short reply fragments were the least reliable, prompting a new 20-character minimum-length precondition for gate eligibility.

*(Note: The gate was not adjusted or re-run to match the labels; the measurement stands as taken and is a measured property of the instrument.)*
"""

with open(r'd:\Attempt 2\docs\method_notes.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
for line in lines:
    if line.strip() == "### Appendix: Full Disagreement List":
        out.append(content)
        out.append(line)
    else:
        out.append(line)

with open(r'd:\Attempt 2\docs\method_notes.md', 'w', encoding='utf-8') as f:
    f.writelines(out)
