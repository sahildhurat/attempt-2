import json, re

search_term_phrases = []
with open('data/pass3/taxonomy_assignments.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        if rec.get('category') == 'search term used':
            search_term_phrases.append(rec.get('phrase'))
            
cue_searches = set()
for phrase in search_term_phrases:
    matches = re.findall(r'["\'](.*?)["\']', phrase)
    if matches:
        cue_searches.update([m.strip() for m in matches if m.strip()])
    else:
        cue_searches.add(phrase.strip())

texts = []
with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip(): continue
        u = json.loads(line)
        texts.append(u.get('text', '') + ' ' + u.get('context', ''))

raw_searches = set()
query_patterns = [
    r'(?:search(?:ed|ing)?\s+(?:for\s+)?)["\'](.*?)["\']',
    r'(?:type(?:d|s)?\s+)["\'](.*?)["\']',
    r'(?:quer(?:y|ies)\s+)["\'](.*?)["\']'
]
for txt in texts:
    for pat in query_patterns:
        for match in re.findall(pat, txt, re.IGNORECASE):
            if match.strip() and len(match.strip()) < 50:
                raw_searches.add(match.strip())

all_searches = list(cue_searches.union(raw_searches))
from collections import defaultdict
grouped = defaultdict(list)
for s in all_searches:
    wc = len(s.split())
    grp = '5+' if wc >= 5 else str(wc)
    
    prov = []
    if s in cue_searches: prov.append('cue')
    if s in raw_searches: prov.append('raw')
    
    grouped[grp].append((s, " + ".join(prov)))

for grp in ['1', '2', '3', '4', '5+']:
    print(f"\n### {grp} word(s):")
    for s, p in sorted(grouped[grp]):
        print(f'- "{s}" ({p})')
