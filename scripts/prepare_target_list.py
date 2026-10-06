import json
import random

def main():
    target_specs = [
        ("stackexchange", "ALL", 1.00),
        ("reddit_assisted", "ALL", 1.00),
        ("appstore", "ALL", 1.00),
        ("help_community", 3000, 6.45),
        ("hn", 1000, 2.13),
        ("playstore", 300, 36.75),
        ("youtube", 200, 32.01)
    ]
    
    # Load all units
    all_units_by_source = {}
    with open("data/archive/all_units_unfiltered.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                u = json.loads(line)
                src = u.get("source", "unknown")
                if src not in all_units_by_source:
                    all_units_by_source[src] = []
                all_units_by_source[src].append(u)
                
    # Load already completed to skip
    completed_ids = set()
    try:
        with open("data/gate_results.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    c = json.loads(line)
                    completed_ids.add(c["id"])
    except FileNotFoundError:
        pass

    target_list = []
    composition = {}
    
    random.seed(42)
    
    for src, count_spec, weight in target_specs:
        units = all_units_by_source.get(src, [])
        # Sort or keep stable before random sampling to ensure reproducibility
        units.sort(key=lambda x: x["id"])
        
        if count_spec == "ALL":
            selected = units
        else:
            selected = random.sample(units, min(count_spec, len(units)))
            
        for u in selected:
            u["weight"] = weight
            
        target_list.extend(selected)
        
        # Count skipped
        skipped = sum(1 for u in selected if u["id"] in completed_ids)
        composition[src] = {
            "total_selected": len(selected),
            "skipped_already_done": skipped,
            "to_process": len(selected) - skipped,
            "weight": weight
        }

    with open("data/target_list.jsonl", "w", encoding="utf-8") as f:
        for u in target_list:
            f.write(json.dumps(u) + "\n")
            
    print("--- TARGET LIST COMPOSITION ---")
    total_selected = 0
    total_to_process = 0
    for src, stats in composition.items():
        print(f"{src}: {stats['total_selected']} selected, {stats['skipped_already_done']} skipped, {stats['to_process']} to process (weight: {stats['weight']})")
        total_selected += stats["total_selected"]
        total_to_process += stats["to_process"]
        
    print(f"\nTotal Selected: {total_selected}")
    print(f"Total To Process: {total_to_process}")

if __name__ == "__main__":
    main()
