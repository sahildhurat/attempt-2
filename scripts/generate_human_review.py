import json

with open(r'd:\Attempt 2\taxonomy_proposed.json', 'r', encoding='utf-8') as f:
    tax = json.load(f)

with open(r'd:\Attempt 2\docs\checkpoint3_review.md', 'w', encoding='utf-8') as f:
    f.write("# Checkpoint 3 Review: Pass 3 Induction Stability\n\n")
    f.write("Stability is assessed by human mapping because label strings differ across runs by construction. Exact string matching cannot reliably detect when two runs find the same category under different labels.\n\n")
    
    for field, runs_data in tax.get("fields", {}).items():
        f.write(f"## Field: {field}\n\n")
        
        # We need to print each of the 4 runs.
        # But wait, in taxonomy_proposed.json, does it still have run_1, run_2, etc.?
        # Earlier I saw it only had "categories" under the field.
        # Let's inspect taxonomy_proposed.json structure again.
