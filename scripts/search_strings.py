import json
import re
from collections import Counter

targets = []
texts = []
with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip(): continue
        u = json.loads(line)
        texts.append(u.get('text', '') + ' ' + u.get('context', ''))

search_term_phrases = []
with open('data/pass3/taxonomy_assignments.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        if rec.get('category') == 'search term used':
            search_term_phrases.append(rec.get('phrase'))
            
case_sensitive_searches = set()
for phrase in search_term_phrases:
    matches = re.findall(r'["\'](.*?)["\']', phrase)
    if matches:
        case_sensitive_searches.update([m.strip() for m in matches if m.strip()])
    else:
        case_sensitive_searches.add(phrase.strip())
        
query_patterns = [
    r'(?:search(?:ed|ing)?\s+(?:for\s+)?)["\'](.*?)["\']',
    r'(?:type(?:d|s)?\s+)["\'](.*?)["\']',
    r'(?:quer(?:y|ies)\s+)["\'](.*?)["\']'
]

for txt in texts:
    for pat in query_patterns:
        for match in re.findall(pat, txt, re.IGNORECASE):
            if match.strip() and len(match.strip()) < 50:
                case_sensitive_searches.add(match.strip())

final_searches = list(case_sensitive_searches)
print('Total distinct:', len(final_searches))

wc = Counter()
noun = 0
person = 0
date = 0
months = {'jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec',
          'january','february','march','april','june','july','august','september','october','november','december'}
          
for s in final_searches:
    words = s.split()
    L = len(words)
    if L >= 5: wc['5+'] += 1
    else: wc[str(L)] += 1
    
    if L == 1 and s.isalpha() and s.islower(): noun += 1
    if re.search(r'\d', s) or any(m in s.lower() for m in months): date += 1
    if not re.search(r'\d', s) and any(w.istitle() for w in words): person += 1
    
for k in sorted(wc.keys()): print(f'{k}: {wc[k]}')
print('Nouns:', noun)
print('Person/Place:', person)
print('Date:', date)
