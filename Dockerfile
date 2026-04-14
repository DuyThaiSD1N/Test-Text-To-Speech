# Railway-optimized Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Railway automatically sets PORT env variable
EXPOSE 8002

# Start server - Railway will inject PORT at runtime
CMD ["sh", "-c", "uvicorn simple_server:app --host 0.0.0.0 --port ${PORT:-8002}"]
