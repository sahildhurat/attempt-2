import json
import html
import re
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def format_unit(unit):
    text = unit.get("text", "")
    if unit.get("is_reply"):
        parent = unit.get("parent_text", "")
        text = f"[PARENT POST]\n{parent}\n\n[REPLY]\n{text}"
    return text

def main():
    units = []
    with open("data/pass2/extracted_units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip(): units.append(json.loads(line))

    with open("analysis_output.txt", "w", encoding="utf-8") as out:
        def p(msg): out.write(str(msg) + "\n")
        
        # 1. FORGOTTEN ASYMMETRY
        p("=== 1. FORGOTTEN ASYMMETRY ===\n")
        p("--- 10 UNITS > 500 CHARACTERS WITH ZERO FORGOTTEN CUES ---")
        count = 0
        for u in units:
            text = format_unit(u)
            ext = u.get("extraction", {})
            if len(text) > 500 and len(ext.get("forgotten", [])) == 0 and len(ext.get("dropped_cues", [])) == 0:
                p(f"\n[UNIT {u['id']} - SOURCE: {u['source']} - LEN: {len(text)}]")
                p(f"TEXT:\n{text}")
                count += 1
                if count >= 10: break

        p("\n--- ALL 60 FORGOTTEN CUES ---")
        cues_printed = 0
        for u in units:
            ext = u.get("extraction", {})
            for c in ext.get("forgotten", []):
                p(f"ID: {u['id']} | CUE: {c['cue']} | SPAN: {c['span']}")
                cues_printed += 1
        p(f"Total forgotten cues printed: {cues_printed}\n")

        # 2. GROUND BREAKDOWN AND WORKAROUND
        p("=== 2. GROUND breakdown AND workaround ===\n")
        metrics = {
            "full": {"breakdown": {"grounded":0, "unverifiable":0, "failed":0, "total":0},
                     "workaround": {"grounded":0, "unverifiable":0, "failed":0, "total":0}},
            "snippet": {"breakdown": {"grounded":0, "unverifiable":0, "failed":0, "total":0},
                        "workaround": {"grounded":0, "unverifiable":0, "failed":0, "total":0}}
        }
        
        for u in units:
            ext = u.get("extraction", {})
            comp = u.get("text_completeness", "snippet")
            text_lower = format_unit(u).lower()
            
            for field in ["breakdown", "workaround"]:
                if ext.get(field):
                    metrics[comp][field]["total"] += 1
                    q = ext.get(f"{field}_quote")
                    if not q:
                        metrics[comp][field]["unverifiable"] += 1
                    elif q.lower() in text_lower:
                        metrics[comp][field]["grounded"] += 1
                    else:
                        metrics[comp][field]["failed"] += 1
                        
        for comp in ["full", "snippet"]:
            p(f"--- {comp.upper()} UNITS ---")
            for field in ["breakdown", "workaround"]:
                m = metrics[comp][field]
                tot = m["total"]
                if tot > 0:
                    p(f"{field}: Total {tot} | Grounded {m['grounded']} ({m['grounded']/tot*100:.1f}%) | "
                          f"Unverifiable {m['unverifiable']} | Failed {m['failed']}")
            p("")

        # 3. FIX THE NORMALISATION
        p("=== 3. FIX THE NORMALISATION ===\n")
        html_entity_pattern = re.compile(r'&[a-zA-Z]+;|&#\d+;')
        sources_with_html = {}
        for u in units:
            text = format_unit(u)
            if html_entity_pattern.search(text):
                src = u.get("source", "unknown")
                sources_with_html[src] = sources_with_html.get(src, 0) + 1
                
        p("Sources still containing raw HTML entities:")
        for src, c in sources_with_html.items():
            p(f"  {src}: {c} units")
            
        recovered_rem = 0
        recovered_forg = 0
        
        for u in units:
            ext = u.get("extraction", {})
            text = format_unit(u)
            norm_text = html.unescape(text).lower()
            
            for drop in ext.get("dropped_cues", []):
                field = drop.get("original_field")
                span = drop.get("span", "")
                if not span: continue
                
                if span.lower() in norm_text or html.unescape(span).lower() in norm_text:
                    if field == "remembered": recovered_rem += 1
                    if field == "forgotten": recovered_forg += 1
                    
        p(f"\nRe-run over normalised text:")
        p(f"Recovered REMEMBERED drops: {recovered_rem} (out of 25)")
        p(f"Recovered FORGOTTEN drops: {recovered_forg} (out of 1)")

if __name__ == '__main__':
    main()
