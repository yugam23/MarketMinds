# MarketMinds

<div align="center">

![MarketMinds](https://img.shields.io/badge/MarketMinds-AI%20Predictions-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-green?style=flat-square&logo=python)
![React](https://img.shields.io/badge/React-18-blue?style=flat-square&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-teal?style=flat-square&logo=fastapi)

- **Sentiment-augmented price prediction platform for Indian Stocks (NSE/BSE).**
- **Secure Authentication** - JWT-based auth with refresh tokens and rate limiting
- **LSTM Neural Network** - Deep learning model for time-series price prediction
- **FinBERT Sentiment Analysis** - Financial domain NLP for news sentiment scoring
- **TradingView-Grade Charts** - Interactive candlestick charts with lightweight-charts
- **Real-time Predictions** - Next-day price forecasts with confidence intervals (INR)
- **Production Ready** - Dockerized with Nginx, Prometheus monitoring, and Sentry tracking
- **Multi-Asset Support** - NSE/BSE Stocks (RELIANCE, TCS, HDFC, etc.)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE (React)                  │
│  - TradingView Charts  - Asset Selector  - Prediction UI   │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────────┐
│                  FASTAPI BACKEND (Python)                   │
│  Endpoints: /prices | /sentiment | /headlines | /predict   │
└───┬─────────────────┬────────────────────┬──────────────────┘
    │                 │                    │
┌───▼────┐     ┌──────▼────────┐    ┌─────▼──────┐
│Database│     │ Sentiment     │    │   LSTM     │
│(Postgres)    │ Engine        │    │   Model    │
│              │ (FinBERT)     │    │ (TensorFlow)│
└──────────────┴───────────────┴────┴────────────┘
```

## 📦 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/marketminds.git
cd marketminds

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/docs
```

### Option 2: Local Development

**Backend:**

```bash
cd server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (Required)
alembic upgrade head

# Start server
uvicorn server.main:app --reload --port 8000
```

**Monitoring (Optional):**

- prometheus: http://localhost:8000/metrics
- health: http://localhost:8000/api/health

````

**Frontend:**

```bash
cd client

# Install dependencies
npm install

# Start development server
npm run dev
````

## 🔌 API Endpoints

| Method | Endpoint                          | Description         | Response Time |
| ------ | --------------------------------- | ------------------- | ------------- |
| GET    | `/api/health`                     | Health check        | <100ms        |
| GET    | `/api/assets`                     | List tracked assets | <200ms        |
| GET    | `/api/prices/{symbol}?days=30`    | OHLC price data     | <500ms        |
| GET    | `/api/sentiment/{symbol}?days=30` | Sentiment scores    | <500ms        |
| GET    | `/api/headlines/{symbol}`         | News headlines      | <500ms        |
| POST   | `/api/predict`                    | Generate prediction | <5s           |

## 📁 Project Structure

```
marketminds/
├── server/                 # FastAPI Backend
│   ├── api/               # API routes
│   ├── core/              # Config, database
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── ml/                # ML models
│   └── tests/             # Backend tests
├── client/                 # React Frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   ├── services/      # API client
│   │   └── types/         # TypeScript types
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🧪 Testing

**Backend:**

```bash
cd server
pytest --cov=. --cov-report=term-missing
```

**Frontend:**

```bash
cd client
npm run test
npm run typecheck
```

## 📊 Tech Stack

| Layer     | Technology               | Purpose                   |
| --------- | ------------------------ | ------------------------- |
| Frontend  | React 18 + TypeScript    | UI Components             |
| Styles    | Tailwind CSS + Framer    | Glassmorphism Theme       |
| Charts    | Recharts                 | Interactive Visualization |
| Backend   | FastAPI + Python 3.11    | Async REST API            |
| Database  | PostgreSQL / SQLite      | Data persistence          |
| ML        | TensorFlow + HuggingFace | LSTM + FinBERT            |
| Cache     | Redis                    | Rate limiting             |
| Container | Docker + Compose         | Deployment                |

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [FinBERT](https://huggingface.co/ProsusAI/finbert) - Financial sentiment model
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance data
- [lightweight-charts](https://github.com/tradingview/lightweight-charts) - TradingView charts
