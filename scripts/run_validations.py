import os
import json
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Literal, List
import time
import random

load_dotenv()

PHOTO_TOKENS = ["photo", "photos", "pic", "picture", "image", "album", "memories"]
RETRIEVAL_TOKENS = ["find", "search", "look for", "locate", "remember", "recall", "where is", "where are", "scroll", "can't see", "missing", "show me", "showing", "disappeared", "gone", "won't come up", "nothing comes up", "no results"]

def pre_filter_unit(unit):
    text = (unit.get("text", "") + " " + unit.get("context", "")).lower()
    has_photo = any(t in text for t in PHOTO_TOKENS)
    has_retrieval = any(t in text for t in RETRIEVAL_TOKENS)
    
    source = unit.get("source", "")
    if source in ["help_community", "stackexchange"]:
        return has_retrieval
    else:
        return has_photo and has_retrieval

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
        parent_text = unit.get("parent_text", "")
        text = f"[PARENT POST]\n{parent_text}\n\n[REPLY]\n{text}"
    return text

# Global rate limiter state
last_request_time = 0.0
RATE_LIMIT_DELAY = 60.0 / 18.0  # ~3.33 seconds between calls to hit 18 calls/min

async def wait_for_rate_limit():
    global last_request_time
    now = time.time()
    elapsed = now - last_request_time
    if elapsed < RATE_LIMIT_DELAY:
        await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)
    last_request_time = time.time()

async def process_single(client, model, prompt, unit):
    text = format_unit(unit)
    for attempt in range(3):
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
                )
            )
            parsed = json.loads(response.text)
            return parsed.get("relevant")
        except Exception as e:
            if attempt == 2: return "error"
            await asyncio.sleep(1)

async def process_batch(client, model, prompt, batch_units):
    text_parts = []
    for i, u in enumerate(batch_units):
        text_parts.append(f"Unit {i+1}:\n{format_unit(u)}\n")
    full_text = "\n".join(text_parts)
    for attempt in range(3):
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
                )
            )
            parsed = json.loads(response.text)
            return parsed.get("decisions", [])
        except Exception as e:
            if attempt == 2: return []
            await asyncio.sleep(1)

async def main():
    with open("prompts/pass1_relevance_gate.md", "r", encoding="utf-8") as f:
        prompt = f.read()
    with open("config/models.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        model = config["pass1_gate"]["model"]
        
    client = genai.Client()
    units = []
    with open("data/unified/units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            units.append(json.loads(line))
            
    print("--- 1. BATCHING AGREEMENT TEST ---")
    test_100 = units[:100]
    
    print("Running 100 single calls at 18 RPM...")
    single_results = {}
    for i, u in enumerate(test_100):
        res = await process_single(client, model, prompt, u)
        single_results[u["id"]] = res
        if (i+1) % 10 == 0: print(f"Single calls: {i+1}/100")
        
    print("Running 4 batch calls at 18 RPM...")
    batch_results = {}
    batches = [test_100[i:i + 25] for i in range(0, 100, 25)]
    for i, b in enumerate(batches):
        decisions = await process_batch(client, model, prompt, b)
        for d in decisions:
            n = d.get("n", 0)
            if 1 <= n <= len(b):
                batch_results[b[n-1]["id"]] = d.get("decision")
        print(f"Batch calls: {i+1}/4")
        
    agreements = 0
    disagreements = []
    for u in test_100:
        s = single_results.get(u["id"], "missing")
        b = batch_results.get(u["id"], "missing")
        if s == b:
            agreements += 1
        else:
            disagreements.append(f"ID {u['id'][:8]}: single={s} vs batch={b} | {format_unit(u)[:60].replace(chr(10), ' ')}")
            
    agreement_rate = agreements / 100
    print(f"Batching Agreement: {agreement_rate:.2%}")
    if disagreements:
        for d in disagreements: print("  Disagreement:", d)
        
    print("\n--- 2. PRE-FILTER RECALL TEST ---")
    rejected = [u for u in units if not pre_filter_unit(u)]
    random.seed(42)
    sample_200 = random.sample(rejected, min(200, len(rejected)))
    batches_200 = [sample_200[i:i + 25] for i in range(0, len(sample_200), 25)]
    print(f"Running 8 batch calls for 200 rejected units at 18 RPM...")
    
    yes_partial = 0
    for i, b in enumerate(batches_200):
        decisions = await process_batch(client, model, prompt, b)
        for d in decisions:
            if d.get("decision") in ["yes", "partial"]:
                yes_partial += 1
        print(f"Recall batches: {i+1}/{len(batches_200)}")
        
    fn_rate = yes_partial / 200
    print(f"False-negative rate: {yes_partial}/200 = {fn_rate:.2%}")

if __name__ == "__main__":
    asyncio.run(main())
