import csv
import json
import collections

# 1. Check for empty text in gate_results.jsonl
empty_by_source = collections.defaultdict(int)
total_gated = 0
with open(r'd:\Attempt 2\data\gate_results.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        total_gated += 1
        item = json.loads(line)
        text = item.get('text', '')
        if not text or len(text.strip()) < 20:
            empty_by_source[item.get('source', 'unknown')] += 1

with open(r'd:\Attempt 2\data\comparison_report.txt', 'w', encoding='utf-8') as out_f:
    out_f.write("--- SHORT TEXT (<20 chars) in gate_results.jsonl ---\n")
    for src, count in empty_by_source.items():
        out_f.write(f"{src}: {count}\n")
    out_f.write("\n")

    # 2. Comparison
    key_data = {}
    with open(r'd:\Attempt 2\data\blind_sample_key.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            key_data[item['id']] = item

    matches = 0
    total = 0
    matrix = collections.defaultdict(lambda: collections.defaultdict(int))
    source_totals = collections.defaultdict(int)
    source_matches = collections.defaultdict(int)

    disagreements = []

    tp_yes, fp_yes, fn_yes = 0, 0, 0
    tp_part, fp_part, fn_part = 0, 0, 0

    with open(r'd:\Attempt 2\data\blind_sample_60.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row['unit_id']
            my_label = row.get('my_label', '').strip().lower()
            if not my_label or uid == 'a692b53b6907e644425d7b9c3eae7ce80c35e46e9c43336db946838ae2b2a514':
                continue
                
            gate_item = key_data.get(uid, {})
            gate_label = gate_item.get('gate_decision', '').lower()
            
            matrix[my_label][gate_label] += 1
            total += 1
            source_totals[row['source']] += 1
            
            if my_label == gate_label:
                matches += 1
                source_matches[row['source']] += 1
            else:
                disagreements.append({
                    'unit_id': uid,
                    'source': row['source'],
                    'text': row['text'],
                    'my_label': my_label,
                    'gate_label': gate_label,
                    'gate_reason': gate_item.get('gate_reason', '')
                })

            # Yes
            if my_label == 'yes' and gate_label == 'yes': tp_yes += 1
            elif gate_label == 'yes' and my_label != 'yes': fp_yes += 1
            elif my_label == 'yes' and gate_label != 'yes': fn_yes += 1
            
            # Partial
            if my_label == 'partial' and gate_label == 'partial': tp_part += 1
            elif gate_label == 'partial' and my_label != 'partial': fp_part += 1
            elif my_label == 'partial' and gate_label != 'partial': fn_part += 1

    out_f.write(f"Overall Agreement: {matches}/{total} ({matches/total*100:.1f}%)\n")
    out_f.write("Confusion Matrix (Row=MyLabel, Col=GateLabel):\n")
    labels = ['yes', 'partial', 'no']
    out_f.write("my\\gt\t" + "\t".join(labels) + "\n")
    for m_l in labels:
        row_str = f"{m_l}\t"
        for g_l in labels:
            row_str += f"{matrix[m_l][g_l]}\t"
        out_f.write(row_str + "\n")

    p_yes = tp_yes / (tp_yes + fp_yes) if (tp_yes + fp_yes) > 0 else 0
    r_yes = tp_yes / (tp_yes + fn_yes) if (tp_yes + fn_yes) > 0 else 0
    out_f.write(f"Yes -> Precision: {p_yes*100:.1f}%, Recall: {r_yes*100:.1f}%\n")

    p_part = tp_part / (tp_part + fp_part) if (tp_part + fp_part) > 0 else 0
    r_part = tp_part / (tp_part + fn_part) if (tp_part + fn_part) > 0 else 0
    out_f.write(f"Partial -> Precision: {p_part*100:.1f}%, Recall: {r_part*100:.1f}%\n")

    out_f.write("\nAgreement by Source:\n")
    for src in source_totals:
        out_f.write(f"{src}: {source_matches[src]}/{source_totals[src]} ({source_matches[src]/source_totals[src]*100:.1f}%)\n")

    out_f.write("\nDISAGREEMENTS:\n")
    for i, d in enumerate(disagreements):
        out_f.write(f"\n--- Disagreement {i+1} ---\n")
        out_f.write(f"ID: {d['unit_id']}\n")
        out_f.write(f"My Label: {d['my_label']} | Gate Label: {d['gate_label']}\n")
        out_f.write(f"Text: {d['text']}\n")
        out_f.write(f"Gate Reason: {d['gate_reason']}\n")
