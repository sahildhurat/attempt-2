import re
with open('test_thread.html', 'r', encoding='utf-8') as f:
    html = f.read()

match = re.search(r'window\.WIZ_global_data\s*=\s*(\{.*?\});', html)
if match:
    data_str = match.group(1)
    strings = re.findall(r'"([^"]*)"', data_str)
    for s in strings:
        if 'music' in s.lower() and len(s) > 20:
            print("Found:", s.replace('\\n', ' ')[:200])
