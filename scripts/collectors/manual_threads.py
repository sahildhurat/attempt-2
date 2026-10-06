import json
import urllib.request
import re
import hashlib
import time

def generate_id(source, source_id):
    return hashlib.sha256(f"{source}_{source_id}".encode()).hexdigest()

HEADERS = {
    "User-Agent": "DiscoveryEngine/1.0 (academic research)"
}

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from network_utils import get_session, fetch_with_rate_limit

def log_failure(failure_type, details):
    with open(f"data/raw/manual_threads/failures.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": failure_type, "details": details}) + "\n")

def fetch_thread(tid):
    url = f"https://support.google.com/photos/thread/{tid}?hl=en"
    session = get_session()
    

    try:
        response = fetch_with_rate_limit(session, "GET", url, "manual_threads", timeout=10)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        if "RATE_LIMITED" in str(e):
            log_failure("manual_threads", "RATE_LIMITED", str(e))
            return [], [] # Or appropriate return value based on signature... Wait, this is tricky to do globally
        if isinstance(e, requests.exceptions.RequestException):
            print(f"Error fetching {tid}: {e}")
            log_failure("NETWORK", f"tid: {tid}, error: {e}")
            return None, []
    except Exception as e:
        print(f"Error reading {tid}: {e}")
        log_failure("PARSE", f"tid: {tid}, error: {e}")
        return None, []
        
    title_match = re.search(r'<title>(.*?)</title>', html)
    title = title_match.group(1).replace(" - Google Photos Community", "").strip() if title_match else ""
    
    # Extract the JS payload which contains the text
    m = re.search(r"var thread_view='(.*?)';var ", html)
    if not m:
        return title, [title]
        
    js_str = m.group(1).replace('\\x22', '\"').replace('\\n', '\n').replace('\\\\', '\\')
    
    # Find all strings that look like message text
    strings = re.findall(r'"([^"]{30,})"', js_str)
    
    messages = []
    for s in strings:
        # Filter out UI strings, HTML fragments, URLs
        if '<html' in s or 'function()' in s or 'https://' in s or len(s) > 10000:
            continue
        # Also filter out exact standard Google strings
        if 'Subject Title Goes Here' in s or 'Titre de votre publication' in s or 'Titel Ihrer Frage hier eingeben' in s or 'Esempio:' in s:
            continue
            
        # Try to unescape unicode (e.g. \\u003c)
        try:
            s = s.encode().decode('unicode_escape')
        except:
            pass
            
        import re as re_mod
        # Remove HTML tags
        text = re_mod.sub(r'<[^>]+>', ' ', s)
        text = re_mod.sub(r'\s+', ' ', text).strip()
        
        # If it looks like a real sentence (contains spaces, starts with letter)
        if len(text) > 30 and ' ' in text:
            if text not in messages:
                messages.append(text)
                
    if not messages:
        messages = [title]
        
    return title, messages

def collect_manual():
    import os
    os.makedirs("data/raw/manual_threads", exist_ok=True)
    
    manual_tids = set()
    raw_count = 0
    with open("config/manual_thread_urls.txt", "r") as f:
        for line in f:
            line = line.strip()
            if 'support.google.com' in line:
                raw_count += 1
                m = re.search(r'/thread/(\d+)', line)
                if m:
                    manual_tids.add(m.group(1))
    
    print(f"Read {raw_count} Google URLs from seed file, found {len(manual_tids)} unique threads. Removed {raw_count - len(manual_tids)} duplicates.")
                
    # Load existing unified TIDs
    existing_tids = set()
    unified_path = "data/unified/help_community.jsonl"
    try:
        with open(unified_path, "r") as f:
            for line in f:
                obj = json.loads(line)
                if obj["source"] == "help_community":
                    existing_tids.add(str(obj["source_id"]))
    except FileNotFoundError:
        pass

    new_tids = manual_tids
    already_present = 0
    
    print(f"Total manual TIDs: {len(manual_tids)}")
    print(f"Already present: {already_present}")
    print(f"New to fetch: {len(new_tids)}")
    
    units = []
    for tid in new_tids:
        print(f"Fetching {tid}...")
        title, messages = fetch_thread(tid)
        if title and messages:
            for i, text in enumerate(messages):
                is_reply = (i > 0)
                unit_id = generate_id("help_community", f"{tid}_{i}") if is_reply else generate_id("help_community", tid)
                units.append({
                    "id": unit_id,
                    "source": "help_community",
                    "source_type": "discussion",
                    "source_id": f"{tid}_{i}" if is_reply else tid,
                    "url": f"https://support.google.com/photos/thread/{tid}?hl=en",
                    "text": text,
                    "created_at": None,
                    "is_reply": is_reply,
                    "parent_id": tid if is_reply else None,
                    "context": title,
                    "category": "manual_search",
                })
        time.sleep(1)
        
    if units:
        with open(unified_path, "a") as f:
            for u in units:
                f.write(json.dumps(u) + "\n")
        print(f"Appended {len(units)} new units to {unified_path}.")

if __name__ == "__main__":
    collect_manual()
