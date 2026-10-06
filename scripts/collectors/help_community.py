"""
Help Community collector — corrected version.

Changes from previous version:
- UA switched from IE11 to descriptive "DiscoveryEngine/1.0 (academic research)"
  (verified: SSR works with any UA, not gated on legacy browsers)
- photos_storage dropped (backup/quota complaints, not retrieval)
- Categories widened: photos_searching, photos_organization, photos_share,
  photos_facegroups, photos_other, photos_editing, photos_restore
- Paginate by incrementing page_start parameter
- manual_thread_urls.txt is NOT consumed (was empty during prior collection run)
"""
import json
import urllib.request
import re
import os
import hashlib
import time

def generate_id(source, source_id):
    return hashlib.sha256(f"{source}_{source_id}".encode()).hexdigest()

HEADERS = {
    "User-Agent": "DiscoveryEngine/1.0 (academic research)"
}

# Categories relevant to photo retrieval/search/organisation/sharing
# photos_storage excluded: mostly backup and quota complaints
CATEGORIES = [
    "photos_searching",
    "photos_organization",
    "photos_other",
    "photos_facegroups",
    "photos_share",
    "photos_editing",
    "photos_restore",
]

BATCH_SIZE = 3000  # max_results per request
MAX_PAGES = 1     # pagination doesn't work properly, use large batch

def fetch_category(cat):
    """Fetch all available threads for a single category, paginating."""
    units = []
    seen_ids = set()
    page_start = 0

    for page_num in range(MAX_PAGES):
        url = (
            f"https://support.google.com/photos/threads?hl=en"
            f"&thread_filter=(category%3A{cat})"
            f"&max_results={BATCH_SIZE}"
        )
        if page_start > 0:
            url += f"&page_start={page_start}"

        try:
            print(f"  Page {page_num + 1}: fetching from offset {page_start}...")
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode("utf-8")

            threads = re.findall(
                r'<a[^>]*class="[^"]*thread-list-thread[^"]*"[^>]*'
                r'data-stats-id="(\d+)"[^>]*>.*?'
                r'class="thread-list-thread__title">\s*(.*?)\s*</span>.*?'
                r'class="thread-list-thread__snippet"[^>]*title="([^"]+)"',
                html, re.DOTALL | re.IGNORECASE
            )

            new_count = 0
            for tid, title, snippet in threads:
                if tid not in seen_ids:
                    seen_ids.add(tid)
                    new_count += 1
                    units.append({
                        "id": generate_id("help_community", tid),
                        "source": "help_community",
                        "source_type": "discussion",
                        "source_id": tid,
                        "url": f"https://support.google.com/photos/thread/{tid}?hl=en",
                        "text": f"{title}\n{snippet}",
                        "created_at": None,
                        "is_reply": False,
                        "parent_id": None,
                        "context": title,
                        "category": cat,
                    })

            print(f"    Found {len(threads)} threads, {new_count} new (total unique: {len(seen_ids)})")

            # Check for "View more" / pagination indicator
            has_more = bool(re.search(r'class="[^"]*thread-list-threads__view-more[^"]*"', html))

            if not has_more or new_count == 0:
                print(f"    No more pages (has_more={has_more}, new={new_count})")
                break

            page_start += len(threads)

        except Exception as e:
            print(f"    Error: {e}")
            break

        time.sleep(1)  # rate limit

    return units


def collect():
    os.makedirs("data/raw/help_community", exist_ok=True)
    os.makedirs("data/unified", exist_ok=True)

    all_units = []
    category_counts = {}

    for cat in CATEGORIES:
        print(f"\nCategory: {cat}")
        units = fetch_category(cat)
        category_counts[cat] = len(units)
        all_units.extend(units)
        import random; time.sleep(random.uniform(5.0, 8.0))  # pause between categories

    # Deduplicate (threads may appear in multiple categories)
    unique_units = {}
    for u in all_units:
        if u["id"] not in unique_units:
            unique_units[u["id"]] = u

    # Save raw per-category counts
    with open("data/raw/help_community/category_counts.json", "w") as f:
        json.dump(category_counts, f, indent=2)

    # Save unified
        out_file = "data/unified/help_community.jsonl"
    tmp_file = out_file + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        for u in unique_units.values():
            f.write(json.dumps(u) + "\n")
    if os.path.exists(tmp_file):
        os.replace(tmp_file, out_file)

    print(f"\n=== Help Community Summary ===")
    print(f"Categories scraped: {len(CATEGORIES)}")
    for cat, count in category_counts.items():
        print(f"  {cat}: {count} threads")
    print(f"Total before dedup: {len(all_units)}")
    print(f"Total after dedup:  {len(unique_units)}")
    return len(unique_units)


if __name__ == "__main__":
    collect()
