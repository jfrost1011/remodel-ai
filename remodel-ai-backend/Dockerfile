FROM python:3.11-slim
WORKDIR /app
# Install system dependencies - add more that might be needed
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
# Copy requirements first
COPY requirements.txt .
# Install Python dependencies with verbose output
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt -v
# Copy the rest of the application
COPY . .
# Set the PORT environment variable
ENV PORT=8000
# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
