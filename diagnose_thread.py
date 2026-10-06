import urllib.request
import re
import json

def fetch_and_dump(tid):
    url = f"https://support.google.com/photos/thread/{tid}?hl=en"
    headers = {"User-Agent": "DiscoveryEngine/1.0 (academic research)"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching {tid}: {e}")
        return
        
    m = re.search(r"var thread_view='(.*?)';var ", html)
    if not m:
        print(f"{tid}: No thread_view found")
        with open(f"thread_{tid}_no_match.html", "w", encoding="utf-8") as f:
            f.write(html)
        return
        
    js_str = m.group(1)
    
    import ast
    try:
        # Decode the JS string literal into a python string
        decoded_str = ast.literal_eval("'" + js_str.replace("'", "\\'") + "'")
    except Exception as e:
        print(f"{tid}: Failed to literal_eval: {e}")
        return
        
    try:
        data = json.loads(decoded_str)
        with open(f"thread_{tid}_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"{tid}: successfully parsed thread_view as JSON. Dumped to thread_{tid}_data.json")
    except json.JSONDecodeError as e:
        print(f"{tid}: Failed to parse as JSON: {e}")
        with open(f"thread_{tid}_raw.txt", "w", encoding="utf-8") as f:
            f.write(js_str)

# 3 of the ones that worked before
good_tids = ["319380955", "386160070", "367230169"]

# 3 of the ones that failed with "No messages returned" in previous run
bad_tids = ["279126945", "335183130", "469087972"]

for tid in good_tids + bad_tids:
    fetch_and_dump(tid)
