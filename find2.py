import re
with open('test_thread.html', 'r', encoding='utf-8') as f:
    html = f.read()

# find first 5 long strings in WIZ_global_data
match = re.search(r'window\.WIZ_global_data\s*=\s*(\{.*?\});', html)
if match:
    data_str = match.group(1)
    # The payload is usually inside a deeply nested array
    # Let's just find all strings > 100 chars
    strings = re.findall(r'"([^"]{100,})"', data_str)
    for s in strings:
        if 'music' in s.lower() or 'photo' in s.lower():
            print("Found:", s.replace('\\n', ' ')[:200])
