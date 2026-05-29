# Sargon — AI Investment Advisor

A full-stack investment advisory application with a FastAPI backend and Streamlit frontend.

## Features

| Module | What it does |
|---|---|
| **Risk Profiler** | 5-question questionnaire → Conservative / Moderate / Aggressive profile with suggested allocation |
| **Portfolio Optimizer** | Modern Portfolio Theory (max Sharpe) on any Yahoo Finance tickers, shows efficient frontier |
| **Tax Optimizer** | Identifies tax-loss harvesting opportunities and flags wash-sale risks |
| **Portfolio Rebalancer** | Compares current holdings to target allocation, recommends BUY / SELL / HOLD |

---

## Local Setup

### Prerequisites
- Python 3.11+
- pip

### 1 — Clone and install dependencies

```bash
git clone https://github.com/emiliomt/sargon.git
cd sargon

# Backend
pip install -r backend/requirements.txt

# Frontend
pip install -r requirements.txt
```

### 2 — Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API docs are at http://localhost:8000/docs

### 3 — Start the frontend (new terminal)

```bash
# from repo root
API_URL=http://localhost:8000 streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## Docker (local)

```bash
docker build -t sargon .
docker run -p 8501:8501 sargon
```

---

## Railway Deployment

1. **Sign up** at [railway.app](https://railway.app) and create a new project.
2. **Connect** your GitHub repo (`emiliomt/sargon`).
3. Railway auto-detects the `Dockerfile` and `railway.toml`.
4. **Set environment variables** (optional):
   - `PORT` — defaults to `8501`
5. Click **Deploy**. Railway builds the image, starts both FastAPI and Streamlit, and gives you a public URL.

The `start.sh` script launches the FastAPI backend on `localhost:8000` and Streamlit on `$PORT` (Railway's auto-assigned public port).

---

## API Reference

### `GET /risk-questions`
Returns the questionnaire options.

### `POST /risk-profile`
```json
{ "answers": { "age": 5, "horizon": 4, "reaction": 3, "income": 5, "goal": 5 } }
```

### `POST /optimize`
```json
{ "tickers": ["SPY", "QQQ", "GLD", "TLT"], "risk_free_rate": 0.05 }
```

### `POST /tax-optimize`
```json
{
  "holdings": [
    { "ticker": "AAPL", "shares": 10, "cost_basis": 180.0, "purchase_date": "2024-01-15" }
  ]
}
```

### `POST /rebalance`
```json
{
  "holdings": { "SPY": 20, "QQQ": 15, "GLD": 10 },
  "target_allocation": { "SPY": 50, "QQQ": 30, "GLD": 20 },
  "threshold": 5.0
}
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `API_URL` | `http://localhost:8000` | URL the Streamlit app uses to reach the FastAPI backend |
| `PORT` | `8501` | Port that Streamlit listens on |
