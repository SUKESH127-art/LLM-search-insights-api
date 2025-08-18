# analysis/clients.py
import os
import httpx
from openai import AsyncOpenAI

openai_api_key = os.getenv("OPENAI_API_KEY")
brightdata_api_key = os.getenv("BRIGHTDATA_API_KEY")

if not openai_api_key:
    print("Warning: OPENAI_API_KEY environment variable not set.")
    openai_api_key = "dummy_key"
if not brightdata_api_key:
    print("Warning: BRIGHTDATA_API_KEY environment variable not set.")
    brightdata_api_key = "dummy_key"

openai_client = AsyncOpenAI(
    api_key=openai_api_key,
    base_url="https://api.openai.com/v1"
)

BRIGHTDATA_API_URL = "https://api.brightdata.com/request"
brightdata_headers = {
    "Authorization": f"Bearer {brightdata_api_key}",
    "Content-Type": "application/json",
}

brightdata_client = httpx.AsyncClient(
    base_url=BRIGHTDATA_API_URL,
    headers=brightdata_headers,
    timeout=60.0,
)
