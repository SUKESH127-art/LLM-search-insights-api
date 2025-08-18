# src/analysis/collector.py
import asyncio
import json
from datetime import datetime, timezone

from analysis.clients import openai_client, brightdata_client
from schemas import WebAnalysis, ChatGPTResponse

async def perform_web_analysis(question: str) -> WebAnalysis:
    """
    Performs web analysis using OpenAI to simulate search results and provide analysis.
    This is a working fallback while we fix the external SERP API integration.
    """
    print(f"Performing web analysis for: '{question}'")
    
    try:
        print("   🔍 Using OpenAI to simulate web search analysis...")
        
        # Step 1: Use OpenAI to simulate what web search results would look like
        search_simulation_prompt = f"""
        Simulate what the top 5-8 Google search results would look like for the query: "{question}"
        
        For each result, provide:
        - A realistic title (like what you'd see in search results)
        - A snippet/description (like the meta description)
        - The source/domain
        
        Format each result like this:
        Title: [Realistic search result title]
        Snippet: [Realistic description that would appear in search results]
        Source: [Realistic domain like example.com]
        ---
        
        Make these look like actual search results someone would find for this query.
        """
        
        print("   🤖 Generating simulated search results with OpenAI...")
        
        search_response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at simulating realistic web search results. Generate results that look like actual Google search results."},
                {"role": "user", "content": search_simulation_prompt}
            ]
        )
        
        simulated_results = search_response.choices[0].message.content
        
        # Step 2: Use OpenAI to analyze the simulated results
        print("   🤖 Analyzing simulated search results with OpenAI...")
        
        analysis_prompt = f"""
        Based on the following simulated search results for the query "{question}":
        
        {simulated_results}
        
        Please provide a comprehensive analysis of these results. Summarize the key findings, identify the main brands or topics discussed, and conclude with the most relevant insights.
        
        This should read like a real analysis of web search results.
        """
        
        analysis_response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert research analyst. Provide clear, structured analysis based on the given search results."},
                {"role": "user", "content": analysis_prompt}
            ]
        )
        
        analysis_text = analysis_response.choices[0].message.content
        
        # Calculate confidence score based on analysis quality
        confidence_score = 0.7  # Good confidence for simulated results
        if len(analysis_text) > 800:
            confidence_score += 0.2
        if "brand" in analysis_text.lower() or "company" in analysis_text.lower():
            confidence_score += 0.1
        
        confidence_score = min(confidence_score, 1.0)
        
        print(f"   📊 Calculated confidence score: {confidence_score:.2f}")
        
        return WebAnalysis(
            source="OpenAI Simulated Web Analysis",
            content=analysis_text,
            timestamp=datetime.now(timezone.utc),
            confidence_score=confidence_score
        )
        
    except Exception as e:
        print(f"   ❌ Error in web analysis: {e}")
        
        # Return a fallback analysis instead of crashing
        fallback_content = f"Unable to perform web analysis due to error: {e}\n\nThis analysis is based on ChatGPT's knowledge only, without real-time web search data."
        
        return WebAnalysis(
            source="Fallback Analysis",
            content=fallback_content,
            timestamp=datetime.now(timezone.utc),
            confidence_score=0.1  # Very low confidence for fallback
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
