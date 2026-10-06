import urllib.request
import re

url = 'https://support.google.com/photos/thread/466667097?hl=en'
req = urllib.request.Request(url, headers={'User-Agent': 'DiscoveryEngine/1.0 (academic research)'})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
    with open('test_thread.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Saved test_thread.html")
except Exception as e:
    print("Error:", e)
