# src/analysis/collector.py
import asyncio
import json
from datetime import datetime, timezone

from src.analysis.clients import openai_client, brightdata_client
from src.schemas import WebAnalysis, ChatGPTResponse

async def perform_web_analysis(question: str) -> WebAnalysis:
    """
    Performs real web analysis using the BrightData SERP API (via Direct Access)
    and OpenAI for summarization.
    """
    print(f"Performing SERP analysis for: '{question}'")
    
    try:
        # Step 1: Construct the target URL and payload as per documentation
        print("   🔍 Preparing BrightData Direct API request...")

        # The query is part of the URL. We must add '&brd_json=1' to get parsed JSON.
        target_url = f"https://www.google.com/search?q={question.replace(' ', '+')}&brd_json=1"

        # The payload for BrightData SERP API
        payload = {
            "zone": "serp_api1", 
            "url": target_url,
            "format": "json"
        }
        
        # Step 2: Make the API call using the correct client and endpoint
        print(f"   📤 Sending request to BrightData...")
        print(f"   📝 Payload: {payload}")
        
        # Try the correct BrightData SERP API endpoint
        try:
            response = await brightdata_client.post(url="/", json=payload)
        except Exception as api_error:
            print(f"   ❌ BrightData API call failed: {api_error}")
            # Fallback to a simpler approach
            payload = {
                "zone": "serp_api1",
                "query": question,
                "format": "json"
            }
            print(f"   🔄 Trying fallback payload: {payload}")
            response = await brightdata_client.post(url="/", json=payload)
        
        if response.status_code != 200:
            print(f"   ❌ BrightData API error: {response.status_code}")
            print(f"   📄 Error response: {response.text}")
            response.raise_for_status()
        
        search_results = response.json()
        print("   ✅ Received structured JSON response from BrightData.")
        
        # Step 3: Extract and combine the useful text snippets for the LLM
        snippets = []
        if isinstance(search_results, list):
            search_results = search_results[0]

        if search_results.get("organic"):
            for result in search_results["organic"][:10]:
                if result.get("title") and result.get("description"):
                    snippets.append(f"Title: {result['title']}\nSnippet: {result['description']}\n---")
        
        if not snippets:
            raise ValueError(f"SERP API did not return any organic results. Response preview: {str(search_results)[:500]}")

        serp_context = "\n".join(snippets)
        
        if len(serp_context) > 8000:
            serp_context = serp_context[:8000] + "... [truncated]"
        
        print(f"   📄 Extracted context for LLM. Length: {len(serp_context)} characters.")
        
        # Step 4: Use OpenAI to analyze the snippets
        print("   🤖 Analyzing SERP data with OpenAI...")
        
        analysis_prompt = f"""
        Based on the following Top 10 Google search result snippets for the query "{question}":
        
        {serp_context}
        
        Please provide a comprehensive analysis of these results. Summarize the key findings, identify the main brands or topics discussed, and conclude with the most relevant insights.
        """
        
        analysis_response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert research analyst. Provide clear, structured analysis based on the given search results."},
                {"role": "user", "content": analysis_prompt}
            ]
        )
        
        analysis_text = analysis_response.choices[0].message.content
        
        return WebAnalysis(
            source="BrightData SERP API + OpenAI",
            content=analysis_text,
            timestamp=datetime.now(timezone.utc),
            confidence_score=0.95
        )
        
    except Exception as e:
        print(f"   ❌ Error in web analysis: {e}")
        return WebAnalysis(
            source="Fallback Analysis",
            content=f"Unable to perform web analysis due to error: {e}",
            timestamp=datetime.now(timezone.utc),
            confidence_score=0.0
        )

async def simulate_chatgpt_response(question: str) -> ChatGPTResponse:
    """
    Gets a real response from OpenAI about the user's question.
    """
    print(f"Getting real OpenAI response for: '{question}'")
    
    try:
        # Use a completely different approach - direct question without complex prompting
        print(f"   🔍 Making main OpenAI call with question: {question}")
        print(f"   🔍 Using client with base_url: {openai_client.base_url}")
        
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant. Answer questions directly and clearly."
                },
                {"role": "user", "content": question}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        response_text = response.choices[0].message.content
        print(f"   ✅ OpenAI response received: {len(response_text)} characters")
        
        # Extract relevant entities from the response
        entity_extraction_prompt = f"""
        Extract the names of relevant companies, technologies, tools, or key entities mentioned in this text:
        
        {response_text}
        
        Return only a JSON array of entity names.
        """
        
        print(f"   🔍 Making entity extraction call with prompt: {entity_extraction_prompt[:100]}...")
        
        entity_response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts entity names from text. Return only JSON."},
                {"role": "user", "content": entity_extraction_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        entities_text = entity_response.choices[0].message.content
        try:
            entities_data = json.loads(entities_text)
            # Handle both list and dict formats from OpenAI JSON response
            identified_brands = entities_data.get('entities', entities_data) if isinstance(entities_data, dict) else entities_data
        except (json.JSONDecodeError, AttributeError):
            identified_brands = []
        
        print(f"   ✅ Entities extracted: {identified_brands}")
        
        return ChatGPTResponse(
            simulated_response=response_text,
            identified_brands=identified_brands
        )
        
    except Exception as e:
        print(f"   ❌ Error in OpenAI call: {e}")
        # Fallback to generic response
        print("   🔄 Falling back to generic response due to OpenAI error")
        
        fallback_response = ChatGPTResponse(
            simulated_response=f"I can provide information about '{question}', but I encountered an error accessing my knowledge base. For the most accurate and up-to-date information, I recommend consulting authoritative sources or conducting further research on this topic.",
            identified_brands=[]
        )
        return fallback_response
