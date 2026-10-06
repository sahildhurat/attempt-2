import os
import json
import asyncio
import sys
import random
import time
import requests
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "collectors"))
import network_utils

load_dotenv()
session = network_utils.get_session()

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

def format_unit(unit):
    text = unit.get("text", "")
    if unit.get("is_reply"):
        parent_text = unit.get("parent_text", "")
        text = f"[PARENT POST]\n{parent_text}\n\n[REPLY]\n{text}"
    return text

def get_tools(completeness):
    base_properties = {
        "evidence_quote": {"type": "string", "description": "A single exact quote from the text supporting this extraction. Do not omit."},
        "target": {"type": "string", "description": "A concise description of the photos they were trying to find"},
        "remembered": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "span": {"type": "string", "description": "exact verbatim substring of the source text supporting this cue, max 20 words"},
                    "cue": {"type": "string", "description": "short phrase describing what they remembered"}
                },
                "required": ["span", "cue"]
            }
        },
        "forgotten": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "span": {"type": "string", "description": "exact verbatim substring of the source text supporting this cue, max 20 words"},
                    "cue": {"type": "string", "description": "short phrase describing what they could not remember"}
                },
                "required": ["span", "cue"]
            }
        }
    }
    
    req = ["evidence_quote", "target", "remembered", "forgotten"]
    
    if completeness == "full":
        base_properties["breakdown_quote"] = {"type": "string", "description": "Quote supporting the breakdown reason"}
        base_properties["breakdown"] = {"type": "string", "description": "The reason the search failed, if stated"}
        base_properties["workaround_quote"] = {"type": "string", "description": "Quote supporting the workaround"}
        base_properties["workaround"] = {"type": "string", "description": "Any alternative method they used to find the photo when search failed"}
        req.extend(["breakdown_quote", "breakdown", "workaround_quote", "workaround"])
        
    return {
        "name": "record_extraction",
        "description": "Record the qualitative extraction for the unit",
        "input_schema": {
            "type": "object",
            "properties": base_properties,
            "required": req
        }
    }

async def call_anthropic(model, prompt, text, completeness):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    tool_def = get_tools(completeness)
    payload = {
        "model": model,
        "max_tokens": 1500,
        "system": prompt,
        "messages": [{"role": "user", "content": text}],
        "tools": [tool_def],
        "tool_choice": {"type": "tool", "name": "record_extraction"}
    }
    
    for attempt in range(5):
        try:
            response = await asyncio.to_thread(
                network_utils.fetch_with_rate_limit,
                session, "POST", url, "anthropic", 
                json=payload, headers=headers
            )
            data = response.json()
            
            usage = data.get("usage", {})
            in_toks = usage.get("input_tokens", 0)
            out_toks = usage.get("output_tokens", 0)
            cost = (in_toks / 1000000.0) * 3.00 + (out_toks / 1000000.0) * 15.00
            
            for block in data.get("content", []):
                if block.get("type") == "tool_use" and block.get("name") == "record_extraction":
                    return block.get("input", {}), cost
            raise Exception("No tool use returned")
        except Exception as e:
            await asyncio.sleep(2)
            
    return None, 0.0

async def call_gemini(model, prompt, text, completeness):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    tool_def = get_tools(completeness)
    gemini_tools = [{
        "functionDeclarations": [{
            "name": tool_def["name"],
            "description": tool_def["description"],
            "parameters": tool_def["input_schema"]
        }]
    }]
    
    payload = {
        "systemInstruction": {
            "parts": [{"text": prompt}]
        },
        "contents": [{
            "parts": [{"text": text}],
            "role": "user"
        }],
        "tools": gemini_tools,
        "toolConfig": {
            "functionCallingConfig": {
                "mode": "ANY",
                "allowedFunctionNames": ["record_extraction"]
            }
        },
        "generationConfig": {
            "temperature": 0.0
        }
    }
    
    for attempt in range(5):
        try:
            response = await asyncio.to_thread(
                network_utils.fetch_with_rate_limit,
                session, "POST", url, "gemini", 
                json=payload
            )
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise Exception("No candidates returned")
                
            parts = candidates[0].get("content", {}).get("parts", [])
            for p in parts:
                if "functionCall" in p and p["functionCall"]["name"] == "record_extraction":
                    args = p["functionCall"].get("args", {})
                    return args, 0.0
            raise Exception("No function call returned")
        except Exception as e:
            if hasattr(e, "response") and e.response is not None and e.response.status_code == 429:
                await asyncio.sleep(5)
            elif hasattr(e, "response") and e.response is not None:
                print("Gemini API error:", e.response.text)
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(2)
            
    return None, 0.0

