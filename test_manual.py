import urllib.request, re, json
req = urllib.request.Request('https://support.google.com/photos/thread/466667097?hl=en', headers={'User-Agent': 'DiscoveryEngine/1.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')

title = re.search(r'<title>(.*?)</title>', html).group(1).replace(' - Google Photos Community', '')
print('Title:', title)

m = re.search(r"var thread_view='(.*?)';var ", html)
if m:
    js_str = m.group(1).replace('\\x22', '\"').replace('\\n', '\n').replace('\\\\', '\\')
    strings = re.findall(r'"([^"]{50,})"', js_str)
    
    messages = []
    for s in strings:
        if '<html' in s or 'function()' in s or len(s) > 10000:
            continue
        messages.append(s)
        
    for i, msg in enumerate(messages):
        print(f'Msg {i}: {msg[:100]}...')
