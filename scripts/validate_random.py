import os
import json
import asyncio
import random
from dotenv import load_dotenv
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "collectors"))
from validate_batching import process_single, process_batch, validate_batch_size

load_dotenv()

async def main():
    with open("prompts/pass1_relevance_gate.md", "r", encoding="utf-8") as f:
        prompt = f.read()
        
    with open("config/models.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        model = config["pass1_gate"]["model"]
        
    all_units = []
    with open("data/archive/all_units_unfiltered.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                all_units.append(json.loads(line))
                
    random.seed(43)
    random_units = random.sample(all_units, 100)
    
    sem = asyncio.Semaphore(5)
    
    print("Running random 100 units one-per-call...")
    single_results = {}
    async def run_single(idx, u):
        res = await process_single(model, prompt, u, sem)
        return (idx, u["id"], res)
        
    tasks = [asyncio.create_task(run_single(i, u)) for i, u in enumerate(random_units)]
    for completed_task in asyncio.as_completed(tasks):
        idx, uid, res = await completed_task
        single_results[uid] = res
        
    rate_25 = await validate_batch_size(random_units, 25, single_results, model, prompt, sem)
    
    # rename disagreements to distinguish it
    if os.path.exists("disagreements.md"):
        os.replace("disagreements.md", "disagreements_random.md")

if __name__ == "__main__":
    asyncio.run(main())
