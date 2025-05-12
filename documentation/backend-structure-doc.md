# RemodelAI Backend Structure Document

## Overview

This document provides a detailed breakdown of the backend architecture for RemodelAI, including file organization, service layers, API design, and data flow.

## Directory Structure

```
remodel-ai-backend/
├── main.py                  # FastAPI application entry point
├── config.py               # Configuration and environment variables
├── schemas.py              # Pydantic models for request/response
├── requirements.txt        # Python dependencies
├── vercel.json            # Vercel deployment configuration
├── .env                   # Environment variables (not in git)
├── .env.example           # Example environment template
│
├── api/                   # API route handlers
│   ├── __init__.py
│   ├── chat.py           # Chat endpoint handlers
│   ├── estimate.py       # Estimate endpoint handlers
│   └── export.py         # Export/PDF endpoint handlers
│
├── services/              # Business logic layer
│   ├── __init__.py
│   ├── chat_service.py   # Chat processing logic
│   ├── estimate_service.py # Cost estimation logic
│   ├── rag_service.py    # RAG/AI integration
│   └── pdf_service.py    # PDF generation logic
│
├── scripts/               # Utility scripts
│   ├── load_data.py      # Load data into Pinecone
│   ├── collection/       # Data collection scripts
│   ├── evaluation/       # RAGAS evaluation scripts
│   └── training/         # Fine-tuning scripts
│
├── exports/              # Generated PDF exports (gitignored)
├── logs/                 # Application logs (gitignored)
└── tests/                # Test files
    ├── __init__.py
    ├── test_api.py
    └── test_services.py
```

## Core Components

### 1. Entry Point (main.py)

The FastAPI application configuration and middleware setup:

```python
# Key responsibilities:
- FastAPI app initialization
- CORS middleware configuration
- Router registration
- Health check endpoints
- Global exception handling
```

### 2. Configuration (config.py)

Centralized configuration management:

```python
# Manages:
- Environment variables
- API keys (OpenAI, Pinecone, SerpAPI)
- Application settings
- In-memory caches (session, estimates)
```

### 3. Data Models (schemas.py)

Pydantic models for type safety and validation:

```python
# Key models:
- ChatRequest/Response
- EstimateRequest/Response
- ProjectDetails (with validation)
- CostBreakdown
- TimelineBreakdown
- ExportRequest/Response
```

## Service Layer Architecture

### 1. RAG Service (rag_service.py)

Core AI functionality:

```python
# Responsibilities:
- Pinecone vector database management
- OpenAI embeddings generation
- LangChain QA chain setup
- System prompt configuration
- Query processing with constraints
```

Key Features:
- California construction expert system prompt
- Topic filtering for construction-only queries
- Geographic validation
- Confidence scoring
- Separate handling for cost estimates vs. general advice

**Important Data Handling**:
```python
# In retrieval logic:
def get_relevant_projects(self, query, location=None):
    # For cost estimates - only use CA projects
    if location in ['San Diego', 'Los Angeles']:
        filter_dict = {'is_cost_eligible': True, 'location': location}
    else:
        # For general construction advice, use all data
        filter_dict = {}
    
    return self.vectorstore.similarity_search(
        query, 
        k=5,
        filter=filter_dict
    )
```

### 2. Chat Service (chat_service.py)

Conversational interface management:

```python
# Responsibilities:
- Session management
- Message history tracking
- Query validation
- Response formatting
- Topic boundary enforcement
```

Key Features:
- Construction-only topic filtering
- Geographic scope validation
- Session persistence
- Context-aware responses

### 3. Estimate Service (estimate_service.py)

Cost estimation logic:

```python
# Responsibilities:
- Project detail processing
- Similar project retrieval
- Cost calculation
- Timeline estimation
- Confidence scoring
```

Key Features:
- LA vs SD pricing adjustments
- Material cost integration
- Breakdown calculations (40/35/5/20)
- Similar project matching

### 4. PDF Service (pdf_service.py)

Report generation:

```python
# Responsibilities:
- PDF layout creation
- Data formatting
- Table generation
- Export management
```

Key Features:
- Professional layout
- Cost breakdown tables
- Timeline visualization
- 30-day validity period

