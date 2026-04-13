# Use Python 3.11 slim image (specific version)
FROM python:3.11.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies with prefer-binary to avoid Rust compilation
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application code and static files
COPY simple_server.py .
COPY simple_ui ./simple_ui
COPY src ./src
COPY .env.example .env

# Create logs directory
RUN mkdir -p logs

# Expose port (Render will override with $PORT)
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8002}/health || exit 1

# Run the application
CMD ["python", "simple_server.py"]
