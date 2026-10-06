import json
with open('data/pass2/extracted_units.jsonl', encoding='utf-8') as f:
    units=[json.loads(l) for l in f if l.strip()]
print(f'Extracted: {len(units)}')
models=[u.get('extraction',{}).get('extraction_model') for u in units]
print(f'claude: {models.count("claude-sonnet-5")}')
print(f'gemini: {models.count("gemini-3.6-flash")}')
