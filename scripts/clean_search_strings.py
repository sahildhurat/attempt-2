import json
import re
from collections import defaultdict

# 1. Load cue phrases
search_term_phrases = []
with open('data/pass3/taxonomy_assignments.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        if rec.get('category') == 'search term used':
            search_term_phrases.append(rec.get('phrase'))

# 2. Extract searches from cues
cue_searches = set()
for phrase in search_term_phrases:
    # Look for quoted strings
    matches = []
    matches.extend(re.findall(r'"([^"]*)"', phrase))
    matches.extend(re.findall(r"'([^']*)'", phrase))
    if matches:
        cue_searches.update([m.strip() for m in matches if m.strip()])
    else:
        cue_searches.add(phrase.strip())

# 3. Load raw texts
texts = []
with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip(): continue
        u = json.loads(line)
        texts.append(u.get('text', '') + ' ' + u.get('context', ''))

# 4. Extract searches from raw text using better regex
raw_searches = set()
# Search for patterns like: searched for "foo", typed 'bar', queried "baz"
# using double quotes or single quotes properly paired
patterns = [
    r'(?:search(?:ed|ing)?\s+(?:for\s+)?)?"([^"]+)"',
    r"(?:search(?:ed|ing)?\s+(?:for\s+)?)?'([^']+)'",
    r'(?:type(?:d|s)?\s+)"([^"]+)"',
    r"(?:type(?:d|s)?\s+)?'([^']+)'",
    r'(?:quer(?:y|ies)\s+)"([^"]+)"',
    r"(?:quer(?:y|ies)\s+)?'([^']+)'"
]
for txt in texts:
    # Use explicit double quotes, or single quotes that have spaces or boundaries around them
    # to avoid matching contractions like didn't -> 't'
    for match in re.finditer(r'(search|type|query)[^"\']*?"([^"]+)"', txt, re.IGNORECASE):
        q = match.group(2)
        if q and len(q.strip()) < 50:
            raw_searches.add(q.strip())
    # For single quotes, only match if it looks like a real quoted string (e.g. preceded and followed by non-word chars)
    for match in re.finditer(r"(search|type|query)[^'\"]*?'([^']+)'(?!\w)", txt, re.IGNORECASE):
        q = match.group(2)
        if q and len(q.strip()) < 50 and not q.startswith('t '):
            raw_searches.add(q.strip())

all_searches = list(cue_searches.union(raw_searches))

# 5. Filter out meta-descriptions
meta_phrases = [
    "a keyword related to the photo",
    "a specific search term that isolates the desired images",
    "correct search words/keywords for the content",
    "first names of people/pets used in search",
    "other keywords that successfully find the same photos",
    "own screenname as search term",
    "partial word match attempt (Boyfriend for boyfriendtv)",
    "person's name used as search term",
    "search terms used to find matching photos",
    "searched by a specific person's name",
    "the exact number/digits they were searching for",
    "the exact word typed into the photo description",
    "the search keyword/term used",
    "searched a person's name",
    "searched by year",
    "search keyword/topic"
]
# Let's also remove the stray tokens we identified
stray_tokens = ["filename", "map", "videos", "WA", "QR", "03-15", "A71"] # some look like model numbers or dates? We will keep those if they are valid queries.
# Wait, "filename" was a stray instructional token. "map" was naming the UI section. "videos" was UI section. 

# We will classify them properly
clean_searches = []
meta_count = 0
stray_count = 0
for s in all_searches:
    s_lower = s.lower()
    is_meta = False
    for m in meta_phrases:
        if m.lower() in s_lower:
            is_meta = True
            break
    if is_meta:
        meta_count += 1
        continue
        
    if s.lower() in ['filename', 'map', 'videos']:
        stray_count += 1
        continue
        
    clean_searches.append(s)

print(f"Total entries (including meta & stray): {len(all_searches)}")
print(f"Meta-descriptions removed: {meta_count}")
print(f"Stray tokens removed: {stray_count}")
print(f"Literal verbatim strings only: {len(clean_searches)}")

from collections import defaultdict
grouped = defaultdict(list)
wc_dist = {'1':0, '2':0, '3':0, '4':0, '5+':0}
for s in clean_searches:
    wc = len(s.split())
    grp = '5+' if wc >= 5 else str(wc)
    wc_dist[grp] += 1
    prov = []
    if s in cue_searches: prov.append('cue')
    if s in raw_searches: prov.append('raw')
    grouped[grp].append((s, " + ".join(prov)))

print("\nWord count distribution for literal verbatim strings:")
for k in ['1', '2', '3', '4', '5+']:
    print(f"  {k} word(s): {wc_dist[k]}")
    
print("\n--- LITERAL STRINGS ---")
for grp in ['1', '2', '3', '4', '5+']:
    print(f"\n### {grp} word(s):")
    for s, p in sorted(grouped[grp], key=lambda x: x[0].lower()):
        print(f'- "{s}" ({p})')
