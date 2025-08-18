# src/analysis/processor.py
from schemas import WebAnalysis, ChatGPTResponse

def process_analysis_results(web_result: WebAnalysis, gpt_result: ChatGPTResponse) -> tuple[WebAnalysis, ChatGPTResponse]:
    """
    Processes and validates the raw analysis results.
    Future logic for cleaning, sentiment analysis, etc., would go here.
    """
    print("Processing analysis results (currently a pass-through)...")
    return web_result, gpt_result
