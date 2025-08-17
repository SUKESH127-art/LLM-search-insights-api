#!/usr/bin/env python3
"""
Beautiful CLI script for LLM Search Insight API analysis.
Usage: python3 analyze.py "Your research question here"
"""

import sys
import asyncio
import time
import json
import requests
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Color codes for beautiful output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ProgressBar:
    def __init__(self, total: int, width: int = 50):
        self.total = total
        self.width = width
        self.current = 0
    
    def update(self, current: int):
        self.current = current
        filled = int(self.width * self.current // self.total)
        bar = '█' * filled + '-' * (self.width - filled)
        percentage = self.current * 100 // self.total
        print(f'\r[{bar}] {percentage}%', end='', flush=True)
    
    def complete(self):
        self.update(self.total)
        print()

class AnalysisCLI:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.session = requests.Session()
    
    def print_header(self, text: str):
        """Print a beautiful header."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}{Colors.ENDC}\n")
    
    def print_step(self, text: str, status: str = "info"):
        """Print a step with appropriate color."""
        if status == "info":
            print(f"{Colors.OKBLUE}🔍 {text}{Colors.ENDC}")
        elif status == "success":
            print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")
        elif status == "warning":
            print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")
        elif status == "error":
            print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")
    
    def print_result(self, title: str, content: str, color: str = Colors.OKCYAN):
        """Print a formatted result section."""
        print(f"\n{color}{Colors.BOLD}{title}:{Colors.ENDC}")
        print(f"{'─' * (len(title) + 1)}")
        print(f"{content}\n")
    
    def submit_analysis(self, question: str) -> Optional[str]:
        """Submit an analysis request and return the analysis ID."""
        try:
            payload = {"research_question": question}
            response = self.session.post(
                f"{self.base_url}/api/v1/analyze",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("analysis_id")
        except requests.exceptions.RequestException as e:
            self.print_step(f"Failed to submit analysis: {str(e)}", "error")
            return None
    
    def monitor_progress(self, analysis_id: str) -> bool:
        """Monitor the progress of an analysis job."""
        progress_bar = ProgressBar(100)
        
        while True:
            try:
                response = self.session.get(f"{self.base_url}/api/v1/analyze/{analysis_id}/status")
                response.raise_for_status()
                data = response.json()
                
                status = data.get("status")
                progress = data.get("progress", 0)
                current_step = data.get("current_step", "")
                
                # Update progress bar
                progress_bar.update(progress)
                
                # Print current step
                if current_step:
                    print(f" {Colors.OKCYAN}{current_step}{Colors.ENDC}")
                
                if status == "COMPLETE":
                    progress_bar.complete()
                    self.print_step("Analysis completed successfully!", "success")
                    return True
                elif status == "ERROR":
                    progress_bar.complete()
                    error_msg = data.get("error_message", "Unknown error")
                    self.print_step(f"Analysis failed: {error_msg}", "error")
                    return False
                
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                self.print_step(f"Failed to check status: {str(e)}", "error")
                return False
    
    def get_results(self, analysis_id: str) -> Optional[dict]:
        """Get the final analysis results."""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/analyze/{analysis_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.print_step(f"Failed to get results: {str(e)}", "error")
            return None
    
    def format_web_results(self, web_results: dict) -> str:
        """Format web analysis results nicely."""
        source = web_results.get("source", "Unknown")
        content = web_results.get("content", "No content available")
        confidence = web_results.get("confidence_score", 0)
        
        formatted = f"Source: {Colors.BOLD}{source}{Colors.ENDC}\n"
        formatted += f"Confidence: {Colors.BOLD}{confidence:.2f}{Colors.ENDC}\n"
        formatted += f"Content:\n{content}"
        
        return formatted
    
    def format_chatgpt_results(self, chatgpt_results: dict) -> str:
        """Format ChatGPT simulation results nicely."""
        response = chatgpt_results.get("simulated_response", "No response available")
        brands = chatgpt_results.get("identified_brands", [])
        
        formatted = f"Response:\n{response}\n\n"
        if brands:
            formatted += f"Identified Brands: {Colors.BOLD}{', '.join(brands)}{Colors.ENDC}"
        
        return formatted
    
    def format_visualization(self, visualization: dict) -> str:
        """Format visualization data nicely."""
        chart_type = visualization.get("chart_type", "Unknown")
        data = visualization.get("data", {})
        
        formatted = f"Chart Type: {Colors.BOLD}{chart_type}{Colors.ENDC}\n"
        formatted += "Data:\n"
        for key, value in data.items():
            formatted += f"  • {key}: {Colors.BOLD}{value}{Colors.ENDC}\n"
        
        return formatted
    
    def run_analysis(self, question: str):
        """Run the complete analysis workflow."""
        self.print_header("LLM Search Insight Analysis")
        self.print_step(f"Research Question: {Colors.BOLD}{question}{Colors.ENDC}")
        
        # Step 1: Submit analysis
        self.print_step("Submitting analysis request...")
        analysis_id = self.submit_analysis(question)
        if not analysis_id:
            return False
        
        self.print_step(f"Analysis submitted with ID: {Colors.BOLD}{analysis_id}{Colors.ENDC}", "success")
        
        # Step 2: Monitor progress
        self.print_step("Monitoring analysis progress...")
        if not self.monitor_progress(analysis_id):
            return False
        
        # Step 3: Get results
        self.print_step("Retrieving analysis results...")
        results = self.get_results(analysis_id)
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

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print(f"{Colors.FAIL}Usage: python3 analyze.py \"Your research question here\"{Colors.ENDC}")
        print(f"{Colors.WARNING}Example: python3 analyze.py \"What are the best frontend frameworks for 2024?\"{Colors.ENDC}")
        sys.exit(1)
    
    question = sys.argv[1]
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code != 200:
            print(f"{Colors.FAIL}❌ API server is not responding properly.{Colors.ENDC}")
            print(f"{Colors.WARNING}Make sure the server is running with: python3 main.py{Colors.ENDC}")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print(f"{Colors.FAIL}❌ Cannot connect to API server at http://localhost:8000{Colors.ENDC}")
        print(f"{Colors.WARNING}Make sure the server is running with: python3 main.py{Colors.ENDC}")
        sys.exit(1)
    
    # Run analysis
    cli = AnalysisCLI()
    success = cli.run_analysis(question)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
