import json, csv, random

# Load user labels from v2 CSV
user_labels = {}
with open('data/pass3/validation_sample_v2.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        n = int(row['n'])
        user_labels[n] = row['your_label'].strip().upper()

# Load classifier labels from v2 key
with open('data/pass3/validation_key_v2.json', 'r', encoding='utf-8') as f:
    key_data = json.load(f)

# Load full classification for reasons
classifier_reasons = {}
with open('data/pass3/cue_classification.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        rec = json.loads(line)
        classifier_reasons[rec['phrase']] = rec.get('reason', '')

# Verify zero overlap with seed-42
all_classified = []
with open('data/pass3/cue_classification.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get('label') in ('CUE', 'SYSTEM'):
            all_classified.append(rec)
random.seed(42)
contaminated_phrases = {rec['phrase'] for rec in random.sample(all_classified, 30)}
v2_phrases = {item['phrase'] for item in key_data}
overlap = v2_phrases & contaminated_phrases
print(f"Overlap with seed-42 sample: {len(overlap)}")

# Build confusion matrix and disagreements
# CUE = positive class
tp = fp = fn = tn = 0
agree = 0
disagree_list = []

for item in key_data:
    n = item['n']
    phrase = item['phrase']
    clf_label = item['classifier_label']
    usr_label = user_labels.get(n, '')

    if usr_label == clf_label:
        agree += 1
    else:
        reason = classifier_reasons.get(phrase, '')
        disagree_list.append((phrase, usr_label, clf_label, reason))

    if usr_label == 'CUE' and clf_label == 'CUE':
        tp += 1
    elif usr_label == 'CUE' and clf_label == 'SYSTEM':
        fn += 1
    elif usr_label == 'SYSTEM' and clf_label == 'CUE':
        fp += 1
    elif usr_label == 'SYSTEM' and clf_label == 'SYSTEM':
        tn += 1

total = len(key_data)
print(f"\nOverall agreement: {agree}/{total} ({agree/total*100:.1f}%)")
print(f"\nConfusion matrix (rows=user, cols=classifier):")
print(f"                  clf:CUE    clf:SYSTEM")
print(f"  user:CUE        {tp:<10} {fn}")
print(f"  user:SYSTEM     {fp:<10} {tn}")

prec = tp / (tp + fp) if (tp + fp) > 0 else 0
rec_val = tp / (tp + fn) if (tp + fn) > 0 else 0
print(f"\nCUE precision: {tp}/{tp+fp} = {prec:.1%}")
print(f"CUE recall:    {tp}/{tp+fn} = {rec_val:.1%}")

if disagree_list:
    print(f"\nDisagreements ({len(disagree_list)}):")
    for phrase, usr, clf, reason in disagree_list:
        print(f'  "{phrase}"')
        print(f"    user={usr}  classifier={clf}  reason: {reason}")
else:
    print("\nNo disagreements.")
