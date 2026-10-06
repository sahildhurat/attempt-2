import json

def run_checks(extracted_units):
    # Check 1 to 3 would be here
    
    # Check 4 — Per-cue grounding
    stats = {
        "remembered": {"total": 0, "grounded": 0, "dropped": 0},
        "forgotten": {"total": 0, "grounded": 0, "dropped": 0}
    }
    
    for unit in extracted_units:
        if "text" not in unit:
            raise ValueError(f"Missing 'text' field in unit: {unit.get('id', 'unknown')}")
            
        for field in ("remembered", "forgotten"):
            kept, dropped = [], []
            extraction_data = unit.get("extraction", unit)
            for item in extraction_data.get(field, []):
                stats[field]["total"] += 1
                if item.get("span") and item["span"] in unit["text"]:
                    kept.append(item)
                    stats[field]["grounded"] += 1
                else:
                    dropped.append(item)
                    stats[field]["dropped"] += 1
                    
            unit[field] = kept
            unit.setdefault("dropped_cues", {})[field] = dropped
            
    # Reporting
    report_lines = ["--- Grounding Check 4 Report ---"]
    halt_error = None
    for field in ("remembered", "forgotten"):
        tot = stats[field]["total"]
        grd = stats[field]["grounded"]
        drp = stats[field]["dropped"]
        drp_pct = (drp / tot * 100) if tot > 0 else 0
        grd_pct = (grd / tot * 100) if tot > 0 else 0
        report_lines.append(f"{field.capitalize()}: {tot} cues total. Grounded: {grd} ({grd_pct:.1f}%). Dropped: {drp} ({drp_pct:.1f}%).")
        
        if drp_pct > 10.0:
            halt_error = RuntimeError(f"HALT: '{field}' field drop rate exceeds 10% ({drp_pct:.1f}%). Prompt needs tightening before proceeding.")
            
    print("\n".join(report_lines))
    
    with open("pass2_report.txt", "a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(report_lines) + "\n")
        
    try:
        with open("summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
    except FileNotFoundError:
        summary = {}
        
    summary["pass2_grounding"] = stats
    with open("summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
            
    if halt_error:
        raise halt_error

    return extracted_units
