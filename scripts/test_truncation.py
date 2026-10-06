import os
import json
import asyncio
import random
from dotenv import load_dotenv
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "collectors"))
import network_utils

load_dotenv()

def format_unit(unit, truncate=None):
    text = unit.get("text", "")
    if unit.get("is_reply"):
        parent_text = unit.get("parent_text", "")
        text = f"[PARENT POST]\n{parent_text}\n\n[REPLY]\n{text}"
    if truncate and len(text) > truncate:
        text = text[:truncate]
    return text

tools_single = [
    {
        "name": "record_decision",
        "description": "Record the relevance decision for the unit",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Brief reason for the decision, max 25 words"},
                "decision": {"type": "string", "enum": ["yes", "partial", "no"]},
                "language": {"type": "string", "description": "ISO 639-1 two-letter code"}
            },
            "required": ["reason", "decision", "language"]
        }
    }
]

async def process_single(session, model, prompt, text, sem):
    async with sem:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": os.environ.get("ANTHROPIC_API_KEY"),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": model,
            "max_tokens": 1024,
            "system": [
                {
                    "type": "text",
                    "text": prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            "messages": [
                {"role": "user", "content": text}
            ],
            "tools": tools_single,
            "tool_choice": {"type": "tool", "name": "record_decision"},
            "temperature": 0.0
        }
        
        try:
            response = await asyncio.to_thread(
                network_utils.fetch_with_rate_limit,
                session, "POST", url, "gate_single", 
                json=payload, headers=headers
            )
            data = response.json()
            usage = data.get("usage", {})
            
            for block in data.get("content", []):
                if block.get("type") == "tool_use" and block.get("name") == "record_decision":
                    input_data = block.get("input", {})
                    return input_data, usage
            return {"decision": "error", "reason": "No tool use", "language": "unknown"}, usage
        except Exception as e:
            return {"decision": "error", "reason": str(e), "language": "unknown"}, {}

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
                u = json.loads(line)
                if len(format_unit(u)) > 600:
                    all_units.append(u)
                    
    random.seed(42)
    test_units = random.sample(all_units, min(200, len(all_units)))
    
    print(f"Found {len(test_units)} units > 600 chars.")
    
    sem = asyncio.Semaphore(8)
    
    results = []
    cache_reads = []
    
    async def run_pair(u):
        full_text = format_unit(u)
        trunc_text = format_unit(u, truncate=600)
        
        full_res, full_usage = await process_single(session, model, prompt, full_text, sem)
        trunc_res, trunc_usage = await process_single(session, model, prompt, trunc_text, sem)
        
        if "cache_read_input_tokens" in full_usage and full_usage["cache_read_input_tokens"] > 0:
            cache_reads.append(full_usage["cache_read_input_tokens"])
        if "cache_read_input_tokens" in trunc_usage and trunc_usage["cache_read_input_tokens"] > 0:
            cache_reads.append(trunc_usage["cache_read_input_tokens"])
            
        return u["id"], full_res.get("decision"), trunc_res.get("decision")
        
    tasks = [asyncio.create_task(run_pair(u)) for u in test_units]
    
    matches = 0
    total = 0
    for completed_task in asyncio.as_completed(tasks):
        uid, full_dec, trunc_dec = await completed_task
        if full_dec == trunc_dec:
            matches += 1
        total += 1
        
    rate = (matches / total) * 100 if total > 0 else 0
    print(f"Truncation 600 Agreement rate: {rate:.2f}% ({matches}/{total})")
    
    if cache_reads:
        print(f"Cache reads observed (n={len(cache_reads)}): avg {sum(cache_reads)/len(cache_reads)} tokens")
    else:
        print("NO CACHE READS OBSERVED. System prompt may be < 1024 tokens.")
        
    if rate >= 98.0:
        print("ACTION: apply 600-char truncation")
    elif rate >= 95.0:
        print("ACTION: rate 95-98%. Testing at 1000 chars...")
        
        # Test at 1000 chars
        matches_1k = 0
        total_1k = 0
        
        async def run_pair_1k(u):
            full_text = format_unit(u)
            trunc_text = format_unit(u, truncate=1000)
            full_res, _ = await process_single(session, model, prompt, full_text, sem)
            trunc_res, _ = await process_single(session, model, prompt, trunc_text, sem)
            return full_res.get("decision"), trunc_res.get("decision")
            
        tasks_1k = [asyncio.create_task(run_pair_1k(u)) for u in test_units]
        for completed_task in asyncio.as_completed(tasks_1k):
            full_dec, trunc_dec = await completed_task
            if full_dec == trunc_dec:
                matches_1k += 1
            total_1k += 1
            
        rate_1k = (matches_1k / total_1k) * 100 if total_1k > 0 else 0
        print(f"Truncation 1000 Agreement rate: {rate_1k:.2f}% ({matches_1k}/{total_1k})")
        if rate_1k >= 98.0:
            print("ACTION: apply 1000-char truncation")
        else:
            print("ACTION: apply NO truncation")
    else:
        print("ACTION: apply NO truncation")

if __name__ == "__main__":
    asyncio.run(main())
