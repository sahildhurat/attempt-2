import json

with open(r'd:\Attempt 2\taxonomy_proposed.json', 'r', encoding='utf-8') as f:
    tax = json.load(f)

with open(r'd:\Attempt 2\docs\checkpoint3_review.md', 'w', encoding='utf-8') as f:
    f.write("# Checkpoint 3 Review: Pass 3 Induction Stability\n\n")
    f.write("This document summarizes the taxonomy induction across 4 shuffled runs to evaluate stability.\n\n")
    
    for field, data in tax.get("fields", {}).items():
        f.write(f"## Field: {field}\n")
        categories = data.get("categories", [])
        
        stable_cats = [c for c in categories if c.get("stable", False)]
        unstable_cats = [c for c in categories if not c.get("stable", False)]
        
        f.write(f"### Stable Categories (Appeared in all 4 runs)\n")
        if not stable_cats:
            f.write("None.\n")
        for c in stable_cats:
            f.write(f"- **{c['name']}** ({c['stability']}): {c['definition']}\n")
            
        f.write(f"\n### Unstable Categories (Appeared in <4 runs)\n")
        if not unstable_cats:
            f.write("None.\n")
        for c in unstable_cats:
            f.write(f"- **{c['name']}** ({c['stability']}): {c['definition']}\n")
            
        f.write("\n")
