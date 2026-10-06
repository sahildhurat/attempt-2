import sys
import os
import json
import time
import hashlib
import re

sys.path.append(os.path.dirname(__file__))
from network_utils import get_session, fetch_with_rate_limit, log_failure, _record_failure, _record_success
from help_community_v2 import clean_text

def generate_id(source, source_id):
    return hashlib.sha256(f"{source}_{source_id}".encode()).hexdigest()

def collect():
    url_file = "config/reddit_thread_urls.txt"
    if not os.path.exists(url_file):
        print(f"File {url_file} not found. Skipping Reddit collection.")
        return 0
        
    os.makedirs("data/raw/reddit", exist_ok=True)
    os.makedirs("data/unified", exist_ok=True)
    
    urls = []
    with open(url_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
                
    # Deduplicate on base36 ID
    unique_threads = {}
    duplicates = 0
    
    for url in urls:
        m = re.search(r'/comments/([^/]+)/', url)
        if m:
            tid = m.group(1)
            if tid in unique_threads:
                duplicates += 1
            else:
                # Store the base JSON url
                unique_threads[tid] = f"https://www.reddit.com/comments/{tid}/.json"
        else:
            print(f"Warning: Could not extract thread ID from URL: {url}")
            
    print(f"Reddit collection: found {len(urls)} URLs, {duplicates} duplicates removed. Fetching {len(unique_threads)} unique threads.")
    
    session = get_session()
    session.headers.update({"User-Agent": "DiscoveryEngine/1.0 (academic research) python-requests"})
    
    all_units = []
    
    for i, (tid, json_url) in enumerate(unique_threads.items()):
        print(f"[{i+1}/{len(unique_threads)}] Fetching thread {tid}...")
        
        try:
            resp = fetch_with_rate_limit(session, "GET", json_url, "reddit", timeout=15)
            data = resp.json()
        except Exception as e:
            if "RATE_LIMITED" in str(e):
                print(f"Rate limited on thread {tid}: {e}")
            else:
                log_failure("reddit", "NETWORK_OR_PARSE", f"tid: {tid}, error: {e}")
                print(f"Error on thread {tid}: {e}")
            time.sleep(6)
            continue
            
        try:
            # Parse OP
            post_data = data[0]["data"]["children"][0]["data"]
            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            op_text = f"{title}\n{selftext}" if selftext else title
            op_created = post_data.get("created_utc")
            
            all_units.append({
                "id": generate_id("reddit", tid),
                "source": "reddit",
                "source_type": "discussion",
                "source_id": tid,
                "url": f"https://www.reddit.com/comments/{tid}/",
                "text": clean_text(op_text),
                "created_at": op_created,
                "is_reply": False,
                "parent_id": None,
                "context": clean_text(title),
                "text_completeness": "full"
            })
            
            # Parse comments (depth 2)
            if len(data) > 1:
                comments = data[1]["data"]["children"]
                for comment in comments:
                    if comment["kind"] != "t1":
                        continue
                    c_data = comment["data"]
                    c_id = c_data.get("id")
                    c_text = c_data.get("body", "")
                    if not c_text: continue
                    
                    all_units.append({
                        "id": generate_id("reddit", c_id),
                        "source": "reddit",
                        "source_type": "discussion",
                        "source_id": c_id,
                        "url": f"https://www.reddit.com/comments/{tid}/comment/{c_id}/",
                        "text": clean_text(c_text),
                        "created_at": c_data.get("created_utc"),
                        "is_reply": True,
                        "parent_id": tid,
                        "context": clean_text(title),
                        "text_completeness": "full"
                    })
                    
                    # Depth 2
                    replies = c_data.get("replies")
                    if replies and isinstance(replies, dict):
                        subcomments = replies.get("data", {}).get("children", [])
                        for subc in subcomments:
                            if subc["kind"] != "t1":
                                continue
                            sc_data = subc["data"]
                            sc_id = sc_data.get("id")
                            sc_text = sc_data.get("body", "")
                            if not sc_text: continue
                            
                            all_units.append({
                                "id": generate_id("reddit", sc_id),
                                "source": "reddit",
                                "source_type": "discussion",
                                "source_id": sc_id,
                                "url": f"https://www.reddit.com/comments/{tid}/comment/{sc_id}/",
                                "text": clean_text(sc_text),
                                "created_at": sc_data.get("created_utc"),
                                "is_reply": True,
                                "parent_id": c_id,
                                "context": clean_text(title),
                                "text_completeness": "full"
                            })
                            
        except Exception as e:
            log_failure("reddit", "PARSE", f"tid: {tid}, error: {e}")
            _record_failure("reddit", "PARSE", f"tid: {tid}, error: {e}")
            print(f"Parse error on thread {tid}: {e}")
            time.sleep(6) # 1 request every 6 seconds (10 QPM)
            continue
            
        _record_success()
        time.sleep(6) # 1 request every 6 seconds (10 QPM)
        
    out_file = "data/unified/reddit.jsonl"
    tmp_file = out_file + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        for u in all_units:
            f.write(json.dumps(u, default=str) + "\n")
    if os.path.exists(tmp_file):
        os.replace(tmp_file, out_file)
        
    print(f"Reddit collection complete: {len(all_units)} total units saved.")
    return len(all_units)

if __name__ == "__main__":
    collect()
