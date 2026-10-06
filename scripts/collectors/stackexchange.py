"""
Stack Exchange collector — corrected version.

Changes from previous version:
- Paginates until has_more is false (100 per page is the API cap, not the total)
- Wider query set beyond just the keyword list
- Covers all three sites: superuser, webapps, android
- Tagged search also used where applicable
"""
import json
import urllib.request
import urllib.parse
import time
import os
import hashlib

def generate_id(source, source_id):
    return hashlib.sha256(f"{source}_{source_id}".encode()).hexdigest()

# Wider query set: original keywords plus additional retrieval-focused queries
QUERIES = [
    "google photos find photo",
    "google photos search photo",
    "google photos memory",
    "google photos retrieve",
    "google photos can't find",
    "google photos old photo",
    "google photos search not working",
    "google photos looking for",
    "google photos lost photo",
    "google photos face recognition",
    "google photos album search",
    "google photos location search",
    "google photos date search",
    "google photos scroll",
    "google photos where is",
    "google photos search results",
    "google photos find picture",
    "google photos screenshot",
]

# Also do tagged searches on webapps.stackexchange.com
TAGGED_QUERIES = [
    {"site": "webapps", "tagged": "google-photos", "q": "find"},
    {"site": "webapps", "tagged": "google-photos", "q": "search"},
    {"site": "webapps", "tagged": "google-photos", "q": ""},
    {"site": "android", "tagged": "google-photos", "q": "find"},
    {"site": "android", "tagged": "google-photos", "q": "search"},
    {"site": "android", "tagged": "google-photos", "q": ""},
]

SITES = ["superuser", "webapps", "android"]
PAGE_SIZE = 100  # API max


import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_paginated(url_base, max_pages=10):
    """Fetch all pages from a SE API endpoint until has_more is false."""
    all_items = []
    page = 1
    
    session = get_session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    while page <= max_pages:
        url = f"{url_base}&page={page}&pagesize={PAGE_SIZE}"
        try:
            response = fetch_with_rate_limit(session, "GET", url, "stackexchange", timeout=15)
            response.raise_for_status()
            
            try:
                data = response.json()
            except Exception as e:
                log_failure("stackexchange", "PARSE", f"URL: {url} Error: {e}")
                break
                
            items = data.get("items", [])
            all_items.extend(items)
            has_more = data.get("has_more", False)
            quota = data.get("quota_remaining", "?")

            print(f"    Page {page}: {len(items)} items (quota: {quota})")

            if not has_more or len(items) == 0:
                if len(items) == 0 and page == 1:
                    log_failure("stackexchange", "EMPTY", f"URL: {url} returned no items on page 1")
                break

            page += 1
            time.sleep(0.5)

        except Exception as e:
            if isinstance(e, requests.exceptions.RequestException):
                log_failure("stackexchange", "NETWORK", f"URL: {url} Error: {e}")
            break

    return all_items

def log_failure(collector_name, failure_type, details):
    with open(f"data/raw/{collector_name}/failures.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": failure_type, "details": details}) + "\n")


def collect():
    os.makedirs("data/raw/stackexchange", exist_ok=True)
    os.makedirs("data/unified", exist_ok=True)

    all_units = []
    site_counts = {s: 0 for s in SITES}

    # 1. Advanced search queries across all sites
    for site in SITES:
        for query_text in QUERIES:
            q = urllib.parse.quote(query_text)
            url_base = (
                f"https://api.stackexchange.com/2.3/search/advanced"
                f"?order=desc&sort=relevance&q={q}&site={site}"
                f"&filter=withbody"
            )

            print(f"SE {site} query '{query_text}'...")
            items = fetch_paginated(url_base, max_pages=5)

            for item in items:
                title_lower = item.get("title", "").lower()
                body_lower = item.get("body", "").lower()

                # Must mention google photos
                if "google photos" not in title_lower and "google photos" not in body_lower:
                    continue

                q_id = str(item["question_id"])
                q_unit = {
                    "id": generate_id("stackexchange", q_id),
                    "source": "stackexchange",
                    "source_type": "discussion",
                    "source_id": q_id,
                    "url": item.get("link", ""),
                    "text": f"{item['title']}\n{item['body']}",
                    "created_at": item.get("creation_date"),
                    "is_reply": False,
                    "parent_id": None,
                    "context": item["title"],
                    "site": site,
                }
                all_units.append(q_unit)
                site_counts[site] += 1

                # Answers
                if "answers" in item:
                    for ans in item["answers"]:
                        a_id = str(ans["answer_id"])
                        a_unit = {
                            "id": generate_id("stackexchange", a_id),
                            "source": "stackexchange",
                            "source_type": "discussion",
                            "source_id": a_id,
                            "url": ans.get("link", ""),
                            "text": ans["body"],
                            "created_at": ans.get("creation_date"),
                            "is_reply": True,
                            "parent_id": q_id,
                            "context": item["title"],
                            "site": site,
                        }
                        all_units.append(a_unit)
                        site_counts[site] += 1

            time.sleep(1)  # rate limit between queries

    # 2. Tagged searches (no keyword needed — just the tag)
    for tq in TAGGED_QUERIES:
        site = tq["site"]
        tagged = tq["tagged"]
        q = urllib.parse.quote(tq["q"]) if tq["q"] else ""

        url_base = (
            f"https://api.stackexchange.com/2.3/search/advanced"
            f"?order=desc&sort=relevance&tagged={tagged}&site={site}"
            f"&filter=withbody"
        )
        if q:
            url_base += f"&q={q}"

        print(f"SE {site} tagged '{tagged}' q='{tq['q']}'...")
        items = fetch_paginated(url_base, max_pages=5)

        for item in items:
            q_id = str(item["question_id"])
            q_unit = {
                "id": generate_id("stackexchange", q_id),
                "source": "stackexchange",
                "source_type": "discussion",
                "source_id": q_id,
                "url": item.get("link", ""),
                "text": f"{item['title']}\n{item['body']}",
                "created_at": item.get("creation_date"),
                "is_reply": False,
                "parent_id": None,
                "context": item["title"],
                "site": site,
            }
            all_units.append(q_unit)
            site_counts[site] += 1

            if "answers" in item:
                for ans in item["answers"]:
                    a_id = str(ans["answer_id"])
                    a_unit = {
                        "id": generate_id("stackexchange", a_id),
                        "source": "stackexchange",
                        "source_type": "discussion",
                        "source_id": a_id,
                        "url": ans.get("link", ""),
                        "text": ans["body"],
                        "created_at": ans.get("creation_date"),
                        "is_reply": True,
                        "parent_id": q_id,
                        "context": item["title"],
                        "site": site,
                    }
                    all_units.append(a_unit)
                    site_counts[site] += 1

        time.sleep(1)

    # Deduplicate
    unique_units = {}
    for u in all_units:
        if u["id"] not in unique_units:
            unique_units[u["id"]] = u

    # Save raw site counts
    with open("data/raw/stackexchange/site_counts.json", "w") as f:
        json.dump(site_counts, f, indent=2)

    # Save unified
        out_file = "data/unified/stackexchange.jsonl"
    tmp_file = out_file + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        for u in unique_units.values():
            f.write(json.dumps(u) + "\n")
    if os.path.exists(tmp_file):
        os.replace(tmp_file, out_file)

    print(f"\n=== Stack Exchange Summary ===")
    for site, count in site_counts.items():
        print(f"  {site}: {count} units (before dedup)")
    print(f"Total before dedup: {len(all_units)}")
    print(f"Total after dedup:  {len(unique_units)}")
    return len(unique_units)


if __name__ == "__main__":
    collect()
