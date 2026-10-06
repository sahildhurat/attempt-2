import os
import json
import time
import argparse
import random
import requests
from dotenv import load_dotenv

load_dotenv()
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")

ERR_PARSE = "parse_error"
ERR_API = "api_error"

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
    except requests.exceptions.RequestException as e:
        return None, 0, 0, ERR_API
    except (json.JSONDecodeError, KeyError, IndexError):
        return None, 0, 0, ERR_PARSE

def get_unique_phrases():
    b = set()
    w = set()
    with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            d = json.loads(line).get('extraction', {})
            v_b = d.get('breakdown')
            if v_b: b.add(v_b.strip())
            v_w = d.get('workaround')
            if v_w: w.add(v_w.strip())
    return {'breakdown': sorted(list(b)), 'workaround': sorted(list(w))}

def run_analysis(output_file):
    if not os.path.exists(output_file):
        return
        
    print("\n" + "="*40)
    print("ANALYSIS RESULTS")
    print("="*40)
    
    assignments_by_field_cat = {'breakdown': {}, 'workaround': {}}
    dup_assignments = {'breakdown': {}, 'workaround': {}}
    unassigned_counts = {'breakdown': 0, 'workaround': 0}
    seen_phrases = {'breakdown': set(), 'workaround': set()}
    
    with open(output_file, 'r', encoding='utf-8') as f:
        for line in f:
            rec = json.loads(line)
            field = rec.get("field")
            phrase = rec.get("phrase")
            cat = rec.get("category")
            
            if field not in dup_assignments: continue
            
            if phrase not in dup_assignments[field]:
                dup_assignments[field][phrase] = []
                
                # count stats only on first occurrence
                seen_phrases[field].add(phrase)
                if cat == "UNASSIGNED":
                    unassigned_counts[field] += 1
                assignments_by_field_cat[field][cat] = assignments_by_field_cat[field].get(cat, 0) + 1
                    
            dup_assignments[field][phrase].append(cat)

    for field in ['breakdown', 'workaround']:
        tot = len(seen_phrases[field])
        if tot == 0: continue
        un_rate = unassigned_counts[field] / tot * 100
        print(f"\n[{field.upper()}] UNASSIGNED rate: {un_rate:.2f}% ({unassigned_counts[field]}/{tot})")
        
        print(f"\nCounts for '{field}' by category:")
        for cat, count in sorted(assignments_by_field_cat[field].items(), key=lambda x: x[1], reverse=True):
            flag = " (FLAG: < 5 phrases)" if count < 5 and cat != "UNASSIGNED" else ""
            print(f"  {cat}: {count}{flag}")
            
        consistent = 0
        total_dups = 0
        for p, cats in dup_assignments[field].items():
            if len(cats) > 1:
                total_dups += 1
                if len(set(cats)) == 1:
                    consistent += 1
                    
        if total_dups > 0:
            rate = consistent / total_dups * 100
            print(f"\nConsistency check: {consistent}/{total_dups} ({rate:.2f}%) duplicate assignments matched.")
            if rate < 75.0:
                print("WARNING: Duplicate consistency is below 75%. Categories may be bleeding into each other.")
                
    print("="*40 + "\n")

