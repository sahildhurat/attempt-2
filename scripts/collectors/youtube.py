import sys
import io

# Force UTF-8 output to avoid cp1252 errors on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

"""
YouTube collector.

Uses the YouTube Data API v3 to collect comments from videos about
Google Photos search/retrieval problems.

Requires YOUTUBE_API_KEY in environment or .env file.
Source type: discussion.

Quota budget (daily limit: 10,000 units):
  - search.list: 100 units per call
  - commentThreads.list: 1 unit per call
  - Max 15 search calls = 1,500 quota units
  - Remaining ~8,500 for comment fetches
"""
import json
import urllib.parse
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

# Search queries — capped at 15 to stay within quota
VIDEO_SEARCH_QUERIES = [
    "google photos search tips",
    "google photos find old photos",
    "google photos search not working",
    "google photos how to find photos",
    "google photos face recognition",
    "google photos search by location",
    "google photos tips and tricks search",
    "google photos organize albums",
    "google photos memories",
    "google photos find deleted photos",
    "google photos search features",
    "can't find photos google photos",
    "google photos lost photos",
    "google photos search update",
    "google photos tutorial search",
]

HEADERS = {
    "User-Agent": "DiscoveryEngine/1.0 (academic research)"
}


def get_api_key():
    """Try to get YouTube API key from env or .env file."""
    key = os.environ.get("YOUTUBE_API_KEY")
    if key:
        return key

    # Check .env at project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("YOUTUBE_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


class QuotaTracker:
    def __init__(self, daily_limit=10000):
        self.limit = daily_limit
        self.used = 0

    def consume(self, cost):
        self.used += cost
        return self.used

    def remaining(self):
        return self.limit - self.used

    def can_afford(self, cost):
        return self.remaining() >= cost


def search_videos(api_key, query, quota, max_results=10):
    """Search for videos and return video IDs. Costs 100 quota units."""
    if not quota.can_afford(100):
        print(f"  QUOTA: Cannot afford search ({quota.remaining()} remaining)")
        return []

    q = urllib.parse.quote(query)
    url = (
        f"https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&type=video&q={q}"
        f"&maxResults={max_results}&relevanceLanguage=en"
        f"&key={api_key}"
    )
    try:
        session = get_session()
        
        
        response = fetch_with_rate_limit(session, "GET", url, "youtube", timeout=15)
        response.raise_for_status()
        data = response.json()
        quota.consume(100)
        return [
            {
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
            }
            for item in data.get("items", [])
            if "videoId" in item.get("id", {})
        ]
    except Exception as e:
        print(f"  Video search error: {e}")
        log_failure("youtube", "NETWORK", f"query: {query}, error: {e}")
        quota.consume(100)  # Still consumed on error
        return []


def get_comments(api_key, video_id, video_title, quota, max_pages=3):
    """Get comment threads for a video. Costs 1 quota unit per page."""
    units = []
    page_token = None

    for page_num in range(max_pages):
        if not quota.can_afford(1):
            print(f"    QUOTA EXHAUSTED at page {page_num + 1}")
            break

        url = (
            f"https://www.googleapis.com/youtube/v3/commentThreads"
            f"?part=snippet,replies&videoId={video_id}"
            f"&maxResults=100&textFormat=plainText"
            f"&key={api_key}"
        )
        if page_token:
            url += f"&pageToken={page_token}"

        session = get_session()
        

        try:
            response = fetch_with_rate_limit(session, "GET", url, "youtube", timeout=15)
            response.raise_for_status()
            try:
                data = response.json()
            except Exception as e:
                log_failure("youtube", "PARSE", f"video: {video_id}, page: {page_num}, error: {e}")
                break
            quota.consume(1)

            for item in data.get("items", []):
                # Top-level comment
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comment_id = item["snippet"]["topLevelComment"]["id"]
                text = snippet.get("textDisplay", "")
                author = snippet.get("authorDisplayName", "")

                if text and len(text.strip()) >= 10:
                    units.append({
                        "id": generate_id("youtube", comment_id),
                        "source": "youtube",
                        "source_type": "discussion",
                        "source_id": comment_id,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "text": text,
                        "created_at": snippet.get("publishedAt"),
                        "is_reply": False,
                        "parent_id": None,
                        "context": video_title,
                        "author_hash": hashlib.sha256(author.encode()).hexdigest() if author else None,
                        "like_count": snippet.get("likeCount", 0),
                    })

                # Replies
                if "replies" in item:
                    for reply in item["replies"]["comments"]:
                        r_snippet = reply["snippet"]
                        r_id = reply["id"]
                        r_text = r_snippet.get("textDisplay", "")
                        r_author = r_snippet.get("authorDisplayName", "")

                        if r_text and len(r_text.strip()) >= 10:
                            units.append({
                                "id": generate_id("youtube", r_id),
                                "source": "youtube",
                                "source_type": "discussion",
                                "source_id": r_id,
                                "url": f"https://www.youtube.com/watch?v={video_id}",
                                "text": r_text,
                                "created_at": r_snippet.get("publishedAt"),
                                "is_reply": True,
                                "parent_id": comment_id,
                                "context": video_title,
                                "author_hash": hashlib.sha256(r_author.encode()).hexdigest() if r_author else None,
                                "like_count": r_snippet.get("likeCount", 0),
                            })

            page_token = data.get("nextPageToken")
            if not page_token:
                break

            time.sleep(0.2)

        except Exception as e:
            if "RATE_LIMITED" in str(e):
                log_failure("youtube", "RATE_LIMITED", str(e))
                return []
            if isinstance(e, requests.exceptions.RequestException):
                if hasattr(e.response, 'status_code') and e.response.status_code == 403:
                    error_body = e.response.text
                    if "commentsDisabled" in error_body:
                        print(f"    Comments disabled on this video")
                    elif "quotaExceeded" in error_body:
                        print(f"    QUOTA EXCEEDED — stopping")
                        quota.used = quota.limit  # Mark exhausted
                    else:
                        print(f"    HTTP 403: {error_body[:200]}")
                    log_failure("youtube", "NETWORK", f"video: {video_id}, page: {page_num}, error: {e}, body: {error_body[:100]}")
                else:
                    print(f"    NETWORK ERROR: {e}")
                    log_failure("youtube", "NETWORK", f"video: {video_id}, page: {page_num}, error: {e}")
                break
        except Exception as e:
            print(f"    Comment fetch error: {e}")
            log_failure("youtube", "NETWORK", f"video: {video_id}, page: {page_num}, error: {e}")
            break

    return units


