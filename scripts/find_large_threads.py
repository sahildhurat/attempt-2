import json
import ast
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures

def create_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "DiscoveryEngine/1.0 (academic research)"})
    return session

def find_threads():
    tids = set()
    with open("data/archive/units_prefiltered.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            u = json.loads(line)
            if u.get("source") == "help_community":
                tids.add(str(u.get("source_id")).split('_')[0])
                
    test_tids = list(tids)[:200] # Check first 200 to find what we need
    session = create_session()
    
    def process(tid):
        try:
            r = session.get(f"https://support.google.com/photos/thread/{tid}?hl=en", timeout=10)
            if r.status_code != 200: return None
            import re
            m = re.search(r"var thread_view='(.*?)';var ", r.text)
            if not m: return None
            js_str = m.group(1)
            decoded_str = ast.literal_eval("'" + js_str.replace("'", "\\'") + "'")
            data = json.loads(decoded_str)
            
            def extract_replies(node):
                res = []
                if isinstance(node, list):
                    if len(node) > 15 and isinstance(node[0], list) and len(node[0]) >= 4 and isinstance(node[0][0], int) and isinstance(node[3], str) and len(node[3]) > 0:
                        res.append(node)
                    for child in node:
                        res.extend(extract_replies(child))
                return res
            
            r39 = extract_replies(data[39]) if len(data) > 39 else []
            r16 = extract_replies(data[16]) if len(data) > 16 else []
            
            ids39 = set(x[0][0] for x in r39)
            ids16 = set(x[0][0] for x in r16)
            
            return tid, len(ids39), len(ids16)
        except Exception as e:
            return None

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for res in executor.map(process, test_tids):
            if res:
                results.append(res)
                
    results.sort(key=lambda x: x[1], reverse=True)
    print("Top threads by reply count (tid, r39_unique, r16_unique):")
    for r in results[:10]:
        print(r)
        
if __name__ == "__main__":
    find_threads()
