import json
import statistics
import sys
sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=== 6a. Help Community Snippet Regression ===")
    hc_categories = {}
    
    # 6d prepare
    yt_dropped = []
    
    # 6c prepare
    manual_thread_counts = {}
    manual_total = 0
    
    # Read raw to get dropped ones
    with open("data/unified/youtube.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            if u.get("lang") != "en":
                yt_dropped.append(u.get("text", ""))
                
    with open("data/unified/units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            src = u.get("source")
            ctx = u.get("context", "")
            
            # 6a
            if src == "help_community":
                cat = "unknown"
                if "Category:" in ctx:
                    cat = ctx.split("Category:")[1].split(")")[0].strip()
                elif "Manual Search" in ctx:
                    cat = "manual_search"
                    
                if cat not in hc_categories:
                    hc_categories[cat] = {"count": 0, "is_reply": 0, "lengths": []}
                
                hc_categories[cat]["count"] += 1
                if u.get("is_reply"):
                    hc_categories[cat]["is_reply"] += 1
                hc_categories[cat]["lengths"].append(len(u.get("text", "")))
                
            # 6c
            if src == "help_community" and "Manual Search" in ctx:
                manual_total += 1
                tid = u.get("source_id", "").split("-")[0]
                if tid not in manual_thread_counts:
                    manual_thread_counts[tid] = 0
                manual_thread_counts[tid] += 1
                
    for cat, data in hc_categories.items():
        if data["lengths"]:
            med = statistics.median(data["lengths"])
        else:
            med = 0
        print(f"Cat: {cat} | count: {data['count']} | is_reply: {data['is_reply']} | median len: {med}")

    print("\n=== 6c. Manual Search Counts ===")
    print(f"Total manual_search units: {manual_total}")
    if manual_thread_counts:
        ratio = manual_total / len(manual_thread_counts)
        print(f"Total threads: {len(manual_thread_counts)}")
        print(f"Units per thread ratio: {ratio:.2f}")
        
    print("\n=== 6d. 20 YouTube Units dropped by language filter ===")
    for i, t in enumerate(yt_dropped[:20]):
        # Strip newlines for single-line display
        print(f"{i+1}: {t.replace(chr(10), ' ')[:100]}")
        
if __name__ == "__main__":
    main()
