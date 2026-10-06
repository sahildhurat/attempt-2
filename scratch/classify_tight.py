import json
import re
import random

def classify_span(span):
    if not span:
        return "USER"
    
    span_lower = span.lower().strip()
    
    # Check for first person pronouns before the advice phrase
    user_pattern = re.compile(r'\b(i|my|me|we|our)\b')
    
    advice_phrases = [
        r"you can", r"you could", r"you should", r"you need to", r"you'd", r"you will",
        r"try ", r"have you", r"did you", r"i'd suggest", r"i would suggest",
        r"i'd recommend", r"i would recommend", r"make sure", r"check if", r"go to"
    ]
    
    for p in advice_phrases:
        # Match if the phrase appears at the very beginning (ignoring leading punctuation/spaces)
        match = re.search(r'^[^a-z0-9]*(' + p + r')', span_lower)
        if match:
            # Technically if it starts with it, there is no preceding first person pronoun.
            # But just in case, check substring before match.
            prefix = span_lower[:match.start()]
            if not user_pattern.search(prefix):
                return "HELPER"
                
    return "USER"

units = []
with open('d:/Attempt 2/data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            units.append(json.loads(line))

cues_stats = {"USER": [], "HELPER": []}
target_stats = {"USER": 0, "HELPER": 0}
breakdown_stats = {"USER": 0, "HELPER": 0}
workaround_stats = {"USER": 0, "HELPER": 0}

for u in units:
    ext = u.get('extraction', {})
    
    # Target
    target = ext.get('target')
    target_quote = ext.get('evidence_quote', '')
    if target:
        cls = classify_span(target_quote)
        ext['target_source'] = cls.lower()
        target_stats[cls] += 1
        
    # Breakdown
    breakdown = ext.get('breakdown')
    breakdown_quote = ext.get('breakdown_quote', '')
    if breakdown:
        cls = classify_span(breakdown_quote)
        ext['breakdown_source'] = cls.lower()
        breakdown_stats[cls] += 1
        
    # Workaround
    workaround = ext.get('workaround')
    workaround_quote = ext.get('workaround_quote', '')
    if workaround:
        cls = classify_span(workaround_quote)
        ext['workaround_source'] = cls.lower()
        workaround_stats[cls] += 1

    # Cues (remembered only for this classification stat)
    for r in ext.get('remembered', []):
        cls = classify_span(r.get('span', ''))
        r['source'] = cls.lower()
        cues_stats[cls].append((r['cue'], r['span']))
        
    # Tag forgotten
    for f in ext.get('forgotten', []):
        cls = classify_span(f.get('span', ''))
        f['source'] = cls.lower()

# Write tagged data back
with open('d:/Attempt 2/data/pass2/extracted_units.jsonl', 'w', encoding='utf-8') as f:
    for u in units:
        f.write(json.dumps(u) + '\n')

with open('d:/Attempt 2/scratch/classification_tight_results.txt', 'w', encoding='utf-8') as f:
    f.write("=== CUES STATS ===\n")
    for cls in ["USER", "HELPER"]:
        f.write(f"{cls}: {len(cues_stats[cls])}\n")
        
    f.write("\n=== HELPER CUES EXHAUSTIVE LIST ===\n")
    for cue, span in cues_stats["HELPER"]:
        f.write(f"CUE: {cue}\nSPAN: {span}\n\n")
        
    f.write("\n=== 50 RANDOM USER CUES ===\n")
    # Take 50 random user cues
    random.seed(42)
    sample = random.sample(cues_stats["USER"], min(50, len(cues_stats["USER"])))
    for cue, span in sample:
        f.write(f"CUE: {cue}\nSPAN: {span}\n\n")

    f.write("\n=== TARGET STATS ===\n")
    f.write(json.dumps(target_stats, indent=2) + "\n")
    f.write("\n=== BREAKDOWN STATS ===\n")
    f.write(json.dumps(breakdown_stats, indent=2) + "\n")
    f.write("\n=== WORKAROUND STATS ===\n")
    f.write(json.dumps(workaround_stats, indent=2) + "\n")
