import sys
import re
import json
sys.path.append('scripts/collectors')
import help_community_v2 as hc2

for tid in ['367230169', '319380955']:
    with open(f'thread_{tid}_raw.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    # fix hex escapes for JSON
    text = re.sub(r'\\x([0-9a-fA-F]{2})', r'\\u00\1', text)
    
    try:
        data = json.loads(text)
    except Exception as e:
        print(f'{tid} json failed:', e)
        continue
        
    if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
        root_data = data[1]
    else:
        root_data = data
        
    units = hc2.parse_thread_data(root_data, tid, f'url_{tid}')
    replies = [u for u in units if u['is_reply']]
    print(f'Thread {tid}: {len(replies)} replies')
