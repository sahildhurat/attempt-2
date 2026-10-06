import json
import os
import sys

def rebuild_review():
    tax_path = r'd:\Attempt 2\taxonomy_proposed.json'
    out_path = r'd:\Attempt 2\docs\checkpoint3_review.md'
    
    if not os.path.exists(tax_path):
        print(f"Error: {tax_path} not found.")
        sys.exit(1)
        
    with open(tax_path, 'r', encoding='utf-8') as f:
        tax = json.load(f)

    # Scoping requirement: CUE only gets full hand mapping table.
    # breakdown and workaround get category counts and top 3 categories only.
    # target is skipped entirely (unless it feeds a reported finding, which it currently doesn't).
    
    # Pre-flight check: ensure 4 runs are present for CUE
    cues_data = tax.get("fields", {}).get("cues", {})
    if not isinstance(cues_data, dict):
        print("Error: 'cues' data is not a dictionary (runs not separated).")
        sys.exit(1)
        
    run_keys = sorted(cues_data.keys())
    if len(run_keys) < 4:
        missing = set([f"run_{i}" for i in range(1, 5)]) - set(run_keys)
        print(f"Error: Found only {len(run_keys)} run(s) for 'cues'. Missing: {', '.join(missing)}")
        sys.exit(1)

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("# Checkpoint 3 Review: Pass 3 Induction Stability\n\n")
        f.write("Stability is assessed by human mapping because label strings differ across runs by construction. Exact string matching cannot reliably detect when two runs find the same category under different labels.\n\n")
        
        # We only process cues for the full mapping, and breakdown/workaround for counts.
        # Skip target.
        for field in ["cues", "breakdown", "workaround"]:
            runs_dict = tax.get("fields", {}).get(field, {})
            if not runs_dict or not isinstance(runs_dict, dict):
                continue
                
            run_keys_field = sorted(runs_dict.keys())
            
            # Check runs for this field
            if len(run_keys_field) < 4:
                missing = set([f"run_{i}" for i in range(1, 5)]) - set(run_keys_field)
                print(f"Error: Found only {len(run_keys_field)} run(s) for '{field}'. Missing: {', '.join(missing)}")
                # Delete partial file and exit
                f.close()
                os.remove(out_path)
                sys.exit(1)
                
            f.write(f"## Field: {field}\n\n")
            
            if field == "cues":
                for run_name in run_keys_field:
                    f.write(f"### {run_name}\n")
                    run_data = runs_dict[run_name]
                    categories = run_data.get("categories", [])
                    
                    for cat in categories:
                        name = cat.get('name', 'Unnamed')
                        defn = cat.get('definition', '')
                        examples = cat.get("examples", [])
                        
                        f.write(f"- **{name}**: {defn}\n")
                        f.write(f"  - Count: {len(examples)} phrase(s)\n")
                        if examples:
                            ex_str = ", ".join(f'"{e}"' for e in examples[:3])
                            f.write(f"  - Examples: {ex_str}\n")
                    f.write("\n")
                    
                f.write(f"### Mapping Table ({field})\n\n")
                header = "| Category Concept | " + " | ".join(run_keys_field) + " |"
                sep = "|---|" + "|".join(["---" for _ in run_keys_field]) + "|"
                f.write(header + "\n" + sep + "\n")
                
                for _ in range(15): # empty rows
                    row = "| | " + " | ".join(["" for _ in run_keys_field]) + " |"
                    f.write(row + "\n")
                f.write("\n")
                
            else:
                # breakdown or workaround: report category count and 3 largest categories by phrase count. No mapping table.
                for run_name in run_keys_field:
                    run_data = runs_dict[run_name]
                    categories = run_data.get("categories", [])
                    f.write(f"### {run_name} (Category Count: {len(categories)})\n")
                    
                    # Sort by phrase count
                    sorted_cats = sorted(categories, key=lambda x: len(x.get("examples", [])), reverse=True)
                    f.write("Top 3 categories by phrase count:\n")
                    for cat in sorted_cats[:3]:
                        name = cat.get('name', 'Unnamed')
                        count = len(cat.get("examples", []))
                        f.write(f"- **{name}** ({count} phrases)\n")
                    f.write("\n")
                    
    print(f"Rebuilt {out_path} successfully.")

if __name__ == '__main__':
    rebuild_review()
