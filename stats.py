import json
import os
import re
from collections import defaultdict
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

unified_dir = "data/unified"
source_files = [f for f in os.listdir(unified_dir) if f.endswith(".jsonl") and f != "units.jsonl"]

stats = defaultdict(lambda: {"raw": 0, "non_en": 0, "dupes": 0, "final": 0})
source_types = defaultdict(int)
seen_texts = set()

for filename in source_files:
    source = filename.replace(".jsonl", "")
    with open(os.path.join(unified_dir, filename), "r", encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            stats[source]["raw"] += 1
            
            text = u.get("text", "")
            if not text:
                continue
                
            lang = u.get("lang")
            if not lang:
                try:
                    lang = detect(text)
                except LangDetectException:
                    lang = "unknown"
            
            if lang != "en":
                stats[source]["non_en"] += 1
                continue
                
            norm_text = normalize_text(text)
            if norm_text in seen_texts:
                stats[source]["dupes"] += 1
                continue
                
            seen_texts.add(norm_text)
            stats[source]["final"] += 1
            source_types[u["source_type"]] += 1

print(f"{'Source':<15} | {'Raw':<6} | {'Non-EN Drop':<11} | {'Dupe Drop':<9} | {'Final'}")
print("-" * 60)
for src, s in sorted(stats.items()):
    print(f"{src:<15} | {s['raw']:<6} | {s['non_en']:<11} | {s['dupes']:<9} | {s['final']}")

print("\nSource Types (Final):")
for st, count in source_types.items():
    print(f"  {st}: {count}")
