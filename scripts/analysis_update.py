import json
import csv
import collections

# 1. Near-empty units in gate_results.jsonl
gated_empty_stats = collections.defaultdict(int)
with open(r'd:\Attempt 2\data\gate_results.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        item = json.loads(line)
        text = item.get('text', '')
        if not text or len(text.strip()) < 20:
            dec = item.get('gate_decision', 'no')
            if dec in ('yes', 'partial'):
                gated_empty_stats[item.get('source', 'unknown')] += 1

print("--- 1. NEAR-EMPTY GATED (YES/PARTIAL) BY SOURCE ---")
for src, count in gated_empty_stats.items():
    print(f"{src}: {count}")
print()

# 2. Recompute agreement by length bands
bands = {'<100': [0, 0], '100-250': [0, 0], '250-500': [0, 0], '500+': [0, 0]}
key_data = {}
with open(r'd:\Attempt 2\data\blind_sample_key.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        item = json.loads(line)
        key_data[item['id']] = item

with open(r'd:\Attempt 2\data\blind_sample_60.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        uid = row['unit_id']
        my_label = row.get('my_label', '').strip().lower()
        text = row.get('text', '').strip()
        if not my_label or len(text) < 20:
            continue
            
        gate_label = key_data.get(uid, {}).get('gate_decision', '').lower()
        
        l = len(text)
        if l < 100: b = '<100'
        elif l <= 250: b = '100-250'
        elif l <= 500: b = '250-500'
        else: b = '500+'
        
        bands[b][1] += 1
        if my_label == gate_label:
            bands[b][0] += 1

print("--- 2. AGREEMENT BY LENGTH BAND (>=20 chars) ---")
for b, counts in bands.items():
    agrees, tot = counts
    pct = (agrees/tot*100) if tot > 0 else 0
    print(f"{b}: {agrees}/{tot} ({pct:.1f}%)")
print()

# 3. Apply content filter for headline numbers
pass_count_by_src = collections.defaultdict(int)
total_extracted = 0
grounded_remembered = 0
grounded_forgotten = 0

with open(r'd:\Attempt 2\data\pass2\extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        total_extracted += 1
        item = json.loads(line)
        
        extraction = item.get('extraction', item)
        # after pass2_checks, valid grounded cues are in extraction['remembered'] directly 
        # (the ones that didn't drop are kept there). Wait, my pass2_checks script replaced it 
        # with just the kept ones! Yes, 'kept' is assigned back to unit['remembered'] or unit['extraction']['remembered'].
        rem = extraction.get('remembered', [])
        
        # Check if they are actually grounded (Check 4 did this, so whatever is here is grounded).
        # We just need len(rem) > 0
        if len(rem) > 0:
            pass_count_by_src[item.get('source', 'unknown')] += 1
            grounded_remembered += len(rem)
            grounded_forgotten += len(extraction.get('forgotten', []))

print("--- 3. HEADLINE FILTER: AT LEAST ONE GROUNDED REMEMBERED CUE ---")
print(f"Total extracted units: {total_extracted}")
total_passed = sum(pass_count_by_src.values())
print(f"Total passing filter: {total_passed}")
for src, count in pass_count_by_src.items():
    print(f"  {src}: {count}")
print(f"Restated Cues (on restricted set):")
print(f"  Remembered: {grounded_remembered}")
print(f"  Forgotten: {grounded_forgotten}")
print()
