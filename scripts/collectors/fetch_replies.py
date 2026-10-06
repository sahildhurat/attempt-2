import os
import json
import time
import sys
sys.path.append("scripts/collectors")
from manual_threads import fetch_thread, generate_id
from network_utils import CircuitBreakerTripped

def run():
    target_tids = set()
    with open("data/pass1/gated_units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            u = json.loads(line)
            if u.get("source") == "help_community" and u.get("relevant") in ["yes", "partial"]:
                target_tids.add(str(u.get("source_id")).split('_')[0])
                
    already_fetched = set()
    out_file = "data/raw/help_community/replies.jsonl"
    tmp_file = out_file + ".tmp"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                u = json.loads(line)
                tid = str(u.get("parent_id")) if u.get("is_reply") else str(u.get("source_id"))
                already_fetched.add(tid)
                
    to_fetch = list(target_tids - already_fetched)
    print(f"Total relevant threads: {len(target_tids)}, Already fetched: {len(already_fetched)}, To fetch: {len(to_fetch)}")
    
    import shutil
    if os.path.exists(out_file):
        shutil.copyfile(out_file, tmp_file)
        
    try:
        with open(tmp_file, "a", encoding="utf-8") as f:
            for i, tid in enumerate(to_fetch):
                print(f"[{i+1}/{len(to_fetch)}] Fetching {tid}...")
                title, messages = fetch_thread(tid)
                if title and messages:
                    for j, text in enumerate(messages):
                        is_reply = (j > 0)
                        unit_id = generate_id("help_community", f"{tid}_{j}") if is_reply else generate_id("help_community", tid)
                        u = {
                            "id": unit_id,
                            "source": "help_community",
                            "source_type": "discussion",
                            "source_id": f"{tid}_{j}" if is_reply else tid,
                            "url": f"https://support.google.com/photos/thread/{tid}?hl=en",
                            "text": text,
                            "created_at": None,
                            "is_reply": is_reply,
                            "parent_id": tid if is_reply else None,
                            "context": title,
                            "category": "photos_searching",
                            "text_completeness": "full"
                        }
                        f.write(json.dumps(u) + "\n")
                time.sleep(1)
                
                if (i + 1) % 100 == 0:
                    f.flush()
                    os.fsync(f.fileno())
                    shutil.copyfile(tmp_file, out_file)
                    
            f.flush()
            os.fsync(f.fileno())
            shutil.copyfile(tmp_file, out_file)
            
    except CircuitBreakerTripped as e:
        print(f"Circuit Breaker Tripped! {e}")
        shutil.copyfile(tmp_file, out_file)
        sys.exit(1)

if __name__ == "__main__":
    run()
