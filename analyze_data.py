import json
import statistics
import os

units_file = "data/archive/all_units_unfiltered.jsonl"
hc_units = []
with open(units_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            u = json.loads(line)
            if u.get("source") == "help_community":
                hc_units.append(u)
                
print(f"Total help_community units: {len(hc_units)}")

lengths = [len(u.get("text", "")) for u in hc_units]
median_length = statistics.median(lengths) if lengths else 0
print(f"Median length: {median_length}")

is_reply_count = sum(1 for u in hc_units if u.get("is_reply"))
print(f"is_reply count: {is_reply_count}")

completeness_dist = {}
for u in hc_units:
    c = u.get("text_completeness", "unknown")
    completeness_dist[c] = completeness_dist.get(c, 0) + 1
print(f"Text completeness distribution: {completeness_dist}")

print("\n5 Verbatim samples:")
for u in hc_units[:5]:
    print(f"---\n{u.get('text', '')[:200]}...\n")

ps_count = sum(1 for line in open(units_file, "r", encoding="utf-8") if json.loads(line).get("source") == "playstore")
print(f"Play Store count in unfiltered: {ps_count}")
