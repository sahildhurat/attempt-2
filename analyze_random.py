import json
import random

all_units = []
with open("data/archive/all_units_unfiltered.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            all_units.append(json.loads(line))
            
random.seed(43)
random_units = random.sample(all_units, 100)
random_dict = {u["id"]: u for u in random_units}

disagreement_ids = set()
with open("disagreements_random.md", "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("### Unit ID: "):
            disagreement_ids.add(line.split("### Unit ID: ")[1].strip())

disagreed = []
agreed = []

for u in random_units:
    if u["id"] in disagreement_ids:
        disagreed.append(u)
    else:
        agreed.append(u)

def get_text_len(u):
    t = u.get("text", "")
    if u.get("is_reply"):
        t += u.get("parent_text", "")
    return len(t)

disagreed_lens = [get_text_len(u) for u in disagreed]
agreed_lens = [get_text_len(u) for u in agreed]

avg_disagreed = sum(disagreed_lens) / len(disagreed_lens) if disagreed_lens else 0
avg_agreed = sum(agreed_lens) / len(agreed_lens) if agreed_lens else 0

print(f"Disagreed (N={len(disagreed)}): Avg Length = {avg_disagreed:.1f}")
print(f"Agreed (N={len(agreed)}): Avg Length = {avg_agreed:.1f}")

# >= 100 chars
over_100_disagreed = sum(1 for l in disagreed_lens if l >= 100)
over_100_agreed = sum(1 for l in agreed_lens if l >= 100)

total_over_100 = over_100_disagreed + over_100_agreed
rate_over_100 = (over_100_agreed / total_over_100) * 100 if total_over_100 > 0 else 0

print(f"Units >= 100 chars: Total={total_over_100}, Agreed={over_100_agreed}, Disagreed={over_100_disagreed}")
print(f"Agreement rate (>= 100 chars): {rate_over_100:.2f}%")

with open("docs/method_notes.md", "a", encoding="utf-8") as f:
    f.write("\n### Character-Length Distribution of Random Sample Disagreements\n")
    f.write(f"In the random sample of 100 units, the {len(disagreed)} disagreements had an average length of {avg_disagreed:.1f} characters, compared to {avg_agreed:.1f} characters for the {len(agreed)} agreements. ")
    f.write(f"When restricting the random sample to units with 100 or more characters (which matters because units below 250 characters are filtered from extraction anyway), the agreement rate rises to {rate_over_100:.2f}% ({over_100_agreed}/{total_over_100}).\n")
