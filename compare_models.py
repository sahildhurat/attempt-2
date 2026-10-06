import json
import random
import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

units = []
with open('data/unified/help_community.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        units.append(json.loads(line))

random.seed(42)
sample = random.sample(units, 20)

prompt = """You are extracting symptom-cause-fix triples from troubleshooting forum posts.
Extract the technical problem described and the solution if present.
Return JSON in this format:
{
  "triples": [
    {
      "symptom": "...",
      "cause": "...",
      "fix": "..."
    }
  ]
}
If no technical problem or solution is found, return {"triples": []}."""

results = []
for i, u in enumerate(sample):
    print(f"Processing unit {i+1}/20...")
    text = u.get('text', '')[:5000]
    
    try:
        r_flash = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=[prompt, text],
            config=genai.types.GenerateContentConfig(response_mime_type='application/json')
        )
        flash_res = r_flash.text
    except Exception as e:
        flash_res = str(e)
        
    time.sleep(3) # avoid rate limits
    
    try:
        r_pro = client.models.generate_content(
            model='gemini-3.1-pro-preview',
            contents=[prompt, text],
            config=genai.types.GenerateContentConfig(response_mime_type='application/json')
        )
        pro_res = r_pro.text
    except Exception as e:
        pro_res = str(e)
        
    time.sleep(3)
        
    results.append({
        'id': u['id'],
        'text': text,
        'flash': flash_res,
        'pro': pro_res
    })

with open('model_comparison.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)
print('Comparison done.')
