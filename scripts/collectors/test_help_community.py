import json
import sys
import time

sys.path.append("scripts")
from collectors.manual_threads import fetch_thread

def run():
    tids = set()
    with open("data/archive/units_prefiltered.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            u = json.loads(line)
            if u.get("source") == "help_community":
                # source_id is something like 468115002_0
                tid = str(u.get("source_id")).split('_')[0]
                tids.add(tid)
                
    test_tids = list(tids)[:20]
    
    threads_attempted = 0
    threads_parsed = 0
    parse_failures = {}
    units_produced = 0
    total_reply_count = 0
    lengths = []
    
    complete_threads = []
    
    for tid in test_tids:
        threads_attempted += 1
        print(f"Fetching {tid}...")
        try:
            title, messages = fetch_thread(tid)
            if not messages:
                parse_failures[tid] = "No messages returned"
                time.sleep(1)
                continue
                
            threads_parsed += 1
            op_text = messages[0]
            replies = messages[1:]
            
            units_produced += (1 + len(replies))
            total_reply_count += len(replies)
            
            lengths.append(len(op_text))
            for r in replies:
                lengths.append(len(r))
                
            if len(complete_threads) < 3:
                thread_str = f"--- THREAD {tid} ---\nTitle: {title}\n[OP]\n{op_text}\n"
                for i, r in enumerate(replies):
                    thread_str += f"\n[REPLY {i+1}]\n{r}\n"
                complete_threads.append(thread_str)
                
        except Exception as e:
            parse_failures[tid] = str(e)
            
        time.sleep(1)
        
    lengths.sort()
    deciles = {f"{i*10}%": lengths[int(len(lengths)*i/10)] for i in range(1, 10)} if lengths else {}
    
    with open("test_help_community_report.txt", "w", encoding="utf-8") as f:
        f.write(f"Threads attempted: {threads_attempted}\n")
        f.write(f"Threads parsed: {threads_parsed}\n")
        f.write(f"Parse failures: {parse_failures}\n")
        f.write(f"Units produced: {units_produced}\n")
        f.write(f"Average units per thread: {units_produced / threads_parsed if threads_parsed else 0:.2f}\n")
        f.write(f"Total reply count: {total_reply_count}\n")
        f.write(f"Character-length deciles: {deciles}\n\n")
        
        f.write("3 COMPLETE THREADS VERBATIM:\n")
        for ct in complete_threads:
            f.write(ct + "\n")

if __name__ == "__main__":
    run()
