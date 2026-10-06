import os
import json
import asyncio
import sys
from dotenv import load_dotenv
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), "collectors"))
import network_utils
import pass2_checks
import call_counter

load_dotenv()

session = network_utils.get_session()

tools_extract = [
    {
        "name": "record_extraction",
        "description": "Record the qualitative extraction for the unit",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "A concise description of the photos they were trying to find"},
                "evidence_quote": {"type": "string", "description": "A single exact quote from the text supporting this extraction"},
                "remembered": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "cue": {"type": "string", "description": "short phrase describing what they remembered"},
                            "span": {"type": "string", "description": "exact verbatim substring of the source text supporting this cue"}
                        },
                        "required": ["cue", "span"]
                    }
                },
                "forgotten": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "cue": {"type": "string", "description": "short phrase describing what they could not remember"},
                            "span": {"type": "string", "description": "exact verbatim substring of the source text supporting this cue"}
                        },
                        "required": ["cue", "span"]
                    }
                },
                "workaround": {"type": "string", "description": "Any alternative method they used to find the photo when search failed"},
                "breakdown": {"type": "string", "description": "The reason the search failed, if stated"}
            },
            "required": ["target", "evidence_quote", "remembered", "forgotten", "workaround", "breakdown"]
        }
    }
]

def format_unit(unit):
    text = unit.get("text", "")
    if unit.get("is_reply"):
        parent_text = unit.get("parent_text", "")
        text = f"[PARENT POST]\n{parent_text}\n\n[REPLY]\n{text}"
    return text

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
            "max_tokens": 2048,
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
            "tools": tools_extract,
            "tool_choice": {"type": "tool", "name": "record_extraction"},
            "temperature": 0.0
        }
        
        for attempt in range(8):
            try:
                response = await asyncio.to_thread(
                    network_utils.fetch_with_rate_limit,
                    session, "POST", url, "extract_single", 
                    json=payload, headers=headers
                )
                data = response.json()
                for block in data.get("content", []):
                    if block.get("type") == "tool_use" and block.get("name") == "record_extraction":
                        data_input = block.get("input", {})
                        for k, v in data_input.items():
                            unit[k] = v
                        call_counter.log_success(model)
                        return unit
                
                raise Exception("No tool use returned")
            except Exception as e:
                print(f"Error on unit {unit.get('id')}: {e}")
                await asyncio.sleep(2)
                
        print(f"Failed to process unit {unit.get('id')}")
        return unit

async def main():
    with open("prompts/pass2_extraction.md", "r", encoding="utf-8") as f:
        prompt = f.read()
        
    with open("config/models.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        model = config["pass2_extraction"]["model"]
        
    sem = asyncio.Semaphore(5)
    
    units = []
    input_file = "data/pass1/relevant_units.jsonl"
    if not os.path.exists(input_file):
        print(f"{input_file} not found. Ensure pass1_gate has been run.")
        return
        
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                units.append(json.loads(line))
                
    print(f"Processing {len(units)} units for pass 2 extraction...")
    
    tasks = [asyncio.create_task(process_single(model, prompt, u, sem)) for u in units]
    extracted_units = []
    
    for idx, completed_task in enumerate(asyncio.as_completed(tasks)):
        u = await completed_task
        extracted_units.append(u)
        if (idx + 1) % 10 == 0:
            print(f"Extracted {idx+1}/{len(units)} units...")
            
    print("Running Pass 2 Checks...")
    extracted_units = pass2_checks.run_checks(extracted_units)
    
    os.makedirs("data/pass2", exist_ok=True)
    with open("data/pass2/extracted_units.jsonl", "w", encoding="utf-8") as f:
        for u in extracted_units:
            f.write(json.dumps(u) + "\n")
            
    print("Pass 2 Extraction Finished. Saved to data/pass2/extracted_units.jsonl")

if __name__ == "__main__":
    asyncio.run(main())
