#!/usr/bin/env python3
"""
Beautiful CLI script for LLM Search Insight API analysis.
Usage: python3 analyze.py "Your research question here"
"""

import sys
import asyncio
import time
import json
import httpx
from typing import Optional
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

# Load environment variables
load_dotenv()

# Initialize Rich console
console = Console()

class AnalysisCLI:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=60.0)
    
    def print_header(self, text: str):
        """Print a beautiful header using Rich."""
        console.print(Panel(text, style="bold blue", box=box.DOUBLE))
    
    def print_step(self, text: str, status: str = "info"):
        """Print a step with appropriate styling."""
        if status == "info":
            console.print(f"🔍 {text}", style="blue")
        elif status == "success":
            console.print(f"✅ {text}", style="green")
        elif status == "warning":
            console.print(f"⚠️  {text}", style="yellow")
        elif status == "error":
            console.print(f"❌ {text}", style="red")
    
    def print_result(self, title: str, content: str):
        """Print a formatted result section using Rich."""
        console.print(Panel(content, title=title, style="cyan"))
    
    async def submit_analysis(self, question: str) -> Optional[str]:
        """Submit an analysis request and return the analysis ID."""
        try:
            payload = {"research_question": question}
            response = await self.client.post(
                f"{self.base_url}/api/v1/analyze",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("analysis_id")
        except httpx.RequestError as e:
            self.print_step(f"Failed to submit analysis: {str(e)}", "error")
            return None
    
    async def monitor_progress(self, analysis_id: str) -> bool:
        """Monitor the progress of an analysis job using Rich progress bar."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Analysis Progress", total=100)
            
            while True:
                try:
                    response = await self.client.get(f"{self.base_url}/api/v1/analyze/{analysis_id}/status")
                    response.raise_for_status()
                    data = response.json()
                    
                    status = data.get("status")
                    progress_value = data.get("progress", 0)
                    current_step = data.get("current_step", "")
                    
                    # Update progress bar
                    progress.update(task, completed=progress_value, description=current_step)
                    
                    if status == "COMPLETE":
                        progress.update(task, completed=100, description="Analysis completed!")
                        self.print_step("Analysis completed successfully!", "success")
                        return True
                    elif status == "ERROR":
                        progress.update(task, completed=100, description="Analysis failed!")
                        error_msg = data.get("error_message", "Unknown error")
                        self.print_step(f"Analysis failed: {error_msg}", "error")
                        return False
                    
                    await asyncio.sleep(1)
                    
                except httpx.RequestError as e:
                    self.print_step(f"Failed to check status: {str(e)}", "error")
                    return False
    
    async def get_results(self, analysis_id: str) -> Optional[dict]:
        """Get the final analysis results."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/analyze/{analysis_id}")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self.print_step(f"Failed to get results: {str(e)}", "error")
            return None
    
    def format_web_results(self, web_results: dict) -> str:
        """Format web analysis results nicely."""
        source = web_results.get("source", "Unknown")
        content = web_results.get("content", "No content available")
        confidence = web_results.get("confidence_score", 0)
        
        formatted = f"Source: {source}\n"
        formatted += f"Confidence: {confidence:.2f}\n"
        formatted += f"Content:\n{content}"
        
        return formatted
    
    def format_chatgpt_results(self, chatgpt_results: dict) -> str:
        """Format ChatGPT simulation results nicely."""
        response = chatgpt_results.get("simulated_response", "No response available")
        brands = chatgpt_results.get("identified_brands", [])
        
        formatted = f"Response:\n{response}\n\n"
        if brands:
            formatted += f"Identified Brands: {', '.join(brands)}"
        
        return formatted
    
    def format_visualization(self, visualization: dict) -> str:
        """Format visualization data nicely."""
        formatted = ""
        
        # Handle the new rich visualization structure
        if "brand_scores" in visualization and visualization["brand_scores"]:
            formatted += "Top Brands by Visibility Score:\n"
            for brand_score in visualization["brand_scores"]:
                brand_name = brand_score.get("brand_name", "Unknown")
                score = brand_score.get("visibility_score", 0)
                rank = brand_score.get("rank", 0)
                mentions = brand_score.get("mentions", 0)
                formatted += f"  {rank}. {brand_name} - Score: {score} (Mentions: {mentions})\n"
        else:
            formatted += "No brand scores available\n"
        
        # Add methodology explanation if available
        methodology = visualization.get("methodology_explanation", "")
        if methodology:
            formatted += f"\nMethodology:\n{methodology}\n"
        
        return formatted
    
    async def run_analysis(self, question: str):
        """Run the complete analysis workflow."""
        self.print_header("LLM Search Insight Analysis")
        self.print_step(f"Research Question: {question}")
        
        # Step 1: Submit analysis
        self.print_step("Submitting analysis request...")
        analysis_id = await self.submit_analysis(question)
        if not analysis_id:
            return False
        
        self.print_step(f"Analysis submitted with ID: {analysis_id}", "success")
        
        # Step 2: Monitor progress
        self.print_step("Monitoring analysis progress...")
        if not await self.monitor_progress(analysis_id):
            return False
        
        # Step 3: Get results
        self.print_step("Retrieving analysis results...")
        results = await self.get_results(analysis_id)
        if not results:
            return False
        
        # Step 4: Display results
        self.print_header("Analysis Results")
        
        # Research question
        self.print_result("Research Question", results.get("research_question", "N/A"))
        
        # Web results
        if "web_results" in results:
            web_formatted = self.format_web_results(results["web_results"])
            self.print_result("Web Analysis", web_formatted)
        
        # ChatGPT results
        if "chatgpt_simulation" in results:
            chatgpt_formatted = self.format_chatgpt_results(results["chatgpt_simulation"])
            self.print_result("ChatGPT Analysis", chatgpt_formatted)
        
        # Visualization
        if "visualization" in results:
            viz_formatted = self.format_visualization(results["visualization"])
            self.print_result("Visualization", viz_formatted)
        
        # Metadata
        completed_at = results.get("completed_at", "N/A")
        if completed_at != "N/A":
            self.print_result("Completed At", completed_at)
        
        self.print_header("Analysis Complete!")
        return True
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

async def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        console.print("Usage: python3 analyze.py \"Your research question here\"", style="red")
        console.print("Example: python3 analyze.py \"What are the best frontend frameworks for 2024?\"", style="yellow")
        sys.exit(1)
    
    question = sys.argv[1]
    
    # Check if server is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/docs")
            if response.status_code != 200:
                console.print("❌ API server is not responding properly.", style="red")
                console.print("Make sure the server is running with: cd src && uvicorn main:app --reload", style="yellow")
                sys.exit(1)
    except httpx.RequestError:
        console.print("❌ Cannot connect to API server at http://localhost:8000", style="red")
        console.print("Make sure the server is running with: cd src && uvicorn main:app --reload", style="yellow")
        sys.exit(1)
    
    # Run analysis
    cli = AnalysisCLI()
    try:
        success = await cli.run_analysis(question)
        if not success:
            sys.exit(1)
    finally:
        await cli.close()

if __name__ == "__main__":
    asyncio.run(main())
