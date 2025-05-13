FROM python:3.11-slim
WORKDIR /app
# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
# Create directories
RUN mkdir -p /app/logs /app/exports
# Copy requirements first
COPY requirements.txt .
# Install requirements with verbose output to see what fails
RUN pip install --no-cache-dir --verbose -r requirements.txt || \
    (echo "Failed to install requirements, trying one by one..." && \
     cat requirements.txt | while read requirement; do \
       echo "Installing: $requirement" && \
       pip install --no-cache-dir "$requirement" || echo "Failed: $requirement"; \
     done)
# Copy application code
COPY . .
# Make Python output unbuffered
ENV PYTHONUNBUFFERED=1
# Create a debug startup script
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'echo "=== RemodelAI Starting ==="' >> /app/start.sh && \
    echo 'echo "Available environment variables:"' >> /app/start.sh && \
    echo 'env | sort' >> /app/start.sh && \
    echo 'echo "=== Starting application ==="' >> /app/start.sh && \
    echo 'exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}' >> /app/start.sh && \
    chmod +x /app/start.sh
CMD ["/app/start.sh"]
