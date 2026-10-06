import json
import asyncio
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Literal, List
import call_counter
import sys
import io

# Ensure utf-8 output for emojis etc.


load_dotenv()

class GateResponseSingle(BaseModel):
    relevant: Literal["yes", "partial", "no"]
    reason: str

class BatchDecision(BaseModel):
    n: int
    decision: Literal["yes", "partial", "no"]
    reason: str

class GateResponseBatch(BaseModel):
    decisions: List[BatchDecision]

def format_unit(unit):
    text = unit.get("text", "")
    if unit.get("is_reply"):
        text = f"[PARENT POST]\n{unit.get('parent_text', '')}\n\n[REPLY]\n{text}"
    return text

last_request_time = 0.0
RATE_LIMIT_DELAY = 3.5

async def wait_for_rate_limit():
    global last_request_time
    now = time.time()
    elapsed = now - last_request_time
    if elapsed < RATE_LIMIT_DELAY:
        await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)
    last_request_time = time.time()

async def process_single(client, model, prompt, unit):
    text = format_unit(unit)
    for attempt in range(10):
        try:
            await wait_for_rate_limit()
            response = await client.aio.models.generate_content(
                model=model,
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    temperature=0.0,
                    response_mime_type="application/json",
                    response_schema=GateResponseSingle,
                    http_options={'timeout': 15000}
                )
            )
            call_counter.log_success(model)
            return json.loads(response.text).get("relevant")
        except Exception as e:
            if "429" in str(e):
                print(f"429 Hit in single. Sleep 15s")
                await asyncio.sleep(15)
            elif "503" in str(e):
                print(f"503 Hit in single. Sleep 10s")
                await asyncio.sleep(10)
            else:
                print(f"Single error: {e}")
                await asyncio.sleep(5)
    return "error"

async def process_batch(client, model, prompt, batch_units):
    text_parts = []
    for i, u in enumerate(batch_units):
        text_parts.append(f"Unit {i+1}:\n{format_unit(u)}\n")
    full_text = "\n".join(text_parts)
    for attempt in range(10):
        try:
            await wait_for_rate_limit()
            response = await client.aio.models.generate_content(
                model=model,
                contents=full_text,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    temperature=0.0,
                    response_mime_type="application/json",
                    response_schema=GateResponseBatch,
                    http_options={'timeout': 15000}
                )
            )
            call_counter.log_success(model)
            return json.loads(response.text).get("decisions", [])
        except Exception as e:
            if "429" in str(e):
                print(f"429 Hit in batch. Sleep 15s")
                await asyncio.sleep(15)
            elif "503" in str(e):
                print(f"503 Hit in batch. Sleep 10s")
                await asyncio.sleep(10)
            else:
                print(f"Batch error: {e}")
                await asyncio.sleep(5)
    return []

async def main():
    with open("prompts/pass1_relevance_gate.md", "r", encoding="utf-8") as f:
        prompt = f.read()
    with open("config/models.json", "r", encoding="utf-8") as f:
        model = json.load(f)["pass1_gate"]["model"]
        
    client = genai.Client()
    units = []
    with open("data/archive/validation_sample.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            units.append(json.loads(line))
            
    print(f"Loaded {len(units)} units from validation sample.")
    print(f"Running 100 single calls on {model}...")
    single_results = {}
    for i, u in enumerate(units):
        res = await process_single(client, model, prompt, u)
        single_results[u["id"]] = res
        print(f"Single {i+1}/100: {res}")
        
    print("Running 4 batch calls...")
    batch_results = {}
    batches = [units[i:i + 25] for i in range(0, 100, 25)]
    for b in batches:
        decisions = await process_batch(client, model, prompt, b)
        for d in decisions:
            n = d.get("n", 0)
            if 1 <= n <= len(b):
                batch_results[b[n-1]["id"]] = d.get("decision")
                
    agreements = 0
    errors = 0
    disagreements = []
    for u in units:
        s = single_results.get(u["id"], "missing")
        b = batch_results.get(u["id"], "missing")
        if s == "error" or b == "error" or s == "missing" or b == "missing":
            errors += 1
            print(f"Error on {u['id'][:8]}: single={s}, batch={b}")
        elif s == b:
            agreements += 1
        else:
            disagreements.append(f"ID {u['id'][:8]}: single={s} vs batch={b} | {format_unit(u)[:100].replace(chr(10), ' ')}")
            
    valid_comparisons = len(units) - errors
    rate = agreements / valid_comparisons if valid_comparisons > 0 else 0
    
    out = []
    out.append(f"Batching Agreement: {rate:.2%} ({agreements}/{valid_comparisons})")
    out.append(f"Errors: {errors}")
    if disagreements:
        out.append("Disagreements:")
        for d in disagreements:
            out.append(f"  {d}")
            
    res_text = "\n".join(out)
    print("\n" + res_text)
    
    with open("agreement_output.txt", "w", encoding="utf-8") as f:
        f.write(res_text + "\n")
        
    print(f"\nRunning total calls: {call_counter.get_running_total()}")

if __name__ == "__main__":
    asyncio.run(main())
