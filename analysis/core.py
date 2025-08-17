# analysis/core.py

import asyncio
import json
from datetime import datetime, timezone

from sqlalchemy import update

# Import our new clients
from analysis.clients import openai_client, web_unlocker_client, BRIGHTDATA_API_URL
from database import AsyncSessionLocal
from models import Analysis
from schemas import (
    StatusEnum,
    FullAnalysisResult,
    WebAnalysis,
    ChatGPTResponse,
    VisualizationData,
)


# --- Private Helper Functions for API Calls ---

async def _perform_web_analysis(question: str) -> WebAnalysis:
    """
    Performs real web analysis using BrightData MCP and OpenAI for summarization.
    """
    print(f"Performing real web analysis for: '{question}'")
    
    try:
        # Step 1: Use BrightData Web Unlocker API to extract web data
        print("   🔍 Extracting web data via BrightData Web Unlocker API...")

        # Create Web Unlocker API request for web scraping
        # Using a relevant website to search for information
        web_unlocker_payload = {
            "zone": "web_unlocker1",  # Using the web_unlocker1 zone
            "url": f"https://www.google.com/search?q={question.replace(' ', '+')}",
            "format": "raw"
        }
        
        # Make the Web Unlocker API call
        print(f"   🔍 Making Web Unlocker API call to: {BRIGHTDATA_API_URL}")
        print(f"   📝 Payload: {web_unlocker_payload}")
        
        response = await web_unlocker_client.post(BRIGHTDATA_API_URL, json=web_unlocker_payload)
        print(f"   📊 Response status: {response.status_code}")
        print(f"   📊 Response headers: {dict(response.headers)}")
        
        response.raise_for_status()
        
        # Handle Web Unlocker API response - it should be raw HTML/text
        response_text = response.text
        print(f"   📄 Raw response length: {len(response_text)} characters")
        print(f"   📄 Response preview: {response_text[:200]}...")
        
        # Use the raw response text for analysis
        serp_data = response_text
        
        # Limit the data size to avoid overwhelming OpenAI
        if len(serp_data) > 5000:
            serp_data = serp_data[:5000] + "... [truncated]"
        
        print(f"   ✅ Web data extracted via Web Unlocker API")
        
        # Step 2: Use OpenAI to analyze and summarize the web data
        print("   🤖 Analyzing web data with OpenAI...")
        
        # Create a prompt for OpenAI to analyze the web data
        analysis_prompt = f"""
        Based on the following web search results about "{question}":
        
        {serp_data}
        
        Please provide a comprehensive analysis including:
        1. Key insights and findings from the search results
        2. Relevant trends or patterns in the data
        3. Important information and recommendations
        4. Summary of the most relevant findings
        
        Format your response as a structured analysis.
        """
        
        # Get analysis from OpenAI
        analysis_response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert research analyst. Provide clear, structured analysis based on the given web search results."},
                {"role": "user", "content": analysis_prompt}
            ]
        )
        
        analysis_text = analysis_response.choices[0].message.content
        
        # Create WebAnalysis object
        web_analysis = WebAnalysis(
            source="BrightData Web Unlocker API + OpenAI",
            content=analysis_text,
            timestamp=datetime.now(timezone.utc),
            confidence_score=0.90  # High confidence for Web Unlocker + OpenAI analysis
        )
        
        print(f"   ✅ Web analysis completed successfully")
        return web_analysis
        
    except Exception as e:
        print(f"   ❌ Error in web analysis: {str(e)}")
        # Return a fallback analysis
        return WebAnalysis(
            source="Fallback Analysis",
            content=f"Unable to perform web analysis due to error: {str(e)}",
            timestamp=datetime.now(timezone.utc),
            confidence_score=0.0
        )

