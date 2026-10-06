import json
import random
import os
import requests

from dotenv import load_dotenv

load_dotenv()
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")

def estimate_cost(input_tokens, output_tokens):
    in_cost = (input_tokens / 1_000_000) * 3.00
    out_cost = (output_tokens / 1_000_000) * 15.00
    return in_cost + out_cost

def call_anthropic(prompt, text, retries=3):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": "claude-sonnet-5",
        "max_tokens": 4096,
        "system": prompt,
        "messages": [
            {"role": "user", "content": text}
        ]
    }
    
    for attempt in range(retries):
        resp = requests.post(url, headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except Exception as e:
            print(f"HTTP Error: {resp.status_code}")
            print(resp.text)
            raise e
        data = resp.json()
        
        usage = data.get("usage", {})
        in_tokens = usage.get("input_tokens", 0)
        out_tokens = usage.get("output_tokens", 0)
        
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content = block.get("text", "")
                break
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        try:
            parsed = json.loads(content)
            return parsed, in_tokens, out_tokens
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error on attempt {attempt+1}! Retrying...")
            if attempt == retries - 1:
                with open("error_raw.txt", "w", encoding="utf-8") as f:
                    f.write(content)
                raise e

def main():
    units = []
    with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip(): units.append(json.loads(line))
            
    fields_data = {"cues": [], "target": [], "breakdown": [], "workaround": []}
    
    for u in units:
        ext = u.get("extraction", {})
        
        # Only process cues as requested
        for r in ext.get("remembered", []):
            if r.get("source") == "user":
                fields_data["cues"].append(r["cue"])
        for f in ext.get("forgotten", []):
            if f.get("gap_type") == "memory_gap" and f.get("source") == "user":
                fields_data["cues"].append(f["cue"])
                
    # Deduplicate phrases before induction
    for k in fields_data:
        fields_data[k] = list(set(fields_data[k]))
        
    cues = fields_data["cues"]
    print(f"Total unique cues: {len(cues)}")
    
    # Rough estimate calculation
    est_chars = len(json.dumps(cues, indent=2))
    est_in_tokens = (est_chars / 4) * 4 # roughly 1 token per 4 chars
    est_out_tokens = 1000 * 4
    proj_cost = estimate_cost(est_in_tokens, est_out_tokens)
    
    print(f"Projected cost: ${proj_cost:.3f}")
    if proj_cost > 0.60:
        print("Projected cost exceeds $0.60. Stopping.")
        return
        
    prompt = '''You are a qualitative researcher building a taxonomy from a list of short phrases.

Group the phrases below into categories derived from the phrases themselves, not from any prior expectation about what categories should exist. Each phrase belongs to at most one category.

Each category must have:
1. A short, descriptive name (1-3 words).
2. A clear definition of what belongs in it.
3. Exactly 3 phrases from the list that belong to it.

Do not create a catch-all category such as "Other" or "Miscellaneous". You need not force every phrase into a category — phrases that do not fit any coherent group may be left unassigned.

Output format must be strictly JSON without any markdown formatting, unescaped newlines, or trailing commas:
{
  "categories": [
    {
      "name": "string",
      "definition": "string",
      "examples": ["string", "string", "string"]
    }
  ]
}
Ensure the output is valid JSON. Escape all inner quotes and do not use unescaped newlines inside strings.'''

    output_data = {
        "generated_date": "2026-10-01",
        "model": "claude-3-5-sonnet",
        "fields": {"cues": {}}
    }
    
    total_cost = 0.0
    runs = {}
    for i in range(1, 5):
        rng = random.Random(i)
        shuffled_phrases = list(cues)
        rng.shuffle(shuffled_phrases)
        
        text_input = "Phrases:\n" + json.dumps(shuffled_phrases, indent=2)
        print(f"Running shuffle {i}...")
        
        res, in_tok, out_tok = call_anthropic(prompt, text_input)
        cost = estimate_cost(in_tok, out_tok)
        total_cost += cost
        
        runs[f"run_{i}"] = res
        
    output_data["fields"]["cues"] = runs
    
    with open("taxonomy_proposed.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"Successfully completed 4 runs on Anthropic. Total cost: ${total_cost:.3f}")

if __name__ == '__main__':
    main()
