import re
with open('temp_thread.html', 'r', encoding='utf-8') as f:
    html = f.read()

for m in re.finditer(r'"([^"]{100,})"', html):
    s = m.group(1)
    if 'Google Photos' in s or 'music' in s:
        print('---')
        print(s[:300])
