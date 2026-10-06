import json
import re

def classify_span(span):
    if not span:
        return "UNCLEAR"
    span_lower = span.lower()
    
    # ADVICE patterns
    advice_patterns = [
        r'\byou can\b', r'\byou could\b', r'\btry\b', r'\bhave you\b', 
        r'\bgo to\b', r'\bclick\b', r'\bopen\b', r'\bcheck\b', 
        r'\buse the\b', r"\bi'd suggest\b", r'\bi would recommend\b'
    ]
    
    for p in advice_patterns:
        if re.search(p, span_lower):
            return "ADVICE"
            
    # USER patterns
    user_patterns = [
        r'\bi\b', r'\bmy\b', r'\bme\b', r'\bwe\b', r'\bour\b'
    ]
    
    for p in user_patterns:
        if re.search(p, span_lower):
            return "USER"
            
    return "UNCLEAR"

units = []
with open('d:/Attempt 2/data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            units.append(json.loads(line))

cues_stats = {"USER": [], "ADVICE": [], "UNCLEAR": []}
target_stats = {"USER": 0, "ADVICE": 0, "UNCLEAR": 0}
breakdown_stats = {"USER": 0, "ADVICE": 0, "UNCLEAR": 0}
workaround_stats = {"USER": 0, "ADVICE": 0, "UNCLEAR": 0}

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
        
    # Also tag forgotten
    for f in ext.get('forgotten', []):
        cls = classify_span(f.get('span', ''))
        f['source'] = cls.lower()

# Write tagged data back
with open('d:/Attempt 2/data/pass2/extracted_units.jsonl', 'w', encoding='utf-8') as f:
    for u in units:
        f.write(json.dumps(u) + '\n')

with open('d:/Attempt 2/scratch/classification_results.txt', 'w', encoding='utf-8') as f:
    f.write("=== CUES STATS ===\n")
    for cls in ["USER", "ADVICE", "UNCLEAR"]:
        f.write(f"{cls}: {len(cues_stats[cls])}\n")
        
    f.write("\n=== 15 EXAMPLES EACH ===\n")
    for cls in ["USER", "ADVICE", "UNCLEAR"]:
        f.write(f"\n[{cls} EXAMPLES]\n")
        for cue, span in cues_stats[cls][:15]:
            f.write(f"CUE: {cue}\nSPAN: {span}\n\n")
            
    f.write("\n=== UNCLEAR EXHAUSTIVE LIST (if <= 30) ===\n")
    if len(cues_stats["UNCLEAR"]) <= 30:
        for cue, span in cues_stats["UNCLEAR"]:
            f.write(f"CUE: {cue}\nSPAN: {span}\n\n")
    else:
        f.write(f"More than 30 ({len(cues_stats['UNCLEAR'])}), skipping exhaustive list.\n")
            
    f.write("\n=== TARGET STATS ===\n")
    f.write(json.dumps(target_stats, indent=2) + "\n")
    f.write("\n=== BREAKDOWN STATS ===\n")
    f.write(json.dumps(breakdown_stats, indent=2) + "\n")
    f.write("\n=== WORKAROUND STATS ===\n")
    f.write(json.dumps(workaround_stats, indent=2) + "\n")
