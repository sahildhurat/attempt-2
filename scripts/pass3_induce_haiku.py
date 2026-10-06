import json
import random
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")

def call_haiku(prompt, text):
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
        "system": prompt,
        "messages": [
            {"role": "user", "content": text}
        ]
    }
    
    for attempt in range(5):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 429:
                time.sleep(5)
                continue
            if resp.status_code == 200:
                data = resp.json()
                content = data["content"][0]["text"]
                usage = data.get("usage", {})
                
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()
                    
                return json.loads(content), usage
        except Exception as e:
            time.sleep(2)
    return None, {}

def run_induction(phrases):
    prompt = '''You are a qualitative researcher building a taxonomy from a list of short phrases.

Group the phrases below into categories derived from the phrases themselves, not from any prior expectation about what categories should exist. Each phrase belongs to at most one category.

Each category must have:
1. A short, descriptive name (1-3 words).
2. A clear definition of what belongs in it.
3. Exactly 3 phrases from the list that belong to it.

Do not create a catch-all category such as "Other" or "Miscellaneous". You need not force every phrase into a category — phrases that do not fit any coherent group may be left unassigned.

Output format must be strictly JSON:
{
  "categories": [
    {
      "name": "string",
      "definition": "string",
      "examples": ["string", "string", "string"]
    }
  ]
}'''
    
    text_input = "Phrases:\n" + json.dumps(phrases, indent=2)
    return call_haiku(prompt, text_input)

def main():
    units = []
    with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip(): units.append(json.loads(line))
            
    fields_data = {"breakdown": set(), "workaround": set()}
    
    for u in units:
        ext = u.get("extraction", {})
            
        b = ext.get("breakdown")
        if b and ext.get("breakdown_source") == "user": fields_data["breakdown"].add(b)
            
        w = ext.get("workaround")
        if w and ext.get("workaround_source") == "user": fields_data["workaround"].add(w)
            
    for k in fields_data:
        fields_data[k] = sorted(list(fields_data[k]))
        
    print(f"Unique phrases for induction:")
    for k, v in fields_data.items():
        print(f"  {k}: {len(v)}")
        
    output_data = {}
    total_in = 0
    total_out = 0
    
    for field, phrases in fields_data.items():
        if not phrases: continue
        
        print(f"Running 4 shuffles for {field}...")
        
        runs = {}
        for i in range(1, 5):
            rng = random.Random(i)
            shuffled_phrases = list(phrases)
            rng.shuffle(shuffled_phrases)
            print(f"  Run {i} starting...")
            res, usage = run_induction(shuffled_phrases)
            if res:
                runs[f"run_{i}"] = res
                total_in += usage.get("input_tokens", 0)
                total_out += usage.get("output_tokens", 0)
            else:
                print(f"  Run {i} failed.")
            
        output_data[field] = runs
        
    with open("taxonomy_haiku.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    cost = (total_in / 1_000_000) * 1.00 + (total_out / 1_000_000) * 5.00
    print(f"Induction complete. Cost: ${cost:.5f}")

if __name__ == '__main__':
    main()
