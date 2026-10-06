import json
import html
import re

def format_unit(unit):
    text = unit.get("text", "")
    if unit.get("is_reply"):
        parent = unit.get("parent_text", "")
        text = f"[PARENT POST]\n{parent}\n\n[REPLY]\n{text}"
    return text

def reclassify_forgotten(cue, span):
    c_lower = cue.lower()
    s_lower = span.lower()
    nav_keywords = ["cannot find", "find the setting", "where the", "how to access", "3 dots", "unhide", "find how", "where is", "figure out anyway", "where to find", "find locker folder", "find the lock folder", "how to see it"]
    prod_keywords = ["no place name", "no distinguishing numbering", "automatically create", "no name to show", "doesn't give the photos"]
    
    combined = c_lower + " " + s_lower
    for nk in nav_keywords:
        if nk in combined: return "navigation_gap"
    for pk in prod_keywords:
        if pk in combined: return "product_gap"
    
    if "remember" in combined or "forget" in combined or "forgot" in combined or "recall" in combined or "date" in combined or "when" in combined or "time" in combined or "name" in combined or "who" in combined or "exact pattern" in combined:
        return "memory_gap"
    
    # default heuristics
    if "where" in combined or "how" in combined or "find" in combined or "locate" in combined or "see albums" in combined:
        return "navigation_gap"
        
    if "no specific" in combined or "no other" in combined or "doesn't always mean" in combined or "skip them" in combined:
        return "product_gap"
        
    return "memory_gap"

def main():
    units = []
    with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip(): units.append(json.loads(line))

    # 1. Exclude ungrounded fields
    excluded_breakdowns = 0
    excluded_workarounds = 0
    for u in units:
        ext = u.get("extraction", {})
        comp = u.get("text_completeness", "snippet")
        
        # Snippets should have these fields set to null if they exist
        if comp == "snippet":
            if ext.get("breakdown"):
                ext["breakdown"] = None
                excluded_breakdowns += 1
            if ext.get("workaround"):
                ext["workaround"] = None
                excluded_workarounds += 1

        # Also for full units, if ungrounded, set to null
        text_lower = format_unit(u).lower()
        if comp == "full":
            bq = ext.get("breakdown_quote")
            if ext.get("breakdown") and (not bq or bq.lower() not in text_lower):
                ext["breakdown"] = None
                excluded_breakdowns += 1
                
            wq = ext.get("workaround_quote")
            if ext.get("workaround") and (not wq or wq.lower() not in text_lower):
                ext["workaround"] = None
                excluded_workarounds += 1

    # 2. Apply Normalization Fix
    html_sources = ["help_community", "stackexchange", "hn"]
    recovered_rem = 0
    recovered_forg = 0
    
    for u in units:
        src = u.get("source", "unknown")
        if src in html_sources:
            if "text" in u: u["text"] = html.unescape(u["text"])
            if "parent_text" in u and u["parent_text"]: u["parent_text"] = html.unescape(u["parent_text"])
            
        ext = u.get("extraction", {})
        norm_text = format_unit(u).lower()
        
        new_dropped = []
        for drop in ext.get("dropped_cues", []):
            field = drop.get("original_field")
            span = drop.get("span", "")
            
            # Check if now grounded
            if span and (span.lower() in norm_text or html.unescape(span).lower() in norm_text):
                if html.unescape(span).lower() in norm_text:
                    drop["span"] = html.unescape(span) # fix the span to match the unescaped text
                
                # Move back to original field
                if field == "remembered": 
                    ext["remembered"] = ext.get("remembered", []) + [{"cue": drop["cue"], "span": drop["span"]}]
                    recovered_rem += 1
                elif field == "forgotten":
                    ext["forgotten"] = ext.get("forgotten", []) + [{"cue": drop["cue"], "span": drop["span"]}]
                    recovered_forg += 1
            else:
                new_dropped.append(drop)
                
        ext["dropped_cues"] = new_dropped

    # 3. Reclassify Forgotten Cues
    gap_counts = {"memory_gap": 0, "navigation_gap": 0, "product_gap": 0}
    for u in units:
        ext = u.get("extraction", {})
        for fg in ext.get("forgotten", []):
            gap_type = reclassify_forgotten(fg["cue"], fg["span"])
            fg["gap_type"] = gap_type
            gap_counts[gap_type] += 1

    # Overwrite the updated units
    with open('data/pass2/extracted_units.jsonl', 'w', encoding='utf-8') as f:
        for u in units:
            f.write(json.dumps(u) + '\n')

    # Final Grounding Table Calculation
    rem_ret, rem_gr, rem_drop = 0, 0, 0
    forg_ret, forg_gr, forg_drop = 0, 0, 0
    
    for u in units:
        ext = u.get("extraction", {})
        rem_gr += len(ext.get("remembered", []))
        forg_gr += len(ext.get("forgotten", []))
        for drop in ext.get("dropped_cues", []):
            fld = drop.get("original_field")
            if fld == "remembered": rem_drop += 1
            if fld == "forgotten": forg_drop += 1
            
    rem_ret = rem_gr + rem_drop
    forg_ret = forg_gr + forg_drop
    
    print(f"Exclusions: {excluded_breakdowns} breakdowns, {excluded_workarounds} workarounds.")
    print(f"Recoveries: {recovered_rem} remembered, {recovered_forg} forgotten.")
    print("\n=== FINAL GROUNDING TABLE ===")
    print(f"Remembered: Returned {rem_ret} | Grounded {rem_gr} | Dropped {rem_drop} ({rem_drop/rem_ret*100 if rem_ret else 0:.1f}%)")
    print(f"Forgotten:  Returned {forg_ret} | Grounded {forg_gr} | Dropped {forg_drop} ({forg_drop/forg_ret*100 if forg_ret else 0:.1f}%)")
    
    print("\n=== RECLASSIFIED FORGOTTEN CUES ===")
    for k,v in gap_counts.items():
        print(f"  {k}: {v}")

if __name__ == '__main__':
    main()
