import json

def find_string(data, target, path="root"):
    if isinstance(data, dict):
        for k, v in data.items():
            find_string(v, target, path + f"['{k}']")
    elif isinstance(data, list):
        for i, v in enumerate(data):
            find_string(v, target, path + f"[{i}]")
    elif isinstance(data, str):
        if target in data:
            print(f"FOUND AT: {path}")
            print(f"Content: {data[:100]}...")
            print("---")

data = json.load(open('thread_367230169_data.json', encoding='utf-8'))
print("Searching for OP body...")
find_string(data, "This started happening yesterday")
print("Searching for REPLY...")
find_string(data, "Have you obtained administrative rights")
