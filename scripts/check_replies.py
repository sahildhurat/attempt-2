import json

def report_thread(tid):
    try:
        with open(f"thread_{tid}_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        print(f"\n--- Thread {tid} ---")
        if not data:
            print("No data")
            return
            
        # The data format from phase A was usually a list of dicts.
        if isinstance(data, list):
            replies = [x for x in data if x.get("is_reply")]
            print(f"Reply count in JSON: {len(replies)}")
            for r in replies:
                print(f"  Reply ID: {r.get('id', r.get('source_id'))} - len {len(r.get('text', ''))}")
        elif isinstance(data, dict):
            replies = data.get("replies", [])
            print(f"Reply count in JSON: {len(replies)}")
            for r in replies:
                print(f"  Reply ID: {r.get('id', r.get('source_id'))} - len {len(r.get('text', ''))}")
    except Exception as e:
        print(f"Error on {tid}: {e}")

report_thread("367230169")
report_thread("319380955")
