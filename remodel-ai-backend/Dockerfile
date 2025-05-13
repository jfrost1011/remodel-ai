FROM python:3.11-slim
WORKDIR /app
# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
# Create directories
RUN mkdir -p /app/logs /app/exports
# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
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