def collect():
    os.makedirs("data/raw/youtube", exist_ok=True)
    os.makedirs("data/unified", exist_ok=True)

    api_key = get_api_key()

    if not api_key:
        print("WARNING: No YOUTUBE_API_KEY found.")
        print("Set YOUTUBE_API_KEY in environment or .env file.")
        print("Saving empty output — YouTube collection requires API key.")

        with open("data/unified/youtube.jsonl", "w") as f:
            pass
        with open("data/raw/youtube/collection_log.json", "w") as f:
            json.dump({"status": "skipped", "reason": "no_api_key"}, f)

        return 0

    quota = QuotaTracker(daily_limit=10000)
    all_units = []
    all_videos = {}

    # Phase 1: Search for relevant videos (budget: 15 searches × 100 = 1,500 quota)
    print("Phase 1: Searching for relevant videos...")
    for query in VIDEO_SEARCH_QUERIES:
        print(f"  Searching: '{query}' (quota: {quota.used}/{quota.limit})...")
        videos = search_videos(api_key, query, quota)
        for v in videos:
            if v["video_id"] not in all_videos:
                all_videos[v["video_id"]] = v
        print(f"    Found {len(videos)} videos ({len(all_videos)} unique total)")
        time.sleep(0.5)

    print(f"\nTotal unique videos found: {len(all_videos)}")
    print(f"Quota used for search: {quota.used}")

    # Save video list BEFORE collecting comments (per user instruction)
    video_list = list(all_videos.values())
    with open("data/raw/youtube/video_list.json", "w", encoding="utf-8") as f:
        json.dump(video_list, f, indent=2, default=str)
    print(f"Video list saved to data/raw/youtube/video_list.json")

    # Phase 2: Get comments (budget: ~8,500 remaining quota)
    print(f"\nPhase 2: Collecting comments (quota remaining: {quota.remaining()})...")
    videos_collected = 0
    videos_planned = len(video_list)

    for i, video in enumerate(video_list):
        if not quota.can_afford(1):
            print(f"\nQUOTA EXHAUSTED after {videos_collected}/{videos_planned} videos")
            break

        vid = video["video_id"]
        title = video["title"]
        safe_title = title[:70].encode('ascii', 'replace').decode('ascii')
        print(f"\n[{i+1}/{videos_planned}] {safe_title}... (quota: {quota.used})")

        comments = get_comments(api_key, vid, title, quota)
        all_units.extend(comments)
        videos_collected += 1
        print(f"  {len(comments)} comment units")

        time.sleep(0.3)

    # Deduplicate
    unique_units = {}
    for u in all_units:
        if u["id"] not in unique_units:
            unique_units[u["id"]] = u

    # Save collection log
    with open("data/raw/youtube/collection_log.json", "w", encoding="utf-8") as f:
        json.dump({
            "status": "completed" if videos_collected == videos_planned else "partial",
            "videos_planned": videos_planned,
            "videos_collected": videos_collected,
            "quota_used": quota.used,
            "quota_limit": quota.limit,
            "total_units": len(unique_units),
        }, f, indent=2)

    # Save unified
        out_file = "data/unified/youtube.jsonl"
    tmp_file = out_file + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        for u in unique_units.values():
            f.write(json.dumps(u, default=str) + "\n")
    if os.path.exists(tmp_file):
        os.replace(tmp_file, out_file)

    print(f"\n=== YouTube Summary ===")
    print(f"Videos found: {len(all_videos)}")
    print(f"Videos collected: {videos_collected}/{videos_planned}")
    print(f"Quota used: {quota.used}/{quota.limit}")
    print(f"Total comment units: {len(all_units)}")
    print(f"After dedup: {len(unique_units)}")
    return len(unique_units)


if __name__ == "__main__":
    collect()
