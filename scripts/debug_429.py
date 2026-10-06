import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

load_dotenv()

async def main():
    client = genai.Client()
    try:
        response = await client.aio.models.generate_content(
            model='gemini-3.8-flash',
            contents='test'
        )
        print("Success, no 429")
    except APIError as e:
        print("APIError details type:", type(e.details))
        print("APIError details repr:", repr(e.details))
        if isinstance(e.details, list):
            for d in e.details:
                print("  item type:", type(d))
                print("  item repr:", repr(d))
    except Exception as e:
        print("Other error:", e)

if __name__ == "__main__":
    asyncio.run(main())
