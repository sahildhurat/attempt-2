"""
App Store collector.

Uses the public RSS feed for customer reviews of Google Photos on iOS.
Multiple storefronts: us, gb, in (as specified in context.md §3.1).
Source type: review.

The RSS feed URL pattern:
  https://itunes.apple.com/{storefront}/rss/customerreviews/id=962194608/sortBy=mostRecent/page={page}/json

Google Photos iOS app ID: 962194608
"""
import json
import os
import hashlib
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def log_failure(collector_name, failure_type, details):
    with open(f"data/raw/{collector_name}/failures.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": failure_type, "details": details}) + "\n")

def generate_id(source, source_id):
    return hashlib.sha256(f"{source}_{source_id}".encode()).hexdigest()

APP_ID = "962194608"  # Google Photos iOS app
STOREFRONTS = ["us", "gb", "in", "au", "ca"]
MAX_PAGES = 10  # RSS feed allows up to 10 pages of 50 reviews each

HEADERS = {
    "User-Agent": "DiscoveryEngine/1.0 (academic research)"
}


def collect():
    os.makedirs("data/raw/appstore", exist_ok=True)
    os.makedirs("data/unified", exist_ok=True)

    all_units = []
    storefront_counts = {}

    for sf in STOREFRONTS:
        sf_count = 0
        print(f"\nStorefront: {sf}")

        for page in range(1, MAX_PAGES + 1):
            url = (
                f"https://itunes.apple.com/{sf}/rss/customerreviews"
                f"/id={APP_ID}/page={page}/json"
            )

            session = get_session()
            

            try:
                response = fetch_with_rate_limit(session, "GET", url, "appstore", timeout=15)
                response.raise_for_status()
                try:
                    data = response.json()
                except Exception as e:
                    log_failure("appstore", "PARSE", f"sf: {sf}, page: {page}, error: {e}")
                    break
                    
                entries = data.get("feed", {}).get("entry", [])
                if not entries:
                    if page == 1:
                        log_failure("appstore", "EMPTY", f"sf: {sf}, page: {page} returned no entries")
                    print(f"  Page {page}: no entries, stopping")
                    break

                # First entry is sometimes the app metadata, skip it
                for entry in entries:
                    # Review entries have "im:rating" and "content"
                    if "im:rating" not in entry:
                        continue

                    review_id = entry.get("id", {}).get("label", "")
                    title = entry.get("title", {}).get("label", "")
                    content = entry.get("content", {}).get("label", "")
                    rating = int(entry.get("im:rating", {}).get("label", "0"))
                    author = entry.get("author", {}).get("name", {}).get("label", "")
                    created_at = entry.get("updated", {}).get("label", "")

                    if not content or len(content.strip()) < 10:
                        continue

                    text = f"{title}\n{content}" if title else content

                    unit = {
                        "id": generate_id("appstore", review_id),
                        "source": "appstore",
                        "source_type": "review",
                        "source_id": review_id,
                        "url": None,
                        "text": text,
                        "created_at": created_at,
                        "is_reply": False,
                        "parent_id": None,
                        "rating": rating,
                        "context": f"Google Photos App Store review ({rating} stars, {sf})",
                        "storefront": sf,
                        "author_hash": hashlib.sha256(author.encode()).hexdigest() if author else None,
                    }
                    all_units.append(unit)
                    sf_count += 1

                print(f"  Page {page}: {len([e for e in entries if 'im:rating' in e])} reviews")

            except Exception as e:
                if isinstance(e, requests.exceptions.RequestException):
                    log_failure("appstore", "NETWORK", f"sf: {sf}, page: {page}, error: {e}")
                    if hasattr(e.response, 'status_code') and e.response.status_code in [403, 404]:
                        break
                break

            time.sleep(1)

        storefront_counts[sf] = sf_count
        print(f"  Total for {sf}: {sf_count}")

    # Deduplicate
    unique_units = {}
    for u in all_units:
        if u["id"] not in unique_units:
            unique_units[u["id"]] = u

    # Save raw counts
    with open("data/raw/appstore/storefront_counts.json", "w") as f:
        json.dump(storefront_counts, f, indent=2)

    # Save unified
        out_file = "data/unified/appstore.jsonl"
    tmp_file = out_file + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        for u in unique_units.values():
            f.write(json.dumps(u, default=str) + "\n")
    if os.path.exists(tmp_file):
        os.replace(tmp_file, out_file)

    print(f"\n=== App Store Summary ===")
    for sf, count in storefront_counts.items():
        print(f"  {sf}: {count}")
    print(f"Total before dedup: {len(all_units)}")
    print(f"Total after dedup:  {len(unique_units)}")
    return len(unique_units)


if __name__ == "__main__":
    collect()
