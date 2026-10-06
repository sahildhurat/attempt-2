import os
import sys
import json
from datetime import date
from dotenv import load_dotenv

load_dotenv()

try:
    import anthropic
except ImportError:
    print("anthropic not installed")
    sys.exit(1)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

models_to_test = {
    "pass1_gate": "claude-haiku-4-5-20251001",
    "pass2_extract": "claude-sonnet-5",
    "pass3_induction": "claude-sonnet-5",
    "pass3_assignment": "claude-sonnet-5"
}

results = {}
failed = False

try:
    available_models = [m.id for m in client.models.list()]
except Exception as e:
    print(f"Error fetching models: {e}")
    available_models = []

for name, model_str in models_to_test.items():
    print(f"Testing {name}: {model_str}")
    try:
        response = client.messages.create(
            model=model_str,
            max_tokens=10,
            messages=[{"role": "user", "content": "hello"}]
        )
        echoed_model = response.model
        print(f"Success! Echoed model: {echoed_model}")
        results[name] = echoed_model
    except Exception as e:
        print(f"Failed! Error: {e}")
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
