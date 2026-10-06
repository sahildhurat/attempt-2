import os
import json
import time
import argparse
import random
import csv
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
        return None, in_tok, out_tok, ERR_PARSE

def get_unique_phrases():
    phrases = []
    # Grounded cues
    with open('data/pass3/cues_only.txt', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                phrases.append(line.strip())
                
    # Memory gaps
    with open('data/pass3/forgotten_validation.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['gap_type'].strip().upper() == 'MEMORY':
                phrases.append(row['phrase'].strip())
                
    return {'cues': sorted(list(set(phrases)))}

def get_provenance_sets():
    remembered = set()
    forgotten = set()
    
    with open('data/pass3/cues_only.txt', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                remembered.add(line.strip())
                
    with open('data/pass3/forgotten_validation.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['gap_type'].strip().upper() == 'MEMORY':
                forgotten.add(row['phrase'].strip())
                
    return remembered, forgotten

def run_analysis(output_file):
    if not os.path.exists(output_file):
        return
        
    print("\n" + "="*40)
    print("ANALYSIS RESULTS")
    print("="*40)
    
    remembered_set, forgotten_set = get_provenance_sets()
                    
    assignments_by_cat = {}
    total_unassigned = 0
    unassigned_by_field = {}
    field_totals = {}
    
    dup_assignments = {} # phrase -> list of categories
    seen_phrases = set()
    
    with open(output_file, 'r', encoding='utf-8') as f:
        for line in f:
            rec = json.loads(line)
            cat = rec.get("category")
            phrase = rec.get("phrase")
            field = rec.get("field")
            
            if phrase not in dup_assignments:
                dup_assignments[phrase] = []
                
                # Count stats ONLY on first occurrence of phrase
                seen_phrases.add(phrase)
                field_totals[field] = field_totals.get(field, 0) + 1
                if cat == "UNASSIGNED":
                    total_unassigned += 1
                    unassigned_by_field[field] = unassigned_by_field.get(field, 0) + 1
                    
                if field == 'cues':
                    if cat not in assignments_by_cat:
                        assignments_by_cat[cat] = {'remembered': 0, 'forgotten': 0}
                    if phrase in remembered_set:
                        assignments_by_cat[cat]['remembered'] += 1
                    if phrase in forgotten_set:
                        assignments_by_cat[cat]['forgotten'] += 1
                        
            dup_assignments[phrase].append(cat)

    total_phrases_processed = sum(field_totals.values())
    if total_phrases_processed > 0:
        print(f"Overall UNASSIGNED rate: {total_unassigned / total_phrases_processed * 100:.2f}%")
        for fld, tot in field_totals.items():
            rate = unassigned_by_field.get(fld, 0) / tot * 100
            print(f"Field '{fld}' UNASSIGNED rate: {rate:.2f}% ({unassigned_by_field.get(fld, 0)}/{tot})")
            
    print("\nProvenance counts for 'cues' by category:")
    for cat, counts in sorted(assignments_by_cat.items(), key=lambda x: (x[1]['remembered']+x[1]['forgotten']), reverse=True):
        print(f"  {cat}: {counts['remembered']} remembered, {counts['forgotten']} forgotten")
        
    print("\nCategories with fewer than 5 phrases:")
    for cat, counts in assignments_by_cat.items():
        if (counts['remembered'] + counts['forgotten']) < 5:
            print(f"  FLAG: '{cat}' has fewer than 5 phrases.")
            
    consistent = 0
    total_dups = 0
    for p, cats in dup_assignments.items():
        if len(cats) > 1:
            total_dups += 1
            if len(set(cats)) == 1:
                consistent += 1
                
    if total_dups > 0:
        print(f"\nConsistency check: {consistent}/{total_dups} ({consistent/total_dups*100:.2f}%) duplicate assignments matched.")
    print("="*40 + "\n")

def load_taxonomy(tax_file):
    if not os.path.exists(tax_file):
        raise FileNotFoundError(f"{tax_file} is required.")
    with open(tax_file, "r", encoding="utf-8") as f:
        tax_data = json.load(f)
    if not tax_data.get("confirmed_by"):
        raise ValueError(f"Invalid schema in {tax_file}: 'confirmed_by' is missing or empty. Human attestation is required.")
    return tax_data

def main():
    parser = argparse.ArgumentParser(description="Assign phrases to taxonomy categories.")
    parser.add_argument("--probe", action="store_true", help="Run a single probe batch to test and estimate costs.")
    args = parser.parse_args()

    tax_file = "taxonomy_confirmed.json"
    taxonomy = load_taxonomy(tax_file)
    
    unique_phrases_by_field = get_unique_phrases()
    total_phrases = sum(len(v) for v in unique_phrases_by_field.values())
    print(f"Total unique phrases in scope: {total_phrases}")
    
    batch_size = 40
    print(f"Batch size: {batch_size}")
    
    if args.probe:
        print("Running in PROBE mode...")
        field = 'cues'
        categories = taxonomy.get("fields", {}).get(field, [])
        cats_str = "\n".join([f"- {c['name']}: {c.get('definition', '')}" for c in categories])
        
        test_phrases = unique_phrases_by_field[field][:batch_size]
        phrases_str = "\n".join([f"{i+1}. {p}" for i, p in enumerate(test_phrases)])
        
        sys_p = f'Assign each numbered phrase below to exactly one category, or "UNASSIGNED" if it genuinely does not fit.\nIf returning UNASSIGNED, also provide a short reason in a "reason" field.\n\nOutput format must be strictly JSON without any markdown formatting:\n{{\n  "assignments": [\n    {{"n": 1, "category": "string", "reason": "string (only if UNASSIGNED)"}},\n    ...\n  ]\n}}'
        tax_p = f'Categories for "{field}":\n{cats_str}'
        phr_p = f"Phrases:\n{phrases_str}"
        prompt = f"{sys_p}\n\n{tax_p}\n\n{phr_p}"
        
        assignments, in_tok, out_tok, err = call_haiku(prompt)
        if err:
            print(f"Probe failed with error: {err}")
            return
            
        cost = (in_tok / 1_000_000) * 1.00 + (out_tok / 1_000_000) * 5.00
        print(f"Probe successful! Cost: ${cost:.5f}")
        total_batches = (total_phrases * 1.05) / batch_size
        print(f"Extrapolated Cost for {int(total_phrases * 1.05)} phrases: ${cost * total_batches:.5f}")
        return

    print("Starting full assignment pass...")
    
    output_file = "data/pass3/taxonomy_assignments.jsonl"
    os.makedirs("data/pass3", exist_ok=True)
    
    completed_phrases_list = []
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    completed_phrases_list.append((rec.get("field"), rec.get("phrase")))
    
    consecutive_errors = 0
    MAX_ERRORS = 3
    MAX_RETRIES = 1
    
    global_phrases_in = 0
    global_assignments_out = 0
    global_fallback_unassigned = 0
    global_retries = 0
    total_in_tok = 0
    total_out_tok = 0
    
    for field, phrases in unique_phrases_by_field.items():
        if not phrases: continue
        
        # Inject duplicates
        random.seed(42)
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
        
        batch_num = 0
        for i in range(0, len(pending), batch_size):
            batch = pending[i:i+batch_size]
            batch_num += 1
            global_phrases_in += len(batch)
            
            phrases_str = "\n".join([f"{j+1}. {p}" for j, p in enumerate(batch)])
            prompt = f"{sys_p}\n\n{tax_p}\n\nPhrases:\n{phrases_str}"
            
            success = False
            for attempt in range(MAX_RETRIES + 1):
                if attempt > 0:
                    global_retries += 1
                    time.sleep(2)
                
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
                            global_assignments_out += 1
                    out_f.flush()
                    print(f"[{field}] Batch {batch_num}/{(len(pending)+batch_size-1)//batch_size} written.")
                    success = True
                    consecutive_errors = 0
                    break
                    
            if not success:
                print(f"[{field}] Batch {batch_num} failed completely. Emitting UNASSIGNED records.")
                consecutive_errors += 1
                for j, p in enumerate(batch):
                    rec = {
                        "field": field,
                        "phrase": p,
                        "category": "UNASSIGNED",
                        "reason": "fallback_after_api_failure"
                    }
                    out_f.write(json.dumps(rec) + "\n")
                    global_assignments_out += 1
                    global_fallback_unassigned += 1
                out_f.flush()
                
            if consecutive_errors >= MAX_ERRORS:
                print("FATAL: Too many consecutive errors. Aborting.")
                out_f.close()
                return
                
        out_f.close()
        
    print("\n--- BATCH RUN SUMMARY ---")
    print(f"Phrases In:                   {global_phrases_in}")
    print(f"Real Assignments Out:         {global_assignments_out}")
    print(f"Fallback UNASSIGNED Records:  {global_fallback_unassigned}")
    print(f"Retries Used:                 {global_retries}")
    
    total_cost = (total_in_tok / 1_000_000) * 1.00 + (total_out_tok / 1_000_000) * 5.00
    print(f"Actual API Cost (Haiku):      ${total_cost:.5f}")
    
    run_analysis(output_file)

if __name__ == "__main__":
    main()
