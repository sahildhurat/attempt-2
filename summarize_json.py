import json

def summarize(data):
    if isinstance(data, dict):
        return {k: summarize(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [summarize(v) for v in data]
    elif isinstance(data, str):
        if len(data) > 50:
            return f"<str, len={len(data)}>"
        return data
    else:
        return data

if __name__ == "__main__":
    data = json.load(open('thread_319380955_data.json', encoding='utf-8'))
    print("=== ROOT[0] ===")
    print(json.dumps(summarize(data[0]), indent=2)[:500])
    print("=== ROOT[3] ===")
    print(json.dumps(summarize(data[3]), indent=2))
