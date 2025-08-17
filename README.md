# LLM Search Insight API

A FastAPI-based API service that provides intelligent search insights using Large Language Models (LLMs). This service processes research questions and returns comprehensive analysis results with caching capabilities.

## Features

- **Async FastAPI Framework**: Built with FastAPI for high-performance async operations
- **SQLAlchemy 2.0**: Modern database ORM with async support
- **Intelligent Caching**: Configurable TTL-based caching for analysis results
- **Status Tracking**: Real-time progress monitoring for analysis tasks
- **Error Handling**: Comprehensive error handling and logging
- **Environment Configuration**: Flexible configuration via environment variables

## Project Structure

```
llm-search-insight-api/
├── analysis/           # Analysis module components
│   ├── __init__.py    # Module initialization
│   ├── core.py        # Core analysis logic
│   └── validator.py   # Data validation utilities
├── models.py          # SQLAlchemy data models
├── database.py        # Database connection and configuration
├── schemas.py         # Pydantic schemas for API
├── main.py            # FastAPI application entry point
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation
```

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Environment variables configured

## Installation

1. Clone the repository:
```bash
git clone https://github.com/SUKESH127-art/LLM-search-insights-api.git
cd llm-search-insights-api
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Environment Variables

Create a `.env` file with the following variables:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
CACHE_TTL_HOURS=24
```

## Usage

1. Start the application:
```bash
uvicorn main:app --reload
```

2. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

- `POST /analysis/`: Create a new analysis request
- `GET /analysis/{id}`: Retrieve analysis results
- `GET /analysis/`: List all analyses
- `DELETE /analysis/{id}`: Delete an analysis

## Development

This project uses:
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy 2.0**: Next-generation Python ORM
- **Pydantic**: Data validation using Python type annotations
- **Alembic**: Database migration tool
- **Uvicorn**: ASGI server for running FastAPI applications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For questions and support, please open an issue on GitHub.
