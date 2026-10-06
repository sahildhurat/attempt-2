import re, json
with open('temp_thread.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r"var thread_view='(.*?)';var ", html)
if m:
    js_str = m.group(1).replace('\\x22', '"')
    try:
        data = json.loads(js_str)
        with open('thread_view.json', 'w', encoding='utf-8') as out:
            json.dump(data, out, indent=2)
        print('Saved thread_view.json')
    except Exception as e:
        print('JSON error:', e)
        with open('thread_view.json', 'w', encoding='utf-8') as out:
            out.write(js_str)
