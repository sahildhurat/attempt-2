import json
import asyncio
import os
import random
import sys
from collectors.network_utils import get_session

# We will import process_single from pass1_gate_full
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pass1_gate_full import process_single

async def main():
    with open("config/models.json", "r") as f:
        model = json.load(f)["pass1_gate"]["model"]
        
    with open("prompts/pass1_relevance_gate.md", "r", encoding="utf-8") as f:
        prompt = f.read()

    playstore_units = []
    with open("data/archive/all_units_unfiltered.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                u = json.loads(line)
                if u["source"] == "playstore":
                    playstore_units.append(u)

    # Sort to ensure stable random state
    playstore_units.sort(key=lambda x: x["id"])
    
    random.seed(42)
    selected = random.sample(playstore_units, min(200, len(playstore_units)))
    
    # Give them the correct weight
    for u in selected:
        u["weight"] = 11025 / 200.0
        
    # Check already processed
    completed_ids = set()
    if os.path.exists("data/gate_results.jsonl"):
        with open("data/gate_results.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    completed_ids.add(json.loads(line)["id"])
                    
    to_process = [u for u in selected if u["id"] not in completed_ids]
    
    print(f"Playstore units to process: {len(to_process)}")
    
    if len(to_process) == 0:
        return
        
    session = get_session()
    sem = asyncio.Semaphore(8)
    total_cost = 0.0
    outcome_counts = {"yes": 0, "partial": 0, "no": 0, "error": 0}
    
    out_f = open("data/gate_results.jsonl", "a", encoding="utf-8")
    
    async def run_task(u):
        res, cost, usage = await process_single(session, model, prompt, u, sem)
        return u, res, cost, usage
        
    tasks = [asyncio.create_task(run_task(u)) for u in to_process]
    
    processed = 0
    for completed_task in asyncio.as_completed(tasks):
        u, res, cost, usage = await completed_task
        total_cost += cost
        processed += 1
        
        decision = res.get("decision", "error")
        outcome_counts[decision] = outcome_counts.get(decision, 0) + 1
        
        u["gate_decision"] = decision
        u["gate_reason"] = res.get("reason", "")
        u["gate_language"] = res.get("language", "unknown")
        
        out_f.write(json.dumps(u) + "\n")
        
    out_f.close()
    
    print(f"Completed playstore processing. Cost: ${total_cost:.4f}")
    print(f"Outcomes: {outcome_counts}")

if __name__ == "__main__":
    asyncio.run(main())
