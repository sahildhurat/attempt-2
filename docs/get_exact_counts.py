import requests
import re
import time

CATEGORIES = [
    ("Search", "photos_searching"),
    ("Organisation", "photos_organize"),
    ("Albums", "photos_albums"),
    ("Manage", "photos_manage"),
    ("Sharing", "photos_sharing"),
    ("Storage", "photos_storage")
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"
}

print("Category | Threads")

for name, cat_id in CATEGORIES:
    url = f"https://support.google.com/photos/threads?hl=en&thread_filter=(category%3A{cat_id})&max_results=500"
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                matches = set(re.findall(r'data-stats-id="(\d+)"', resp.text))
                print(f"{name} | {len(matches)} threads")
                break
            else:
                print(f"{name} | Failed {resp.status_code}")
                break
        except Exception as e:
            time.sleep(2)
            if attempt == 2:
                print(f"{name} | Timeout/Error")
