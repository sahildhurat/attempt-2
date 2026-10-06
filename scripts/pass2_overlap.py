import json

def get_cues(ext, field):
    cues = ext.get(field, [])
    # Filter for grounded cues? The instruction asks for "agreement on cue count, cue content, and span validity"
    return [(c.get("cue", "").lower(), c.get("span", "").lower()) for c in cues]

def main():
    overlap_units = []
    with open("data/pass2/extracted_units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                u = json.loads(line)
                if "gemini_overlap_extraction" in u:
                    overlap_units.append(u)
                    
    if not overlap_units:
        print("No overlap units found. Fallback might not have triggered.")
        return
        
    print(f"Analyzing overlap for {len(overlap_units)} units...")
    
    total_anthropic_cues = 0
    total_gemini_cues = 0
    exact_match_cues = 0
    
    for u in overlap_units:
        a_ext = u.get("extraction", {})
        g_ext = u.get("gemini_overlap_extraction", {})
        
        a_cues = get_cues(a_ext, "remembered") + get_cues(a_ext, "forgotten")
        g_cues = get_cues(g_ext, "remembered") + get_cues(g_ext, "forgotten")
        
        total_anthropic_cues += len(a_cues)
        total_gemini_cues += len(g_cues)
        
        # A simple matching metric: how many Gemini cues exactly match Anthropic's cue + span
        for g_cue in g_cues:
            if g_cue in a_cues:
                exact_match_cues += 1
                
    agreement = (exact_match_cues / total_anthropic_cues * 100) if total_anthropic_cues > 0 else 0
    
    print(f"Anthropic total cues: {total_anthropic_cues}")
    print(f"Gemini total cues: {total_gemini_cues}")
    print(f"Exact match cues: {exact_match_cues}")
    print(f"Agreement on content & span validity: {agreement:.1f}%")

if __name__ == "__main__":
    main()
