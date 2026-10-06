import os
import json
import asyncio
from dotenv import load_dotenv
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "scripts", "collectors"))
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))
import network_utils
from pass1_gate_full import process_single, format_unit, calculate_cost

load_dotenv()

async def main():
    session = network_utils.get_session()
    
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
                if len(all_units) >= 5:
                    break
                    
    sem = asyncio.Semaphore(1)
    
    print("Testing 5 units sequentially to check caching...")
    total_cost = 0
    total_cache_reads = 0
    for i, u in enumerate(all_units):
        res, cost, usage = await process_single(session, model, prompt, u, sem)
        print(f"Call {i+1}:")
        print(f"  Usage: {usage}")
        print(f"  Cost: ${cost:.6f}")
        total_cost += cost
        if "cache_read_input_tokens" in usage:
            total_cache_reads += usage["cache_read_input_tokens"]
            
    print("\nExtrapolation for 1,000 units:")
    avg_cost = total_cost / len(all_units)
    proj_1000 = avg_cost * 1000
    proj_41000 = avg_cost * 41006
    print(f"  Estimated spend for 1,000 units: ${proj_1000:.4f}")
    print(f"  Estimated spend for 41,006 units: ${proj_41000:.4f}")
    print(f"  Estimated cache reads for 1,000 units: {int((total_cache_reads/len(all_units))*1000)}")

if __name__ == "__main__":
    asyncio.run(main())
