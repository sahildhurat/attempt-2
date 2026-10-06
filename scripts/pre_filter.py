import json
import random
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Literal, List

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

async def process_batch(client, model, prompt, batch_units, sem):
    async with sem:
        text_parts = []
        for i, u in enumerate(batch_units):
            text_parts.append(f"Unit {i+1}:\n{format_unit(u)}\n")
        full_text = "\n".join(text_parts)
        for attempt in range(8):
            try:
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
                print(f"429 sleep {60}...")
                await asyncio.sleep(60)
        return []

async def main():
    units = []
    with open("data/unified/units.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            units.append(json.loads(line))
            
    rejected_units = []
    accepted_units = []
    source_loss = {}
    
    for u in units:
        src = u.get("source", "unknown")
        if src not in source_loss:
            source_loss[src] = {"total": 0, "lost": 0}
            
        source_loss[src]["total"] += 1
        if pre_filter_unit(u):
            accepted_units.append(u)
        else:
            rejected_units.append(u)
            source_loss[src]["lost"] += 1
            
    random.seed(42)
    sample = random.sample(rejected_units, min(200, len(rejected_units)))
    
    with open("prompts/pass1_relevance_gate.md", "r", encoding="utf-8") as f:
        prompt = f.read()
        
    with open("config/models.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        model = config["pass1_gate"]["model"]
        
    client = genai.Client()
    sem = asyncio.Semaphore(1)  # ONE AT A TIME!
    
    batches = [sample[i:i + 25] for i in range(0, len(sample), 25)]
    tasks = [asyncio.create_task(process_batch(client, model, prompt, b, sem)) for b in batches]
    
    yes_partial = 0
    total = len(sample)
    
    for completed_task in asyncio.as_completed(tasks):
        decisions = await completed_task
        for d in decisions:
            if d.get("decision") in ["yes", "partial"]:
                yes_partial += 1
                
    fn_rate = yes_partial / total
    
    result_text = f"""
--- Pre-Filter Loss by Source ---
"""
    for src, counts in source_loss.items():
        result_text += f"{src}: {counts['lost']}/{counts['total']} lost ({(counts['lost']/counts['total']):.2%})\n"
        
    result_text += f"\nTotal accepted: {len(accepted_units)}, Total rejected: {len(rejected_units)}\n"
    result_text += f"\nFalse-negative rate: {yes_partial}/{total} = {fn_rate:.2%}"
    if fn_rate > 0.02:
        result_text += "\nWARNING: False-negative rate exceeds 2%!"
        
    print(result_text)
    
    with open("docs/prefilter_results.txt", "w", encoding="utf-8") as f:
        f.write(result_text)

if __name__ == "__main__":
    asyncio.run(main())
