import json
import re
import html
import string
from collections import Counter

def classify_drop(span, text):
    t = text.lower()
    s = span.lower()
    if s in t: return "case_insensitive_match"
    if re.sub(r'\s+', '', s) in re.sub(r'\s+', '', t): return "whitespace_difference"
    if s.strip(string.punctuation) in t: return "punctuation_difference"
    if html.unescape(s) in t or html.unescape(s) in html.unescape(t) or s in html.unescape(t): return "html_entity_difference"
    
    # check for truncation / partial match (e.g. they dropped a word at the end)
    # simplest check: if a large substring of s is in t
    if len(s) > 10 and s[:int(len(s)*0.8)] in t: return "truncation_suffix"
    if len(s) > 10 and s[int(len(s)*0.2):] in t: return "truncation_prefix"
    
    return "paraphrase_or_hallucinated"

def format_unit(unit):
    text = unit.get("text", "")
    if unit.get("is_reply"):
        parent = unit.get("parent_text", "")
        text = f"[PARENT POST]\n{parent}\n\n[REPLY]\n{text}"
    return text

def main():
    units = []
    with open('data/pass2/extracted_units.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip(): units.append(json.loads(line))
            
    print("1. GROUNDING TABLE (720 units)")
    rem_ret, rem_gr, rem_drop = 0, 0, 0
    forg_ret, forg_gr, forg_drop = 0, 0, 0
    
    drop_reasons = []
    
    for u in units:
        ext = u.get("extraction", {})
        rem_g = len(ext.get("remembered", []))
        forg_g = len(ext.get("forgotten", []))
        
        rem_gr += rem_g
        forg_gr += forg_g
        
        text = format_unit(u)
        for drop in ext.get("dropped_cues", []):
            field = drop.get("original_field")
            span = drop.get("span", "")
            reason = classify_drop(span, text)
            drop_reasons.append(reason)
            
            if field == "remembered": rem_drop += 1
            if field == "forgotten": forg_drop += 1
            
    rem_ret = rem_gr + rem_drop
    forg_ret = forg_gr + forg_drop
    
    rem_pct = (rem_drop/rem_ret*100) if rem_ret else 0
    forg_pct = (forg_drop/forg_ret*100) if forg_ret else 0
    
    print(f"  Remembered: Returned {rem_ret} | Grounded {rem_gr} | Dropped {rem_drop} ({rem_pct:.1f}%)")
    print(f"  Forgotten:  Returned {forg_ret} | Grounded {forg_gr} | Dropped {forg_drop} ({forg_pct:.1f}%)")
    
    print("\nMost common REASONS spans failed to resolve:")
    for reason, count in Counter(drop_reasons).most_common(10):
        print(f"  {reason}: {count}")

    print("\n2. MEMORY MAP DENOMINATORS BY SOURCE")
    sources = set(u.get("source", "unknown") for u in units)
    for src in sources:
        src_units = [u for u in units if u.get("source", "unknown") == src]
        rem_u = 0
        forg_u = 0
        both_u = 0
        tot_rem = 0
        tot_forg = 0
        for u in src_units:
            ext = u.get("extraction", {})
            rg = len(ext.get("remembered", []))
            fg = len(ext.get("forgotten", []))
            if rg > 0: rem_u += 1
            if fg > 0: forg_u += 1
            if rg > 0 and fg > 0: both_u += 1
            tot_rem += rg
            tot_forg += fg
        print(f"  {src}:")
        print(f"    Units w/ >=1 grounded REMEMBERED: {rem_u}")
        print(f"    Units w/ >=1 grounded FORGOTTEN: {forg_u}")
        print(f"    Units w/ BOTH: {both_u}")
        print(f"    Total grounded REMEMBERED cues: {tot_rem}")
        print(f"    Total grounded FORGOTTEN cues: {tot_forg}")

    print("\n3. THREE COMPLETE EXTRACTIONS (Different sources)")
    seen_sources = set()
    for u in units:
        src = u.get("source", "unknown")
        if src not in seen_sources:
            seen_sources.add(src)
            print(f"\n--- SOURCE: {src} | UNIT ID: {u['id']} ---")
            print(json.dumps(u.get("extraction"), indent=2))
            if len(seen_sources) >= 3: break

    print("\n4. FIELD COVERAGE (by completeness)")
    for comp in ["full", "snippet"]:
        comp_units = [u for u in units if u.get("text_completeness") == comp]
        if not comp_units: continue
        print(f"  Completeness: {comp} ({len(comp_units)} units)")
        fields = ["target", "evidence_quote", "remembered", "forgotten", "breakdown", "workaround"]
        for fld in fields:
            # For lists like remembered/forgotten, non-null means length > 0
            if fld in ["remembered", "forgotten"]:
                c = sum(1 for u in comp_units if len(u.get("extraction", {}).get(fld, [])) > 0)
            else:
                c = sum(1 for u in comp_units if u.get("extraction", {}).get(fld))
            print(f"    {fld}: {c}")

if __name__ == '__main__':
    main()
