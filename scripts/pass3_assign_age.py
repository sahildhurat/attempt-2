import os
import json
import time
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
    
    # 10% duplicates for firmer measurement
    random.seed(42)
    k = max(1, int(len(unique_targets) * 0.10))
    dups = random.sample(unique_targets, k)
    all_targets = unique_targets + dups
    random.shuffle(all_targets)
    
    output_file = "data/pass3/age_assignments.jsonl"
    completed = []
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    completed.append(json.loads(line).get('phrase'))
                    
    pending = [p for p in all_targets if all_targets.count(p) > completed.count(p)]
    
    valid_categories = {"OLDER", "RECENT", "UNSTATED"}
    
    sys_p = (
        'Classify each numbered target phrase on one axis only: does the target reference a photo from the distant past, from recent months, or is age unstated?\n\n'
        'Categories:\n'
        '- OLDER: explicitly years back, a previous phone, a named past year, "old photos"\n'
        '- RECENT: days or weeks, "just took", "recently added"\n'
        '- UNSTATED: age is not mentioned\n\n'
        'Output format must be strictly JSON without any markdown formatting:\n'
        '{\n  "assignments": [\n    {"n": 1, "category": "OLDER"},\n    ...\n  ]\n}'
    )
    
    batch_size = 40
    out_f = open(output_file, "a", encoding="utf-8")
    total_in_tok = 0
    total_out_tok = 0
    
    retries = 0
    out_of_tax_rejections = 0
    
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i+batch_size]
        phrases_str = "\n".join([f"{j+1}. {p}" for j, p in enumerate(batch)])
        prompt = f"{sys_p}\n\nPhrases:\n{phrases_str}"
        
        success = False
        for attempt in range(2):
            if attempt > 0: 
                time.sleep(2)
                retries += 1
                
            assignments, in_tok, out_tok, err = call_haiku(prompt)
            if err: continue
            
            if assignments is None or len(assignments) != len(batch):
                continue
                
            # Integrity guard
            valid_batch = True
            expected_n = set(range(1, len(batch) + 1))
            got_n = set()
            
            for a in assignments:
                cat = a.get("category", "")
                n = a.get("n", 0)
                got_n.add(n)
                if cat not in valid_categories:
                    out_of_tax_rejections += 1
                    valid_batch = False
                    break
                    
            if got_n != expected_n:
                valid_batch = False
                
            if valid_batch:
                total_in_tok += in_tok
                total_out_tok += out_tok
                
                assignments.sort(key=lambda x: x.get("n", 0))
                
                for idx, a in enumerate(assignments):
                    rec = {
                        "phrase": batch[idx],
                        "category": a.get("category", "UNSTATED")
                    }
                    out_f.write(json.dumps(rec) + "\n")
                out_f.flush()
                print(f"Batch {i//batch_size + 1} written.")
                success = True
                break
                
        if not success:
            print(f"Batch {i//batch_size + 1} failed after retries.")
            for p in batch:
                out_f.write(json.dumps({"phrase": p, "category": "UNSTATED"}) + "\n")
                
    out_f.close()
    
    total_cost = (total_in_tok / 1_000_000) * 1.00 + (total_out_tok / 1_000_000) * 5.00
    print(f"\nCost: ${total_cost:.5f}")
    
    assignments_by_cat = {}
    dup_assignments = {}
    
    with open(output_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            rec = json.loads(line)
            p = rec.get('phrase')
            c = rec.get('category')
            
            if p not in dup_assignments:
                dup_assignments[p] = []
                assignments_by_cat[c] = assignments_by_cat.get(c, 0) + 1
            dup_assignments[p].append(c)
            
    consistent = 0
    total_dups = 0
    for p, cats in dup_assignments.items():
        if len(cats) > 1:
            total_dups += 1
            if len(set(cats)) == 1:
                consistent += 1
                
    if total_dups > 0:
        c_rate = consistent/total_dups*100
        print(f"Duplicate consistency: {consistent}/{total_dups} ({c_rate:.2f}%)")
        
    print("\nPer-category counts:")
    for c, count in sorted(assignments_by_cat.items(), key=lambda x: x[1], reverse=True):
        print(f"  {c}: {count}")

if __name__ == '__main__':
    main()
