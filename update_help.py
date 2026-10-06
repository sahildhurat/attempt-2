import json
import sys
sys.path.append('scripts/collectors')
from help_community import fetch_category

existing = {}
with open('data/unified/help_community.jsonl', 'r') as f:
    for line in f:
        obj = json.loads(line)
        existing[obj['id']] = obj

print('Existing total:', len(existing))

for cat in ['photos_searching', 'photos_organization']:
    units = fetch_category(cat)
    for u in units:
        existing[u['id']] = u
        
with open('data/unified/help_community.jsonl', 'w') as f:
    for u in existing.values():
        f.write(json.dumps(u) + '\n')
        
print('New total:', len(existing))
