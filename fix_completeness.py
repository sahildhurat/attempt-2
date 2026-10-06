import json
from collections import Counter

input_file = "data/archive/all_units_unfiltered.jsonl"
output_file = "data/archive/all_units_unfiltered_fixed.jsonl"

completeness_dist = Counter()

with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
    for line in f_in:
        if not line.strip():
            continue
        u = json.loads(line)
        
        c = u.get("text_completeness")
        if c is None or c == "None":
            source = u.get("source")
            if source in ["playstore", "youtube", "appstore"]:
                u["text_completeness"] = "snippet"
            elif source in ["hn", "stackexchange"]:
                u["text_completeness"] = "full"
            elif source == "reddit_assisted":
                # should already be set, but just in case it's None
                u["text_completeness"] = "unknown"
            elif source == "help_community":
                u["text_completeness"] = "snippet"
                
        completeness_dist[str(u.get("text_completeness"))] += 1
        f_out.write(json.dumps(u) + "\n")

import os
os.replace(output_file, input_file)

print("\nFinal text_completeness distribution across all sources:")
for k, v in completeness_dist.items():
    print(f"  {k}: {v}")