async def _simulate_chatgpt_response(question: str) -> ChatGPTResponse:
    """
    Gets a real response from OpenAI about the user's question.
    """
    print(f"Getting real OpenAI response for: '{question}'")
    
    try:
        # Create a completely generic prompt
        generic_prompt = f"""
        Answer this question: "{question}"
        
        Provide a comprehensive, well-structured response that includes:
        1. Clear explanation of the topic
        2. Key points and insights
        3. Practical examples or use cases
        4. Recommendations or best practices
        
        Keep your response focused only on the question asked.
        """
        
        from analysis.clients import openai_client
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": generic_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content
        print(f"   ✅ OpenAI response received: {len(response_text)} characters")
        
        # Extract relevant entities from the response
        entity_extraction_prompt = f"""
        Extract the names of relevant companies, technologies, tools, or key entities mentioned in this text:
        
        {response_text}
        
        Return only a JSON array of entity names.
        """
        
        entity_response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": entity_extraction_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        entities_text = entity_response.choices[0].message.content
        try:
            entities_data = json.loads(entities_text)
            identified_brands = entities_data.get('brands', []) if isinstance(entities_data, dict) else entities_data
        except json.JSONDecodeError:
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


# --- Database Interaction Functions ---

async def update_job_status(analysis_id: str, status: StatusEnum, progress: int = 0, current_step: str = ""):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = update(Analysis).where(Analysis.id == analysis_id).values(status=status, progress=progress, current_step=current_step)
            await session.execute(stmt)

async def save_final_result(analysis_id: str, result: dict):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = update(Analysis).where(Analysis.id == analysis_id).values(status=StatusEnum.COMPLETE, progress=100, current_step="Finished", full_result=result)
            await session.execute(stmt)

async def handle_error(analysis_id: str, error_message: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = update(Analysis).where(Analysis.id == analysis_id).values(status=StatusEnum.ERROR, error_message=error_message, current_step="Error")
            await session.execute(stmt)


# --- Main Background Task (Refactored) ---

async def run_full_analysis(analysis_id: str):
    """
    The main background task orchestrator.
    """
    print(f"Starting analysis for job ID: {analysis_id}")
    try:
        await update_job_status(analysis_id, StatusEnum.PROCESSING, 10, "Fetching research question")

        async with AsyncSessionLocal() as session:
            analysis_record = await session.get(Analysis, analysis_id)
            if not analysis_record:
                raise ValueError("Analysis record not found at start of analysis.")
            research_question = analysis_record.research_question

        await update_job_status(analysis_id, StatusEnum.PROCESSING, 20, "Starting parallel data gathering")

        # --- Parallel Execution using asyncio.gather ---
        # This is the core of our async optimization.
        results = await asyncio.gather(
            _perform_web_analysis(research_question),
            _simulate_chatgpt_response(research_question)
        )
        
        web_analysis_result: WebAnalysis = results[0]
        chatgpt_simulation_result: ChatGPTResponse = results[1]
        
        print(f"[{analysis_id}] Parallel data gathering complete.")
        
        await update_job_status(analysis_id, StatusEnum.SYNTHESIZING, 75, "Synthesizing final report")

        # --- Synthesis Step ---
        # Here you could add logic to create a better visualization based on both results
        final_visualization = VisualizationData(
            chart_type="comparison_bar",
            data={"Web Analysis": 1, "GPT Analysis": 1} # Both analyses completed successfully
        )

        final_result = FullAnalysisResult(
            analysis_id=analysis_id,
            research_question=research_question,
            completed_at=datetime.now(timezone.utc),
            web_results=web_analysis_result,
            chatgpt_simulation=chatgpt_simulation_result,
            visualization=final_visualization,
        )

        result_dict = final_result.model_dump()
        
        # Convert all datetime fields to ISO format strings for JSON serialization
        if 'completed_at' in result_dict:
            result_dict['completed_at'] = result_dict['completed_at'].isoformat()
        
        # Convert timestamp in web_results if it exists
        if 'web_results' in result_dict and 'timestamp' in result_dict['web_results']:
            result_dict['web_results']['timestamp'] = result_dict['web_results']['timestamp'].isoformat()

        await save_final_result(analysis_id, result_dict)
        print(f"Successfully completed analysis for job ID: {analysis_id}")

    except Exception as e:
        print(f"ERROR during analysis for job ID {analysis_id}: {e}")
        await handle_error(analysis_id, str(e))