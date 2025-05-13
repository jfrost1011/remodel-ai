FROM python:3.11-slim
WORKDIR /app
# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
# Install Python dependencies one by one
RUN pip install --upgrade pip setuptools wheel
# Core packages
RUN pip install fastapi==0.109.0
RUN pip install "uvicorn[standard]==0.25.0"
RUN pip install pydantic==2.5.0
RUN pip install pydantic-settings==2.1.0
RUN pip install python-dotenv==1.0.0
# OpenAI and LangChain
RUN pip install openai==1.3.0
RUN pip install langchain==0.0.350
RUN pip install langchain-community==0.0.10
RUN pip install langchain-openai==0.0.5
# Pinecone
RUN pip install pinecone-client==2.2.4
# Copy the application
COPY . .
# Run the application
CMD python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
