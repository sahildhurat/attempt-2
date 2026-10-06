import urllib.request
import re

url = "https://support.google.com/photos/threads?hl=en&max_results=5000"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        html = response.read().decode('utf-8')
        matches = set(re.findall(r'data-stats-id="(\d+)"', html))
        print(f"Total Unique Threads: {len(matches)}")
        
        has_more = "load-more-button" in html
        print(f"Has More: {has_more}")
        
        date_groups = re.findall(r'class="thread-list-group__heading"[^>]*>([^<]+)<', html)
        if date_groups:
            print(f"Oldest Group: {date_groups[-1].strip()}")
except Exception as e:
    print(f"Error: {e}")
