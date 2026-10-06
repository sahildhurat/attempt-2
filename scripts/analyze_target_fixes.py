import json

# Taxonomy reference
cat_1_7 = [
    "a specific person", "a pet or animal", "an object, scene or subject",
    "a document, ID or text", "an event, occasion or trip", "a place",
    "media of a particular type"
]
cat_8_11 = [
    "an app feature or location", "content believed missing or lost",
    "an app malfunction", "one photo by a technical handle"
]
valid_categories = set(cat_1_7 + cat_8_11 + ["unspecified", "UNASSIGNED"])

dup_assignments = {}
out_of_tax = {}

with open('data/pass3/target_assignments.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip(): continue
        rec = json.loads(line)
        p = rec.get('phrase')
        c = rec.get('category')
        
        if c not in valid_categories:
            out_of_tax[c] = out_of_tax.get(c, 0) + 1
            
        if p not in dup_assignments:
            dup_assignments[p] = []
        dup_assignments[p].append(c)

print("--- OUT OF TAXONOMY ---")
total_out = sum(out_of_tax.values())
print(f"Total out-of-taxonomy assignments: {total_out}")
for c, count in out_of_tax.items():
    print(f"  {c}: {count}")

print("\n--- DUPLICATE DISAGREEMENTS ---")
disagreements = []
for p, cats in dup_assignments.items():
    if len(cats) > 1 and len(set(cats)) > 1:
        disagreements.append((p, cats))

cross_group = 0
within_group = 0

def get_group(c):
    # Normalize before checking group for the sake of the duplicate analysis
    # because they might have disagreed with an un-prefixed one.
    # Actually, we should just map the rogue ones to their groups for this logic
    c_norm = c
    if c == "app malfunction": c_norm = "an app malfunction"
    elif c == "app feature or location": c_norm = "an app feature or location"
    elif c == "event, occasion or trip": c_norm = "an event, occasion or trip"
    elif c == "unassigned": c_norm = "UNASSIGNED"
    elif c == "a date range": c_norm = "one photo by a technical handle"
    
    if c_norm in cat_1_7: return 1
    if c_norm in cat_8_11: return 2
    return 3

for p, cats in disagreements:
    c1, c2 = cats[0], cats[1]
    g1 = get_group(c1)
    g2 = get_group(c2)
    if g1 == g2:
        within_group += 1
        print(f"[WITHIN] {cats} | Phrase: '{p[:100]}...'")
    else:
        cross_group += 1
        print(f"[CROSS]  {cats} | Phrase: '{p[:100]}...'")

print(f"\nWithin group: {within_group}")
print(f"Cross group: {cross_group}")

print("\n--- CROSS-TABULATION (Rollup vs Breakdown) ---")
# Build target map (resolving duplicates to their first category, and normalizing)
target_map = {}
for p, cats in dup_assignments.items():
    c_norm = cats[0]
    if c_norm == "app malfunction": c_norm = "an app malfunction"
    elif c_norm == "app feature or location": c_norm = "an app feature or location"
    elif c_norm == "event, occasion or trip": c_norm = "an event, occasion or trip"
    elif c_norm == "unassigned": c_norm = "UNASSIGNED"
    elif c_norm == "a date range": c_norm = "one photo by a technical handle"
    target_map[p] = get_group(c_norm) # 1="a photo", 2="not a photo", 3="other"

bw_map = {}
with open('data/pass3/bw_assignments.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        if rec.get('field') == 'breakdown':
            bw_map[rec.get('phrase')] = rec.get('category')

cross_tab = {1: {}, 2: {}, 3: {}}

with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip(): continue
        u = json.loads(line)
        ext = u.get('extraction', {})
        t = ext.get('target', '').strip()
        b = ext.get('breakdown', '')
        if b: b = b.strip()
        b_src = ext.get('breakdown_source')
        
        if t and b and b_src == 'user':
            t_grp = target_map.get(t)
            b_cat = bw_map.get(b)
            if t_grp and b_cat:
                cross_tab[t_grp][b_cat] = cross_tab[t_grp].get(b_cat, 0) + 1

top_breakdowns = ["text and keyword search fails", "the capability does not exist", 
                  "display and platform inconsistency", "content not yet indexed or synced"]

for grp, name in [(1, "A Photo (1-7)"), (2, "Not a Photo (8-11)")]:
    print(f"\n{name}:")
    for b_cat in top_breakdowns:
        print(f"  {b_cat}: {cross_tab[grp].get(b_cat, 0)}")

