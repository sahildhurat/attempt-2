"""
Classify cue phrases as CUE or SYSTEM.

CUE  = something the person remembered ABOUT A PHOTO they were trying to find:
       its subject, people in it, place, date, filename, album, device, or the
       search term they used for it.
SYSTEM = anything about the app's state, settings, behaviour, history, or an
         action the person took: album counts, face grouping, backup status,
         feature changes, settings, storage actions.

The test is whether the phrase describes the PHOTO or the SYSTEM.

Uses Haiku 4.5, thinking disabled, batched at 40 phrases per call.
"""
import os
import json
import random
import csv
import time
import requests
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in .env")

BATCH_SIZE = 40
MAX_RETRIES = 2
RATE_LIMIT_WAIT = 30

SYSTEM_PROMPT = """You are classifying phrases extracted from Google Photos support threads.

Each phrase was previously labelled as a "cue" — something a user mentioned while
trying to find or describe a photo. Some of these are genuine cues about a photo
(what was in it, where it was taken, when, what device, what album, etc.).
Others are actually about the SYSTEM — the state of the app, settings, features,
actions the user took, or observations about how the service behaved.

For each numbered phrase, assign exactly one label:

CUE    — The phrase describes something about A PHOTO the person was looking for:
         its subject, people/animals in it, place, date, filename, album name,
         device/camera used, file format, or the search term they typed.

SYSTEM — The phrase describes something about the APP, SETTINGS, BEHAVIOUR, HISTORY,
         or an ACTION the person took: album counts, face grouping on/off, backup
         status, feature changes, storage actions, sharing settings, upload status,
         sync state, account configuration, app version, etc.

The test: does this phrase describe THE PHOTO or THE SYSTEM?
Not whether it is useful. Not whether it relates to retrieval.

Output strictly as JSON, no markdown:
{
  "classifications": [
    {"n": 1, "label": "CUE", "reason": "one-line reason"},
    {"n": 2, "label": "SYSTEM", "reason": "one-line reason"},
    ...
  ]
}"""


