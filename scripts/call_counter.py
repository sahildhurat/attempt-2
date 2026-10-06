import json
import os
import datetime

LOG_FILE = "data/daily_calls.json"

def log_success(model: str):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    counts = {}
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                counts = json.load(f)
        except Exception:
            pass
            
    if today not in counts:
        counts[today] = {}
        
    counts[today][model] = counts[today].get(model, 0) + 1
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    with open(LOG_FILE, "w") as f:
        json.dump(counts, f, indent=2)

def get_running_total():
    if not os.path.exists(LOG_FILE):
        return 0
    try:
        with open(LOG_FILE, "r") as f:
            counts = json.load(f)
        total = 0
        for day, models in counts.items():
            for m, count in models.items():
                total += count
        return total
    except Exception:
        return 0
