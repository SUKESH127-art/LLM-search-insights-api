# analysis/core.py

import asyncio
from datetime import datetime, timezone

from sqlalchemy import update

# Import our new clients
from analysis.clients import openai_client, http_client, BRIGHTDATA_API_BASE_URL
from database import AsyncSessionLocal
from models import Analysis
from schemas import (
    StatusEnum,
    FullAnalysisResult,
    WebAnalysis,
    ChatGPTResponse,
    VisualizationData,
    BrandRanking,
)


# --- Private Helper Functions for API Calls ---

async def _perform_web_analysis(question: str) -> WebAnalysis:
    """
    Simulates the multi-step process of using BrightData for search
    and OpenAI for summarizing the results.
    """
    print(f"Performing web analysis for: '{question}'")
    # In a real implementation:
    # 1. Construct the BrightData SERP API payload
    # payload = {"country": "US", "query": question}
    # 2. Make the async call using our http_client
    # response = await http_client.post("/", json=payload)
    # response.raise_for_status() # Raise an exception for bad status codes
    # search_results = response.json()
    # 3. Pass search_results to an OpenAI model for summarization and ranking
    
    # For now, we simulate the delay and return mock data.
    await asyncio.sleep(5) 
    
    mock_web_analysis = WebAnalysis(
        rankings=[BrandRanking(brand_name="Brand A (from Web)", rank=1, mentions=10)],
        summary="Based on web search, Brand A is the clear leader."
    )
    return mock_web_analysis

async def _simulate_chatgpt_response(question: str) -> ChatGPTResponse:
    """
    Simulates a direct query to OpenAI to get a generative response.
    """
    print(f"Simulating direct ChatGPT response for: '{question}'")
    # In a real implementation:
    # response = await openai_client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[
    #         {"role": "system", "content": "You are a helpful assistant."},
    #         {"role": "user", "content": question},
    #     ],
    # )
    # simulated_text = response.choices[0].message.content
    # Then, a second call might be needed to extract brand names from the text.
    
    # For now, we simulate the delay and return mock data.
    await asyncio.sleep(3)

    mock_chatgpt_response = ChatGPTResponse(
        simulated_response="When asked directly, ChatGPT tends to mention Brand B as a strong competitor.",
        identified_brands=["Brand B (from GPT)"]
    )
    return mock_chatgpt_response


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
            data={"Web Mentions": web_analysis_result.rankings[0].mentions, "GPT Mentions": 1} # Mocking a GPT mention count
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
        if 'completed_at' in result_dict:
            result_dict['completed_at'] = result_dict['completed_at'].isoformat()

        await save_final_result(analysis_id, result_dict)
        print(f"Successfully completed analysis for job ID: {analysis_id}")

    except Exception as e:
        print(f"ERROR during analysis for job ID {analysis_id}: {e}")
        await handle_error(analysis_id, str(e))