import json

def get_metrics(units, model_filter=None):
    metrics = {
        "remembered": {"returned": 0, "grounded": 0, "dropped": 0},
        "forgotten": {"returned": 0, "grounded": 0, "dropped": 0}
    }
    
    for u in units:
        ext = u.get("extraction", {})
        if model_filter and ext.get("extraction_model") != model_filter:
            continue
            
        metrics["remembered"]["grounded"] += len(ext.get("remembered", []))
        metrics["forgotten"]["grounded"] += len(ext.get("forgotten", []))
        
        for dropped in ext.get("dropped_cues", []):
            fld = dropped.get("original_field")
            if fld in metrics:
                metrics[fld]["dropped"] += 1
                
    for fld in metrics:
        metrics[fld]["returned"] = metrics[fld]["grounded"] + metrics[fld]["dropped"]
        total = metrics[fld]["returned"]
        metrics[fld]["drop_rate"] = (metrics[fld]["dropped"] / total * 100) if total > 0 else 0
        
    return metrics

def print_metrics(title, metrics):
    print(f"\n=== {title} ===")
    for fld in metrics:
        m = metrics[fld]
        print(f"{fld.upper()}: Returned {m['returned']} | Grounded {m['grounded']} | Dropped {m['dropped']} ({m['drop_rate']:.1f}%)")

def main():
    units = []
    with open("data/pass2/extracted_units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                units.append(json.loads(line))
                
    print(f"Total units extracted: {len(units)}")
    
    # Grounding table full
    full_metrics = get_metrics(units)
    print_metrics("FULL GROUNDING TABLE", full_metrics)
    
    anthropic_metrics = get_metrics(units, "claude-sonnet-5")
    print_metrics("ANTHROPIC GROUNDING TABLE", anthropic_metrics)
    
    gemini_metrics = get_metrics(units, "gemini-3.6-flash")
    if any(m["returned"] > 0 for m in gemini_metrics.values()):
        print_metrics("GEMINI GROUNDING TABLE", gemini_metrics)
        
    # Extraction counts by source
    counts = {}
    for u in units:
        src = u.get("source", "unknown")
        counts[src] = counts.get(src, 0) + 1
    print("\nExtraction counts by source:")
    for src, c in counts.items():
        print(f"  {src}: {c}")
        
    # Counts by field
    fields_count = {"target": 0, "evidence_quote": 0, "remembered": 0, "forgotten": 0, "workaround": 0, "breakdown": 0}
    for u in units:
        ext = u.get("extraction", {})
        for f in fields_count:
            if f in ["remembered", "forgotten"]:
                if len(ext.get(f, [])) > 0: fields_count[f] += 1
            elif ext.get(f):
                fields_count[f] += 1
    print("\nExtraction counts by field (units with at least one):")
    for f, c in fields_count.items():
        print(f"  {f}: {c}")
        
    # Units with >=1 grounded REMEMBERED, >=1 grounded FORGOTTEN
    rem_units = sum(1 for u in units if len(u.get("extraction", {}).get("remembered", [])) > 0)
    forg_units = sum(1 for u in units if len(u.get("extraction", {}).get("forgotten", [])) > 0)
    print("\nMemory map denominators:")
    print(f"  Units with >=1 grounded REMEMBERED cue: {rem_units}")
    print(f"  Units with >=1 grounded FORGOTTEN cue: {forg_units}")
    
    anthropic_count = sum(1 for u in units if u.get("extraction", {}).get("extraction_model") == "claude-sonnet-5")
    gemini_count = sum(1 for u in units if u.get("extraction", {}).get("extraction_model") == "gemini-3.6-flash")
    print(f"\nUnits extracted per model:\n  claude-sonnet-5: {anthropic_count}\n  gemini-3.6-flash: {gemini_count}")
    
    print("\n=== THREE COMPLETE EXTRACTIONS VERBATIM ===")
    for i in range(min(3, len(units))):
        print(f"\n--- Unit {units[i]['id']} ({units[i].get('source')}) ---")
        print(json.dumps(units[i].get("extraction", {}), indent=2))
        
if __name__ == "__main__":
    main()
