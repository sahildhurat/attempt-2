import json
import re
import html
import os
import numpy as np

def clean_text(text):
    if not text:
        return text
    original = text
    # 1. Strip tags
    text = re.sub(r'<[^>]+>', '', text)
    # 2. Unescape entities
    text = html.unescape(text)
    # 3. Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text, text != original

def process_file(filepath, text_fields=['text', 'context']):
    if not os.path.exists(filepath):
        return
    print(f"Processing {filepath}...")
    affected = 0
    total = 0
    affected_by_source = {}
    lengths_help_community = []
    
    out_path = filepath + ".tmp"
    with open(filepath, 'r', encoding='utf-8') as f_in, open(out_path, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            if not line.strip():
                continue
            item = json.loads(line)
            total += 1
            source = item.get('source', 'unknown')
            changed_any = False
            
            for field in text_fields:
                if field in item and isinstance(item[field], str):
                    new_val, changed = clean_text(item[field])
                    item[field] = new_val
                    if changed:
                        changed_any = True
                        
            if changed_any:
                affected += 1
                affected_by_source[source] = affected_by_source.get(source, 0) + 1
                
            if source == 'help_community' and 'text' in item and isinstance(item['text'], str):
                lengths_help_community.append(len(item['text']))
                
            f_out.write(json.dumps(item) + "\n")
            
    os.replace(out_path, filepath)
    print(f"  {affected}/{total} affected")
    if affected_by_source:
        print("  By source:", affected_by_source)
    if lengths_help_community:
        deciles = np.percentile(lengths_help_community, np.arange(10, 101, 10))
        print("  help_community length deciles:", [int(d) for d in deciles])

# Process the main corpus files
base_dir = r"d:\Attempt 2\data"
files_to_process = [
    (os.path.join(base_dir, "target_list.jsonl"), ['text', 'context']),
    (os.path.join(base_dir, "gate_results.jsonl"), ['text', 'context']),
    (os.path.join(base_dir, "blind_sample_key.jsonl"), ['text', 'context']),
    (os.path.join(base_dir, "pass2", "extracted_units.jsonl"), ['text', 'context']),
]

for filepath, fields in files_to_process:
    process_file(filepath, fields)
