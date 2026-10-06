import json
import urllib.request
import re
import sys
sys.path.append("scripts")
from collectors.manual_threads import fetch_thread

def run():
    units = []
    with open("data/unified/units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            if u.get("source") == "help_community":
                units.append(u)
                if len(units) >= 3:
                    break
                    
    for u in units:
        tid = str(u.get("source_id")).split('_')[0]
        stored_text = u.get("text", "")
        print(f"\n--- THREAD {tid} ---")
        print("STORED TEXT:\n", stored_text[:200] + ("..." if len(stored_text) > 200 else ""))
        
        # Fetch live
        title, messages = fetch_thread(tid)
        if messages:
            live_text = messages[0]
            print("\nLIVE TEXT:\n", live_text[:200] + ("..." if len(live_text) > 200 else ""))
            
            if live_text.startswith(stored_text) and len(live_text) > len(stored_text):
                print(">>> CONCLUSION: TRUNCATED (Stored text is a prefix that ends mid-sentence)")
            elif stored_text == live_text:
                print(">>> CONCLUSION: EXACT MATCH")
            else:
                print(">>> CONCLUSION: DIFFERENT")
        else:
            print("Failed to fetch live text")

if __name__ == "__main__":
    run()
