import os
import json
import time
import argparse
import random
import requests
from dotenv import load_dotenv

load_dotenv()
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")

def call_haiku(prompt):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 4096,
        "thinking": {"type": "disabled"},
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage", {})
        in_tok = usage.get("input_tokens", 0)
        out_tok = usage.get("output_tokens", 0)
        
        content = data["content"][0]["text"]
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        parsed = json.loads(content)
        return parsed.get("assignments", []), in_tok, out_tok, None
    except Exception as e:
        return None, 0, 0, str(e)

def main():
    tax_file = "taxonomy_confirmed_target.json"
    with open(tax_file, "r", encoding="utf-8") as f:
        taxonomy = json.load(f)
        
    targets = []
    with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            u = json.loads(line)
            t = u.get('extraction', {}).get('target')
            if t:
                targets.append(t.strip())
                
    unique_targets = sorted(list(set(targets)))
    print(f"Total unique targets: {len(unique_targets)}")
    
    random.seed(42)
    k = max(1, int(len(unique_targets) * 0.05))
    dups = random.sample(unique_targets, k)
    all_targets = unique_targets + dups
    random.shuffle(all_targets)
    
    output_file = "data/pass3/target_assignments.jsonl"
    completed = []
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    completed.append(json.loads(line).get('phrase'))
                    
    pending = [p for p in all_targets if all_targets.count(p) > completed.count(p)]
    
    categories = taxonomy.get("fields", {}).get("target", [])
    cats_str = "\n".join([f"- {c['name']}: {c.get('definition', '')}" for c in categories])
    sys_p = 'Assign each numbered phrase below to exactly one category, or "UNASSIGNED" if it genuinely does not fit.\nIf returning UNASSIGNED, also provide a short reason in a "reason" field.\n\nOutput format must be strictly JSON without any markdown formatting:\n{\n  "assignments": [\n    {"n": 1, "category": "string", "reason": "string"},\n    ...\n  ]\n}'
    tax_p = f'Categories for "target":\n{cats_str}'
    
    batch_size = 40
    out_f = open(output_file, "a", encoding="utf-8")
    total_in_tok = 0
    total_out_tok = 0
    out_count = 0
    
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i+batch_size]
        phrases_str = "\n".join([f"{j+1}. {p}" for j, p in enumerate(batch)])
        prompt = f"{sys_p}\n\n{tax_p}\n\nPhrases:\n{phrases_str}"
        
        success = False
        for attempt in range(2):
            if attempt > 0: time.sleep(2)
            assignments, in_tok, out_tok, err = call_haiku(prompt)
            if not err and len(assignments) == len(batch):
                total_in_tok += in_tok
                total_out_tok += out_tok
                for a in assignments:
                    idx = a.get("n", 0) - 1
                    if 0 <= idx < len(batch):
                        rec = {
                            "phrase": batch[idx],
                            "category": a.get("category", "UNASSIGNED")
                        }
                        out_f.write(json.dumps(rec) + "\n")
                        out_count += 1
                out_f.flush()
                print(f"Batch {i//batch_size + 1} written.")
                success = True
                break
        if not success:
            print(f"Batch {i//batch_size + 1} failed.")
            for p in batch:
                out_f.write(json.dumps({"phrase": p, "category": "UNASSIGNED"}) + "\n")
                out_count += 1
                
    out_f.close()
    
    total_cost = (total_in_tok / 1_000_000) * 1.00 + (total_out_tok / 1_000_000) * 5.00
    print(f"\nCost: ${total_cost:.5f}")
    
    # Analysis
    assignments_by_cat = {}
    dup_assignments = {}
    unassigned = 0
    seen = set()
    
    with open(output_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            rec = json.loads(line)
            p = rec.get('phrase')
            c = rec.get('category')
            
            if p not in dup_assignments:
                dup_assignments[p] = []
                seen.add(p)
                assignments_by_cat[c] = assignments_by_cat.get(c, 0) + 1
                if c == "UNASSIGNED":
                    unassigned += 1
            dup_assignments[p].append(c)
            
    tot = len(seen)
    un_rate = unassigned / tot * 100
    print(f"UNASSIGNED rate: {un_rate:.2f}% ({unassigned}/{tot})")
    
    consistent = 0
    total_dups = 0
    for p, cats in dup_assignments.items():
        if len(cats) > 1:
            total_dups += 1
            if len(set(cats)) == 1:
                consistent += 1
                
    if total_dups > 0:
        print(f"Duplicate consistency: {consistent}/{total_dups} ({consistent/total_dups*100:.2f}%)")
        
    print("\nPer-category counts:")
    cat_names = [c['name'] for c in categories]
    cat_1_7 = cat_names[0:7]
    cat_8_11 = cat_names[7:11]
    
    group_1_7_count = 0
    group_8_11_count = 0
    
    for c, count in sorted(assignments_by_cat.items(), key=lambda x: x[1], reverse=True):
        print(f"  {c}: {count}")
        if c in cat_1_7: group_1_7_count += count
        if c in cat_8_11: group_8_11_count += count
        
    print(f"\nRollups:")
    print(f"Categories 1-7 ('a photo'): {group_1_7_count} ({group_1_7_count/tot*100:.1f}%)")
    print(f"Categories 8-11 ('not a photo'): {group_8_11_count} ({group_8_11_count/tot*100:.1f}%)")
    
    # Cross tabulation against breakdown
    # Load BW assignments
    bw_map = {}
    if os.path.exists('data/pass3/bw_assignments.jsonl'):
        with open('data/pass3/bw_assignments.jsonl', 'r', encoding='utf-8') as f:
            for line in f:
                rec = json.loads(line)
                if rec.get('field') == 'breakdown':
                    bw_map[rec.get('phrase')] = rec.get('category')
                    
    # Target map (unique to a category)
    target_map = {p: cats[0] for p, cats in dup_assignments.items()}
                    
    cross_tab = {} # cross_tab[target_cat][breakdown_cat] = count
    
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
                t_cat = target_map.get(t)
                b_cat = bw_map.get(b)
                if t_cat and b_cat:
                    if t_cat not in cross_tab:
                        cross_tab[t_cat] = {}
                    cross_tab[t_cat][b_cat] = cross_tab[t_cat].get(b_cat, 0) + 1
                    
    print("\nCross-tabulation (Target Category -> Breakdown Category):")
    for t_cat in sorted(cross_tab.keys()):
        print(f"\n[{t_cat}]")
        for b_cat, count in sorted(cross_tab[t_cat].items(), key=lambda x: x[1], reverse=True):
            print(f"  {b_cat}: {count}")

if __name__ == '__main__':
    main()
