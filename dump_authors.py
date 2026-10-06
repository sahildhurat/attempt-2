import json, ast, requests, sys
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def fetch(tid):
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=['GET'])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({'User-Agent': 'DiscoveryEngine/1.0 (academic research)'})
    r = session.get(f'https://support.google.com/photos/thread/{tid}?hl=en', timeout=10)
    import re
    m = re.search(r"var thread_view='(.*?)';var ", r.text)
    js_str = m.group(1)
    decoded_str = ast.literal_eval("'" + js_str.replace("'", "\\'") + "'")
    return json.loads(decoded_str)

data = fetch('440606295')

def extract_replies(node):
    res = []
    if isinstance(node, list):
        if len(node) > 15 and isinstance(node[0], list) and len(node[0]) >= 4 and isinstance(node[0][0], int) and isinstance(node[3], str) and len(node[3]) > 0:
            res.append(node)
        for child in node:
            res.extend(extract_replies(child))
    return res

r16 = extract_replies(data[16])
r39 = extract_replies(data[39])

sys.stdout.reconfigure(encoding='utf-8')
print('=== r16 replies ===')
for r in r16:
    print('ID:', r[0][0])
    author = r[2][0][0] if len(r)>2 and isinstance(r[2], list) and len(r[2])>0 and isinstance(r[2][0], list) and len(r[2][0])>0 else 'Unknown'
    badge = r[2][1][2] if len(r)>2 and isinstance(r[2], list) and len(r[2])>1 and isinstance(r[2][1], list) and len(r[2][1])>2 else 'None'
    print(f'Author: {author} (Badge: {badge})')
    print('Text:', r[3][:100].replace('\n', ' '))
    print('---')

print('=== ALL replies (r39) ===')
for r in r39:
    print('ID:', r[0][0])
    author = r[2][0][0] if len(r)>2 and isinstance(r[2], list) and len(r[2])>0 and isinstance(r[2][0], list) and len(r[2][0])>0 else 'Unknown'
    badge = r[2][1][2] if len(r)>2 and isinstance(r[2], list) and len(r[2])>1 and isinstance(r[2][1], list) and len(r[2][1])>2 else 'None'
    print(f'Author: {author} (Badge: {badge})')
    print('Text:', r[3][:100].replace('\n', ' '))
    print('---')
