import json
import os
from collections import Counter

input_file = "data/archive/all_units_unfiltered.jsonl"
output_file = "data/archive/all_units_unfiltered_fixed.jsonl"

completeness_dist = Counter()
printed_one = False

with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
    for line in f_in:
        if not line.strip():
            continue
        u = json.loads(line)
        
        if u.get("source") == "help_community":
            if not printed_one:
                text = u.get("text", "")
                print(f"--- FULL UNTRUNCATED HELP_COMMUNITY UNIT ---")
                print(f"Character count: {len(text)}")
                print(text)
                print(f"--------------------------------------------")
                printed_one = True
                
            if u.get("text_completeness") == "unknown":
                u["text_completeness"] = "snippet"
                
        completeness_dist[u.get("text_completeness")] += 1
        f_out.write(json.dumps(u) + "\n")

import shutil
shutil.move(output_file, input_file)

print("\nFinal text_completeness distribution across all sources:")
for k, v in completeness_dist.items():
    print(f"  {k}: {v}")
