import os
import json
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel
from typing import Literal, List
import time
import random

load_dotenv()

PHOTO_TOKENS = ["photo", "photos", "pic", "picture", "image", "album", "memories"]
RETRIEVAL_TOKENS_NEW = ["find", "search", "look for", "locate", "remember", "recall", "where is", "where are", "scroll", "can't see", "missing", "show me", "showing", "disappeared", "gone", "won't come up", "nothing comes up", "no results"]

def pre_filter_unit_new(unit):
    text = (unit.get("text", "") + " " + unit.get("context", "")).lower()
    has_photo = any(t in text for t in PHOTO_TOKENS)
    has_retrieval = any(t in text for t in RETRIEVAL_TOKENS_NEW)
    source = unit.get("source", "")
    if source in ["help_community", "stackexchange"]:
        return has_retrieval
    return has_photo and has_retrieval

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

def log_success():
    import datetime, os
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = "data/daily_calls.json"
    counts = {}
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            counts = json.load(f)
    counts[today] = counts.get(today, 0) + 1
    with open(log_file, "w") as f:
        json.dump(counts, f)
        
async def process_batch(client, model, prompt, batch_units):
    text_parts = []
    for i, u in enumerate(batch_units):
        text_parts.append(f"Unit {i+1}:\n{format_unit(u)}\n")
    full_text = "\n".join(text_parts)
    for attempt in range(8):
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
            log_success()
            return json.loads(response.text).get("decisions", [])
        except APIError as e:
            print(f"429 Hit. Sleep 60s")
            await asyncio.sleep(60)
        except Exception as e:
            await asyncio.sleep(60)
    return []

async def main():
    with open("prompts/pass1_relevance_gate.md", "r", encoding="utf-8") as f:
        prompt = f.read()
    with open("config/models.json", "r", encoding="utf-8") as f:
        model = json.load(f)["pass1_gate"]["model"]
        
    client = genai.Client()
    units = []
    with open("data/unified/units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            units.append(json.loads(line))
            
    rejected_new = [u for u in units if not pre_filter_unit_new(u)]
    random.seed(42)
    sample_200 = random.sample(rejected_new, min(200, len(rejected_new)))
    
    # Get 10 known 'yes' units from gated_units.jsonl
    known_yes = []
    if os.path.exists("data/pass1/gated_units.jsonl"):
        with open("data/pass1/gated_units.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    u = json.loads(line)
                    if u.get("relevant") == "yes":
                        known_yes.append(u)
    
    injected_10 = random.sample(known_yes, min(10, len(known_yes)))
    injected_ids = {u["id"] for u in injected_10}
    
    test_set = sample_200 + injected_10
    random.shuffle(test_set)
    
    print("Running positive control recall test...")
    batches = [test_set[i:i+25] for i in range(0, len(test_set), 25)]
    
    dist = {"yes": 0, "partial": 0, "no": 0, "missing/error": 0}
    received_decisions = 0
    injected_results = []
    
    for i, b in enumerate(batches):
        decisions = await process_batch(client, model, prompt, b)
        dec_map = {d.get("n"): d.get("decision") for d in decisions}
        for n_idx, u in enumerate(b):
            n = n_idx + 1
            decision = dec_map.get(n)
            if decision in ["yes", "partial", "no"]:
                dist[decision] += 1
                received_decisions += 1
            else:
                dist["missing/error"] += 1
            
            if u["id"] in injected_ids:
                injected_results.append(f"Injected {u['id'][:8]}: {decision}")
                
        print(f"Batch {i+1}/{len(batches)} done.")
                
    with open("positive_control_results.txt", "w", encoding="utf-8") as f:
        f.write(f"Received decisions: {received_decisions}/{len(test_set)}\n")
        f.write(f"Distribution: {dist}\n")
        f.write("Injected unit results:\n")
        for res in injected_results:
            f.write(f"  {res}\n")
            
        f.write("\n10 Rejected Units (Raw Text):\n")
        for j, u in enumerate(sample_200[:10]):
            f.write(f"Unit {j+1}: {format_unit(u)}\n---\n")

if __name__ == "__main__":
    asyncio.run(main())
