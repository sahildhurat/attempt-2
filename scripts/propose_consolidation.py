import os
import json
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
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    return resp.json()["content"][0]["text"]

def main():
    with open('taxonomy_haiku.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    out_file = 'docs/breakdown_workaround_consolidation.md'
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write("# Proposed Breakdown and Workaround Consolidation\n\n")
        f.write("This document proposes a consolidated taxonomy for the `breakdown` and `workaround` fields based on the four induction runs. It is for review only and has not yet been assigned against the corpus.\n\n")

    for field in ['breakdown', 'workaround']:
        print(f"Processing {field}...")
        
        # Gather all categories across runs
        runs = data.get(field, {})
        runs_text = ""
        for run_id, run_data in runs.items():
            runs_text += f"\n--- {run_id} ---\n"
            for cat in run_data.get('categories', []):
                runs_text += f"Category: {cat.get('name')}\n"
                runs_text += f"Definition: {cat.get('definition')}\n"
                runs_text += f"Examples: {'; '.join(cat.get('examples', []))[:200]}...\n"

        prompt = f"""
You are an expert qualitative researcher. I have run 4 independent topic induction passes over the '{field}' field from my qualitative data.
Because the induction was stochastic, the 4 runs produced overlapping and redundant categories that describe the exact same underlying concepts but with slightly different names or splits.

Your job is to read the categories generated across all 4 runs and CONSOLIDATE them into a single, clean proposed taxonomy of distinct concepts.
Merge categories that are semantically identical or heavily overlapping.

Here are the categories from the 4 runs:
{runs_text}

Output a Markdown document with:
1. An H2 heading for `{field}`
2. For each consolidated concept, provide:
   - **[Concept Name]**: A concise definition.
   - *Merged from*: (List the names of the original categories from the runs that map to this concept)
   - *Example phrases*: (Provide 2-3 short example phrases demonstrating this concept)

Make the definitions sharp and mutually exclusive. DO NOT USE ANY MARKDOWN CODE BLOCKS (no ```markdown). Just output the raw markdown text.
"""
        result = call_haiku(prompt)
        if "```markdown" in result:
            result = result.split("```markdown")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].strip()
            
        with open(out_file, 'a', encoding='utf-8') as f:
            f.write(result + "\n\n")
            
    print("Done.")

if __name__ == "__main__":
    main()
