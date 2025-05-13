FROM python:3.11-slim
WORKDIR /app
# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
# Copy requirements
COPY requirements.txt .
# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
# Copy the application
COPY . .
# Run the application  
CMD python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
