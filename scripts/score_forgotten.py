"""
Score the extractor's original gap_type against the human re-coded labels.
This is a discrepancy audit, not a validation.
"""
import json
import csv
from collections import Counter

# Load human labels from the edited validation CSV
human_labels = {}
with open('data/pass3/forgotten_validation.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        phrase = row['phrase'].strip()
        label = row['gap_type'].strip().upper()
        human_labels[phrase] = label

# Load extractor's original labels from the key file
with open('data/pass3/forgotten_key.json', 'r', encoding='utf-8') as f:
    key_data = json.load(f)

extractor_labels = {}
for item in key_data:
    phrase = item['phrase']
    orig = item['original_gap_type']
    extractor_labels[phrase] = orig

# Verify counts
print(f"Human-labelled phrases: {len(human_labels)}")
print(f"Extractor-labelled phrases: {len(extractor_labels)}")

# Human label distribution
print("\nHuman label distribution:")
human_dist = Counter(human_labels.values())
for label, count in sorted(human_dist.items(), key=lambda x: -x[1]):
    print(f"  {label}: {count}")

# Build confusion matrix: rows = human labels, cols = extractor labels
human_cats = sorted(set(human_labels.values()))
extractor_cats = sorted(set(extractor_labels.values()))

print(f"\nExtractor categories: {extractor_cats}")
print(f"Human categories: {human_cats}")

# Count agreements and disagreements
agree = 0
disagree = 0
disagreements = []

# Build matrix
matrix = {}
for hc in human_cats:
    matrix[hc] = Counter()

for phrase, h_label in human_labels.items():
    e_label = extractor_labels.get(phrase, "MISSING")
    matrix[h_label][e_label] += 1
    
    # Normalize for comparison
    h_norm = h_label.upper()
    e_norm = e_label.upper().replace("_", "")
    
    # Direct mapping check
    match = False
    mapping = {
        "MEMORY": "memory_gap",
        "NAVIGATION": "navigation_gap",
        "PRODUCT": "product_gap",
        "SYSTEM": "system_failure",
        "NOT_CUE": "not_user_cue",
    }
    if mapping.get(h_label) == e_label:
        match = True
    # account_event has no direct human equivalent
    
    if match:
        agree += 1
    else:
        disagree += 1
        disagreements.append((phrase, h_label, e_label))

total = agree + disagree
print(f"\nDiscrepancy audit: {agree}/{total} match ({agree/total*100:.1f}%), {disagree} discrepancies")

# Print confusion matrix
print(f"\nConfusion matrix (rows=human, cols=extractor):")
all_ext_cats = sorted(set(extractor_labels.values()))
header = f"{'Human':<12}" + "".join(f"{c:<18}" for c in all_ext_cats)
print(header)
print("-" * len(header))
for hc in human_cats:
    row = f"{hc:<12}"
    for ec in all_ext_cats:
        row += f"{matrix[hc].get(ec, 0):<18}"
    print(row)

# List all discrepancies
if disagreements:
    print(f"\nDiscrepancies ({len(disagreements)}):")
    for phrase, h, e in sorted(disagreements, key=lambda x: x[1]):
        print(f'  "{phrase}"')
        print(f"    human={h}  extractor={e}")

# Count temporal items among MEMORY
temporal_phrases = [
    "date/when the beer photo was taken",
    "when the photo was taken",
    "exact date or year of the photo",
    "the time the photo was taken",
    "no specific date or timeframe mentioned",
    "when the older photo was taken",
    "exact date of the photos",
    "the year the picture was taken",
    "correct original date/time photos were taken",
    "original metadata (date/time/location) of the recovered images",
]
memory_count = human_dist.get("MEMORY", 0)
temporal_in_memory = sum(1 for p in temporal_phrases if human_labels.get(p) == "MEMORY")
print(f"\n--- Analysis ---")
print(f"Grounded cues: 554")
print(f"Memory gaps: {memory_count}")
print(f"Ratio (cues : memory gaps): {554/memory_count:.1f}:1")
print(f"Temporal memory gaps: {temporal_in_memory} of {memory_count} ({temporal_in_memory/memory_count*100:.1f}%)")
