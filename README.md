# LLM Search Insight API

A FastAPI-based service that runs an LLM-powered research workflow: it collects web signals, synthesizes them with an LLM, and produces a structured visualization of brand visibility. The project now uses a standard Python `src/` layout and a separate `cli/` HTTP client.

## Features

- **FastAPI + Async**: High performance API with async SQLAlchemy
- **Modular analysis pipeline**: `collector`, `processor`, `visualizer`, orchestrated by `orchestrator`
- **Job tracking**: Create jobs, poll status, fetch final results
- **SQLite by default**: Pluggable via `DATABASE_URL`
- **Decoupled CLI**: Separate async HTTP client using `httpx` and `rich`
- **Public API**: Fully deployed and accessible at https://llm-search-insights-api.onrender.com

## Project Structure

```
llm-search-insight-api/
├── cli/
│   └── analyze.py                 # Async HTTP client (uses httpx + rich)
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── database.py                # DB engine/session/base
│   ├── models.py                  # SQLAlchemy models
│   ├── schemas.py                 # Pydantic schemas
│   └── analysis/
│       ├── __init__.py
│       ├── clients.py             # External API clients (OpenAI, BrightData)
│       ├── collector.py           # Data collection (SERP + LLM summaries)
│       ├── processor.py           # Result processing (currently pass-through)
│       ├── visualizer.py          # Visualization data extraction via LLM
│       └── orchestrator.py        # run_full_analysis() coordinator
├── requirements.txt
└── README.md
```

## Public API Access

**🌐 Live API:** https://llm-search-insights-api.onrender.com  
**📚 Interactive Documentation:** https://llm-search-insights-api.onrender.com/docs  
**🔧 OpenAPI Specification:** https://llm-search-insights-api.onrender.com/openapi.json  
**📋 API Version:** 5.1 (OAS 3.1)

---

## API Usage Guide

### **Typical Workflow**

Interacting with the API follows a simple asynchronous pattern:

1. **Submit Job:** Make a `POST` request to `/api/v1/analyze` with your research question. You will receive an `analysis_id`.
2. **Poll Status:** Periodically make `GET` requests to `/api/v1/analyze/{analysis_id}/status` to check the job's progress.
3. **Retrieve Results:** Once the status is `COMPLETE`, make a `GET` request to `/api/v1/analyze/{analysis_id}` to fetch the full report.

---

### **API Endpoints**

#### 1. Submit a New Analysis Job

**Endpoint:** `POST /api/v1/analyze`  
**Purpose:** Initiates a new research analysis job

**Request Body:**
```json
{
  "research_question": "What are the leading AI companies in 2024?"
}
```

**Request Validation:**
| Field | Type | Constraints | Required | Description |
|-------|------|-------------|----------|-------------|
| `research_question` | string | 10-500 characters | Yes | The research question to analyze |

**Example cURL Request:**
```bash
curl -X POST 'https://llm-search-insights-api.onrender.com/api/v1/analyze' \
  -H 'Content-Type: application/json' \
  -d '{
    "research_question": "What are the leading AI companies in 2024?"
  }'
```

**Response Codes:**
- **`202 Accepted`** - Job successfully queued
- **`422 Validation Error`** - Invalid request format
- **`500 Internal Server Error`** - Server processing error

**Successful Response:**
```json
{
  "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "QUEUED"
}
```

---

#### 2. Check Analysis Job Status

