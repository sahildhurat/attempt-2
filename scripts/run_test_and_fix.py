import json
import csv
import collections

# 1 & 2: Fix the filter and denominator
pass_count_by_src = collections.defaultdict(int)
total_extracted = 0
grounded_remembered = 0
grounded_forgotten = 0

with open(r'd:\Attempt 2\data\pass2\extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        item = json.loads(line)
        text = item.get('text', '')
        
        if not text or len(text.strip()) < 20:
            continue
            
        total_extracted += 1
        
        extraction = item.get('extraction', item)
        rem = extraction.get('remembered', [])
        fgt = extraction.get('forgotten', [])
        
        if len(rem) > 0 or len(fgt) > 0:
            pass_count_by_src[item.get('source', 'unknown')] += 1
            grounded_remembered += len(rem)
            grounded_forgotten += len(fgt)

print("--- 1 & 2. FILTER FIX AND DENOMINATOR ---")
print(f"Total extracted units (excluding <20 chars): {total_extracted}")
total_passed = sum(pass_count_by_src.values())
print(f"Total passing filter (>=1 grounded cue of ANY kind): {total_passed}")
for src, count in pass_count_by_src.items():
    print(f"  {src}: {count}")
print(f"Restated Cues (on restricted set):")
print(f"  Remembered: {grounded_remembered}")
print(f"  Forgotten: {grounded_forgotten}")
print()

# 3. Filter validity test
key_data = {}
with open(r'd:\Attempt 2\data\blind_sample_key.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        item = json.loads(line)
        key_data[item['id']] = item

validity_units = []
with open(r'd:\Attempt 2\data\blind_sample_60.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        uid = row['unit_id']
        my_label = row.get('my_label', '').strip().lower()
        if not my_label or uid == 'a692b53b6907e644425d7b9c3eae7ce80c35e46e9c43336db946838ae2b2a514':
            continue
            
        gate_item = key_data.get(uid, {})
        gate_label = gate_item.get('gate_decision', '').lower()
        
        if my_label == 'no' and gate_label in ('yes', 'partial'):
            validity_units.append(uid)

produced_cue_count = 0
produced_no_cue_count = 0
found_units = set()

with open(r'd:\Attempt 2\data\pass2\extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        item = json.loads(line)
        if item['id'] in validity_units:
            found_units.add(item['id'])
            extraction = item.get('extraction', item)
            rem = extraction.get('remembered', [])
            fgt = extraction.get('forgotten', [])
            if len(rem) > 0 or len(fgt) > 0:
                produced_cue_count += 1
            else:
                produced_no_cue_count += 1
                
produced_no_cue_count += len(validity_units) - len(found_units)

print("--- 3. FILTER VALIDITY TEST ---")
print(f"15 units evaluated (Gate = yes/partial, Human = no):")
print(f"Produced >=1 grounded cue: {produced_cue_count}")
print(f"Produced 0 grounded cues : {produced_no_cue_count}")
print()
