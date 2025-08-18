# src/analysis/collector.py
import asyncio
import json
from datetime import datetime, timezone

from analysis.clients import openai_client, brightdata_client
from schemas import WebAnalysis, ChatGPTResponse

def calculate_web_analysis_confidence(
    search_results: dict,
    serp_context: str,
    analysis_text: str,
    api_response_quality: dict
) -> float:
    """
    Calculate a sophisticated confidence score for web analysis based on multiple factors.
    
    The confidence score is calculated using a weighted approach that considers:
    1. **Data Quality (40%)**: How complete and relevant the SERP results are
    2. **Content Richness (30%)**: The depth and structure of the generated analysis
    3. **API Reliability (20%)**: How well the external APIs performed
    4. **Processing Success (10%)**: Whether all steps completed without errors
    
    Scoring breakdown:
    - 0.0-0.3: Poor quality (insufficient data, API failures, minimal analysis)
    - 0.4-0.6: Fair quality (some data, basic analysis, minor issues)
    - 0.7-0.8: Good quality (adequate data, structured analysis, few issues)
    - 0.9-1.0: Excellent quality (rich data, comprehensive analysis, no issues)
    
    Args:
        search_results: Raw response from BrightData SERP API
        serp_context: Processed text context sent to LLM
        analysis_text: Generated analysis from OpenAI
        api_response_quality: Dict with API performance metrics
    
    Returns:
        float: Confidence score between 0.0 and 1.0
    """
    
    # SIMPLE TEST CASE - Let's see what's happening
    print(f"\n🔍 SIMPLE TEST: Let's debug this confidence calculation!")
    print(f"🔍 Input lengths - SERP: {len(serp_context)}, Analysis: {len(analysis_text)}")
    
    # Factor 1: Data Quality (40% weight) - How good are the SERP results?
    data_quality_score = 0.0
    
    # Check if we have organic search results
    if search_results.get("organic"):
        organic_count = len(search_results["organic"])
        # More results = higher confidence (up to 10 results)
        organic_score = min(organic_count / 10.0, 1.0)
        
        # Check result completeness (title + description)
        complete_results = 0
        for result in search_results["organic"]:
            if result.get("title") and result.get("description"):
                complete_results += 1
        
        completeness_score = complete_results / max(organic_count, 1)
        
        # Check content length (longer descriptions = more detail)
        total_content_length = sum(
            len(str(result.get("description", ""))) 
            for result in search_results["organic"]
        )
        content_length_score = min(total_content_length / 5000.0, 1.0)  # Normalize to 5000 chars
        
        data_quality_score = (organic_score * 0.4 + completeness_score * 0.4 + content_length_score * 0.2)
        
        print(f"🔍 Data Quality: {organic_count} results, {complete_results} complete, {total_content_length} chars → Score: {data_quality_score:.3f}")
    else:
        print(f"🔍 Data Quality: No organic results → Score: 0.000")
    
    # Factor 2: Content Richness (30% weight) - How good is the generated analysis?
    content_richness_score = 0.0
    
    if analysis_text:
        # Length analysis (longer analysis = more comprehensive)
        analysis_length = len(analysis_text)
        length_score = min(analysis_length / 2000.0, 1.0)  # Normalize to 2000 chars
        
        # Structure analysis (check for organized sections)
        has_sections = any(marker in analysis_text.lower() for marker in [
            "key findings", "conclusion", "summary", "insights", "main topics"
        ])
        structure_score = 1.0 if has_sections else 0.5
        
        # Content diversity (check for varied analysis points)
        analysis_points = analysis_text.count("•") + analysis_text.count("-") + analysis_text.count("1.") + analysis_text.count("2.")
        diversity_score = min(analysis_points / 5.0, 1.0)  # Normalize to 5 points
        
        content_richness_score = (length_score * 0.4 + structure_score * 0.4 + diversity_score * 0.2)
        
        print(f"🔍 Content Richness: {analysis_length} chars, sections: {has_sections}, points: {analysis_points} → Score: {content_richness_score:.3f}")
    else:
        print(f"🔍 Content Richness: No analysis text → Score: 0.000")
    
    # Factor 3: API Reliability (20% weight) - How well did external services perform?
    api_reliability_score = 0.0
    
    if api_response_quality.get("brightdata_success", False):
        # BrightData API worked
        api_reliability_score += 0.6
        
        # Check response time (faster = more reliable)
        response_time = api_response_quality.get("brightdata_response_time", 10.0)
        if response_time < 5.0:
            api_reliability_score += 0.2
        elif response_time < 10.0:
            api_reliability_score += 0.1
        
        print(f"🔍 API Reliability - BrightData: Success, {response_time:.2f}s → Score: {api_reliability_score:.3f}")
    else:
        print(f"🔍 API Reliability - BrightData: Failed")
    
    if api_response_quality.get("openai_success", False):
        # OpenAI API worked
        api_reliability_score += 0.4
        
        # Check if we got a substantial response
        openai_response_length = len(api_response_quality.get("openai_response", ""))
        if openai_response_length > 100:
            api_reliability_score += 0.1
        
        print(f"🔍 API Reliability - OpenAI: Success, {openai_response_length} chars → Score: {api_reliability_score:.3f}")
    else:
        print(f"🔍 API Reliability - OpenAI: Failed")
    
    # Factor 4: Processing Success (10% weight) - Did all steps complete?
    processing_score = 1.0  # Default to success
    
    # Check for any processing errors
    if not serp_context or len(serp_context.strip()) < 100:
        processing_score = 0.5  # Reduced context
    
    if not analysis_text or len(analysis_text.strip()) < 100:
        processing_score = 0.3  # Minimal analysis
    
    print(f"🔍 Processing Success: {processing_score:.3f}")
    
    # Calculate weighted final score
    final_confidence = (
        data_quality_score * 0.40 +      # 40% weight
        content_richness_score * 0.30 +  # 30% weight
        api_reliability_score * 0.20 +   # 20% weight
        processing_score * 0.10          # 10% weight
    )
    
    print(f"\n🔍 FINAL CALCULATION:")
    print(f"   Data Quality ({data_quality_score:.3f} × 0.40) = {data_quality_score * 0.40:.4f}")
    print(f"   Content Richness ({content_richness_score:.3f} × 0.30) = {content_richness_score * 0.30:.4f}")
    print(f"   API Reliability ({api_reliability_score:.3f} × 0.20) = {api_reliability_score * 0.20:.4f}")
    print(f"   Processing Success ({processing_score:.3f} × 0.10) = {processing_score * 0.10:.4f}")
    print(f"   Raw Total = {final_confidence:.4f}")
    
    # Ensure score is within bounds and round to 2 decimal places
    final_confidence = max(0.0, min(1.0, final_confidence))
    final_confidence = round(final_confidence, 2)
    
    print(f"🔍 Final Rounded Confidence: {final_confidence}")
    print(f"🔍 End of debug output\n")
    
    return final_confidence

