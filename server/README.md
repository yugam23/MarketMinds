# MarketMinds Backend

FastAPI-based backend for MarketMinds.

## Features

- **Authentication**: JWT access/refresh tokens.
- **ML Pipeline**: LSTM training and FinBERT inference.
- **Data Ingestion**: Yahoo Finance and NewsAPI integration.
- **Monitoring**: Prometheus metrics, Sentry error tracking, Structured logging.
- **Rate Limiting**: Redis-backed rate limiting using `slowapi`.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run migrations:

   ```bash
   alembic upgrade head
   ```

3. Start server:
   ```bash
   uvicorn server.main:app --reload
   ```

## Testing

```bash
pytest --cov=.
```

## API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI Spec: `openapi.json` (generated via `scripts/export_openapi.py`)
