import json
import random
import parse_and_report

def rebuild_sample():
    units = []
    # Load all except reddit
    with open("data/archive/units_prefiltered.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            u = json.loads(line)
            if len(u.get("text", "")) >= 250:
                units.append(u)
                
    # Load reddit
    import hashlib
    reddit_units = parse_and_report.parse_file(r"d:\Attempt 2\data\raw\reddit_assisted\conversations.txt")
    for i, u in enumerate(reddit_units):
        if len(u.get("text", "")) >= 250:
            u["id"] = hashlib.sha256(u["text"].encode('utf-8')).hexdigest()
            units.append(u)
            
    by_source = {
        "help_community": [],
        "reddit_assisted": [],
        "hn": [],
        "youtube": [],
        "stackexchange": []
    }
    
    for u in units:
        src = u.get("source")
        if src in by_source:
            by_source[src].append(u)
            
    random.seed(42)
    for src in by_source:
        random.shuffle(by_source[src])
        
    sample = (
        by_source["help_community"][:40] +
        by_source["reddit_assisted"][:30] +
        by_source["hn"][:15] +
        by_source["youtube"][:10] +
        by_source["stackexchange"][:5]
    )
    
    random.shuffle(sample)
    
    with open("data/archive/validation_sample.jsonl", "w", encoding="utf-8") as f:
        for u in sample:
            f.write(json.dumps(u) + "\n")
            
    print("Sample Composition:")
    counts = {}
    for u in sample:
        counts[u["source"]] = counts.get(u["source"], 0) + 1
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"Total: {sum(counts.values())}")

if __name__ == "__main__":
    rebuild_sample()
