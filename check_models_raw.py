import os
import sys
import json
import urllib.request
import urllib.error
from datetime import date
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("ANTHROPIC_API_KEY not found in .env")
    sys.exit(1)

models_to_test = {
    "pass1_gate": "claude-haiku-4-5-20251001",
    "pass2_extract": "claude-sonnet-5",
    "pass3_induction": "claude-sonnet-5",
    "pass3_assignment": "claude-sonnet-5"
}

results = {}
failed = False
available_models = []

def call_anthropic(model_str):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": model_str,
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "hello"}]
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read()
            res_json = json.loads(res_body)
            return True, res_json.get("model", "")
    except urllib.error.HTTPError as e:
        err_body = e.read()
        return False, f"HTTPError {e.code}: {err_body.decode('utf-8')}"
    except Exception as e:
        return False, str(e)

def get_models():
    url = "https://api.anthropic.com/v1/models"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    req = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read()
            res_json = json.loads(res_body)
            return [m["id"] for m in res_json.get("data", [])]
    except Exception as e:
        print("Failed to get models list", e)
        return []

print("Fetching available models...")
available_models = get_models()

for name, model_str in models_to_test.items():
    print(f"Testing {name}: {model_str}")
    success, echoed_model = call_anthropic(model_str)
    if success:
        print(f"Success! Echoed model: {echoed_model}")
        results[name] = echoed_model
    else:
        print(f"Failed! Error: {echoed_model}")
        failed = True

if failed:
    print("\nSome models failed to resolve.")
    print("Available models according to API:")
    for m in available_models:
        print(m)
else:
    print("\nAll models resolved!")
    config_dir = "config"
    os.makedirs(config_dir, exist_ok=True)
    with open(os.path.join(config_dir, "models.json"), "w") as f:
        json.dump({
            "confirmed": True,
            "date": str(date.today()),
            "models": results
        }, f, indent=2)
    print("Wrote to config/models.json")
