import os
import json
import re
from collections import defaultdict
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0

def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    unified_dir = "data/unified"
    out_file = os.path.join(unified_dir, "units.jsonl")
    
    source_files = [f for f in os.listdir(unified_dir) if f.endswith(".jsonl") and f != "units.jsonl"]
    
    total_raw = 0
    non_english = 0
    duplicates = 0
    
    seen_texts = set()
    final_units = []
    
    source_counts = defaultdict(lambda: {"total": 0, "non_en": 0, "dupes": 0, "final": 0})
    
    print(f"Reading from {len(source_files)} source files...")
    
    for filename in source_files:
        source_name = filename.replace(".jsonl", "")
        filepath = os.path.join(unified_dir, filename)
        
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                unit = json.loads(line)
                total_raw += 1
                source_counts[source_name]["total"] += 1
                
                text = unit.get("text", "")
                if not text:
                    continue
                
                # Language detection
                lang = unit.get("lang")
                if not lang:
                    try:
                        lang = detect(text)
                    except LangDetectException:
                        lang = "unknown"
                    unit["lang"] = lang
                
                if lang != "en":
                    non_english += 1
                    source_counts[source_name]["non_en"] += 1
                    continue
                
                # Deduplication
                norm_text = normalize_text(text)
                if norm_text in seen_texts:
                    duplicates += 1
                    source_counts[source_name]["dupes"] += 1
                    continue
                    
                seen_texts.add(norm_text)
                source_counts[source_name]["final"] += 1
                final_units.append(unit)
                
    with open(out_file, "w", encoding="utf-8") as f:
        for unit in final_units:
            f.write(json.dumps(unit) + "\n")
            
    print("\nSource Breakdown (After language filter & dedup):")
    print(f"{'Source':<15} | {'Raw':<6} | {'Non-EN Drop':<11} | {'Dupe Drop':<9} | {'Final'}")
    print("-" * 60)
    for src, counts in sorted(source_counts.items()):
        print(f"{src:<15} | {counts['total']:<6} | {counts['non_en']:<11} | {counts['dupes']:<9} | {counts['final']}")
        
    print("\nSource Type Breakdown (Final Units):")
    source_types = defaultdict(int)
    for u in final_units:
        source_types[u["source_type"]] += 1
    for st, count in source_types.items():
        print(f"  {st}: {count}")
        
    print(f"\nTotal raw: {total_raw}")
    print(f"Total after language filter: {total_raw - non_english} ({non_english} non-English removed)")
    print(f"Total after dedup (Final): {len(final_units)} ({duplicates} duplicates removed)")

if __name__ == '__main__':
    main()
