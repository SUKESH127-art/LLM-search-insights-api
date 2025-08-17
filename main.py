# main.py

from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession


# Import project components
from database import engine, Base, AsyncSessionLocal
from models import Analysis
from schemas import (
    AnalysisRequest,
    AnalysisResponse,
    StatusResponse,
    FullAnalysisResult,
    ErrorResponse,
    ErrorType,
    StatusEnum,
)
# We will create this function in the next step, for now, we import it.
from analysis.core import run_full_analysis 

# --- Application Lifecycle ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    print("Application startup: Creating database tables...")
    async with engine.begin() as conn:
        # In a real production app, you would use Alembic for migrations.
        # This is a shortcut for the MVP to create tables from models.
        await conn.run_sync(Base.metadata.create_all)
    yield
    # On shutdown
    print("Application shutdown.")


# --- FastAPI App Initialization ---

app = FastAPI(
    title="LLM Search Insight API",
    version="5.0",
    lifespan=lifespan,
    responses={
        404: {"model": ErrorResponse, "description": "Resource Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)


# --- Database Dependency ---

async def get_db() -> AsyncSession:
    """
    Dependency that provides a database session for each request.
    It ensures the session is always closed after the request is handled.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# --- API Endpoints ---

@app.post(
    "/api/v1/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a new analysis job",
)
async def submit_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Accepts a research question, creates a new analysis job record in the database,
    and queues the analysis to be run in the background.
    """
    # Create a new Analysis record in the database
    new_analysis = Analysis(
        id=str(uuid.uuid4()),
        research_question=request.research_question,
        status=StatusEnum.QUEUED,
        progress=0,
    )
    db.add(new_analysis)
    await db.commit()
    await db.refresh(new_analysis)

    # Start the background analysis task
    background_tasks.add_task(run_full_analysis, new_analysis.id)

    return AnalysisResponse(
        analysis_id=new_analysis.id,
        status=new_analysis.status
    )


@app.get(
    "/api/v1/analyze/{analysis_id}/status",
    response_model=StatusResponse,
    summary="Check analysis job status",
)
async def get_analysis_status(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """
    Poll this endpoint to get the current status and progress of an analysis job.
    """
    analysis = await db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": ErrorType.NOT_FOUND, "details": {"message": "Analysis ID not found"}},
        )
    return StatusResponse(
        status=analysis.status,
        progress=analysis.progress,
        current_step=analysis.current_step,
        error_message=analysis.error_message
    )


@app.get(
    "/api/v1/analyze/{analysis_id}",
    response_model=FullAnalysisResult,
    summary="Get final analysis results",
)
async def get_analysis_result(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve the full analysis report once the status is COMPLETE.
    """
    analysis = await db.get(Analysis, analysis_id)
    
    # Per TDD, return 404 if not found or not yet complete
    # TODO: Implement expiration filtering - currently disabled due to SQLite datetime handling complexity
    # The TZDateTime TypeDecorator approach needs further investigation for proper implementation
    if not analysis or analysis.status != StatusEnum.COMPLETE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": ErrorType.NOT_FOUND, "details": {"message": "Result not found or not complete"}},
        )
        
    return analysis.full_result