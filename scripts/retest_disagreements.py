import os
import json
import asyncio
from dotenv import load_dotenv
import sys

sys.path.append(os.path.dirname(__file__))
from validate_batching import process_single, process_batch

load_dotenv()

TARGET_IDS = [
    "2491b1d4d40bd75ed7d948a14bf70ff7373b613b52ea093095048cd0ad323758",
    "1a51e61340bd44b5301291b5229a5ed1e4f49001b0baf93f590ad03225d91741",
    "748f93c47ca4297746abcee43e20b2064227a72e7b134728537c3c0adbbd4304",
    "6003c8d413b109c4e095422c74efe77cea8379fe0e19e4795bb362fa9cc5cf7c",
    "fe417d0542c2a52057d542963a04ca6e8a40b921d7b8f591364a69f5f6f73577",
    "6ba13d264e35a1abbde9de9d8a8d344ebe27d3f0302696eb5d268beb045d8b54",
    "425b0228302bc06b4c36e292bc55f6a3beb662090c5bf0fa36e488766f6dc6be",
    "f7b307b390906ba3ad3fefb5a27073e53d54d9da7f40acb13f0a6ae9ec7ec3e5",
    "4fafb85e249194dc20e63258c1fe94347ba0a4843d2659fc2db62bfa1c777ece",
    "5590a80247d54bc2808c1f8e5b8a69ccd5d30ec5826862b69f80046e8d5a097d",
    "e47226558010783c42a6362e87b49ac6d0bb4174a87f7a08f16f683f1e98b10a",
    "e36605794d27e0045867fe60b61ef86aa918ca398f666d94ec3f4d481aa1799d",
    "134088e155b39b25c9b069588b674c6ea3495246de7242972165a618a9e3e862",
    "adeb4eb9ccccc5a27bce88bf3b12de2eea0b8c11eed63272d912717627772bb7",
    "bb55c18c8145ed38c7b2fd3a5b6e4bc2305028421fd6017bd98ab2026e275c20",
    "4693ee18b8f1748c4d9cf6d0b97e3742e33e8165c384bc46260cce69cb68ef99",
    "d993cb8aa3e58583ab09dda446905dbdba038b8ee80c529823be02e7352a5386",
    "7d6d79389061fdc6c0e8c6b13bc987e4fb70f2a51d42e3d49de89b64fd41d5e8"
]

async def main():
    with open("prompts/pass1_relevance_gate.md", "r", encoding="utf-8") as f:
        prompt = f.read()
        
    with open("config/models.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        model = config["pass1_gate"]["model"]
        
    units_to_test = []
    with open("data/archive/units_prefiltered.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            if u["id"] in TARGET_IDS:
                units_to_test.append(u)
                
    sem = asyncio.Semaphore(5)
    
    print(f"Testing {len(units_to_test)} original disagreement units...")
    
    # Run Single
    single_results = {}
    async def run_single(u):
        res = await process_single(model, prompt, u, sem)
        single_results[u["id"]] = res
        
    await asyncio.gather(*(run_single(u) for u in units_to_test))
    
    # Run Batch (as one single batch of 18)
    batch_decisions = await process_batch(model, prompt, units_to_test, sem)
    batch_results = {}
    for d in batch_decisions:
        n = d.get("n", 0)
        if 1 <= n <= len(units_to_test):
            batch_results[units_to_test[n-1]["id"]] = d
            
    # Output comparison
    with open("retest_results.md", "w", encoding="utf-8") as f:
        f.write("# Retest of Original 18 Disagreements (New Rules)\n\n")
        
        for u in units_to_test:
            uid = u["id"]
            s_res = single_results.get(uid, {})
            b_res = batch_results.get(uid, {})
            
            s_dec = s_res.get("relevant", "missing")
            b_dec = b_res.get("decision", "missing")
            
            converged = (s_dec == b_dec)
            status = "CONVERGED" if converged else "DISAGREEMENT"
            
            f.write(f"### Unit ID: {uid} [{status}]\n")
            f.write(f"**Single:** {s_dec} | Reason: {s_res.get('reason', '')}\n")
            f.write(f"**Batch:** {b_dec} | Reason: {b_res.get('reason', '')}\n")
            f.write(f"**Text:** {u.get('text', '')[:100]}...\n")
            f.write("---\n")
            
    print("Retest complete. Results in retest_results.md")

if __name__ == "__main__":
    asyncio.run(main())
