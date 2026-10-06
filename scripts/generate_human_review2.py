import json

with open(r'd:\Attempt 2\taxonomy_proposed.json', 'r', encoding='utf-8') as f:
    tax = json.load(f)

with open(r'd:\Attempt 2\docs\checkpoint3_review.md', 'w', encoding='utf-8') as f:
    f.write("# Checkpoint 3 Review: Pass 3 Induction Stability\n\n")
    f.write("Stability is assessed by human mapping because label strings differ across runs by construction. Exact string matching cannot reliably detect when two runs find the same category under different labels.\n\n")
    
    for field, field_data in tax.get("fields", {}).items():
        categories = field_data.get("categories", [])
        if not categories:
            continue
            
        runs = []
        current_run = []
        
        for cat in categories:
            name = cat['name'].lower()
            if len(current_run) > 0 and ('date' in name and 'time' in name):
                runs.append(current_run)
                current_run = []
            current_run.append(cat)
        if current_run:
            runs.append(current_run)
            
        f.write(f"## Field: {field}\n\n")
        
        for i, run_cats in enumerate(runs, 1):
            f.write(f"### Run {i}\n")
            for cat in run_cats:
                f.write(f"- **{cat['name']}**: {cat['definition']}\n")
                examples = cat.get('examples', [])
                if examples:
                    ex_str = ", ".join(f'"{e}"' for e in examples[:3])
                    f.write(f"  - Examples: {ex_str}\n")
            f.write("\n")
            
        f.write(f"### Mapping Table ({field})\n\n")
        # Ensure 4 columns even if only 3 runs were found in the json list
        num_cols = max(4, len(runs))
        header = "| Category Concept | " + " | ".join([f"Run {i}" for i in range(1, num_cols+1)]) + " |"
        sep = "|---|" + "|".join(["---" for _ in range(num_cols)]) + "|"
        f.write(header + "\n" + sep + "\n")
        for _ in range(15): # empty rows
            row = "| | " + " | ".join(["" for _ in range(num_cols)]) + " |"
            f.write(row + "\n")
        f.write("\n")
