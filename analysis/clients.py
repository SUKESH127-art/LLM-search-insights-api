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

# BrightData SERP API configuration
BRIGHTDATA_API_URL = "https://api.brightdata.com/request"
BRIGHTDATA_API_HEADERS = {
    "Authorization": f"Bearer {brightdata_api_key}",
    "Content-Type": "application/json"
}

# Create a client for BrightData SERP API calls
serp_client = httpx.AsyncClient(
    headers=BRIGHTDATA_API_HEADERS,
    timeout=30.0
)

# Keep the old client for backward compatibility (can be removed later)
http_client = None
mcp_client = None
BRIGHTDATA_MCP_URL = None
BRIGHTDATA_MCP_TOOLS = None
web_unlocker_client = None
