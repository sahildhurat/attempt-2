import json

# Read original
with open('docs/checkpoint3_review.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Extract cues portion
cues_lines = []
for line in lines:
    if line.strip() == '## Field: breakdown':
        break
    cues_lines.append(line)

# Now rebuild the file
with open('taxonomy_haiku.json', 'r', encoding='utf-8') as f:
    tax_data = json.load(f)

with open('docs/checkpoint3_review.md', 'w', encoding='utf-8') as out:
    out.writelines(cues_lines)
    
    for field in ['breakdown', 'workaround']:
        if field not in tax_data: continue
        out.write(f'\n## Field: {field}\n')
        runs = tax_data[field]
        
        all_cats = []
        for run_id in sorted(runs.keys()):
            out.write(f'\n### {run_id}\n')
            cats = runs[run_id].get('categories', [])
            all_cats.append(len(cats))
            for c in cats:
                name = c.get('name', 'Unknown')
                definition = c.get('definition', '')
                out.write(f'- **{name}**: {definition}\n')
                examples_list = c.get('examples', [])
                out.write(f'  - Count: {len(examples_list)} phrase(s)\n')
                examples = ", ".join(f'"{ex}"' for ex in examples_list)
                out.write(f'  - Examples: {examples}\n')
                
        out.write(f'\n### Mapping Table ({field})\n\n')
        out.write('| Category Concept | run_1 | run_2 | run_3 | run_4 |\n')
        out.write('|---|---|---|---|---|\n')
        
        max_rows = max(all_cats) if all_cats else 0
        for _ in range(max_rows):
            out.write('| |  |  |  |  |\n')
