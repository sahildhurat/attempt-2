import json

def run():
    units = []
    with open("data/unified/units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            units.append(json.loads(line))
            
    for u in units:
        text_len = len(u.get("text", "")) + len(u.get("context", ""))
        source = u.get("source", "")
        
        # Floor: 100 characters. If it's shorter, it's considered a snippet.
        if source == "help_community":
            u["text_completeness"] = "full" if text_len >= 100 else "snippet"
        elif source == "youtube":
            u["text_completeness"] = "full" if text_len >= 50 else "snippet"
        else:
            u["text_completeness"] = "full"
            
    with open("data/unified/units.jsonl", "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps(u) + "\n")
            
if __name__ == "__main__":
    run()
