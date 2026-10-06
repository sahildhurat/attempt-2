import json
import os

def format_unit(unit):
    text = unit.get("text", "")
    if unit.get("is_reply"):
        parent_text = unit.get("parent_text", "")
        text = f"[PARENT POST]\n{parent_text}\n\n[REPLY]\n{text}"
    return text

def main():
    final_list = []
    
    with open("data/gate_results.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                u = json.loads(line)
                if u.get("gate_decision") == "yes":
                    if len(format_unit(u)) >= 250:
                        final_list.append(u)
                            
    final_list.sort(key=lambda x: x["id"])
    
    os.makedirs("data/pass2", exist_ok=True)
    with open("data/pass2/target_list.jsonl", "w", encoding="utf-8") as f:
        for u in final_list:
            f.write(json.dumps(u) + "\n")
            
    print(f"Total units available and selected: {len(final_list)}")

if __name__ == "__main__":
    main()
