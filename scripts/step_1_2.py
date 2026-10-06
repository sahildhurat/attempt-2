import json
import csv

# 1. Re-run Filter Test
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
            
        gate_label = key_data.get(uid, {}).get('gate_decision', '').lower()
        
        if my_label == 'no' and gate_label in ('yes', 'partial'):
            validity_units.append(uid)

a_not_present = 0
b_present_with_cue = 0
c_present_no_cue = 0

extracted_uids = {}
with open(r'd:\Attempt 2\data\pass2\extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        item = json.loads(line)
        extraction = item.get('extraction', item)
        rem = extraction.get('remembered', [])
        fgt = extraction.get('forgotten', [])
        
        has_cue = (len(rem) > 0 or len(fgt) > 0)
        extracted_uids[item['id']] = has_cue

for uid in validity_units:
    if uid not in extracted_uids:
        a_not_present += 1
    else:
        if extracted_uids[uid]:
            b_present_with_cue += 1
        else:
            c_present_no_cue += 1

print("--- 1. FILTER VALIDITY TEST ---")
print(f"Total 15 units:")
print(f"(a) NOT PRESENT in extracted_units.jsonl: {a_not_present}")
print(f"(b) PRESENT, >=1 grounded cue: {b_present_with_cue}")
print(f"(c) PRESENT, 0 grounded cues: {c_present_no_cue}")
print()

# 2. Explain the 14.4%
gate_totals = {'yes': 0, 'partial': 0, 'unknown': 0}
no_cue_totals = {'yes': 0, 'partial': 0, 'unknown': 0}

with open(r'd:\Attempt 2\data\pass2\extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        item = json.loads(line)
        gate_dec = item.get('gate_decision', 'unknown').lower()
        if gate_dec not in gate_totals:
            gate_dec = 'unknown' # fallback if something else
            
        gate_totals[gate_dec] += 1
        
        if not extracted_uids.get(item['id'], False):
            no_cue_totals[gate_dec] += 1

print("--- 2. EXPLAIN THE 14.4% NO-CUE RATE ---")
print(f"Total extracted: {sum(gate_totals.values())}")
for g_type in ['yes', 'partial']:
    tot = gate_totals[g_type]
    noc = no_cue_totals[g_type]
    rate = (noc / tot * 100) if tot > 0 else 0
    print(f"Gated '{g_type}': {tot} units. No-cue rate: {noc}/{tot} ({rate:.1f}%)")
