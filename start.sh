#!/usr/bin/env bash
set -e

# Start the FastAPI backend on localhost:8000 in the background
cd /app/backend
uvicorn main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait briefly so the backend is up before Streamlit starts
sleep 2

# Start the Streamlit frontend on the Railway-assigned PORT (default 8501)
cd /app
export API_URL="http://127.0.0.1:8000"
streamlit run app.py \
  --server.port "${PORT:-8501}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false

# If Streamlit exits, clean up
kill $BACKEND_PID 2>/dev/null || true