async def perform_web_analysis(question: str) -> WebAnalysis:
    """
    Performs real web analysis using the BrightData SERP API (via Direct Access)
    and OpenAI for summarization.
    """
    print(f"Performing SERP analysis for: '{question}'")
    
    # Track API performance metrics for confidence calculation
    api_quality_metrics = {
        "brightdata_success": False,
        "brightdata_response_time": 0.0,
        "openai_success": False,
        "openai_response": ""
    }
    
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
        
        # Track timing for confidence calculation
        import time
        brightdata_start = time.time()
        
        # Try the correct BrightData SERP API endpoint
        try:
            response = await brightdata_client.post(url="/", json=payload)
            api_quality_metrics["brightdata_success"] = True
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
            api_quality_metrics["brightdata_success"] = True
        
        brightdata_end = time.time()
        api_quality_metrics["brightdata_response_time"] = brightdata_end - brightdata_start
        
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
        
        openai_start = time.time()
        analysis_response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert research analyst. Provide clear, structured analysis based on the given search results."},
                {"role": "user", "content": analysis_prompt}
            ]
        )
        openai_end = time.time()
        
        analysis_text = analysis_response.choices[0].message.content
        api_quality_metrics["openai_success"] = True
        api_quality_metrics["openai_response"] = analysis_text
        
        # Calculate sophisticated confidence score
        confidence_score = calculate_web_analysis_confidence(
            search_results=search_results,
            serp_context=serp_context,
            analysis_text=analysis_text,
            api_response_quality=api_quality_metrics
        )
        
        print(f"   📊 Calculated confidence score: {confidence_score:.2f}")
        
        return WebAnalysis(
            source="BrightData SERP API + OpenAI",
            content=analysis_text,
            timestamp=datetime.now(timezone.utc),
            confidence_score=confidence_score
        )
        
    except Exception as e:
        print(f"   ❌ Error in web analysis: {e}")
        
        # Calculate confidence for error case (will be very low)
        error_confidence = calculate_web_analysis_confidence(
            search_results={},
            serp_context="",
            analysis_text=f"Error: {e}",
            api_response_quality=api_quality_metrics
        )
        
        return WebAnalysis(
            source="Fallback Analysis",
            content=f"Unable to perform web analysis due to error: {e}",
            timestamp=datetime.now(timezone.utc),
            confidence_score=error_confidence
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
