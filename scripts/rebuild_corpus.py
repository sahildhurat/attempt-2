import os
import json
import glob

def main():
    unified_dir = "data/unified"
    out_file = "data/archive/all_units_unfiltered.jsonl"
    
    source_files = [f for f in os.listdir(unified_dir) if f.endswith(".jsonl") and f != "units.jsonl"]
    
    seen_ids = set()
    total_raw = 0
    final_units = []
    
    src_counts = {}
    
    for filename in source_files:
        filepath = os.path.join(unified_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                unit = json.loads(line)
                total_raw += 1
                
                uid = unit.get("id")
                if uid in seen_ids:
                    continue
                    
                seen_ids.add(uid)
                src = unit.get("source", "unknown")
                src_counts[src] = src_counts.get(src, 0) + 1
                final_units.append(unit)
                
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        for unit in final_units:
            f.write(json.dumps(unit) + "\n")
            
    print(f"Rebuilt full corpus from per-source files.")
    print(f"Total lines read: {total_raw}")
    print(f"Total unique IDs written: {len(seen_ids)}")
    print("Breakdown by source:")
    for k, v in src_counts.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
