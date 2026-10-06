import os, json, time, requests, random
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

PHOTO_TOKENS = ["photo", "photos", "pic", "picture", "image", "album", "memories"]
RETRIEVAL_TOKENS_NEW = ["find", "search", "look for", "locate", "remember", "recall", "where is", "where are", "scroll", "can't see", "missing", "show me", "showing", "disappeared", "gone", "won't come up", "nothing comes up", "no results"]

def pre_filter_unit_new(unit):
    text = (unit.get("text", "") + " " + unit.get("context", "")).lower()
    has_photo = any(t in text for t in PHOTO_TOKENS)
    has_retrieval = any(t in text for t in RETRIEVAL_TOKENS_NEW)
    source = unit.get("source", "")
    if source in ["help_community", "stackexchange"]:
        return has_retrieval
    return has_photo and has_retrieval

def format_unit(unit):
    text = unit.get("text", "")
    if unit.get("is_reply"):
        text = f"[PARENT POST]\n{unit.get('parent_text', '')}\n\n[REPLY]\n{text}"
    return text

def generate_content(prompt, content_text, schema):
    url = f"https://generativelanguage.googleapis.com/v1alpha/models/gemini-3.8-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": content_text}]}],
        "systemInstruction": {"parts": [{"text": prompt}]},
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json",
            "responseSchema": schema
        }
    }
    for attempt in range(20):
        try:
            resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            elif resp.status_code == 429:
                err = resp.json()
                delay = 5
                details = err.get("error", {}).get("details", [])
                for d in details:
                    if d.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                        delay = float(d.get("retryDelay", "5s").replace("s", ""))
                        break
                print(f"429 Hit. Sleep {delay}s")
                time.sleep(delay + 1)
            else:
                print(f"Error {resp.status_code}: {resp.text}")
                time.sleep(5)
        except Exception as e:
            print("Exception:", e)
            time.sleep(5)
    return {}

def run():
    with open("prompts/pass1_relevance_gate.md", "r", encoding="utf-8") as f:
        prompt = f.read()
    
    schema = {
        "type": "OBJECT",
        "properties": {
            "decisions": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "n": {"type": "INTEGER"},
                        "decision": {"type": "STRING"},
                        "reason": {"type": "STRING"}
                    }
                }
            }
        }
    }
    
    units = []
    with open("data/unified/units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            units.append(json.loads(line))
            
    rejected_new = [u for u in units if not pre_filter_unit_new(u)]
    random.seed(42)
    sample_200 = random.sample(rejected_new, min(200, len(rejected_new)))
    
    known_yes = []
    if os.path.exists("data/pass1/gated_units.jsonl"):
        with open("data/pass1/gated_units.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    u = json.loads(line)
                    if u.get("relevant") == "yes":
                        known_yes.append(u)
                        
    injected_10 = random.sample(known_yes, min(10, len(known_yes)))
    injected_ids = {u["id"] for u in injected_10}
    test_set = sample_200 + injected_10
    random.shuffle(test_set)
    
    batches = [test_set[i:i+25] for i in range(0, len(test_set), 25)]
    dist = {"yes": 0, "partial": 0, "no": 0, "missing/error": 0}
    received = 0
    injected_results = []
    
    for i, b in enumerate(batches):
        text_parts = []
        for idx, u in enumerate(b):
            text_parts.append(f"Unit {idx+1}:\n{format_unit(u)}\n")
        full_text = "\n".join(text_parts)
        
        print(f"Batch {i+1}/{len(batches)}")
        res = generate_content(prompt, full_text, schema)
        decisions = res.get("decisions", [])
        dec_map = {d.get("n"): d.get("decision") for d in decisions}
        
        for idx, u in enumerate(b):
            n = idx + 1
            decision = dec_map.get(n)
            if decision in ["yes", "partial", "no"]:
                dist[decision] += 1
                received += 1
            else:
                dist["missing/error"] += 1
                
            if u["id"] in injected_ids:
                injected_results.append(f"Injected {u['id'][:8]}: {decision}")
        
        time.sleep(3.5)
        
    with open("positive_control_results.txt", "w", encoding="utf-8") as f:
        f.write(f"Received decisions: {received}/{len(test_set)}\n")
        f.write(f"Distribution: {dist}\n")
        f.write("Injected unit results:\n")
        for r in injected_results:
            f.write(f"  {r}\n")
        f.write("\n10 Rejected Units (Raw Text):\n")
        for j, u in enumerate(sample_200[:10]):
            f.write(f"Unit {j+1}:\n{format_unit(u)}\n---\n")

if __name__ == "__main__":
    run()
