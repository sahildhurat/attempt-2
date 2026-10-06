import re

with open('test_thread.html', 'r', encoding='utf-8') as f:
    html = f.read()

title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
title = title_match.group(1).strip() if title_match else 'No title'

body_match = re.search(r'class="[^"]*thread-question__payload[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
body = body_match.group(1).strip() if body_match else 'No body'

with open('extracted.txt', 'w', encoding='utf-8') as out:
    out.write('TITLE: ' + title + '\n')
    out.write('BODY: ' + body[:500] + '\n')
