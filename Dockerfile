# Use Python 3.11 slim image
FROM python:3.11.9-slim

# Set working directory
WORKDIR /app

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install dependencies in order to use cached wheels
# Install pydantic and pydantic-core first with specific versions that have wheels
RUN pip install --only-binary=:all: "pydantic==2.5.3" "pydantic-core==2.14.6" || \
    pip install "pydantic==2.5.3" "pydantic-core==2.14.6"

# Install remaining dependencies
RUN pip install -r requirements.txt

# Copy application code and static files
COPY simple_server.py .
COPY simple_ui ./simple_ui
COPY src ./src
COPY .env.example .env

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8002}/health || exit 1

# Run the application
CMD ["python", "simple_server.py"]
