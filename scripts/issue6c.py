import json

def analyze():
    count = 0
    threads = set()
    with open("data/unified/units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            if u.get("category") == "manual_search":
                count += 1
                pid = u.get("parent_id") or u.get("source_id")
                threads.add(pid)
                
    ratio = count / len(threads) if threads else 0
    print(f"manual_search units: {count}")
    print(f"manual_search threads: {len(threads)}")
    print(f"Units per thread ratio: {ratio:.2f}")

if __name__ == "__main__":
    analyze()
