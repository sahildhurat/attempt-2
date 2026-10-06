import json
import ast
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
import html
import hashlib

def generate_id(source, source_id):
    return hashlib.sha256(f"{source}_{source_id}".encode()).hexdigest()

def log_failure(collector_name, failure_type, details):
    with open(f"data/raw/{collector_name}/failures.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": failure_type, "details": details}) + "\n")

def clean_text(text):
    if not text:
        return ""
    # 1. Strip HTML tags FIRST (so literal &lt;div&gt; isn't eaten)
    text = re.sub(r'<[^>]+>', ' ', text)
    # 2. Unescape HTML entities
    text = html.unescape(text)
    # 3. Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

import sys
import os
sys.path.append(os.path.dirname(__file__))
from network_utils import get_session, fetch_with_rate_limit, log_failure, _record_failure, _record_success

def fetch_and_parse(session, tid):
    url = f"https://support.google.com/photos/thread/{tid}?hl=en"
    
    import os
    try:
        response = fetch_with_rate_limit(session, "GET", url, "help_community")
        html_content = response.text
    except Exception as e:
        if "RATE_LIMITED" in str(e):
            return "RATE_LIMITED", f"Rate limited: {e}", []
        return "NETWORK", f"Network error: {e}", []

    m = re.search(r"var thread_view='(.*?)';var ", html_content)
    if not m:
        log_failure("help_community", "EMPTY", f"tid: {tid} had no thread_view")
        _record_failure("help_community", "EMPTY", f"tid: {tid} had no thread_view")
        return "EMPTY", "No thread_view payload found", []
        
    js_str = m.group(1)
    
    try:
        decoded_str = ast.literal_eval("'" + js_str.replace("'", "\\'") + "'")
        data = json.loads(decoded_str)
    except Exception as e:
        log_failure("help_community", "PARSE", f"tid: {tid}, error: {e}")
        _record_failure("help_community", "PARSE", f"tid: {tid}, error: {e}")
        return "PARSE", f"Parse error: {e}", [js_str]

    return parse_thread(tid, data, url)
    
def parse_thread(tid, data, url):
    messages = []
    
    # Extract OP
    try:
        op_node = data[1]
        title = op_node[8]
        op_text = op_node[12]
        op_author = data[3][0][0] if data[3] else "Unknown"
        created_at = op_node[0][1] # Microseconds
    except Exception as e:
        return "PARSE", f"Error extracting OP: {e}", []
        
    messages.append({
        "id": generate_id("help_community", tid),
        "source": "help_community",
        "source_type": "discussion",
        "source_id": tid,
        "url": url,
        "text": clean_text(op_text),
        "created_at": created_at,
        "is_reply": False,
        "parent_id": None,
        "context": clean_text(title),
        "text_completeness": "full"
    })
    
    # Extract replies
    raw_replies = []
    def find_messages(node):
        if isinstance(node, list):
            # The outer reply object contains the inner message node at index 0
            if len(node) > 2 and isinstance(node[0], list) and len(node[0]) > 15 and isinstance(node[0][0], list) and len(node[0][0]) >= 4 and isinstance(node[0][0][0], int) and isinstance(node[0][3], str):
                raw_replies.append(node)
            for child in node:
                find_messages(child)
                
    find_messages(data)
    
    # Identify highlighted (recommended) replies from root[16]
    highlighted_ids = set()
    if len(data) > 16 and isinstance(data[16], list):
        # We can just extract them from data[16] specifically
        highlighted_nodes = []
        find_messages(data[16])
        for r in raw_replies:
            # wait, find_messages appends to raw_replies globally. 
            pass
            
    # Better way: just run a fresh find on data[16]
    def get_ids_from(node):
        res = set()
        if isinstance(node, list):
            if len(node) > 2 and isinstance(node[0], list) and len(node[0]) > 15 and isinstance(node[0][0], list) and len(node[0][0]) >= 4 and isinstance(node[0][0][0], int) and isinstance(node[0][3], str):
                res.add(node[0][0][0])
            for child in node:
                res.update(get_ids_from(child))
        return res
        
    highlighted_ids = get_ids_from(data[16]) if len(data) > 16 else set()
    
    # Dedupe and filter out OP
    unique_replies = {}
    for r in raw_replies:
        msg_id = r[0][0][0]
        if msg_id != int(tid):
            unique_replies[msg_id] = r
            
    import datetime
    for msg_id, r in unique_replies.items():
        inner_node = r[0]
        
        # parent_id: node[36] for nested replies, thread id for top-level
        parent_id = str(inner_node[36]) if len(inner_node) > 36 and inner_node[36] else str(tid)
        text = inner_node[3]
        
        # created_at: microseconds to iso8601
        created_at_micro = inner_node[0][1]
        try:
            dt = datetime.datetime.fromtimestamp(float(created_at_micro) / 1000000.0, tz=datetime.timezone.utc)
            created_at = dt.isoformat()
        except:
            created_at = None
        
        # author metadata
        author_name = "Unknown"
        author_badge_level = None
        
        if len(r) > 2 and isinstance(r[2], list) and len(r[2]) > 0 and isinstance(r[2][0], list) and len(r[2][0]) > 0:
            author_name = r[2][0][0]
            
        if len(r) > 2 and isinstance(r[2], list) and len(r[2]) > 1 and isinstance(r[2][1], list) and len(r[2][1]) > 2:
            author_badge_level = r[2][1][2]
            
        author_is_expert = author_badge_level is not None and author_badge_level > 0
        is_highlighted = msg_id in highlighted_ids
        
        messages.append({
            "id": generate_id("help_community", f"{tid}_{msg_id}"),
            "source": "help_community",
            "source_type": "discussion",
            "source_id": f"{tid}_{msg_id}",
            "url": url,
            "text": clean_text(text),
            "created_at": created_at,
            "is_reply": True,
            "parent_id": parent_id,
            "context": clean_text(title),
            "text_completeness": "full",
            "author_name": author_name,
            "author_badge_level": author_badge_level,
            "author_is_expert": author_is_expert,
            "in_root16": is_highlighted,
            "is_recommended": None
        })
        
    _record_success()
    return "SUCCESS", "", messages

