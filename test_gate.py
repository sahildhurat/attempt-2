import asyncio
from google import genai
from pydantic import BaseModel
from typing import Literal

class GateResponse(BaseModel):
    relevant: Literal["yes", "partial", "no"]
    reason: str

async def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    client = genai.Client()
    response = await client.aio.models.generate_content(
        model="gemini-3.8-flash",
        contents="I can't find my old photo of my cat.",
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GateResponse,
        )
    )
    print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
