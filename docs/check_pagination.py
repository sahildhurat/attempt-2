import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import time
import re

CATEGORIES = [
    ("Search", "photos_searching"),
    ("Organisation", "photos_organize"),
    ("Albums", "photos_albums"),
    ("Manage", "photos_manage"),
    ("Sharing", "photos_sharing"),
    ("Storage", "photos_storage")
]

# IE11 user agent triggers Google's SSR fallback for the Help Community
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"
}

def fetch_category(category_id, max_results=500):
    url = f"https://support.google.com/photos/threads?hl=en&thread_filter=(category%3A{category_id})&max_results={max_results}"
    req = urllib.request.Request(url, headers=HEADERS)
    print(f"Fetching {category_id}...")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            threads = soup.find_all('a', class_=re.compile(r'thread-list-thread'))
            
            # Extract dates/timestamps
            date_groups = soup.find_all('div', class_='thread-list-group__heading')
            oldest_date = date_groups[-1].text.strip() if date_groups else "Unknown"
            
            # Check for pagination / view more
            view_more = soup.find('button', class_=re.compile(r'load-more-button'))
            
            return {
                "count": len(threads),
                "has_more": bool(view_more),
                "oldest_group": oldest_date
            }
    except Exception as e:
        return {"error": str(e)}

print(f"{'Category':<15} | {'Count':<6} | {'Has More':<8} | {'Oldest Group'}")
print("-" * 55)

for cat_name, cat_id in CATEGORIES:
    result = fetch_category(cat_id, 1000) # Try a large max_results
    if "error" in result:
        print(f"{cat_name:<15} | ERROR: {result['error']}")
    else:
        print(f"{cat_name:<15} | {result['count']:<6} | {str(result['has_more']):<8} | {result['oldest_group']}")
    time.sleep(1)
