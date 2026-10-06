import json
import statistics

def analyze():
    cats = {"photos_searching": {"count": 0, "lengths": [], "is_reply_count": 0},
            "photos_share": {"count": 0, "lengths": [], "is_reply_count": 0}}
    
    with open("data/unified/units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            if u.get("source") == "help_community":
                cat = u.get("category")
                if cat in cats:
                    cats[cat]["count"] += 1
                    text_len = len(u.get("text", ""))
                    cats[cat]["lengths"].append(text_len)
                    if u.get("is_reply"):
                        cats[cat]["is_reply_count"] += 1
                        
    for cat, stats in cats.items():
        median_len = statistics.median(stats["lengths"]) if stats["lengths"] else 0
        print(f"Category: {cat}")
        print(f"  Count: {stats['count']}")
        print(f"  Median Text Length: {median_len}")
        print(f"  is_reply Count: {stats['is_reply_count']}")

if __name__ == "__main__":
    analyze()
