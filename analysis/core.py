# analysis/core.py

import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from database import AsyncSessionLocal
from models import Analysis
from schemas import StatusEnum, FullAnalysisResult, WebAnalysis, ChatGPTResponse, VisualizationData, BrandRanking


async def update_job_status(analysis_id: str, status: StatusEnum, progress: int = 0, current_step: str = ""):
    """A helper function to update the job status in the database."""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = (
                update(Analysis)
                .where(Analysis.id == analysis_id)
                .values(status=status, progress=progress, current_step=current_step)
            )
            await session.execute(stmt)

async def save_final_result(analysis_id: str, result: FullAnalysisResult):
    """A helper function to save the final result and mark the job as COMPLETE."""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = (
                update(Analysis)
                .where(Analysis.id == analysis_id)
                .values(
                    status=StatusEnum.COMPLETE,
                    progress=100,
                    current_step="Finished",
                    full_result=result.model_dump(), # Use model_dump for Pydantic v2
                )
            )
            await session.execute(stmt)

async def handle_error(analysis_id: str, error_message: str):
    """A helper function to log an error and mark the job as ERROR."""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = (
                update(Analysis)
                .where(Analysis.id == analysis_id)
                .values(
                    status=StatusEnum.ERROR,
                    error_message=error_message,
                    current_step="Error",
                )
            )
            await session.execute(stmt)


async def run_full_analysis(analysis_id: str):
    """
    The main background task for running the full analysis.
    This function simulates a multi-step process with API calls.
    """
    print(f"Starting analysis for job ID: {analysis_id}")
    try:
        # Step 1: Set status to PROCESSING
        await update_job_status(
            analysis_id, StatusEnum.PROCESSING, progress=10, current_step="Initializing analysis"
        )
        await asyncio.sleep(2) # Simulate work

        # Step 2: Simulate SCRAPING phase
        await update_job_status(
            analysis_id, StatusEnum.SCRAPING, progress=30, current_step="Calling BrightData and OpenAI for web analysis"
        )
        # In a real implementation, this is where you would use httpx and openai clients
        await asyncio.sleep(5) # Simulate long API call
        print(f"[{analysis_id}] Scraping phase complete.")

        # Step 3: Simulate SYNTHESIZING phase
        await update_job_status(
            analysis_id, StatusEnum.SYNTHESIZING, progress=75, current_step="Synthesizing results and generating insights"
        )
        await asyncio.sleep(3) # Simulate data processing
        print(f"[{analysis_id}] Synthesizing phase complete.")

        # Step 4: Create mock final result object
        # First, get the original question from the DB
        async with AsyncSessionLocal() as session:
            analysis_record = await session.get(Analysis, analysis_id)
            if not analysis_record:
                raise ValueError("Analysis record not found in database during final step.")
            research_question = analysis_record.research_question

        # Now, build the final result Pydantic model
        final_result = FullAnalysisResult(
            analysis_id=analysis_id,
            research_question=research_question,
            completed_at=datetime.now(timezone.utc),
            web_results=WebAnalysis(
                rankings=[BrandRanking(brand_name="Brand A", rank=1, mentions=10)],
                summary="Brand A is dominant in web search results."
            ),
            chatgpt_simulation=ChatGPTResponse(
                simulated_response="In my simulation, Brand B was mentioned.",
                identified_brands=["Brand B"]
            ),
            visualization=VisualizationData(
                chart_type="bar",
                data={"Brand A": 10, "Brand B": 5}
            )
        )

        # Step 5: Save the final result to the database
        await save_final_result(analysis_id, final_result)
        print(f"Successfully completed analysis for job ID: {analysis_id}")

    except Exception as e:
        print(f"ERROR during analysis for job ID {analysis_id}: {e}")
        await handle_error(analysis_id, str(e))