**Endpoint:** `GET /api/v1/analyze/{analysis_id}/status`  
**Purpose:** Check the current status and progress of an analysis job

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analysis_id` | string | Yes | Unique identifier from job submission |

**Response Schema:**
```json
{
  "status": "PROCESSING",
  "progress": 65,
  "current_step": "Analyzing web data",
  "error_message": null
}
```

**Status Values:**
- **`QUEUED`** - Job waiting in processing queue
- **`PROCESSING`** - Job has started execution
- **`SCRAPING`** - Collecting web data and information
- **`SYNTHESIZING`** - AI analysis and synthesis in progress
- **`COMPLETE`** - Analysis finished successfully
- **`ERROR`** - Job failed (check error_message)

**Example Usage:**
```bash
curl 'https://llm-search-insights-api.onrender.com/api/v1/analyze/a1b2c3d4-e5f6-7890-abcd-ef1234567890/status'
```

---

#### 3. Retrieve Analysis Results

**Endpoint:** `GET /api/v1/analyze/{analysis_id}`  
**Purpose:** Fetch the complete analysis report (only available when status is `COMPLETE`)

**Response Schema:**
```json
{
  "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "research_question": "What are the leading AI companies in 2024?",
  "status": "COMPLETE",
  "completed_at": "2024-01-15T14:30:00Z",
  "web_results": {
    "source": "Simulated web analysis",
    "content": "Comprehensive analysis of AI industry leaders...",
    "timestamp": "2024-01-15T14:30:00Z",
    "confidence_score": 0.95
  },
  "chatgpt_simulation": {
    "simulated_response": "Based on the analysis, the leading AI companies include...",
    "identified_brands": ["OpenAI", "Anthropic", "Google AI", "Microsoft AI", "Meta AI"]
  },
  "visualization": {
    "chart_type": "bar_chart_brand_visibility",
    "title": "Top 5 AI Companies by Market Visibility",
    "x_axis_label": "Company Name",
    "y_axis_label": "Visibility Score (1-100)",
    "top_5_brands": ["OpenAI", "Anthropic", "Google AI", "Microsoft AI", "Meta AI"],
    "brand_scores": [
      {
        "brand_name": "OpenAI",
        "visibility_score": 95,
        "rank": 1,
        "mentions": 12
      }
    ],
    "methodology_explanation": "Visibility scores calculated based on market presence, media coverage, and technological innovation..."
  }
}
```

---

### **Data Models & Schemas**

#### Core Schemas

**`AnalysisRequest`**
```json
{
  "research_question": "string (10-500 chars)"
}
```

**`AnalysisResponse`**
```json
{
  "analysis_id": "string (UUID)",
  "status": "StatusEnum"
}
```

**`StatusResponse`**
```json
{
  "status": "StatusEnum",
  "progress": "integer (0-100)",
  "current_step": "string (optional)",
  "error_message": "string (optional)"
}
```

**`FullAnalysisResult`**
```json
{
  "analysis_id": "string",
  "research_question": "string",
  "status": "StatusEnum",
  "completed_at": "datetime",
  "web_results": "WebAnalysis",
  "chatgpt_simulation": "ChatGPTResponse",
  "visualization": "VisualizationData"
}
```

#### Supporting Schemas

**`WebAnalysis`**
```json
{
  "source": "string",
  "content": "string",
  "timestamp": "datetime",
  "confidence_score": "float (0.0-1.0)"
}
```

**`ChatGPTResponse`**
```json
{
  "simulated_response": "string",
  "identified_brands": ["string[]"]
}
```

**`VisualizationData`**
```json
{
  "chart_type": "string",
  "title": "string",
  "x_axis_label": "string",
  "y_axis_label": "string",
  "top_5_brands": ["string[]"],
  "brand_scores": ["BrandVisibilityScore[]"],
  "methodology_explanation": "string"
}
```

**`BrandVisibilityScore`**
```json
{
  "brand_name": "string",
  "visibility_score": "integer (1-100)",
  "rank": "integer",
  "mentions": "integer"
}
```

---

### **Integration Examples**

#### JavaScript/Node.js

```javascript
class LLMSearchInsightAPI {
  constructor(baseURL = 'https://llm-search-insights-api.onrender.com') {
    this.baseURL = baseURL;
  }