def get_unique_phrases():
    """Extract unique cue phrases from extracted_units.jsonl."""
    phrases = set()
    with open('data/pass2/extracted_units.jsonl', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            u = json.loads(line)
            ext = u.get('extraction', {})
            for r in ext.get('remembered', []):
                if r.get('source') == 'user':
                    phrases.add(r.get('cue'))
            for f_g in ext.get('forgotten', []):
                if f_g.get('gap_type') == 'memory_gap' and f_g.get('source') == 'user':
                    phrases.add(f_g.get('cue'))
    return sorted(phrases)


def call_haiku(prompt):
    """Call Haiku 4.5 with thinking disabled. Returns (parsed, in_tok, out_tok, err)."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 4096,
        "thinking": {"type": "disabled"},
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
    except requests.exceptions.RequestException as e:
        return None, 0, 0, f"NETWORK: {e}"

    if resp.status_code == 429:
        return None, 0, 0, "RATE_LIMITED"

    if resp.status_code != 200:
        return None, 0, 0, f"HTTP_{resp.status_code}"

    data = resp.json()
    usage = data.get("usage", {})
    in_tok = usage.get("input_tokens", 0)
    out_tok = usage.get("output_tokens", 0)

    content = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            content = block.get("text", "")
            break

    if not content.strip():
        return None, in_tok, out_tok, "EMPTY"

    # Strip markdown fences if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].strip()

    try:
        parsed = json.loads(content)
        return parsed.get("classifications", []), in_tok, out_tok, None
    except json.JSONDecodeError:
        return None, in_tok, out_tok, "PARSE"


def build_prompt(phrases_batch):
    """Build the classification prompt for a batch of phrases."""
    phrases_str = "\n".join([f"{i+1}. {p}" for i, p in enumerate(phrases_batch)])
    return f"{SYSTEM_PROMPT}\n\nPhrases:\n{phrases_str}"


def main():
    phrases = get_unique_phrases()
    print(f"Total unique phrases: {len(phrases)}")

    output_file = "data/pass3/cue_classification.jsonl"
    os.makedirs("data/pass3", exist_ok=True)

    # Resume support: load already-classified phrases
    completed = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    completed.add(rec.get("phrase"))
        print(f"Resuming: {len(completed)} already classified")

    remaining = [p for p in phrases if p not in completed]
    print(f"Remaining to classify: {len(remaining)}")

    if not remaining:
        print("All phrases already classified.")
    else:
        batches = [remaining[i:i + BATCH_SIZE] for i in range(0, len(remaining), BATCH_SIZE)]
        total_in = 0
        total_out = 0
        consecutive_errors = 0

        for bi, batch in enumerate(batches):
            prompt = build_prompt(batch)
            success = False
            err = None

            for attempt in range(MAX_RETRIES + 1):
                if attempt > 0:
                    print(f"  Retry {attempt} for batch {bi+1}...")

                classifications, in_tok, out_tok, err = call_haiku(prompt)

                if err == "RATE_LIMITED":
                    print(f"  Rate limited, waiting {RATE_LIMIT_WAIT}s...")
                    time.sleep(RATE_LIMIT_WAIT)
                    continue

                if err:
                    print(f"  Batch {bi+1} attempt {attempt+1} error: {err}")
                    continue

                # Integrity checks
                if len(classifications) != len(batch):
                    err = f"Count mismatch: got {len(classifications)}, expected {len(batch)}"
                    print(f"  {err}")
                    continue

                returned_ns = {c.get("n") for c in classifications if isinstance(c, dict)}
                expected_ns = set(range(1, len(batch) + 1))
                if returned_ns != expected_ns:
                    err = f"N mismatch: expected {expected_ns}, got {returned_ns}"
                    print(f"  {err}")
                    continue

                valid_labels = {"CUE", "SYSTEM"}
                bad_labels = [c for c in classifications if isinstance(c, dict) and c.get("label") not in valid_labels]
                if bad_labels:
                    err = f"Invalid labels: {[c.get('label') for c in bad_labels]}"
                    print(f"  {err}")
                    continue

                success = True
                total_in += in_tok
                total_out += out_tok
                break

            if not success:
                print(f"  FATAL: Batch {bi+1} failed after all retries: {err}")
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    print("Circuit breaker: 3 consecutive batch failures. Stopping.")
                    break
                # Write fallback
                with open(output_file, "a", encoding="utf-8") as f:
                    for phrase in batch:
                        rec = {"phrase": phrase, "label": "UNKNOWN", "reason": f"Classification failed: {err}"}
                        f.write(json.dumps(rec) + "\n")
                continue

            consecutive_errors = 0

            # Write results
            with open(output_file, "a", encoding="utf-8") as f:
                for idx, phrase in enumerate(batch):
                    n = idx + 1
                    c = next((x for x in classifications if isinstance(x, dict) and x.get("n") == n), {})
                    label = c.get("label", "UNKNOWN")
                    reason = c.get("reason", "")
                    rec = {"phrase": phrase, "label": label, "reason": reason}
                    f.write(json.dumps(rec) + "\n")
                    f.flush()

            print(f"  Batch {bi+1}/{len(batches)} done ({in_tok} in / {out_tok} out)")

        cost = (total_in / 1_000_000) * 1.00 + (total_out / 1_000_000) * 5.00
        print(f"\nClassification cost: ${cost:.4f} ({total_in} in / {total_out} out)")

    # --- Split into CUE and SYSTEM files ---
    cue_phrases = []
    system_phrases = []
    unknown_phrases = []

    with open(output_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            label = rec.get("label")
            phrase = rec.get("phrase")
            reason = rec.get("reason", "")
            if label == "CUE":
                cue_phrases.append((phrase, reason))
            elif label == "SYSTEM":
                system_phrases.append((phrase, reason))
            else:
                unknown_phrases.append((phrase, reason))

    total = len(cue_phrases) + len(system_phrases) + len(unknown_phrases)
    system_rate = len(system_phrases) / total * 100 if total > 0 else 0

    print(f"\n{'='*50}")
    print(f"CLASSIFICATION RESULTS")
    print(f"{'='*50}")
    print(f"Total phrases:   {total}")
    print(f"CUE:             {len(cue_phrases)}  ({len(cue_phrases)/total*100:.1f}%)")
    print(f"SYSTEM:          {len(system_phrases)}  ({len(system_phrases)/total*100:.1f}%)")
    if unknown_phrases:
        print(f"UNKNOWN:         {len(unknown_phrases)}")
    print(f"SYSTEM rate:     {system_rate:.1f}%")
    print(f"{'='*50}")

    # Write CUE phrases
    cue_file = "data/pass3/cues_only.txt"
    with open(cue_file, 'w', encoding='utf-8') as f:
        for phrase, _ in sorted(cue_phrases):
            f.write(phrase + "\n")
    print(f"Wrote {len(cue_phrases)} CUE phrases to {cue_file}")

    # Write SYSTEM phrases with reasons
    sys_file = "data/pass3/system_only.txt"
    with open(sys_file, 'w', encoding='utf-8') as f:
        for phrase, reason in sorted(system_phrases):
            f.write(f"{phrase}\t{reason}\n")
    print(f"Wrote {len(system_phrases)} SYSTEM phrases to {sys_file}")

    # --- Generate blind validation sample ---
    all_classified = []
    with open(output_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("label") in ("CUE", "SYSTEM"):
                all_classified.append(rec)

    random.seed(42)
    sample = random.sample(all_classified, min(30, len(all_classified)))
    random.shuffle(sample)  # Extra shuffle for blindness

    val_file = "data/pass3/validation_sample.csv"
    with open(val_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["n", "phrase", "your_label"])
        for i, rec in enumerate(sample):
            writer.writerow([i + 1, rec["phrase"], ""])
    print(f"Wrote {len(sample)}-phrase blind validation sample to {val_file}")

    # Save the classifier's hidden labels for later comparison
    key_file = "data/pass3/validation_key.json"
    key_data = [{"n": i + 1, "phrase": rec["phrase"], "classifier_label": rec["label"]} for i, rec in enumerate(sample)]
    with open(key_file, 'w', encoding='utf-8') as f:
        json.dump(key_data, f, indent=2)
    print(f"Saved answer key to {key_file} (DO NOT SHOW TO USER)")


if __name__ == "__main__":
    main()
