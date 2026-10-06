import json

with open(r'd:\Attempt 2\taxonomy_proposed.json', 'r', encoding='utf-8') as f:
    tax = json.load(f)

with open(r'd:\Attempt 2\docs\checkpoint3_review.md', 'w', encoding='utf-8') as f:
    f.write("# Checkpoint 3 Review: Pass 3 Induction Stability\n\n")
    f.write("Stability is assessed by human mapping because label strings differ across runs by construction. Exact string matching cannot reliably detect when two runs find the same category under different labels.\n\n")
    
    for field, runs_dict in tax.get("fields", {}).items():
        if not runs_dict:
            continue
            
        f.write(f"## Field: {field}\n\n")
        
        # Sort runs to ensure run_1, run_2, etc.
        run_keys = sorted(runs_dict.keys())
        for run_name in run_keys:
            f.write(f"### {run_name}\n")
            run_data = runs_dict[run_name]
            categories = run_data.get("categories", [])
            for cat in categories:
                f.write(f"- **{cat.get('name', 'Unnamed')}**: {cat.get('definition', '')}\n")
                examples = cat.get("examples", [])
                if examples:
                    ex_str = ", ".join(f'"{e}"' for e in examples[:3])
                    f.write(f"  - Examples ({len(examples)}): {ex_str}\n")
            f.write("\n")
            
        f.write(f"### Mapping Table ({field})\n\n")
        header = "| Category Concept | " + " | ".join([r for r in run_keys]) + " |"
        sep = "|---|" + "|".join(["---" for _ in run_keys]) + "|"
        f.write(header + "\n" + sep + "\n")
        for _ in range(15): # empty rows
            row = "| | " + " | ".join(["" for _ in run_keys]) + " |"
            f.write(row + "\n")
        f.write("\n")