def process_grounding(ext, text, model_name):
    dropped_cues = []
    valid_remembered = []
    valid_forgotten = []
    
    text_lower = text.lower()
    
    for c in ext.get("remembered", []):
        if not isinstance(c, dict): continue
        span = c.get("span", "")
        if span and span.lower() in text_lower:
            valid_remembered.append(c)
        else:
            c["original_field"] = "remembered"
            dropped_cues.append(c)
            
    for c in ext.get("forgotten", []):
        if not isinstance(c, dict): continue
        span = c.get("span", "")
        if span and span.lower() in text_lower:
            valid_forgotten.append(c)
        else:
            c["original_field"] = "forgotten"
            dropped_cues.append(c)
            
    ext["remembered"] = valid_remembered
    ext["forgotten"] = valid_forgotten
    ext["dropped_cues"] = dropped_cues
    ext["extraction_model"] = model_name
    return ext

async def process_unit(u, model_name, is_gemini, prompt, sem, result_list, state):
    async with sem:
        if state["gemini_failed"]:
            return
            
        text = format_unit(u)
        completeness = u.get("text_completeness", "snippet")
        
        if not is_gemini:
            ext, cost = await call_anthropic(model_name, prompt, text, completeness)
            state["cost"] += cost
        else:
            ext, cost = await call_gemini(model_name, prompt, text, completeness)
            
        if ext is None:
            if is_gemini:
                state["gemini_failed"] = True
                print("Gemini failed cleanly. Stopping extraction.")
            else:
                print(f"Failed to extract unit {u['id']} with Anthropic.")
            return
            
        ext = process_grounding(ext, text, model_name)
        u["extraction"] = ext
        result_list.append(u)

async def main():
    with open("prompts/pass2_extraction.md", "r", encoding="utf-8") as f:
        prompt = f.read()
        
    with open("config/models.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        anthropic_model = config["pass2_extraction"]["model"]
        
    gemini_model = "gemini-3.6-flash"
    
    units = []
    with open("data/pass2/target_list.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                units.append(json.loads(line))
                
    budget_limit = 8.16
    state = {"cost": 0.0, "gemini_failed": False}
    
    extracted_units = []
    if os.path.exists("data/pass2/extracted_units.jsonl"):
        with open("data/pass2/extracted_units.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    extracted_units.append(json.loads(line))
        state["cost"] = len([u for u in extracted_units if u.get("extraction", {}).get("extraction_model") == anthropic_model]) * 0.0113
        print(f"Resuming with {len(extracted_units)} existing units. Estimated cost spent: ${state['cost']:.4f}")

    extracted_ids = {u["id"] for u in extracted_units}
    units = [u for u in units if u["id"] not in extracted_ids]
    
    print(f"Starting extraction for {len(units)} remaining units. Budget limit: ${budget_limit:.2f}")
    
    sem = asyncio.Semaphore(10)
    
    idx = 0
    while idx < len(units):
        chunk = units[idx:idx+20]
        idx += 20
        
        if state["cost"] >= budget_limit:
            break
            
        tasks = [asyncio.create_task(process_unit(u, anthropic_model, False, prompt, sem, extracted_units, state)) for u in chunk]
        await asyncio.gather(*tasks)
        
        print(f"Processed {len(extracted_units)} units. Current Cost: ${state['cost']:.4f}")
        with open("data/pass2/extracted_units.jsonl", "w", encoding="utf-8") as f:
            for eu in extracted_units:
                f.write(json.dumps(eu) + "\n")
                
    if state["cost"] >= budget_limit and idx < len(units):
        print(f"\n--- BUDGET EXHAUSTED --- ($ {state['cost']:.4f})")
        print("Running 20-UNIT OVERLAP with Gemini...")
        
        overlap_units = [x for x in extracted_units if x.get("extraction", {}).get("extraction_model") == anthropic_model][-20:]
        
        async def run_overlap(ou):
            otext = format_unit(ou)
            ocomp = ou.get("text_completeness", "snippet")
            g_ext, _ = await call_gemini(gemini_model, prompt, otext, ocomp)
            if g_ext:
                g_ext = process_grounding(g_ext, otext, gemini_model)
                ou["gemini_overlap_extraction"] = g_ext
                
        await asyncio.gather(*(run_overlap(ou) for ou in overlap_units))
        print("Overlap complete. Switching to Gemini for remaining units.")
        
        gemini_idx = idx
        while gemini_idx < len(units):
            chunk = units[gemini_idx:gemini_idx+20]
            gemini_idx += 20
            
            tasks = [asyncio.create_task(process_unit(u, gemini_model, True, prompt, sem, extracted_units, state)) for u in chunk]
            await asyncio.gather(*tasks)
            
            if state["gemini_failed"]:
                break
                
            print(f"Processed {len(extracted_units)} units (Gemini).")
            with open("data/pass2/extracted_units.jsonl", "w", encoding="utf-8") as f:
                for eu in extracted_units:
                    f.write(json.dumps(eu) + "\n")
                    
    with open("data/pass2/extracted_units.jsonl", "w", encoding="utf-8") as f:
        for eu in extracted_units:
            f.write(json.dumps(eu) + "\n")
            
    print("\n=== COMPLETE ===")
    print(f"Extracted {len(extracted_units)} units.")
    print(f"Total Anthropic Spend: ${state['cost']:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
