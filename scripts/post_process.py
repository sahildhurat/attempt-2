import json
import pandas as pd
import random
import os

input_file = "data/gate_results.jsonl"
if not os.path.exists(input_file):
    print("Gate results not found.")
    exit(1)

# Deduplicate in memory
unique_units = {}
with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            u = json.loads(line)
            unique_units[u["id"]] = u
            
units = list(unique_units.values())

# Hardcode weights based on actual processing counts
weights_map = {
    "stackexchange": 1.0,
    "reddit_assisted": 1.0,
    "appstore": 1.0,
    "help_community": 19345.0 / 5426.0,
    "hn": 2125.0 / 105.0,
    "playstore": 11025.0 / 200.0,
    "youtube": 32.01
}

for u in units:
    u["weight"] = weights_map.get(u["source"], 1.0)

df = pd.DataFrame(units)

def report_distribution(column, df):
    raw_counts = df[column].value_counts()
    weighted_counts = df.groupby(column)['weight'].sum().sort_values(ascending=False)
    
    res = pd.DataFrame({'Raw Count': raw_counts, 'Weighted Count': weighted_counts})
    print(f"\n--- Distribution by {column} ---")
    print(res.to_string(float_format="%.2f"))

print("\n=== FINAL YIELD REPORT ===")
report_distribution("source", df)
report_distribution("source_type", df)
report_distribution("gate_language", df)
report_distribution("text_completeness", df)

print("\n--- Detailed Source Yields ---")
sources = df["source"].unique()
for src in sorted(sources):
    src_df = df[df["source"] == src]
    if len(src_df) > 0:
        raw_yield = len(src_df)
        implied_pop = src_df['weight'].sum()
        
        yes_df = src_df[src_df['gate_decision'] == 'yes']
        partial_df = src_df[src_df['gate_decision'] == 'partial']
        no_df = src_df[src_df['gate_decision'] == 'no']
        
        yes_raw = len(yes_df)
        yes_w = yes_df['weight'].sum()
        partial_raw = len(partial_df)
        partial_w = partial_df['weight'].sum()
        no_raw = len(no_df)
        no_w = no_df['weight'].sum()
        
        rel_rate_raw = (yes_raw + partial_raw) / raw_yield * 100 if raw_yield > 0 else 0
        rel_rate_w = (yes_w + partial_w) / implied_pop * 100 if implied_pop > 0 else 0
        
        print(f"\n{src.upper()}")
        print(f"Processed: {raw_yield} raw (Implied Population: {implied_pop:.2f})")
        print(f"Yes: {yes_raw} raw / {yes_w:.2f} weighted")
        print(f"Partial: {partial_raw} raw / {partial_w:.2f} weighted")
        print(f"No: {no_raw} raw / {no_w:.2f} weighted")
        print(f"Relevance Rate (Yes+Partial): {rel_rate_raw:.2f}% raw / {rel_rate_w:.2f}% weighted")


