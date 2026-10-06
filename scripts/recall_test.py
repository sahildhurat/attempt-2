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
RETRIEVAL_TOKENS = ["find", "search", "look for", "locate", "remember", "recall", "where is", "where are", "scroll", "can't see", "missing"]

def pre_filter_unit_old(unit):
    text = (unit.get("text", "") + " " + unit.get("context", "")).lower()
    has_photo = any(t in text for t in PHOTO_TOKENS)
    has_retrieval = any(t in text for t in RETRIEVAL_TOKENS)
    return has_photo and has_retrieval

def pre_filter_unit_new(unit):
    RETRIEVAL_TOKENS_NEW = RETRIEVAL_TOKENS + ["show me", "showing", "disappeared", "gone", "won't come up", "nothing comes up", "no results"]
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

async def process_batch(client, model, prompt, batch_units):
    text_parts = []
    for i, u in enumerate(batch_units):
        text_parts.append(f"Unit {i+1}:\n{format_unit(u)}\n")
    full_text = "\n".join(text_parts)
    for attempt in range(3):
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
            if attempt == 2: return []
            await asyncio.sleep(1)

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
            
    rejected_old = [u for u in units if not pre_filter_unit_old(u)]
    random.seed(42)
    sample_200 = random.sample(rejected_old, min(200, len(rejected_old)))
    
    print("Running OLD recall test...")
    batches_200 = [sample_200[i:i+25] for i in range(0, len(sample_200), 25)]
    yes_partial_old = 0
    for i, b in enumerate(batches_200):
        decisions = await process_batch(client, model, prompt, b)
        for d in decisions:
            if d.get("decision") in ["yes", "partial"]:
                yes_partial_old += 1
        await asyncio.sleep(3.5)
        
    old_rate = yes_partial_old / len(sample_200)
    print(f"Old False-negative rate: {yes_partial_old}/{len(sample_200)} = {old_rate:.2%}")
    
    if old_rate > 0.02:
        print("Loss exceeds 2%, running NEW recall test...")
        rejected_new = [u for u in units if not pre_filter_unit_new(u)]
        random.seed(42)
        sample_200_new = random.sample(rejected_new, min(200, len(rejected_new)))
        batches_200_new = [sample_200_new[i:i+25] for i in range(0, len(sample_200_new), 25)]
        yes_partial_new = 0
        for i, b in enumerate(batches_200_new):
            decisions = await process_batch(client, model, prompt, b)
            for d in decisions:
                if d.get("decision") in ["yes", "partial"]:
                    yes_partial_new += 1
            await asyncio.sleep(3.5)
        new_rate = yes_partial_new / len(sample_200_new)
        print(f"New False-negative rate: {yes_partial_new}/{len(sample_200_new)} = {new_rate:.2%}")

if __name__ == "__main__":
    asyncio.run(main())
