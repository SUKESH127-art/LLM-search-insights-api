# src/analysis/orchestrator.py
import asyncio
from datetime import datetime, timezone
from sqlalchemy import update

from database import AsyncSessionLocal
from models import Analysis
from schemas import StatusEnum, FullAnalysisResult

# Import from our new, specialized modules
from analysis.collector import perform_web_analysis, simulate_chatgpt_response
from analysis.processor import process_analysis_results
from analysis.visualizer import extract_visualization_data

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
            perform_web_analysis(research_question),
            simulate_chatgpt_response(research_question)
        )
        
        web_analysis_result = results[0]
        chatgpt_simulation_result = results[1]
        
        print(f"[{analysis_id}] Parallel data gathering complete.")
        
        await update_job_status(analysis_id, StatusEnum.PROCESSING, 50, "Processing analysis results")
        
        # Process the results through our processor module
        web_analysis_result, chatgpt_simulation_result = process_analysis_results(
            web_analysis_result, chatgpt_simulation_result
        )
        
        await update_job_status(analysis_id, StatusEnum.SYNTHESIZING, 75, "Synthesizing final report and visualization")

        # Check if web analysis was successful or failed
        print(f"[{analysis_id}] 🔍 Starting visualization extraction...")
        print(f"[{analysis_id}] 📝 Web analysis content length: {len(web_analysis_result.content)}")
        print(f"[{analysis_id}] 📝 Web analysis preview: {web_analysis_result.content[:200]}...")
        
        # Determine if web analysis was successful or failed
        if "Unable to perform web analysis" in web_analysis_result.content or "SERP API did not return" in web_analysis_result.content:
            # Web analysis failed - create fallback visualization using ChatGPT data
            print(f"[{analysis_id}] 🔄 Web analysis failed, creating fallback visualization from ChatGPT data...")
            
            # Create meaningful visualization data from ChatGPT response
            chatgpt_brands = chatgpt_simulation_result.identified_brands[:5]  # Top 5 brands
            if chatgpt_brands:
                brand_scores = []
                for i, brand in enumerate(chatgpt_brands):
                    brand_scores.append({
                        "brand_name": brand,
                        "visibility_score": max(1, 100 - (i * 20)),  # Score from 100 down to 1
                        "rank": i + 1,
                        "mentions": 1  # ChatGPT mentioned each brand once
                    })
                
                final_visualization = {
                    "chart_type": "bar_chart_brand_visibility",
                    "title": "Top 5 Brands by LLM Search Visibility",
                    "x_axis_label": "Brand Name",
                    "y_axis_label": "Visibility Score (1-100)",
                    "top_5_brands": chatgpt_brands,
                    "brand_scores": brand_scores,
                    "methodology_explanation": "Web analysis failed, so brand visibility scores are estimated based on ChatGPT's knowledge ranking. Higher scores indicate brands that ChatGPT considers more prominent in the industry."
                }
            else:
                # No brands identified by ChatGPT either
                final_visualization = {
                    "chart_type": "bar_chart_brand_visibility",
                    "title": "Top 5 Brands by LLM Search Visibility",
                    "x_axis_label": "Brand Name",
                    "y_axis_label": "Visibility Score (1-100)",
                    "top_5_brands": ["No brands identified"],
                    "brand_scores": [{
                        "brand_name": "No brands identified",
                        "visibility_score": 1,
                        "rank": 1,
                        "mentions": 0
                    }],
                    "methodology_explanation": "Neither web analysis nor ChatGPT could identify specific brands for this query."
                }
        else:
            # Web analysis succeeded - try to extract visualization data normally
            print(f"[{analysis_id}] ✅ Web analysis succeeded, extracting visualization data...")
            final_visualization = await extract_visualization_data(
                web_analysis_text=web_analysis_result.content
            )
            # Convert to dict for JSON serialization
            final_visualization = final_visualization.model_dump()
        
        print(f"[{analysis_id}] ✅ Visualization extraction complete!")
        print(f"[{analysis_id}] 📊 Final visualization: {final_visualization}")

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
