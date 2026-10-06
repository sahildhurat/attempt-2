import os
import json
import random
import time
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
    
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    content = data["content"][0]["text"]
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].strip()
    return content

def call_haiku_text(prompt):
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
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    return resp.json()["content"][0]["text"]

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
    
    runs = {}
    print(f"Total unique targets: {len(unique_targets)}")
    
    for i in range(1, 5):
        print(f"Run {i} starting...")
        random.seed(42 + i)
        shuffled = unique_targets[:]
        random.shuffle(shuffled)
        
        phrases_str = "\n".join([f"- {p}" for p in shuffled])
        prompt = f"""
You are an expert qualitative researcher. Your task is to induce a taxonomy of categories from the following list of 'target' values extracted from a user feedback corpus.
These values describe the specific photos or items users were trying to retrieve.
Create a set of distinct concepts that categorize *what kind of photo/item* the user was looking for (e.g., specific person, specific event, specific document, specific location, etc.).
Ensure categories are mutually exclusive. Group specific instances into broader concepts.
Output ONLY valid JSON matching this schema:
{{
  "categories": [
    {{
      "name": "lowercase short name",
      "definition": "Clear concise definition",
      "examples": ["example 1", "example 2"]
    }}
  ]
}}

Phrases:
{phrases_str}
"""
        try:
            res = call_haiku(prompt)
            data = json.loads(res)
            runs[f"run_{i}"] = data
            print(f"Run {i} yielded {len(data.get('categories', []))} categories.")
        except Exception as e:
            print(f"Error on run {i}: {e}")
            runs[f"run_{i}"] = {"categories": []}
            
    with open('data/pass3/target_induction.json', 'w', encoding='utf-8') as f:
        json.dump(runs, f, indent=2)
        
    print("Generating consolidation...")
    runs_text = ""
    for run_id, run_data in runs.items():
        runs_text += f"\n--- {run_id} ---\n"
        for cat in run_data.get('categories', []):
            runs_text += f"Category: {cat.get('name')}\n"
            runs_text += f"Definition: {cat.get('definition')}\n"
            runs_text += f"Examples: {'; '.join(cat.get('examples', []))[:200]}...\n"
            
    consolidation_prompt = f"""
You are an expert qualitative researcher. I ran 4 induction passes over 'target' values indicating what kind of photos users struggle to retrieve.
Consolidate the overlapping categories from these 4 runs into a single, clean proposed taxonomy of distinct concepts.

Here are the categories:
{runs_text}

Output a Markdown document with:
1. An H2 heading for `target`
2. For each consolidated concept, provide:
   - **[Concept Name]**: A concise definition.
   - *Merged from*: (Original category names)
   - *Example phrases*: (2-3 short example phrases)

Do not use Markdown code blocks for the output text itself, just output raw markdown text.
"""
    result = call_haiku_text(consolidation_prompt)
    if "```markdown" in result:
        result = result.split("```markdown")[1].split("```")[0].strip()
    elif "```" in result:
        result = result.split("```")[1].strip()
        
    with open('docs/target_consolidation.md', 'w', encoding='utf-8') as f:
        f.write("# Proposed Target Taxonomy Consolidation\n\n" + result + "\n")
        
    print("Done generating consolidation.")

if __name__ == '__main__':
    main()
