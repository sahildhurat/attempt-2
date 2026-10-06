"""
Hacker News collector.

Uses the public Algolia HN Search API (no auth required).
Source type: discussion.

API docs: https://hn.algolia.com/api
"""
import json
import urllib.parse
import os
import hashlib
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def generate_id(source, source_id):
    return hashlib.sha256(f"{source}_{source_id}".encode()).hexdigest()

HEADERS = {
    "User-Agent": "DiscoveryEngine/1.0 (academic research)"
}

# Search queries — broader than just "google photos search"
QUERIES = [
    "google photos",
    "google photos search",
    "google photos find",
    "google photos memory",
    "google photos organize",
    "google photos album",
    "google photos face recognition",
    "google photos AI",
    "google photos lost",
    "photo search",
    "photo retrieval",
    "photo organization",
]

# Also fetch by specific story IDs that are known to be relevant
# (HN stories about Google Photos)
HN_API_BASE = "https://hn.algolia.com/api/v1"


def search_hn(query, tags="(story,comment)", page=0, hits_per_page=100):
    """Search HN via Algolia API."""
    q = urllib.parse.quote(query)
    url = (
        f"{HN_API_BASE}/search"
        f"?query={q}&tags={tags}"
        f"&hitsPerPage={hits_per_page}&page={page}"
    )
    
    session = get_session()
    

    try:
        response = fetch_with_rate_limit(session, "GET", url, "hn", timeout=15)
        response.raise_for_status()
        try:
            return "SUCCESS", response.json()
        except Exception as e:
            return "PARSE", None
    except Exception as e:
        if "RATE_LIMITED" in str(e):
            log_failure("hn", "RATE_LIMITED", str(e))
            return [], [] # Or appropriate return value based on signature... Wait, this is tricky to do globally
        if isinstance(e, requests.exceptions.RequestException):
            return "NETWORK", None

def log_failure(collector_name, failure_type, details):
    with open(f"data/raw/{collector_name}/failures.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": failure_type, "details": details}) + "\n")

def collect():
    os.makedirs("data/raw/hn", exist_ok=True)
    os.makedirs("data/unified", exist_ok=True)

    all_units = []
    seen_ids = set()

    for query in QUERIES:
        print(f"\nSearching HN for: '{query}'...")

        # Search both stories and comments
        for tags in ["story", "comment"]:
            page = 0
            total_hits = 0

            while page < 5:  # max 5 pages per query
                status, result = search_hn(query, tags=tags, page=page)
                if status != "SUCCESS":
                    log_failure("hn", status, f"Query '{query}' page {page}")
                    break

                hits = result.get("hits", [])
                nb_pages = result.get("nbPages", 0)

                if not hits:
                    log_failure("hn", "EMPTY", f"Query '{query}' page {page} returned no hits")
                    break

                for hit in hits:
                    obj_id = hit.get("objectID", "")
                    if obj_id in seen_ids:
                        continue
                    seen_ids.add(obj_id)

                    # Build text from available fields
                    title = hit.get("title") or hit.get("story_title") or ""
                    comment_text = hit.get("comment_text") or ""
                    story_text = hit.get("story_text") or ""

                    text = ""
                    if comment_text:
                        text = comment_text
                    elif story_text:
                        text = f"{title}\n{story_text}" if title else story_text
                    elif title:
                        text = title
                    else:
                        continue

                    # Skip very short entries
                    if len(text.strip()) < 15:
                        continue

                    # Must be at least tangentially related to Google Photos
                    text_lower = text.lower()
                    if "google photo" not in text_lower and "gphotos" not in text_lower:
                        # For stories, check if title mentions it
                        title_lower = title.lower() if title else ""
                        if "google photo" not in title_lower and "gphotos" not in title_lower:
                            continue

                    is_comment = tags == "comment"
                    parent_id = hit.get("parent_id")
                    story_id = hit.get("story_id")

                    unit = {
                        "id": generate_id("hn", obj_id),
                        "source": "hn",
                        "source_type": "discussion",
                        "source_id": obj_id,
                        "url": hit.get("url") or f"https://news.ycombinator.com/item?id={obj_id}",
                        "text": text,
                        "created_at": hit.get("created_at"),
                        "is_reply": is_comment,
                        "parent_id": str(parent_id) if parent_id else None,
                        "context": title or hit.get("story_title", ""),
                        "author_hash": hashlib.sha256(hit.get("author", "").encode()).hexdigest() if hit.get("author") else None,
                        "points": hit.get("points"),
                    }
                    all_units.append(unit)
                    total_hits += 1

                page += 1
                if page >= nb_pages:
                    break
                time.sleep(0.5)

            print(f"  {tags}: {total_hits} hits")

        time.sleep(1)  # rate limit between queries

    # Deduplicate
    unique_units = {}
    for u in all_units:
        if u["id"] not in unique_units:
            unique_units[u["id"]] = u

    # Save unified
        out_file = "data/unified/hn.jsonl"
    tmp_file = out_file + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        for u in unique_units.values():
            f.write(json.dumps(u, default=str) + "\n")
    if os.path.exists(tmp_file):
        os.replace(tmp_file, out_file)

    print(f"\n=== Hacker News Summary ===")
    print(f"Total units (before dedup): {len(all_units)}")
    print(f"Total units (after dedup):  {len(unique_units)}")
    return len(unique_units)


if __name__ == "__main__":
    collect()
