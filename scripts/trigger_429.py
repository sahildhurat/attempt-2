import os
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

def trigger_429():
    url = f"https://generativelanguage.googleapis.com/v1alpha/models/gemini-3.8-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": "Hello, world!"}]}]
    }

    # Spam until 429
    for i in range(200):
        try:
            resp = requests.post(url, headers=headers, json=data)
            if resp.status_code == 429:
                print("=== 429 TRIGGERED ===")
                print(resp.json())
                break
            elif resp.status_code != 200:
                print("Error:", resp.status_code, resp.json())
                break
        except Exception as e:
            print("Request failed:", e)

if __name__ == "__main__":
    trigger_429()
