import sys
import re
import json
sys.path.append('scripts/collectors')
import help_community_v2 as hc2

tid = '367230169'
with open(f'thread_{tid}_raw.txt', 'r', encoding='utf-8') as f:
    html_content = f.read()

m = re.search(r"var thread_view='(.*?)';var ", html_content)
if m:
    raw_js = m.group(1)
    raw_js = raw_js.encode('utf-8').decode('unicode_escape')
    raw_js = raw_js.replace('\\/', '/')
    
    data = json.loads(raw_js)
    root_data = data[1]
    
    if len(root_data) > 2 and isinstance(root_data[2], list):
        replies_data = root_data[2]
        print('replies_data count:', len(replies_data))
        for r in replies_data:
            print("Reply item type:", type(r))
            
    print("Units parsed by hc2:", len(hc2.parse_thread_data(root_data, tid, f"url_{tid}")))
