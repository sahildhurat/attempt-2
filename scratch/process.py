import json

units = []
with open('d:/Attempt 2/data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip(): units.append(json.loads(line))

memory_gaps = []
for u in units:
    ext = u.get('extraction', {})
    for f in ext.get('forgotten', []):
        if f.get('gap_type') == 'memory_gap':
            memory_gaps.append(f)

# the mapping (1-indexed based on the printout we had)
reclass = {
    7: 'system_failure', 9: 'system_failure', 12: 'system_failure', 24: 'system_failure',
    19: 'navigation_gap', 20: 'navigation_gap', 22: 'navigation_gap', 27: 'navigation_gap', 28: 'navigation_gap', 30: 'navigation_gap', 31: 'navigation_gap',
    3: 'account_event', 29: 'account_event',
    10: 'not_user_cue', 11: 'not_user_cue', 15: 'not_user_cue', 32: 'not_user_cue', 33: 'not_user_cue', 34: 'not_user_cue'
}

for idx, f in enumerate(memory_gaps):
    i = idx + 1
    if i in reclass:
        f['gap_type'] = reclass[i]

with open('d:/Attempt 2/data/pass2/extracted_units.jsonl', 'w', encoding='utf-8') as f_out:
    for u in units:
        f_out.write(json.dumps(u) + '\n')

helper_cues = []
total_remembered = 0

for u in units:
    ext = u.get('extraction', {})
    is_helper = False
    
    src = u.get('source', '')
    meta = u.get('metadata', {})
    text = u.get('text', '')
    text_lower = text.lower()
    
    if src == 'help_community':
        if meta.get('is_reply') and meta.get('author_badge_level') is not None:
            is_helper = True
    elif src == 'reddit_assisted':
        if meta.get('is_reply'):
            is_helper = True
            
    if "from google photos help" in text_lower or "google photos help" in text_lower:
        is_helper = True
        
    for r in ext.get('remembered', []):
        total_remembered += 1
        if is_helper:
            helper_cues.append((r['cue'], text, u['id']))

with open('d:/Attempt 2/scratch/helper_cues.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total remembered cues: {total_remembered}\n")
    f.write(f"Helper cues: {len(helper_cues)} ({(len(helper_cues)/total_remembered)*100:.1f}%)\n\n")
    
    for idx, (cue, text, uid) in enumerate(helper_cues[:10]):
        f.write(f"[{idx+1}] CUE: {cue}\nUNIT ID: {uid}\nTEXT: {text.strip()}\n\n")

print(f"Total remembered cues: {total_remembered}")
print(f"Helper cues: {len(helper_cues)} ({(len(helper_cues)/total_remembered)*100:.1f}%)")