def run_100_thread_test():
    tids = set()
    with open("data/archive/units_prefiltered.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            u = json.loads(line)
            if u.get("source") == "help_community":
                tid = str(u.get("source_id")).split('_')[0]
                tids.add(tid)
                
    test_tids = list(tids)[:100]
    session = get_session()
    
    results = {"SUCCESS": 0, "NETWORK": 0, "PARSE": 0, "EMPTY": 0}
    parse_errors = []
    
    for i, tid in enumerate(test_tids):
        status, msg, data = fetch_and_parse(session, tid)
        results[status] += 1
        print(f"[{i+1}/100] {tid}: {status}")
        
        if status == "PARSE":
            with open(f"parse_error_{tid}.txt", "w", encoding="utf-8") as f:
                f.write(data[0]) # dump raw JS
                
    print(f"\\n--- 100 THREAD TEST RESULTS ---")
    print(results)
    
def run_20_thread_reprove():
    tids = set()
    with open("data/archive/units_prefiltered.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            u = json.loads(line)
            if u.get("source") == "help_community":
                tid = str(u.get("source_id")).split('_')[0]
                tids.add(tid)
                
    test_tids = list(tids)[:20]
    session = get_session()
    
    complete_threads = []
    
    for i, tid in enumerate(test_tids):
        status, msg, units = fetch_and_parse(session, tid)
        if status == "SUCCESS" and len(complete_threads) < 20:
            op = [u for u in units if not u['is_reply']][0]
            replies = [u for u in units if u['is_reply']]
            
            thread_str = f"--- THREAD {tid} ---\nTitle: {op['context']}\n[OP | Author: {op.get('author_name', 'Unknown')} | Badge: {op.get('author_badge_level', 'None')}]\n{op['text']}\n"
            for j, r in enumerate(replies):
                flags = []
                if r.get('author_is_expert'): flags.append('EXPERT')
                if r.get('is_recommended'): flags.append('RECOMMENDED')
                flag_str = f" | Flags: {', '.join(flags)}" if flags else ""
                thread_str += f"\n[REPLY {j+1} | Author: {r.get('author_name', 'Unknown')} | Badge: {r.get('author_badge_level', 'None')}{flag_str} | Parent: {r.get('parent_id')}]\n{r['text']}\n"
            complete_threads.append(thread_str)
            
    with open("reprove_20_threads.txt", "w", encoding="utf-8") as f:
        for t in complete_threads:
            f.write(t + "\n")
            
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "100":
        run_100_thread_test()
    else:
        run_20_thread_reprove()
