import json
import re

terms_to_check = ["filename", "edited", "videos", "map", "driver", "pink", "me", "Me"]

texts = []
with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip(): continue
        u = json.loads(line)
        texts.append(u.get('text', '') + ' ' + u.get('context', ''))

print("--- CONTEXT FOR ONE-WORD STRINGS ---")
for term in terms_to_check:
    found = False
    for txt in texts:
        # looking for quotes around the term
        matches = re.finditer(r'[\"\']' + re.escape(term) + r'[\"\']', txt, re.IGNORECASE)
        for match in matches:
            # extract surrounding sentence
            start = max(0, match.start() - 80)
            end = min(len(txt), match.end() + 80)
            snippet = txt[start:end].replace('\n', ' ')
            print(f'[{term}] ...{snippet}...')
            found = True
            break
        if found: break