## API Layer Design

### 1. Chat Endpoints (api/chat.py)

```
POST /api/v1/chat
- Handles conversational interactions
- Validates construction scope
- Manages session state

GET /api/v1/chat/sessions/{session_id}/history
- Retrieves conversation history
```

### 2. Estimate Endpoints (api/estimate.py)

```
POST /api/v1/estimate
- Creates new cost estimates
- Validates location (SD/LA only)
- Returns detailed breakdown

GET /api/v1/estimate/{estimate_id}
- Retrieves existing estimates
```

### 3. Export Endpoints (api/export.py)

```
POST /api/v1/export
- Generates PDF reports
- Supports multiple formats (future)

GET /api/v1/export/download/{estimate_id}
- Downloads generated PDFs
```

## Data Flow

### 1. Chat Flow

```mermaid
User Input → Chat API → Query Validation → RAG Service → Response Generation → User
                    ↓
                Session Storage
```

### 2. Estimate Flow

```mermaid
Project Details → Estimate API → RAG Query → Similar Projects → Cost Calculation → Response
                            ↓                              ↓
                        Validation                   Material Pricing
```

### 3. Export Flow

```mermaid
Estimate ID → Export API → Retrieve Data → PDF Generation → File Storage → Download
```

## External Integrations

### 1. OpenAI Integration

- **Model**: GPT-4o-mini
- **Embeddings**: text-embedding-ada-002
- **Purpose**: Chat responses, query understanding

### 2. Pinecone Integration

- **Index**: remodel-ai-mvp
- **Dimension**: 1536
- **Purpose**: Vector similarity search

### 3. SerpAPI Integration

- **Engine**: Home Depot Product Search
- **Purpose**: Real-time material pricing
- **Key Parameters**:
  - `q`: Search query (product name)
  - `location`: Geographic location
  - `engine`: "home_depot"
  - `lowe's_zip`: ZIP code for accurate local pricing
  
**Implementation Example**:
```python
from serpapi import GoogleSearch

class MaterialPriceService:
    def get_material_prices(self, materials: List[str], location: str):
        # Map city to ZIP code
        zip_codes = {
            'San Diego': '92101',
            'Los Angeles': '90001'
        }
        
        params = {
            'engine': 'home_depot',
            'q': material,
            'lowe's_zip': zip_codes.get(location, '92101'),
            'api_key': self.api_key
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Extract product prices
        if 'products' in results:
            for product in results['products']:
                price = product.get('price', {}).get('current', 0)
                unit = product.get('unit', '')
                availability = product.get('availability', {})
```

## Error Handling

### 1. API Level

- HTTP status codes
- Detailed error messages
- Request validation errors

### 2. Service Level

- Try-catch blocks
- Logging with context
- Graceful degradation

### 3. External API Failures

- Retry logic
- Fallback options
- Cache utilization

## Caching Strategy

### 1. Session Cache

- In-memory dictionary
- Session-based chat history
- Temporary storage

### 2. Estimate Cache

- In-memory storage
- Estimate results
- Quick retrieval

### 3. Material Price Cache

- Time-based expiration
- API response caching
- Performance optimization

## Security Considerations

### 1. Input Validation

- Pydantic models
- Schema validation
- SQL injection prevention

### 2. API Security

- CORS configuration
- Rate limiting
- API key management

### 3. Data Protection

- No PII storage
- Secure API communication
- Environment variables

## Testing Structure

### 1. Unit Tests

- Service function tests
- Utility function tests
- Model validation tests

### 2. Integration Tests

- API endpoint tests
- External API mocking
- Database operations

### 3. End-to-End Tests

- Full flow testing
- Performance benchmarks
- Error scenarios

## Deployment Configuration

### 1. Vercel Setup

- Python runtime
- Function configuration
- Environment variables

### 2. Production Settings

- API rate limits
- Error tracking
- Performance monitoring

## Future Enhancements

### 1. Database Integration

- PostgreSQL for persistence
- Redis for caching
- Migration scripts

### 2. Advanced Features

- WebSocket support
- Background jobs
- Advanced analytics

### 3. Scalability

- Load balancing
- Microservices
- Container orchestration