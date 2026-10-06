import asyncio
from google import genai
from pydantic import BaseModel
from typing import Literal
import os, json
from dotenv import load_dotenv

class GateResponse(BaseModel):
    relevant: Literal['yes', 'partial', 'no']
    reason: str

async def main():
    load_dotenv()
    client = genai.Client()
    
    with open('data/unified/units.jsonl', 'r', encoding='utf-8') as f:
        unit = json.loads(f.readline())
        
    with open('prompts/pass1_relevance_gate.md', 'r', encoding='utf-8') as f:
        prompt = f.read()
        
    text = unit.get('text', '')
    if unit.get('is_reply'):
        text = f"[PARENT POST]\n{unit.get('parent_text', '')}\n\n[REPLY]\n{text}"
        
    print('Testing unit:', unit['id'])
    print('Text:', text[:200].replace('\n', ' '))
    
    response = await client.aio.models.generate_content(
        model='gemini-3.8-flash',
        contents=text,
        config=genai.types.GenerateContentConfig(
            system_instruction=prompt,
            temperature=0.0,
            response_mime_type='application/json',
            response_schema=GateResponse,
        )
    )
    print('\nModel output:')
    print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
