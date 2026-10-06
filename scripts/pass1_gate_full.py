import os
import json
import asyncio
from dotenv import load_dotenv
import time
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "collectors"))
import network_utils

load_dotenv()

# Claude 3.5 Haiku Pricing (estimated fallback)
# Input: $1.00 / 1M, Output: $5.00 / 1M
# Cache Write: $1.25 / 1M, Cache Read: $0.10 / 1M

def calculate_cost(usage):
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cache_creation = usage.get("cache_creation_input_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)
    
    # Base inputs are input_tokens minus the cache creation tokens
    base_input = input_tokens
    
    cost = (base_input / 1_000_000) * 1.00
    cost += (output_tokens / 1_000_000) * 5.00
    cost += (cache_creation / 1_000_000) * 1.25
    cost += (cache_read / 1_000_000) * 0.10
    
    return cost

def format_unit(unit):
    text = unit.get("text", "")
    if unit.get("is_reply"):
        parent_text = unit.get("parent_text", "")
        text = f"[PARENT POST]\n{parent_text}\n\n[REPLY]\n{text}"
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

async def process_single(session, model, prompt, unit, sem):
    async with sem:
        text = format_unit(unit)
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
                    "text": prompt
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
            cost = calculate_cost(usage)
            
            for block in data.get("content", []):
                if block.get("type") == "tool_use" and block.get("name") == "record_decision":
                    input_data = block.get("input", {})
                    return input_data, cost, usage
            return {"decision": "error", "reason": "No tool use", "language": "unknown"}, cost, usage
        except Exception as e:
            return {"decision": "error", "reason": str(e), "language": "unknown"}, 0.0, {}

async def main():
    session = network_utils.get_session()
    
    with open("prompts/pass1_relevance_gate.md", "r", encoding="utf-8") as f:
        prompt = f.read()
        
    with open("config/models.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        model = config["pass1_gate"]["model"]
        
    input_file = "data/target_list.jsonl"
    output_file = "data/gate_results.jsonl"
    
    completed_ids = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    completed_ids.add(json.loads(line)["id"])
                    
    units_to_process = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                u = json.loads(line)
                if u["id"] not in completed_ids:
                    units_to_process.append(u)
                    
    total_to_process = len(units_to_process)
    print(f"Total units remaining to process: {total_to_process}")
    
    if total_to_process == 0:
        return
        
    sem = asyncio.Semaphore(8)
    
    total_cost = 0.0
    processed_count = 0
    total_cache_reads = 0
    outcome_counts = {"yes": 0, "partial": 0, "no": 0, "error": 0}
    
    out_f = open(output_file, "a", encoding="utf-8")
    
    # Process in chunks of 200 for flushing
    chunk_size = 200
    for i in range(0, total_to_process, chunk_size):
        chunk = units_to_process[i:i+chunk_size]
        
        async def run_task(u):
            res, cost, usage = await process_single(session, model, prompt, u, sem)
            return u, res, cost, usage
            
        tasks = [asyncio.create_task(run_task(u)) for u in chunk]
        
        for completed_task in asyncio.as_completed(tasks):
            u, res, cost, usage = await completed_task
            total_cost += cost
            processed_count += 1
            if usage and "cache_read_input_tokens" in usage:
                total_cache_reads += usage["cache_read_input_tokens"]
                
            decision = res.get("decision", "error")
            outcome_counts[decision] = outcome_counts.get(decision, 0) + 1
            
            u["gate_decision"] = decision
            u["gate_reason"] = res.get("reason", "")
            u["gate_language"] = res.get("language", "unknown")
            
            out_f.write(json.dumps(u) + "\n")
            
            if processed_count > 0 and processed_count % 250 == 0:
                print(f"--- PROGRESS UPDATE ---")
                print(f"Processed {processed_count}/{total_to_process} units.")
                print(f"Actual spend so far: ${total_cost:.4f}")
                print(f"Outcome Distribution: {outcome_counts}")
                
                if total_cost > 11.0:
                    print(f"Actual cost ${total_cost:.4f} exceeds $11.00 budget. FLUSHING AND STOPPING execution.")
                    out_f.flush()
                    out_f.close()
                    sys.exit(1)
                
        out_f.flush()
        
    out_f.close()
    
    print("\n=== GATE RUN COMPLETED ===")
    print(f"Total processed in this run: {processed_count}")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Final distribution: {outcome_counts}")

if __name__ == "__main__":
    asyncio.run(main())
