# LLM Search Insight API

A FastAPI-based service that runs an LLM-powered research workflow: it collects web signals, synthesizes them with an LLM, and produces a structured visualization of brand visibility. The project now uses a standard Python `src/` layout and a separate `cli/` HTTP client.

## Features

- **FastAPI + Async**: High performance API with async SQLAlchemy
- **Modular analysis pipeline**: `collector`, `processor`, `visualizer`, orchestrated by `orchestrator`
- **Job tracking**: Create jobs, poll status, fetch final results
- **SQLite by default**: Pluggable via `DATABASE_URL`
- **Decoupled CLI**: Separate async HTTP client using `httpx` and `rich`

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

## Prerequisites

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

## Running the API Server

**Important**: Run the server from the `src/` directory so imports resolve correctly for the `src` layout:

```bash
# From project root
source venv/bin/activate
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open the interactive docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

- `POST /api/v1/analyze`
  - Request body:
    ```json
    { "research_question": "What are the best frontend frameworks for 2024?" }
    ```
  - Response:
    ```json
    { "analysis_id": "<uuid>", "status": "PROCESSING" }
    ```

- `GET /api/v1/analyze/{analysis_id}/status`
  - Response:
    ```json
    { "status": "PROCESSING", "progress": 42, "current_step": "...", "error_message": null }
    ```

- `GET /api/v1/analyze/{analysis_id}`
  - Response (once complete):
    ```json
    {
      "analysis_id": "<uuid>",
      "research_question": "...",
      "status": "COMPLETE",
      "completed_at": "2025-01-01T00:00:00Z",
      "web_results": { "source": "...", "content": "...", "timestamp": "...", "confidence_score": 0.95 },
      "chatgpt_simulation": { "simulated_response": "...", "identified_brands": ["..."] },
      "visualization": {
        "chart_type": "bar_chart_brand_visibility",
        "title": "Top 5 Brands by LLM Search Visibility",
        "x_axis_label": "Brand Name",
        "y_axis_label": "Visibility Score (1-100)",
        "top_5_brands": ["..."],
        "brand_scores": [ { "brand_name": "...", "visibility_score": 95, "rank": 1, "mentions": 8 } ],
        "methodology_explanation": "..."
      }
    }
    ```

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
