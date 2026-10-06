import json
import random
import re
from collections import Counter

def analyze_gaps():
    print("="*40)
    print("GAP 1: TARGET FIELD & PHOTO AGE")
    print("="*40)
    
    targets = []
    texts = []
    units = []
    
    with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            u = json.loads(line)
            units.append(u)
            ext = u.get('extraction', {})
            t = ext.get('target')
            if t:
                targets.append(t)
            texts.append(u.get('text', '') + ' ' + u.get('context', ''))
            
    print(f"Total units with a target field: {len(targets)}")
    unique_targets = list(set(targets))
    print(f"Unique target values: {len(unique_targets)}")
    
    print("\n30 Random Targets (Seed 42):")
    random.seed(42)
    sample = random.sample(unique_targets, min(30, len(unique_targets)))
    for i, t in enumerate(sample, 1):
        print(f"{i}. {t}")
        
    print("\nSignal for HOW OLD the photo was:")
    # Check if there is any explicit age/year mention in targets or text
    # Look for "years ago", 4-digit years between 1990 and 2026, "old photos", etc.
    year_pattern = re.compile(r'\b(199[0-9]|20[0-2][0-9])\b')
    ago_pattern = re.compile(r'\b\d+\s+years?\s+ago\b', re.IGNORECASE)
    
    target_year_count = sum(1 for t in targets if year_pattern.search(t))
    target_ago_count = sum(1 for t in targets if ago_pattern.search(t))
    
    print(f"Targets mentioning a year (e.g., 2018): {target_year_count}")
    print(f"Targets mentioning 'X years ago': {target_ago_count}")
    print("Conclusion: The signal is present in the free text of the target field but is sparse (only a subset explicitly state the age). The corpus does not have a dedicated structured field for 'photo age'.\n")

    print("="*40)
    print("GAP 2: SEARCH FORMULATION & WORKAROUNDS")
    print("="*40)
    
    search_strings = []
    
    # 1. Get the 41 "search term used" cues
    search_term_phrases = []
    try:
        with open('data/pass3/taxonomy_assignments.jsonl', 'r', encoding='utf-8') as f:
            for line in f:
                rec = json.loads(line)
                if rec.get('category') == 'search term used':
                    search_term_phrases.append(rec.get('phrase'))
    except Exception as e:
        pass
        
    # Find the actual quoted terms inside the cues if possible
    for phrase in search_term_phrases:
        matches = re.findall(r'["\'](.*?)["\']', phrase)
        if matches:
            search_strings.extend([m.lower().strip() for m in matches if m.strip()])
        else:
            # If no quotes, perhaps the phrase itself is the search term or describes it
            search_strings.append(phrase.lower().strip())
            
    # 2. Extract quoted queries from raw unit text
    # Look for things like: search for "term", searched 'term', typed "term"
    query_patterns = [
        r'(?:search(?:ed|ing)?\s+(?:for\s+)?)["\'](.*?)["\']',
        r'(?:type(?:d|s)?\s+)["\'](.*?)["\']',
        r'(?:quer(?:y|ies)\s+)["\'](.*?)["\']'
    ]
    
    for txt in texts:
        for pat in query_patterns:
            for match in re.findall(pat, txt, re.IGNORECASE):
                if match.strip() and len(match.strip()) < 50: # exclude long quoted sentences
                    search_strings.append(match.lower().strip())
                    
    # Deduplicate and clean
    unique_searches = set()
    for s in search_strings:
        # basic clean up
        cleaned = s.strip('.,?!;')
        if cleaned:
            unique_searches.add(cleaned)
            
    unique_searches = list(unique_searches)
    print(f"Distinct literal search strings found: {len(unique_searches)}")
    
    word_counts = Counter()
    is_noun_count = 0
    is_person_count = 0
    is_place_count = 0
    is_date_count = 0
    
    # Heuristics for classification
    # Single common noun: 1 word, purely alphabetic, all lowercase (we lowercased earlier)
    # Person: contains proper names (we'll just use a basic heuristic: in the original phrase, was it title cased? But we lowercased. Let's re-extract case-sensitive for heuristics)
    
    # Let's rebuild unique searches case-sensitive for better heuristics
    case_sensitive_searches = set()
    for phrase in search_term_phrases:
        matches = re.findall(r'["\'](.*?)["\']', phrase)
        if matches: case_sensitive_searches.update([m.strip() for m in matches if m.strip()])
    for txt in texts:
        for pat in query_patterns:
            for match in re.findall(pat, txt, re.IGNORECASE):
                if match.strip() and len(match.strip()) < 50:
                    case_sensitive_searches.add(match.strip())
                    
    # Let's map back to case sensitive
    final_searches = list(case_sensitive_searches)
    
    months = {'jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec',
              'january','february','march','april','june','july','august','september','october','november','december'}
              
    for s in final_searches:
        words = s.split()
        wc = len(words)
        if wc >= 5: word_counts['5+'] += 1
        else: word_counts[str(wc)] += 1
        
        # single common noun (1 word, strictly lower case in original text implies common noun, or just 1 word alphabetic)
        if wc == 1 and s.isalpha() and s.islower():
            is_noun_count += 1
            
        # date: contains numbers or month names
        if re.search(r'\d', s) or any(m in s.lower() for m in months):
            is_date_count += 1
            
        # person/place: contains Title Case words (and isn't a date)
        # rough heuristic
        if not re.search(r'\d', s) and any(w.istitle() for w in words):
            is_person_count += 1 # we combine person/place since without NLP it's hard to distinguish
            
    print(f"Word count distribution:")
    for k in sorted(word_counts.keys()):
        print(f"  {k} word(s): {word_counts[k]}")
        
    print(f"Single common nouns (approx heuristic): {is_noun_count}")
    print(f"Name a person/place (Title Case heuristic): {is_person_count}")
    print(f"Name a date (Numbers/Months heuristic): {is_date_count}")
    print("\n(Note: Counts are based on regex heuristics and serve as a baseline without NLP classification.)")

    print("\n--- Workaround & Breakdown Cross-Tabulation ---")
    
    # Load BW assignments
    bw_map = {'breakdown': {}, 'workaround': {}}
    try:
        with open('data/pass3/bw_assignments.jsonl', 'r', encoding='utf-8') as f:
            for line in f:
                rec = json.loads(line)
                field = rec.get('field')
                phrase = rec.get('phrase')
                cat = rec.get('category')
                bw_map[field][phrase] = cat
    except: pass
    
    reformulate_count = 0
    switch_route_count = 0
    abandon_count = 0
    other_wa_count = 0
    
    # Cross tabulation: breakdown_cat -> reformulate count
    cross_tab = Counter()
    
    for u in units:
        ext = u.get('extraction', {})
        b_phrase = ext.get('breakdown')
        b_phrase = b_phrase.strip() if b_phrase else ''
        w_phrase = ext.get('workaround')
        w_phrase = w_phrase.strip() if w_phrase else ''
        b_src = ext.get('breakdown_source')
        w_src = ext.get('workaround_source')
        
        if w_phrase and w_src == 'user':
            w_cat = bw_map['workaround'].get(w_phrase)
            
            if w_cat == 'reformulate the query':
                reformulate_count += 1
                if b_phrase and b_src == 'user':
                    b_cat = bw_map['breakdown'].get(b_phrase)
                    if b_cat: cross_tab[b_cat] += 1
            elif w_cat in ['try a different search route', 'switch interface or device', 'leave the app']:
                switch_route_count += 1
            elif w_cat == 'no workaround found':
                abandon_count += 1
            elif w_cat:
                other_wa_count += 1
                
    print(f"Reformulate query: {reformulate_count}")
    print(f"Switch route/device/leave: {switch_route_count}")
    print(f"Abandon (no workaround): {abandon_count}")
    print(f"Other/Unassigned workarounds: {other_wa_count}")
    
    print("\nCross-tabulation: Breakdowns driving 'Reformulate the query':")
    for b_cat, count in cross_tab.most_common():
        print(f"  {b_cat}: {count}")

if __name__ == '__main__':
    analyze_gaps()
