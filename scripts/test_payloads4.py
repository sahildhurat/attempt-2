import sys
import json
import ast
import re
sys.path.append('scripts/collectors')
import help_community_v2 as hc2

for tid in ['367230169', '319380955']:
    with open(f'thread_{tid}_raw.txt', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # It's not HTML, the saved payload is literally the content of thread_view
    # BUT wait, is it JS string or raw JSON?
    if html_content.startswith('[[['):
        # It's raw JSON! But earlier json.loads failed on \x3d.
        js_str = html_content
    else:
        m = re.search(r"var thread_view='(.*?)';var ", html_content)
        js_str = m.group(1) if m else html_content

    try:
        decoded_str = ast.literal_eval("'" + js_str.replace("'", "\\'") + "'")
        data = json.loads(decoded_str)
    except Exception as e:
        print(f"[{tid}] AST Eval Failed:", e)
        # Try raw json loads with hex replace
        try:
            fixed = re.sub(r'\\x([0-9a-fA-F]{2})', r'\\u00\1', js_str)
            data = json.loads(fixed)
        except Exception as e2:
            print(f"[{tid}] JSON Loads Failed:", e2)
            continue
            
    if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
        root_data = data[1]
    else:
        root_data = data

    units = hc2.parse_thread(tid, data, f'url_{tid}')
    if not isinstance(units, list):
        print(f"[{tid}] Error returned:", units)
        continue
    replies = [u for u in units if u['is_reply']]
    print(f"Thread {tid}: {len(replies)} replies")
