import sys
import os
sys.path.append(os.path.dirname(__file__))
from network_utils import log_failure
import time
"""
Play Store collector.

Uses google-play-scraper to collect Google Photos reviews.
Uses reviews_all() to paginate fully, or reviews() with continuation tokens.
Source type: review (critical for triangulation — without review-type sources,
no category can score above 0.85 on the triangulation weight).
"""
import json
import os
import hashlib
import time

def generate_id(source, source_id):
    return hashlib.sha256(f"{source}_{source_id}".encode()).hexdigest()

APP_ID = "com.google.android.apps.photos"

def collect():
    os.makedirs("data/raw/playstore", exist_ok=True)
    os.makedirs("data/unified", exist_ok=True)

    try:
        from google_play_scraper import reviews, Sort
    except ImportError:
        print("ERROR: google-play-scraper not installed. Run: pip install google-play-scraper")
        return 0

    all_reviews = []
    continuation_token = None

    # Collect using continuation tokens — reviews() returns (results, token)
    # We collect in batches until we exhaust or hit our cap
    MAX_REVIEWS = 15000  # safety cap
    batch_num = 0

    def log_failure(failure_type, details):
        with open(f"data/raw/playstore/failures.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"type": failure_type, "details": details}) + "\n")

    # Collect both "most relevant" and "newest" sorts for breadth
    for sort_order, sort_name in [(Sort.MOST_RELEVANT, "relevant"), (Sort.NEWEST, "newest")]:
        continuation_token = None
        batch_num = 0
        collected_for_sort = 0

        print(f"\nCollecting {sort_name} reviews...")

        while collected_for_sort < MAX_REVIEWS // 2:
            batch_num += 1
            try:
                result, continuation_token = reviews(
                    APP_ID,
                    lang="en",
                    country="us",
                    sort=sort_order,
                    count=200,  # per batch
                    continuation_token=continuation_token,
                )

                if not result:
                    if batch_num == 1:
                        log_failure("EMPTY", f"sort: {sort_name} returned no result on batch 1")
                    print(f"  Batch {batch_num}: empty, stopping")
                    break

                all_reviews.extend(result)
                collected_for_sort += len(result)
                print(f"  Batch {batch_num}: {len(result)} reviews (total {sort_name}: {collected_for_sort})")

                if continuation_token is None or not continuation_token.token:
                    print(f"  No continuation token, stopping")
                    break

                time.sleep(0.5)

            except Exception as e:
                err_str = str(e).lower()
                if "network" in err_str or "connection" in err_str or "timeout" in err_str:
                    log_failure("NETWORK", f"sort: {sort_name}, batch: {batch_num}, error: {e}")
                else:
                    log_failure("PARSE", f"sort: {sort_name}, batch: {batch_num}, error: {e}")
                print(f"  Batch {batch_num} error: {e}")
                break

    print(f"\nTotal raw reviews fetched: {len(all_reviews)}")

    # Convert to unit schema
    all_units = []
    for rev in all_reviews:
        review_id = rev.get("reviewId", "")
        if not review_id:
            continue

        text = rev.get("content", "")
        if not text or len(text.strip()) < 10:
            continue

        unit = {
            "id": generate_id("playstore", review_id),
            "source": "playstore",
            "source_type": "review",
            "source_id": review_id,
            "url": None,
            "text": text,
            "created_at": rev.get("at", "").isoformat() if hasattr(rev.get("at", ""), "isoformat") else str(rev.get("at", "")),
            "is_reply": False,
            "parent_id": None,
            "rating": rev.get("score"),
            "context": f"Google Photos Play Store review ({rev.get('score', '?')} stars)",
            "thumbs_up": rev.get("thumbsUpCount", 0),
        }
        all_units.append(unit)

    # Deduplicate
    unique_units = {}
    for u in all_units:
        if u["id"] not in unique_units:
            unique_units[u["id"]] = u

    # Save raw
    with open("data/raw/playstore/raw_reviews.json", "w", encoding="utf-8") as f:
        json.dump([{k: str(v) if not isinstance(v, (str, int, float, bool, type(None), list, dict)) else v for k, v in r.items()} for r in all_reviews], f, indent=2, default=str)

    # Save unified
        out_file = "data/unified/playstore.jsonl"
    tmp_file = out_file + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        for u in unique_units.values():
            f.write(json.dumps(u, default=str) + "\n")
    if os.path.exists(tmp_file):
        os.replace(tmp_file, out_file)

    print(f"\n=== Play Store Summary ===")
    print(f"Raw reviews fetched: {len(all_reviews)}")
    print(f"Units (after text filter): {len(all_units)}")
    print(f"Units (after dedup): {len(unique_units)}")
    return len(unique_units)


if __name__ == "__main__":
    collect()
