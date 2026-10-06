"""
Run cue induction on the cleaned CUE-only set (554 phrases).
Four shuffles, Haiku 4.5, thinking disabled, A3 constraints.
Persisted as run_1..run_4.

Then rebuild docs/checkpoint3_review.md from the four new runs (cues only)
plus the existing breakdown/workaround runs from taxonomy_haiku.json.
"""
import json
import random
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")

INDUCTION_PROMPT = '''You are a qualitative researcher building a taxonomy from a list of short phrases.

Group the phrases below into categories derived from the phrases themselves, not from any prior expectation about what categories should exist. Each phrase belongs to at most one category.

Each category must have:
1. A short, descriptive name (1-3 words).
2. A clear definition of what belongs in it.
3. Exactly 3 phrases from the list that belong to it.

Do not create a catch-all category such as "Other" or "Miscellaneous". You need not force every phrase into a category — phrases that do not fit any coherent group may be left unassigned.

Output format must be strictly JSON:
{
  "categories": [
    {
      "name": "string",
      "definition": "string",
      "examples": ["string", "string", "string"]
    }
  ]
}'''


def call_haiku(system_prompt, user_text):
    """Call Haiku 4.5, thinking disabled. Returns (parsed, usage)."""
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
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_text}
        ]
    }

    for attempt in range(5):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"    Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code == 200:
                data = resp.json()
                content = data["content"][0]["text"]
                usage = data.get("usage", {})

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()

                return json.loads(content), usage
            else:
                print(f"    HTTP {resp.status_code}, retrying...")
                time.sleep(5)
        except Exception as e:
            print(f"    Error: {e}, retrying...")
            time.sleep(5)
    return None, {}


