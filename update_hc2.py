import json
import os
from collections import Counter

input_file = "data/archive/all_units_unfiltered.jsonl"
output_file = "data/archive/all_units_unfiltered_fixed.jsonl"

completeness_dist = Counter()

with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
    for line in f_in:
        if not line.strip():
            continue
        u = json.loads(line)
        
        if u.get("source") == "help_community":
            c = u.get("text_completeness")
            if c is None or c == "unknown":
                u["text_completeness"] = "snippet"
                
        # Also clean up "unknown" from other sources if any
        if u.get("text_completeness") == "unknown":
            u["text_completeness"] = "snippet"
            
        c = u.get("text_completeness")
        if c is None:
            # The instruction: "nothing should remain unknown". If there's no text_completeness, 
            # perhaps they also need to be assigned something? Wait, the user said "All 19,345 help_community units are 'unknown'... Set them to 'snippet' ... nothing should remain 'unknown'."
            # Let's set missing to 'full' for non-help_community, or whatever it should be?
            pass
            
        completeness_dist[str(u.get("text_completeness"))] += 1
        f_out.write(json.dumps(u) + "\n")

import shutil
shutil.move(output_file, input_file)

print("\nFinal text_completeness distribution across all sources:")
for k, v in completeness_dist.items():
    print(f"  {k}: {v}")
