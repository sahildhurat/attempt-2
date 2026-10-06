import json

units = []
with open('d:/Attempt 2/data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip(): units.append(json.loads(line))

fields_data = {'cues': [], 'target': [], 'breakdown': [], 'workaround': []}
memory_gaps = []

for u in units:
    ext = u.get('extraction', {})
    
    t = ext.get('target')
    if t: fields_data['target'].append(t)
        
    b = ext.get('breakdown')
    if b: fields_data['breakdown'].append(b)
        
    w = ext.get('workaround')
    if w: fields_data['workaround'].append(w)
        
    for r in ext.get('remembered', []):
        fields_data['cues'].append(r['cue'])
    for f in ext.get('forgotten', []):
        if f.get('gap_type') == 'memory_gap':
            fields_data['cues'].append(f['cue'])
            memory_gaps.append((f['cue'], u.get('text', '')))

with open('d:/Attempt 2/scratch/counts.txt', 'w', encoding='utf-8') as f:
    for k in fields_data:
        f.write(f"Total {k}: {len(fields_data[k])}, Unique: {len(set(fields_data[k]))}\n")

    f.write(f"\nTotal memory_gap items: {len(memory_gaps)}\n")
    for idx, (cue, text) in enumerate(memory_gaps):
        f.write(f"[{idx+1}] CUE: {cue}\n    TEXT: {text.strip()}\n")