def load_cue_phrases():
    """Load the 554 CUE-labelled phrases."""
    phrases = []
    with open('data/pass3/cues_only.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                phrases.append(line)
    return phrases


def run_induction_pass(phrases, run_seed):
    """Run one induction pass with given seed for shuffle."""
    rng = random.Random(run_seed)
    shuffled = list(phrases)
    rng.shuffle(shuffled)
    text_input = "Phrases:\n" + json.dumps(shuffled, indent=2)
    return call_haiku(INDUCTION_PROMPT, text_input)


def build_checkpoint3(cue_runs, bw_data):
    """Rebuild docs/checkpoint3_review.md from cue runs + existing breakdown/workaround."""

    lines = []
    lines.append("# Checkpoint 3 Review: Pass 3 Induction Stability\n")
    lines.append("Stability is assessed by human mapping because label strings differ across runs by construction. Exact string matching cannot reliably detect when two runs find the same category under different labels.\n")

    # --- Field: cues (from new induction) ---
    lines.append("## Field: cues\n")
    for run_name in ["run_1", "run_2", "run_3", "run_4"]:
        run = cue_runs.get(run_name, {})
        categories = run.get("categories", [])
        lines.append(f"### {run_name}")
        for cat in categories:
            name = cat.get("name", "")
            defn = cat.get("definition", "")
            examples = cat.get("examples", [])
            lines.append(f"- **{name}**: {defn}")
            lines.append(f"  - Count: {len(examples)} phrase(s)")
            lines.append(f'  - Examples: {", ".join([repr(e) for e in examples])}')
        lines.append("")

    # Mapping table placeholder for cues
    num_concepts = max(len(r.get("categories", [])) for r in cue_runs.values()) if cue_runs else 10
    num_concepts = max(num_concepts, 10)
    lines.append("### Mapping Table (cues)\n")
    lines.append("| Category Concept | run_1 | run_2 | run_3 | run_4 |")
    lines.append("|---|---|---|---|---|")
    for _ in range(num_concepts):
        lines.append("| |  |  |  |  |")
    lines.append("")
    lines.append("")

    # --- Field: breakdown (from existing taxonomy_haiku.json) ---
    if "breakdown" in bw_data:
        lines.append("## Field: breakdown\n")
        for run_name in ["run_1", "run_2", "run_3", "run_4"]:
            run = bw_data["breakdown"].get(run_name, {})
            categories = run.get("categories", [])
            lines.append(f"### {run_name}")
            for cat in categories:
                name = cat.get("name", "")
                defn = cat.get("definition", "")
                examples = cat.get("examples", [])
                lines.append(f"- **{name}**: {defn}")
                lines.append(f"  - Count: {len(examples)} phrase(s)")
                lines.append(f'  - Examples: {", ".join([repr(e) for e in examples])}')
            lines.append("")

        bk_concepts = max(len(r.get("categories", [])) for r in bw_data["breakdown"].values()) if bw_data.get("breakdown") else 10
        bk_concepts = max(bk_concepts, 10)
        lines.append("### Mapping Table (breakdown)\n")
        lines.append("| Category Concept | run_1 | run_2 | run_3 | run_4 |")
        lines.append("|---|---|---|---|---|")
        for _ in range(bk_concepts):
            lines.append("| |  |  |  |  |")
        lines.append("")

    # --- Field: workaround (from existing taxonomy_haiku.json) ---
    if "workaround" in bw_data:
        lines.append("## Field: workaround\n")
        for run_name in ["run_1", "run_2", "run_3", "run_4"]:
            run = bw_data["workaround"].get(run_name, {})
            categories = run.get("categories", [])
            lines.append(f"### {run_name}")
            for cat in categories:
                name = cat.get("name", "")
                defn = cat.get("definition", "")
                examples = cat.get("examples", [])
                lines.append(f"- **{name}**: {defn}")
                lines.append(f"  - Count: {len(examples)} phrase(s)")
                lines.append(f'  - Examples: {", ".join([repr(e) for e in examples])}')
            lines.append("")

        wk_concepts = max(len(r.get("categories", [])) for r in bw_data["workaround"].values()) if bw_data.get("workaround") else 10
        wk_concepts = max(wk_concepts, 10)
        lines.append("### Mapping Table (workaround)\n")
        lines.append("| Category Concept | run_1 | run_2 | run_3 | run_4 |")
        lines.append("|---|---|---|---|---|")
        for _ in range(wk_concepts):
            lines.append("| |  |  |  |  |")
        lines.append("")

    return "\n".join(lines)


def main():
    phrases = load_cue_phrases()
    print(f"Loaded {len(phrases)} CUE phrases for induction")

    total_in = 0
    total_out = 0
    cue_runs = {}

    for i in range(1, 5):
        print(f"Run {i} starting...")
        result, usage = run_induction_pass(phrases, run_seed=i)
        if result:
            cue_runs[f"run_{i}"] = result
            in_tok = usage.get("input_tokens", 0)
            out_tok = usage.get("output_tokens", 0)
            total_in += in_tok
            total_out += out_tok
            cat_count = len(result.get("categories", []))
            print(f"  Run {i} done: {cat_count} categories ({in_tok} in / {out_tok} out)")
        else:
            print(f"  Run {i} FAILED")

    # Save cue induction results
    os.makedirs("data/pass3", exist_ok=True)
    with open("data/pass3/cue_induction.json", "w", encoding="utf-8") as f:
        json.dump(cue_runs, f, indent=2)
    print(f"\nSaved cue induction to data/pass3/cue_induction.json")

    cost = (total_in / 1_000_000) * 1.00 + (total_out / 1_000_000) * 5.00
    print(f"Total cost: ${cost:.5f} ({total_in} in / {total_out} out)")

    # Load existing breakdown/workaround from taxonomy_haiku.json
    bw_data = {}
    if os.path.exists("taxonomy_haiku.json"):
        with open("taxonomy_haiku.json", "r", encoding="utf-8") as f:
            bw_data = json.load(f)

    # Rebuild checkpoint3_review.md
    md = build_checkpoint3(cue_runs, bw_data)
    with open("docs/checkpoint3_review.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("Rebuilt docs/checkpoint3_review.md")

    # Summary
    print(f"\n{'='*50}")
    print("INDUCTION SUMMARY")
    print(f"{'='*50}")
    for rname, rdata in cue_runs.items():
        print(f"  {rname}: {len(rdata.get('categories', []))} categories")
    print(f"  Cost: ${cost:.5f}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
