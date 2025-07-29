# TestPilot AI Backend

FastAPI-based backend for AI-powered test generation and execution.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Run the development server:**
   ```bash
   python main.py
   # Or with uvicorn directly:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Project Structure

```
backend/
├── app/
│   ├── api/          # API routes and endpoints
│   ├── config.py     # Application configuration
│   ├── models/       # Data models and schemas
│   └── services/     # Business logic and external services
├── main.py           # FastAPI application entry point
├── requirements.txt  # Python dependencies
└── .env.example     # Environment variables template
```

## API Endpoints

- `GET /` - API information
- `GET /healthcheck` - Health check endpoint

## Development

- **Linting:** `black . && isort . && flake8 .`
- **Testing:** `pytest`
- **Type checking:** `mypy .`

## Docker

Build and run with Docker:

```bash
docker build -t testpilot-backend .
docker run -p 8000:8000 testpilot-backend
``` 