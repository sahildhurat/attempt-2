import csv
import json
import sys
import re
import html

def clean_text(text):
    if not text: return text
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    # Load original jsonl to map text -> id
    text_to_id = {}
    with open(r'd:\Attempt 2\data\blind_sample_eval.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            text_to_id[item['text']] = item['id']
            
    # Load key jsonl to map id -> gate_decision
    id_to_decision = {}
    with open(r'd:\Attempt 2\data\blind_sample_key.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            id_to_decision[item['id']] = item['gate_decision']

    # Read current CSV
    rows = []
    with open(r'd:\Attempt 2\data\blind_sample_eval.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            original_text = row['text']
            if original_text in text_to_id:
                row['unit_id'] = text_to_id[original_text]
            else:
                print(f"Warning: Could not find ID for text: {original_text[:50]}")
            
            # Clean text
            row['text'] = clean_text(original_text)
            rows.append(row)

    # Write fixed 200 row CSV
    fieldnames = ['row', 'unit_id', 'source', 'text', 'my_label', 'hard']
    with open(r'd:\Attempt 2\data\blind_sample_eval.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Pick 60 rows
    rows_60 = []
    decisions = {'yes': 0, 'partial': 0, 'no': 0}
    for i in range(60):
        # every third row from the original 200
        original_idx = i * 3
        if original_idx < len(rows):
            new_row = rows[original_idx].copy()
            new_row['row'] = i + 1  # Re-number 1 to 60
            rows_60.append(new_row)
            
            decision = id_to_decision.get(new_row['unit_id'])
            if decision in decisions:
                decisions[decision] += 1
            else:
                decisions[decision] = 1

    # Write 60 row CSV
    with open(r'd:\Attempt 2\data\blind_sample_60.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_60)

    # Report stats
    total = sum(decisions.values())
    print("60-row split:")
    for k, v in decisions.items():
        print(f"{k}: {v} ({v/total*100:.1f}%)")

if __name__ == '__main__':
    main()
