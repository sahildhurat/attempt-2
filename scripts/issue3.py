import json
import statistics

def get_deciles(data):
    if not data: return []
    data = sorted(data)
    n = len(data)
    return [data[int(i * n / 10)] for i in range(1, 10)]

def run():
    lengths = []
    with open("data/unified/units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            if u.get("source") == "help_community":
                lengths.append(len(u.get("text", "")))
                
    deciles = get_deciles(lengths)
    print("Help Community text length deciles (10% to 90%):")
    for i, d in enumerate(deciles):
        print(f"  {(i+1)*10}%: {d}")

if __name__ == "__main__":
    run()
