import json
import asyncio
import os
import sys
import random
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "collectors"))
import network_utils

load_dotenv()

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
        
    return [{
        "name": "record_extraction",
        "description": "Record the qualitative extraction for the unit",
        "input_schema": {
            "type": "object",
            "properties": base_properties,
            "required": req
        }
    }]

def format_unit(unit):
    text = unit.get("text", "")
    if unit.get("is_reply"):
        parent_text = unit.get("parent_text", "")
        text = f"[PARENT POST]\n{parent_text}\n\n[REPLY]\n{text}"
    return text

async def process_single(session, model, prompt, unit, sem):
    async with sem:
        text = format_unit(unit)
        completeness = unit.get("text_completeness", "snippet")
        tools = get_tools(completeness)
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": os.environ.get("ANTHROPIC_API_KEY"),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": model,
            "max_tokens": 1500,
            "system": prompt,
            "messages": [{"role": "user", "content": text}],
            "tools": tools,
            "tool_choice": {"type": "tool", "name": "record_extraction"}
        }
        
        for attempt in range(8):
            try:
                response = await asyncio.to_thread(
                    network_utils.fetch_with_rate_limit,
                    session, "POST", url, "extract_pilot", 
                    json=payload, headers=headers
                )
                data = response.json()
                
                # Check actual token usage cost
                usage = data.get("usage", {})
                in_toks = usage.get("input_tokens", 0)
                out_toks = usage.get("output_tokens", 0)
                # claude-3-5-sonnet-20241022 costs: $3.00 / 1M input, $15.00 / 1M output
                cost = (in_toks / 1000000.0) * 3.00 + (out_toks / 1000000.0) * 15.00
                
                for block in data.get("content", []):
                    if block.get("type") == "tool_use" and block.get("name") == "record_extraction":
                        ext = block.get("input", {})
                        
                        # Grounding check
                        dropped_cues = []
                        valid_remembered = []
                        valid_forgotten = []
                        
                        text_lower = text.lower()
                        
                        for c in ext.get("remembered", []):
                            span = c.get("span", "")
                            if span and span.lower() in text_lower:
                                valid_remembered.append(c)
                            else:
                                c["original_field"] = "remembered"
                                dropped_cues.append(c)
                                
                        for c in ext.get("forgotten", []):
                            span = c.get("span", "")
                            if span and span.lower() in text_lower:
                                valid_forgotten.append(c)
                            else:
                                c["original_field"] = "forgotten"
                                dropped_cues.append(c)
                                
                        ext["remembered"] = valid_remembered
                        ext["forgotten"] = valid_forgotten
                        ext["dropped_cues"] = dropped_cues
                        ext["extraction_model"] = model
                        
                        unit["extraction"] = ext
                        return unit, cost
                
                raise Exception("No tool use returned")
            except Exception as e:
                # If error is 400 Bad Request, could be model name issue
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Error on unit {unit.get('id')}: {e.response.status_code} - {e.response.text}")
                else:
                    import traceback
                    print(f"Error on unit {unit.get('id')}: {e}")
                    traceback.print_exc()
                await asyncio.sleep(2)
                
        print(f"Failed to process unit {unit.get('id')}")
        return unit, 0.0

async def main():
    with open("prompts/pass2_extraction.md", "r", encoding="utf-8") as f:
        prompt = f.read()
        
    with open("config/models.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        model = config["pass2_extraction"]["model"]
        
    # Draw pilot units
    units = []
    with open("data/gate_results.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                units.append(json.loads(line))
                
    candidates_reddit = [u for u in units if u["source"] == "reddit_assisted" and u.get("gate_decision") == "yes" and len(format_unit(u)) >= 250]
    candidates_help = [u for u in units if u["source"] == "help_community" and u.get("gate_decision") == "yes" and len(format_unit(u)) >= 250]
    
    # Sort for stable seed
    candidates_reddit.sort(key=lambda x: x["id"])
    candidates_help.sort(key=lambda x: x["id"])
    
    random.seed(42)
    sample_reddit = random.sample(candidates_reddit, min(15, len(candidates_reddit)))
    sample_help = random.sample(candidates_help, min(15, len(candidates_help)))
    
    pilot_units = sample_reddit + sample_help
    print(f"Pilot sample: {len(sample_reddit)} reddit, {len(sample_help)} help community.")
    
    session = network_utils.get_session()
    sem = asyncio.Semaphore(5)
    
    tasks = [asyncio.create_task(process_single(session, model, prompt, u, sem)) for u in pilot_units]
    
    total_cost = 0.0
    extracted_units = []
    
    for completed_task in asyncio.as_completed(tasks):
        u, cost = await completed_task
        total_cost += cost
        extracted_units.append(u)
        
    # Calculate grounding metrics
    metrics = {
        "remembered": {"returned": 0, "grounded": 0, "dropped": 0},
        "forgotten": {"returned": 0, "grounded": 0, "dropped": 0}
    }
    
    for u in extracted_units:
        ext = u.get("extraction", {})
        metrics["remembered"]["grounded"] += len(ext.get("remembered", []))
        metrics["forgotten"]["grounded"] += len(ext.get("forgotten", []))
        
        for dropped in ext.get("dropped_cues", []):
            fld = dropped.get("original_field")
            if fld in metrics:
                metrics[fld]["dropped"] += 1
                
    for fld in metrics:
        metrics[fld]["returned"] = metrics[fld]["grounded"] + metrics[fld]["dropped"]
        total = metrics[fld]["returned"]
        metrics[fld]["drop_rate"] = (metrics[fld]["dropped"] / total * 100) if total > 0 else 0
        
    os.makedirs("data/pass2", exist_ok=True)
    with open("data/pass2/pilot_results.jsonl", "w", encoding="utf-8") as f:
        for u in extracted_units:
            f.write(json.dumps(u) + "\n")
            
    with open("data/pass2/summary.json", "w", encoding="utf-8") as f:
        json.dump({"metrics": metrics, "cost": total_cost, "units": len(extracted_units)}, f, indent=2)
        
    print("\n=== PILOT GROUNDING TABLE ===")
    for fld in metrics:
        m = metrics[fld]
        print(f"{fld.upper()}: Returned {m['returned']} | Grounded {m['grounded']} | Dropped {m['dropped']} ({m['drop_rate']:.1f}%)")
        
    print(f"\nTotal Cost: ${total_cost:.4f}")
    if len(extracted_units) > 0:
        print(f"Cost per unit: ${total_cost / len(extracted_units):.4f}")
        
    print("\n=== THREE VERBATIM EXTRACTIONS ===")
    for i in range(min(3, len(extracted_units))):
        print(f"\n--- Unit {extracted_units[i]['id']} ---")
        print(json.dumps(extracted_units[i].get("extraction", {}), indent=2))
        
    max_drop = max(metrics["remembered"]["drop_rate"], metrics["forgotten"]["drop_rate"])
    print(f"\nMax drop rate: {max_drop:.1f}%")
    
    if max_drop > 10.0:
        print("STOP CONDITION MET: Drop rate > 10%. Please review extraction prompt.")
        print(prompt)
    elif max_drop >= 5.0:
        print("STOP CONDITION MET: Drop rate 5-10%. Waiting for decision.")
    else:
        print("Drop rate < 5%. Pilot successful. Continue automatically to step 2.")

if __name__ == "__main__":
    asyncio.run(main())
