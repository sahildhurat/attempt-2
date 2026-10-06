import os
import json
import asyncio
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "collectors"))
import network_utils
import call_counter

load_dotenv()

session = network_utils.get_session()

def format_unit(unit):
    text = unit.get("text", "")
    if unit.get("is_reply"):
        parent_text = unit.get("parent_text", "")
        text = f"[PARENT POST]\n{parent_text}\n\n[REPLY]\n{text}"
    return text

tools_batch = [
    {
        "name": "record_batch_decisions",
        "description": "Record the relevance decisions for the batch of units",
        "input_schema": {
            "type": "object",
            "properties": {
                "decisions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "n": {"type": "integer", "description": "Unit number (1-indexed)"},
                            "reason": {"type": "string", "description": "Brief reason for the decision"},
                            "decision": {"type": "string", "enum": ["yes", "partial", "no"]},
                            "language": {"type": "string", "description": "Language of the text"}
                        },
                        "required": ["n", "reason", "decision", "language"]
                    }
                }
            },
            "required": ["decisions"]
        }
    }
]

async def process_batch(model, prompt, batch_units, sem, f_all, f_rel):
    async with sem:
        text_parts = []
        for i, u in enumerate(batch_units):
            text_parts.append(f"Unit {i+1}:\n{format_unit(u)}\n")
        full_text = "\n".join(text_parts)
        
        batch_decisions = []
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": os.environ.get("ANTHROPIC_API_KEY"),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": model,
            "max_tokens": 4096,
            "system": [
                {
                    "type": "text",
                    "text": prompt + "\n\nJudge each unit independently. Your decision on one unit must not be influenced by your decisions on the others. The units in a batch are unrelated to each other, and a run of similar decisions is not evidence about the next one.",
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            "messages": [
                {"role": "user", "content": full_text}
            ],
            "tools": tools_batch,
            "tool_choice": {"type": "tool", "name": "record_batch_decisions"},
            "temperature": 0.0
        }
        
        try:
            response = await asyncio.to_thread(
                network_utils.fetch_with_rate_limit,
                session, "POST", url, "gate_batch", 
                json=payload, headers=headers
            )
            data = response.json()
            for block in data.get("content", []):
                if block.get("type") == "tool_use" and block.get("name") == "record_batch_decisions":
                    batch_decisions = block.get("input", {}).get("decisions", [])
                    break
            call_counter.log_success(model)
        except Exception as e:
            print(f"Batch Error: {e}")
            
        returned_map = {d.get("n"): d for d in batch_decisions if isinstance(d, dict)}
        
        results = []
        for i, u in enumerate(batch_units):
            n = i + 1
            d = returned_map.get(n, {})
            u["relevant"] = d.get("decision", "error")
            u["reason"] = d.get("reason", "Missing/Error")
            u["language"] = d.get("language", "unknown")
            
            json_str = json.dumps(u) + "\n"
            f_all.write(json_str)
            f_all.flush()
            if u["relevant"] in ["yes", "partial"]:
                f_rel.write(json_str)
                f_rel.flush()
            results.append(u)
        return results

async def main():
    with open("prompts/pass1_relevance_gate.md", "r", encoding="utf-8") as f:
        prompt = f.read()
        
    with open("config/models.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        model = config["pass1_gate"]["model"]
        
    os.makedirs("data/pass1", exist_ok=True)
    all_out_path = "data/pass1/gated_units.jsonl"
    rel_out_path = "data/pass1/relevant_units.jsonl"
    
    completed_ids = set()
    if os.path.exists(all_out_path):
        with open(all_out_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    completed_ids.add(json.loads(line)["id"])
                    
    print(f"Loaded {len(completed_ids)} already completed units.")
    
    units = []
    with open("data/archive/all_units_unfiltered.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                u = json.loads(line)
                if u.get("id") not in completed_ids:
                    units.append(u)
                
    print(f"Processing {len(units)} units (no pre-filter)...")
    
    sem = asyncio.Semaphore(1) 
    
    batch_size = 25
    batches = [units[i:i + batch_size] for i in range(0, len(units), batch_size)]
    
    f_all = open(all_out_path, "a", encoding="utf-8")
    f_rel = open(rel_out_path, "a", encoding="utf-8")
    
    processed = 0
    yes_count = 0
    partial_count = 0
    
    try:
        for i, b in enumerate(batches):
            batch_results = await process_batch(model, prompt, b, sem, f_all, f_rel)
            processed += len(batch_results)
            for u in batch_results:
                rel = u.get("relevant")
                if rel == "yes":
                    yes_count += 1
                elif rel == "partial":
                    partial_count += 1
                    
            if (i + 1) % 100 == 0 or i == len(batches) - 1:
                total_calls = call_counter.get_running_total()
                print(f"Batch {i+1}/{len(batches)} (Processed {processed}/{len(units)} units). Yes: {yes_count}, Partial: {partial_count}. Running total calls: {total_calls}", flush=True)
    except SystemExit:
        print("Gate run aborted by circuit breaker.", flush=True)
    finally:
        f_all.close()
        f_rel.close()
    
    print("\nPass 1 Gate Execution Finished.", flush=True)
    
    # Calculate yield by source, source_type, language, text_completeness
    yield_stats = {}
    decision_dist = {}
    
    with open(all_out_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            u = json.loads(line)
            src = u.get("source", "unknown")
            stype = u.get("source_type", "unknown")
            lang = u.get("language", "unknown")
            comp = u.get("text_completeness", "unknown")
            rel = u.get("relevant", "error")
            
            if src not in decision_dist:
                decision_dist[src] = {"yes": 0, "partial": 0, "no": 0, "error": 0}
            if rel in decision_dist[src]:
                decision_dist[src][rel] += 1
            else:
                decision_dist[src]["error"] += 1
                
            if rel in ["yes", "partial"]:
                if src not in yield_stats: yield_stats[src] = {}
                if stype not in yield_stats[src]: yield_stats[src][stype] = {}
                if lang not in yield_stats[src][stype]: yield_stats[src][stype][lang] = {}
                if comp not in yield_stats[src][stype][lang]: yield_stats[src][stype][lang][comp] = 0
                yield_stats[src][stype][lang][comp] += 1
                
    print("\n--- Decision Distribution by Source ---", flush=True)
    for src, d in decision_dist.items():
        print(f"{src}: yes={d['yes']} partial={d['partial']} no={d['no']} error={d['error']}", flush=True)
        
    print("\n--- Stage 1 Yield (Yes/Partial) ---", flush=True)
    import pprint
    pprint.pprint(yield_stats)
            
    # Generate stratified blind sample
    import random
    all_yes, all_partial, all_no = {}, {}, {}
    with open(all_out_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            u = json.loads(line)
            src = u.get("source", "unknown")
            rel = u.get("relevant")
            
            if rel == "yes":
                all_yes.setdefault(src, []).append(u)
            elif rel == "partial":
                all_partial.setdefault(src, []).append(u)
            elif rel == "no":
                all_no.setdefault(src, []).append(u)
                
    def stratify(pool_dict, target):
        sources = list(pool_dict.keys())
        if not sources: return []
        selected = []
        quota = {s: 0 for s in sources}
        for i in range(target):
            quota[sources[i % len(sources)]] += 1
            
        random.seed(42)
        for s in sources:
            pool = pool_dict[s]
            random.shuffle(pool)
            k = min(quota[s], len(pool))
            selected.extend(pool[:k])
            
        return selected

    s_yes = stratify(all_yes, 80)
    s_partial = stratify(all_partial, 40)
    s_no = stratify(all_no, 80)
    
    blind_sample = s_yes + s_partial + s_no
    random.seed(42)
    random.shuffle(blind_sample)
    
    answer_key = []
    with open("data/pass1/blind_sample.jsonl", "w", encoding="utf-8") as f:
        for u in blind_sample:
            answer_key.append({"id": u["id"], "gate_decision": u.get("relevant"), "gate_reason": u.get("reason"), "language": u.get("language")})
            u_out = {k: v for k, v in u.items() if k not in ["relevant", "reason", "language"]}
            u_out["my_label"] = ""
            f.write(json.dumps(u_out) + "\n")
            
    import shutil
    shutil.copy("data/pass1/blind_sample.jsonl", "data/pass1/blind_sample_copy2.jsonl")
            
    with open("data/pass1/blind_sample_key.jsonl", "w", encoding="utf-8") as f:
        for a in answer_key:
            f.write(json.dumps(a) + "\n")
            
    print(f"\nGenerated stratified {len(blind_sample)}-unit blind sample and answer key.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
