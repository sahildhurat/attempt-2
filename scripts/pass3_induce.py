import json
import random
import asyncio
import os
from collections import Counter
from dotenv import load_dotenv

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "collectors"))
import network_utils

load_dotenv()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

async def call_gemini(prompt, text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "systemInstruction": {"parts": [{"text": prompt}]},
        "contents": [{"parts": [{"text": text}], "role": "user"}],
        "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}
    }
    
    session = network_utils.get_session()
    for attempt in range(5):
        try:
            resp = await asyncio.to_thread(network_utils.fetch_with_rate_limit, session, "POST", url, "gemini", json=payload)
            data = resp.json()
            if "candidates" in data and data["candidates"]:
                text_out = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_out)
        except Exception as e:
            if hasattr(e, "response") and e.response is not None and e.response.status_code == 429:
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(2)
    return None

async def run_induction(phrases):
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
    return await call_gemini(prompt, text_input)



async def main():
    units = []
    with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip(): units.append(json.loads(line))
            
    fields_data = {"cues": [], "target": [], "breakdown": [], "workaround": []}
    
    for u in units:
        ext = u.get("extraction", {})
        
        # Targets
        t = ext.get("target")
        if t and ext.get("target_source") == "user": fields_data["target"].append(t)
            
        # Breakdowns
        b = ext.get("breakdown")
        if b and ext.get("breakdown_source") == "user": fields_data["breakdown"].append(b)
            
        # Workarounds
        w = ext.get("workaround")
        if w and ext.get("workaround_source") == "user": fields_data["workaround"].append(w)
            
        # Cues
        for r in ext.get("remembered", []):
            if r.get("source") == "user":
                fields_data["cues"].append(r["cue"])
        for f in ext.get("forgotten", []):
            if f.get("gap_type") == "memory_gap" and f.get("source") == "user":
                fields_data["cues"].append(f["cue"])
                
    # Deduplicate phrases before induction
    for k in fields_data:
        fields_data[k] = list(set(fields_data[k]))
        
    print(f"Unique phrases for induction:")
    for k, v in fields_data.items():
        print(f"  {k}: {len(v)}")
        
    output_data = {
        "generated_date": "2026-10-01",
        "model": "gemini-3.6-flash",
        "fields": {}
    }
    
    for field, phrases in fields_data.items():
        if not phrases: continue
        
        print(f"Running 4 shuffles for {field}...")
        
        runs = {}
        for i in range(1, 5):
            rng = random.Random(i)
            shuffled_phrases = list(phrases)
            rng.shuffle(shuffled_phrases)
            print(f"  Run {i} starting...")
            res = await run_induction(shuffled_phrases)
            runs[f"run_{i}"] = res
            
        output_data["fields"][field] = runs
        
    with open("taxonomy_proposed.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    print("Induction complete. Results saved to taxonomy_proposed.json")

if __name__ == '__main__':
    asyncio.run(main())
