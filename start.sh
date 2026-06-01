#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8501}"
echo "Starting Sargon (Streamlit on 0.0.0.0:${PORT}, FastAPI on 127.0.0.1:8000)"

# Start the FastAPI backend in the background
cd /app/backend
uvicorn main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait for the backend to become ready (up to 60s)
for _ in $(seq 1 60); do
  if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "Backend is ready"
    break
  fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "ERROR: Backend process exited unexpectedly" >&2
    exit 1
  fi
  sleep 1
done

if ! curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
  echo "ERROR: Backend failed to start within 60s" >&2
  exit 1
fi

# Start Streamlit as the main process (Railway tracks this PID)
cd /app
export API_URL="http://127.0.0.1:8000"
exec streamlit run app.py \
  --server.port "${PORT}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.fileWatcherType none \
  --browser.gatherUsageStats false
