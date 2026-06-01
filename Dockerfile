FROM python:3.11-slim

# System deps for scipy / numpy builds
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend deps first (better layer caching)
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install frontend deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY backend/ backend/
COPY app.py .
COPY start.sh .
COPY .streamlit/ .streamlit/
RUN chmod +x start.sh

# Railway injects PORT at runtime — do not hardcode it here
CMD ["bash", "start.sh"]
