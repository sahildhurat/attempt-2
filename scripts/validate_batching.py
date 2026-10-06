import os
import json
import asyncio
from dotenv import load_dotenv
import requests
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "collectors"))
import network_utils

load_dotenv()

session = network_utils.get_session()

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
                "reason": {"type": "string", "description": "Brief reason for the decision"},
                "relevant": {"type": "string", "enum": ["yes", "partial", "no"]}
            },
            "required": ["reason", "relevant"]
        }
    }
]

async def process_single(model, prompt, unit, sem):
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
            for block in data.get("content", []):
                if block.get("type") == "tool_use" and block.get("name") == "record_decision":
                    return block.get("input", {})
            return {"relevant": "error", "reason": "No tool use"}
        except Exception as e:
            print(f"Single Error: {e}")
            return {"relevant": "error", "reason": str(e)}

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
                        "required": ["n", "reason", "decision"]
                    }
                }
            },
            "required": ["decisions"]
        }
    }
]

async def process_batch(model, prompt, batch_units, sem):
    async with sem:
        text_parts = []
        for i, u in enumerate(batch_units):
            text_parts.append(f"Unit {i+1}:\n{format_unit(u)}\n")
        full_text = "\n".join(text_parts)
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
                    return block.get("input", {}).get("decisions", [])
            return []
        except Exception as e:
            print(f"Batch Error: {e}")
            return []

async def validate_batch_size(units, batch_size, single_results, model, prompt, sem):
    print(f"\n--- Testing batch size {batch_size} ---")
    batch_results = {}
    
    async def run_batch(idx, b):
        res = await process_batch(model, prompt, b, sem)
        return (idx, b, res)
        
    batches = [units[i:i + batch_size] for i in range(0, len(units), batch_size)]
    tasks = [asyncio.create_task(run_batch(i, b)) for i, b in enumerate(batches)]
    
    for completed_task in asyncio.as_completed(tasks):
        idx, b, decisions = await completed_task
        for d in decisions:
            n = d.get("n", 0)
            if 1 <= n <= len(b):
                unit_id = b[n - 1]["id"]
                batch_results[unit_id] = d
    
    agreements = 0
    disagreements = []
    
    for u in units:
        uid = u["id"]
        s_data = single_results.get(uid, {})
        b_data = batch_results.get(uid, {})
        
        s_res = s_data.get("relevant", "missing")
        b_res = b_data.get("decision", "missing")
        
        if s_res == b_res:
            agreements += 1
        else:
            disagreements.append({
                "id": uid,
                "text": format_unit(u),
                "single_decision": s_res,
                "single_reason": s_data.get("reason", "none"),
                "batch_decision": b_res,
                "batch_reason": b_data.get("reason", "none")
            })
            
    rate = agreements / len(units)
    print(f"Agreement rate: {rate:.2%}")
    
    if disagreements:
        with open("disagreements.md", "w", encoding="utf-8") as f:
            f.write(f"# Disagreements (Rate: {rate:.2%})\n\n")
            for d in disagreements:
                f.write(f"### Unit ID: {d['id']}\n")
                f.write(f"**Single Decision:** {d['single_decision']}\n")
                f.write(f"**Single Reason:** {d['single_reason']}\n\n")
                f.write(f"**Batch Decision:** {d['batch_decision']}\n")
                f.write(f"**Batch Reason:** {d['batch_reason']}\n\n")
                f.write(f"**Text:**\n```\n{d['text']}\n```\n")
                f.write("---\n")
                
    return rate

async def main():
    with open("prompts/pass1_relevance_gate.md", "r", encoding="utf-8") as f:
        prompt = f.read()
        
    with open("config/models.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        model = config["pass1_gate"]["model"]
        
    units = []
    with open("data/archive/units_prefiltered.jsonl", "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            units.append(json.loads(line))
            if i >= 99:
                break
                
    sem = asyncio.Semaphore(5)
    
    async def run_single(idx, u):
        res = await process_single(model, prompt, u, sem)
        return (idx, u["id"], res)

    print("Running 100 units one-per-call...")
    tasks = [asyncio.create_task(run_single(i, u)) for i, u in enumerate(units)]
    single_results = {}
    for completed_task in asyncio.as_completed(tasks):
        idx, uid, res = await completed_task
        single_results[uid] = res
        
    rate_25 = await validate_batch_size(units, 25, single_results, model, prompt, sem)
    
if __name__ == "__main__":
    asyncio.run(main())
