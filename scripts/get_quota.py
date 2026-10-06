import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

def trigger():
    url = f"https://generativelanguage.googleapis.com/v1alpha/models/gemini-3.8-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": "Hello"}]}]}
    for _ in range(50):
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 429:
            data = resp.json()
            details = data.get("error", {}).get("details", [])
            for d in details:
                if d.get("@type") == "type.googleapis.com/google.rpc.QuotaFailure":
                    print("--- ENTIRE VIOLATIONS ARRAY ---")
                    import json
                    print(json.dumps(d.get("violations", []), indent=2))
                    return
            break

if __name__ == "__main__":
    trigger()
