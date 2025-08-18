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

# Initialize the OpenAI async client, EXPLICITLY setting the base_url.
# This overrides any environment variables like OPENAI_BASE_URL and forces
# the client to talk directly to the official OpenAI API, bypassing any proxies.
openai_client = AsyncOpenAI(
    base_url="https://api.openai.com/v1"
)

# BrightData API configuration (Corrected)
BRIGHTDATA_API_URL = "https://api.brightdata.com/request"  # <-- CORRECTED ENDPOINT
brightdata_headers = {
    "Authorization": f"Bearer {brightdata_api_key}",
    "Content-Type": "application/json",
}

# Create a general-purpose client for BrightData API calls
brightdata_client = httpx.AsyncClient(
    base_url=BRIGHTDATA_API_URL,  # <-- CORRECTED BASE URL
    headers=brightdata_headers,
    timeout=60.0,  # Increased timeout slightly for potentially long scrapes
)

# Clean up old/unused client variables
serp_client = None 
http_client = None
mcp_client = None
BRIGHTDATA_MCP_URL = None
BRIGHTDATA_MCP_TOOLS = None
web_unlocker_client = None