  async submitAnalysis(question) {
    const response = await fetch(`${this.baseURL}/api/v1/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ research_question: question })
    });
    
    if (response.status === 202) {
      return await response.json();
    }
    throw new Error(`Failed to submit analysis: ${response.status}`);
  }

  async checkStatus(analysisId) {
    const response = await fetch(`${this.baseURL}/api/v1/analyze/${analysisId}/status`);
    return await response.json();
  }

  async getResults(analysisId) {
    const response = await fetch(`${this.baseURL}/api/v1/analyze/${analysisId}`);
    return await response.json();
  }

  async waitForCompletion(analysisId, pollInterval = 2000) {
    while (true) {
      const status = await this.checkStatus(analysisId);
      
      if (status.status === 'COMPLETE') {
        return await this.getResults(analysisId);
      } else if (status.status === 'ERROR') {
        throw new Error(`Analysis failed: ${status.error_message}`);
      }
      
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
  }
}

// Usage
const api = new LLMSearchInsightAPI();
const analysis = await api.submitAnalysis("What are the best programming languages for AI?");
const results = await api.waitForCompletion(analysis.analysis_id);
console.log(results);
```

#### Python

```python
import requests
import time
from typing import Dict, Any

class LLMSearchInsightAPI:
    def __init__(self, base_url: str = "https://llm-search-insights-api.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def submit_analysis(self, question: str) -> Dict[str, Any]:
        """Submit a new analysis job."""
        response = self.session.post(
            f"{self.base_url}/api/v1/analyze",
            json={"research_question": question}
        )
        response.raise_for_status()
        return response.json()
    
    def check_status(self, analysis_id: str) -> Dict[str, Any]:
        """Check the status of an analysis job."""
        response = self.session.get(
            f"{self.base_url}/api/v1/analyze/{analysis_id}/status"
        )
        response.raise_for_status()
        return response.json()
    
    def get_results(self, analysis_id: str) -> Dict[str, Any]:
        """Get the final analysis results."""
        response = self.session.get(
            f"{self.base_url}/api/v1/analyze/{analysis_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, analysis_id: str, poll_interval: int = 2) -> Dict[str, Any]:
        """Wait for analysis completion and return results."""
        while True:
            status = self.check_status(analysis_id)
            
            if status["status"] == "COMPLETE":
                return self.get_results(analysis_id)
            elif status["status"] == "ERROR":
                raise Exception(f"Analysis failed: {status.get('error_message')}")
            
            time.sleep(poll_interval)

# Usage
api = LLMSearchInsightAPI()
analysis = api.submit_analysis("What are the best programming languages for AI?")
results = api.wait_for_completion(analysis["analysis_id"])
print(results)
```

#### cURL Examples

```bash
# Submit analysis
curl -X POST 'https://llm-search-insights-api.onrender.com/api/v1/analyze' \
  -H 'Content-Type: application/json' \
  -d '{"research_question": "What are the top cloud providers in 2024?"}'

# Check status
curl 'https://llm-search-insights-api.onrender.com/api/v1/analyze/{analysis_id}/status'

# Get results
curl 'https://llm-search-insights-api.onrender.com/api/v1/analyze/{analysis_id}'
```

---

### **Error Handling**

#### Standard Error Response Format
```json
{
  "error": "ErrorType",
  "details": {
    "message": "Human-readable error description",
    "additional_info": "Any additional context"
  }
}
```

#### Common Error Types
- **`ValidationError`** - Request format or validation issues
- **`NotFound`** - Requested resource not found
- **`InternalError`** - Server processing errors

#### HTTP Status Codes
- **`200 OK`** - Successful response
- **`202 Accepted`** - Job successfully queued
- **`400 Bad Request`** - Invalid request format
- **`404 Not Found`** - Resource not found
- **`422 Validation Error`** - Request validation failed
- **`500 Internal Server Error`** - Server processing error

---

### **Best Practices**

#### 1. **Asynchronous Processing**
- Always implement proper polling mechanisms
- Use exponential backoff for status checks
- Handle timeouts gracefully

#### 2. **Error Handling**
- Implement comprehensive error handling
- Log errors for debugging
- Provide user-friendly error messages

#### 3. **Rate Limiting**
- Respect API rate limits
- Implement request throttling
- Use appropriate polling intervals

#### 4. **Data Validation**
- Validate research questions before submission
- Ensure proper error handling for validation failures
- Implement client-side validation

---

### **Use Cases**

#### 1. **Market Research**
- Competitive analysis
- Brand visibility assessment
- Industry trend analysis

#### 2. **Content Creation**
- Research-based content generation
- Topic exploration
- Source material analysis

#### 3. **Business Intelligence**
- Market positioning insights
- Competitor analysis
- Industry benchmarking

#### 4. **Academic Research**
- Literature review assistance
- Research question exploration
- Source synthesis

---

## Prerequisites (If you wanna use the CLI)

- Python 3.10+
- A virtual environment (recommended)
- Environment variables (see below)

## Installation

```bash
# Clone
git clone https://github.com/SUKESH127-art/LLM-search-insights-api.git
cd LLM-search-insight-api

# Create venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install deps
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root (same directory as `requirements.txt`).

```env
# Database (defaults to SQLite if not provided). Example values:
# SQLite (relative to working dir):
# DATABASE_URL=sqlite+aiosqlite:///./llm_insights.db
# PostgreSQL example:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
DATABASE_URL=sqlite+aiosqlite:///./llm_insights.db

# Cache TTL (hours) for analysis expiration
CACHE_TTL_HOURS=24

# External services (required for real API calls)
OPENAI_API_KEY=your_openai_api_key
BRIGHTDATA_API_KEY=your_brightdata_api_key
```

Notes:
- If `DATABASE_URL` is not set, the app defaults to `sqlite+aiosqlite:///./llm_insights.db` relative to the current working directory (when you run the server from `src/`, the DB file will be created there).
- The CLI and API are decoupled; only the API needs the OpenAI/BrightData keys. If absent, startup will warn or fail depending on code paths.

## Using the CLI Client

**Important**: The CLI must be run from the **project root** (where `requirements.txt` is located), not from the `src/` directory. Ensure the API server is running first.

```bash
# From project root (NOT from src/)
source venv/bin/activate
python cli/analyze.py "What is the future of AI in software development?"
```

The CLI will:
- Submit a job
- Show a live progress bar
- Print the final results and visualization data

## Development Notes

- The analysis pipeline is modular:
  - `collector.py`: SERP collection and LLM summarization
  - `processor.py`: Post-collection processing (placeholder pass-through)
  - `visualizer.py`: Converts analysis into structured visualization via LLM
  - `orchestrator.py`: Coordinates the end-to-end workflow
- The API schedules `run_full_analysis` as a background task when you submit a job.

## Troubleshooting

- Address already in use: Stop any prior uvicorn process or change the port:
  ```bash
  # Find and kill uvicorn (macOS/Linux)
  pkill -f "uvicorn main:app" || true
  # Or run on a different port
  uvicorn main:app --reload --port 8001
  ```
- Missing API keys: Set `OPENAI_API_KEY` and `BRIGHTDATA_API_KEY` in your environment or `.env`.
- SQLite file location: If using the default `DATABASE_URL`, the DB is created in the current working directory (e.g., `src/`).
- CLI not found: Make sure you're running the CLI from the project root, not from the `src/` directory.

## License

This project is open source under the MIT License.