def main():
    tax_file = "taxonomy_confirmed_bw.json"
    with open(tax_file, "r", encoding="utf-8") as f:
        taxonomy = json.load(f)
        
    unique_phrases_by_field = get_unique_phrases()
    for field in ['breakdown', 'workaround']:
        print(f"Total unique {field} phrases: {len(unique_phrases_by_field[field])}")
        
    batch_size = 40
    print(f"Batch size: {batch_size}")
    
    output_file = "data/pass3/bw_assignments.jsonl"
    os.makedirs("data/pass3", exist_ok=True)
    
    completed_phrases_list = []
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    completed_phrases_list.append((rec.get("field"), rec.get("phrase")))
    
    MAX_ERRORS = 3
    MAX_RETRIES = 1
    
    global_stats = {
        'breakdown': {'in': 0, 'out': 0},
        'workaround': {'in': 0, 'out': 0}
    }
    total_in_tok = 0
    total_out_tok = 0
    
    for field in ['breakdown', 'workaround']:
        phrases = unique_phrases_by_field[field]
        if not phrases: continue
        
        # Inject duplicates (5%)
        random.seed(42 + len(field))
        k = max(1, int(len(phrases) * 0.05))
        dups = random.sample(phrases, k)
        all_phrases = phrases + dups
        random.shuffle(all_phrases)
        
        pending = [p for p in all_phrases if (field, p) not in completed_phrases_list]
        if not pending: continue
        
        print(f"Processing {len(pending)} phrases for {field}...")
        
        categories = taxonomy.get("fields", {}).get(field, [])
        cats_str = "\n".join([f"- {c['name']}: {c.get('definition', '')}" for c in categories])
        sys_p = f'Assign each numbered phrase below to exactly one category, or "UNASSIGNED" if it genuinely does not fit.\nIf returning UNASSIGNED, also provide a short reason in a "reason" field.\n\nOutput format must be strictly JSON without any markdown formatting:\n{{\n  "assignments": [\n    {{"n": 1, "category": "string", "reason": "string"}},\n    ...\n  ]\n}}'
        tax_p = f'Categories for "{field}":\n{cats_str}'
        
        out_f = open(output_file, "a", encoding="utf-8")
        consecutive_errors = 0
        batch_num = 0
        
        for i in range(0, len(pending), batch_size):
            batch = pending[i:i+batch_size]
            batch_num += 1
            global_stats[field]['in'] += len(batch)
            
            phrases_str = "\n".join([f"{j+1}. {p}" for j, p in enumerate(batch)])
            prompt = f"{sys_p}\n\n{tax_p}\n\nPhrases:\n{phrases_str}"
            
            success = False
            for attempt in range(MAX_RETRIES + 1):
                if attempt > 0: time.sleep(2)
                
                assignments, in_tok, out_tok, err = call_haiku(prompt)
                if not err and len(assignments) == len(batch):
                    total_in_tok += in_tok
                    total_out_tok += out_tok
                    for a in assignments:
                        idx = a.get("n", 0) - 1
                        if 0 <= idx < len(batch):
                            rec = {
                                "field": field,
                                "phrase": batch[idx],
                                "category": a.get("category", "UNASSIGNED"),
                            }
                            reason = a.get("reason")
                            if reason: rec["reason"] = reason
                            out_f.write(json.dumps(rec) + "\n")
                            global_stats[field]['out'] += 1
                    out_f.flush()
                    print(f"[{field}] Batch {batch_num} written.")
                    success = True
                    consecutive_errors = 0
                    break
                    
            if not success:
                print(f"[{field}] Batch {batch_num} failed completely.")
                consecutive_errors += 1
                for j, p in enumerate(batch):
                    rec = {
                        "field": field,
                        "phrase": p,
                        "category": "UNASSIGNED",
                        "reason": "fallback_after_api_failure"
                    }
                    out_f.write(json.dumps(rec) + "\n")
                    global_stats[field]['out'] += 1
                out_f.flush()
                
            if consecutive_errors >= MAX_ERRORS:
                print("FATAL: Too many consecutive errors. Aborting.")
                out_f.close()
                return
                
        out_f.close()
        
    print("\n--- BATCH RUN SUMMARY ---")
    for f in ['breakdown', 'workaround']:
        print(f"[{f}] Phrases In: {global_stats[f]['in']} | Assignments Out: {global_stats[f]['out']}")
    
    total_cost = (total_in_tok / 1_000_000) * 1.00 + (total_out_tok / 1_000_000) * 5.00
    print(f"Actual API Cost (Haiku): ${total_cost:.5f}")
    
    run_analysis(output_file)

if __name__ == "__main__":
    main()
