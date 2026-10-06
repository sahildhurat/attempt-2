"""
Master collection runner — runs all collectors and reports final counts.
"""
import sys
import os
import json
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all():
    results = {}

    print("=" * 60)
    print("COLLECTION RUN — ALL SOURCES")
    print("=" * 60)

    # 1. Help Community (corrected: modern UA, wider categories)
    print("\n" + "=" * 60)
    print("SOURCE 1: Help Community")
    print("=" * 60)
    try:
        from collectors.help_community import collect as hc_collect
        results["help_community"] = {"count": hc_collect(), "source_type": "discussion"}
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback; traceback.print_exc()
        results["help_community"] = {"count": 0, "source_type": "discussion", "error": str(e)}

    # 2. Stack Exchange (corrected: full pagination)
    print("\n" + "=" * 60)
    print("SOURCE 2: Stack Exchange")
    print("=" * 60)
    try:
        from collectors.stackexchange import collect as se_collect
        results["stackexchange"] = {"count": se_collect(), "source_type": "discussion"}
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback; traceback.print_exc()
        results["stackexchange"] = {"count": 0, "source_type": "discussion", "error": str(e)}

    # 3. Play Store
    print("\n" + "=" * 60)
    print("SOURCE 3: Play Store")
    print("=" * 60)
    try:
        from collectors.playstore import collect as ps_collect
        results["playstore"] = {"count": ps_collect(), "source_type": "review"}
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback; traceback.print_exc()
        results["playstore"] = {"count": 0, "source_type": "review", "error": str(e)}

    # 4. App Store
    print("\n" + "=" * 60)
    print("SOURCE 4: App Store")
    print("=" * 60)
    try:
        from collectors.appstore import collect as as_collect
        results["appstore"] = {"count": as_collect(), "source_type": "review"}
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback; traceback.print_exc()
        results["appstore"] = {"count": 0, "source_type": "review", "error": str(e)}

    # 5. YouTube
    print("\n" + "=" * 60)
    print("SOURCE 5: YouTube")
    print("=" * 60)
    try:
        from collectors.youtube import collect as yt_collect
        results["youtube"] = {"count": yt_collect(), "source_type": "discussion"}
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback; traceback.print_exc()
        results["youtube"] = {"count": 0, "source_type": "discussion", "error": str(e)}

    # 6. Hacker News
    print("\n" + "=" * 60)
    print("SOURCE 6: Hacker News")
    print("=" * 60)
    try:
        from collectors.hn import collect as hn_collect
        results["hn"] = {"count": hn_collect(), "source_type": "discussion"}
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback; traceback.print_exc()
        results["hn"] = {"count": 0, "source_type": "discussion", "error": str(e)}

    # Summary
    print("\n" + "=" * 60)
    print("FINAL UNIT COUNTS BY SOURCE AND SOURCE_TYPE")
    print("=" * 60)

    total = 0
    discussion_total = 0
    review_total = 0

    print(f"\n{'Source':<20} {'Source Type':<15} {'Units':>8}")
    print("-" * 45)
    for source, info in sorted(results.items()):
        count = info["count"]
        stype = info["source_type"]
        error = info.get("error", "")
        suffix = f" (ERROR: {error})" if error else ""
        print(f"{source:<20} {stype:<15} {count:>8}{suffix}")
        total += count
        if stype == "discussion":
            discussion_total += count
        elif stype == "review":
            review_total += count

    print("-" * 45)
    print(f"{'TOTAL':<20} {'all':<15} {total:>8}")
    print(f"{'  discussion':<20} {'':<15} {discussion_total:>8}")
    print(f"{'  review':<20} {'':<15} {review_total:>8}")

    # Save summary
    os.makedirs("data", exist_ok=True)
    with open("data/collection_summary.json", "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "results": results,
            "total": total,
            "discussion_total": discussion_total,
            "review_total": review_total,
        }, f, indent=2)

    print(f"\nSummary saved to data/collection_summary.json")
    return results


if __name__ == "__main__":
    run_all()
