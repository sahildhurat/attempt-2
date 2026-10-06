import os
import json
import csv
import requests
import time
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
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    data = resp.json()
    usage = data.get("usage", {})
    in_tok = usage.get("input_tokens", 0)
    out_tok = usage.get("output_tokens", 0)
    content = data["content"][0]["text"]
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].strip()
    return json.loads(content).get("assignments", []), in_tok, out_tok

def main():
    # 1. Load taxonomy
    with open('taxonomy_confirmed.json', 'r', encoding='utf-8') as f:
        tax = json.load(f)
    categories = tax.get('fields', {}).get('cues', [])
    cats_str = "\n".join([f"- {c['name']}: {c.get('definition', '')}" for c in categories])
    
    # 2. Get 26 MEMORY phrases
    memory_phrases = []
    with open('data/pass3/forgotten_validation.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['gap_type'].strip().upper() == 'MEMORY':
                memory_phrases.append(row['phrase'].strip())
                
    # 3. Assign them
    print(f"Assigning {len(memory_phrases)} MEMORY gaps...")
    system_prompt = f'Assign each numbered phrase below to exactly one category, or "UNASSIGNED" if it genuinely does not fit.\nIf returning UNASSIGNED, also provide a short reason in a "reason" field.\n\nOutput format must be strictly JSON without any markdown formatting:\n{{\n  "assignments": [\n    {{"n": 1, "category": "string", "reason": "string (only if UNASSIGNED)"}},\n    ...\n  ]\n}}'
    taxonomy_prompt = f'Categories for "cues":\n{cats_str}'
    phrases_str = "\n".join([f"{i+1}. {p}" for i, p in enumerate(memory_phrases)])
    phrases_prompt = f"Phrases:\n{phrases_str}"
    prompt = f"{system_prompt}\n\n{taxonomy_prompt}\n\n{phrases_prompt}"
    
    assignments, in_tok, out_tok = call_haiku(prompt)
    cost = (in_tok / 1_000_000) * 1.00 + (out_tok / 1_000_000) * 5.00
    print(f"Batch cost: ${cost:.5f}")
    
    forgotten_counts = {}
    temporal_phrases = [
        "date/when the beer photo was taken",
        "when the photo was taken",
        "exact date or year of the photo",
        "the time the photo was taken",
        "no specific date or timeframe mentioned",
        "when the older photo was taken",
        "exact date of the photos",
        "the year the picture was taken",
        "correct original date/time photos were taken",
        "original metadata (date/time/location) of the recovered images",
    ]
    
    date_and_time_count = 0
    for a in assignments:
        cat = a.get("category", "UNASSIGNED")
        forgotten_counts[cat] = forgotten_counts.get(cat, 0) + 1
        n = a.get("n")
        phrase = memory_phrases[n-1]
        if cat == "date and time":
            date_and_time_count += 1
            
    print(f"date and time count in forgotten: {date_and_time_count}")
    
    # 4. Deduplicate remembered phrases from taxonomy_assignments_clean.jsonl
    remembered_counts = {}
    seen_phrases = set()
    with open('data/pass3/taxonomy_assignments_clean.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            rec = json.loads(line)
            phrase = rec.get("phrase")
            cat = rec.get("category")
            if phrase not in seen_phrases:
                seen_phrases.add(phrase)
                remembered_counts[cat] = remembered_counts.get(cat, 0) + 1
                
    # 5. Print merged table
    print("\nProvenance counts for 'cues' by category:")
    all_cats = set(remembered_counts.keys()).union(set(forgotten_counts.keys()))
    
    cat_stats = []
    for cat in all_cats:
        r = remembered_counts.get(cat, 0)
        f = forgotten_counts.get(cat, 0)
        cat_stats.append((cat, r, f, r+f))
        
    for cat, r, f, tot in sorted(cat_stats, key=lambda x: x[3], reverse=True):
        print(f"  {cat}: {r} remembered, {f} forgotten")

if __name__ == "__main__":
    main()
