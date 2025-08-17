import os
import httpx
from openai import AsyncOpenAI

# --- Environment Variable Check ---
# It's good practice to fail fast if essential configuration is missing.
openai_api_key = os.getenv("OPENAI_API_KEY")
brightdata_api_key = os.getenv("BRIGHTDATA_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")
if not brightdata_api_key:
    raise ValueError("BRIGHTDATA_API_KEY environment variable not set.")

# --- Client Initialization ---

# Initialize the OpenAI async client
# The library automatically handles authentication by reading the OPENAI_API_KEY env var.
openai_client = AsyncOpenAI()

# Initialize the HTTPX async client for BrightData
# We use a context manager (`async with`) when making calls, but we can define
# the base URL and headers for reuse here.
BRIGHTDATA_API_BASE_URL = "https://api.brightdata.com/serp/req"
brightdata_headers = {
    "Authorization": f"Bearer {brightdata_api_key}",
    "Content-Type": "application/json",
}

# You can also create a long-lived client instance if you need to manage
# connection pooling, timeouts, and other advanced configurations.
http_client = httpx.AsyncClient(
    headers=brightdata_headers,
    base_url=BRIGHTDATA_API_BASE_URL,
    timeout=30.0 # Set a default timeout for all requests
)
