# analysis/clients.py
import os
import httpx
from openai import AsyncOpenAI
from typing import Optional

def get_required_api_key(key_name: str, env_var: str) -> str:
    """Get a required API key from environment variables."""
    api_key = os.getenv(env_var)
    if not api_key:
        raise ValueError(
            f"Missing required API key: {key_name}\n"
            f"Please set the {env_var} environment variable.\n"
            f"You can do this by:\n"
            f"1. Creating a .env file with {env_var}=your_api_key_here\n"
            f"2. Setting it in your shell: export {env_var}=your_api_key_here\n"
            f"3. Setting it in your deployment environment"
        )
    return api_key

# Get required API keys - will raise ValueError if missing
try:
    openai_api_key = get_required_api_key("OpenAI", "OPENAI_API_KEY")
    brightdata_api_key = get_required_api_key("Bright Data", "BRIGHTDATA_API_KEY")
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    print("💡 Please set your API keys before running the application.")
    raise

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=openai_api_key,
    base_url="https://api.openai.com/v1"
)

# Initialize Bright Data client
BRIGHTDATA_API_URL = "https://api.brightdata.com"
brightdata_headers = {
    "Authorization": f"Bearer {brightdata_api_key}",
    "Content-Type": "application/json",
}

brightdata_client = httpx.AsyncClient(
    base_url=BRIGHTDATA_API_URL,
    headers=brightdata_headers,
    timeout=60.0,
)
