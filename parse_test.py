import re
html = open('thread_test.html', encoding='utf-8').read()

og_desc = re.search(r'<meta property="og:description" content="([^"]+)"', html)
print('OG Description:', og_desc.group(1) if og_desc else 'None')

og_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
print('OG Title:', og_title.group(1) if og_title else 'None')

title_tag = re.search(r'<title>(.*?)</title>', html)
print('Title:', title_tag.group(1) if title_tag else 'None')
