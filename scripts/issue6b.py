import json
import os

def backfill():
    unified_dir = "data/unified"
    files = [f for f in os.listdir(unified_dir) if f.endswith(".jsonl")]
    for filename in files:
        filepath = os.path.join(unified_dir, filename)
        new_lines = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                u = json.loads(line)
                u["text_completeness"] = "snippet" if u.get("source") == "help_community" else "full"
                new_lines.append(json.dumps(u) + "\n")
        with open(filepath, "w", encoding="utf-8") as f:
            for line in new_lines:
                f.write(line)
                
if __name__ == "__main__":
    backfill()
