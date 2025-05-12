# RemodelAI Implementation Plan for CursorAI

## Overview

This implementation plan is specifically designed for CursorAI to follow when building the RemodelAI project. It emphasizes the strict requirement to NOT modify the frontend UI/UX and focuses on backend implementation.

## Critical Instructions

**DO NOT MODIFY THE FRONTEND UI/UX**
- The frontend from V0 export is final and approved
- Only implement backend integration
- Do not suggest UI improvements
- Do not change styles or components
- Only modify API endpoints and data fetching logic

## Phase 1: Project Setup

### Task 1.1: Initialize Backend Structure

Create the following directory structure:
```
remodel-ai-backend/
├── main.py
├── config.py
├── schemas.py
├── requirements.txt
├── vercel.json
├── .env.example
├── api/
│   ├── __init__.py
│   ├── chat.py
│   ├── estimate.py
│   └── export.py
├── services/
│   ├── __init__.py
│   ├── chat_service.py
│   ├── estimate_service.py
│   ├── rag_service.py
│   └── pdf_service.py
└── scripts/
    └── load_data.py
```

### Task 1.2: Install Dependencies

Create `requirements.txt` with:
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
openai==1.3.0
langchain==0.0.350
langchain-community==0.0.10
langchain-openai==0.0.5
pinecone-client==2.2.4
pandas==2.1.3
numpy==1.25.2
reportlab==4.0.7
python-dotenv==1.0.0
httpx==0.25.2
```

## Phase 2: Core Configuration

### Task 2.1: Implement config.py

```python
from pydantic_settings import BaseSettings
from typing import Dict, Any

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    pinecone_api_key: str
    pinecone_index: str = "remodel-ai-mvp"
    serp_api_key: str = ""
    
    # URLs
    frontend_url: str = "http://localhost:3000"
    
    # OpenAI Settings
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-ada-002"
    
    class Config:
        env_file = ".env"

settings = Settings()

# In-memory storage for MVP
estimates_cache: Dict[str, Any] = {}
chat_sessions: Dict[str, list] = {}
```

### Task 2.2: Implement schemas.py

Implement all Pydantic models with proper validation:
- ProjectDetails with city validation (SD/LA only)
- ChatRequest/Response
- EstimateRequest/Response
- CostBreakdown
- ExportRequest/Response

**Critical**: Include validators for city restriction to San Diego and Los Angeles only.

### Task 2.3: Data Preprocessing

Before implementing services, preprocess the CSV data:

1. **Standardize locations** - Map variations like "LA", "L.A." to "Los Angeles"
2. **Standardize project types** - Map to enum values in schemas.py
3. **Create metadata flags** - Mark which projects are eligible for cost estimates
4. **Clean cost data** - Ensure consistency in data types

Add to data loading script:
```python
def preprocess_data(df):
    # Standardize locations
    location_mapping = {
        'LA': 'Los Angeles',
        'L.A.': 'Los Angeles',
        'SD': 'San Diego'
    }
    
    # Flag CA projects for cost eligibility
    df['is_california'] = df['Location'].isin(['San Diego', 'Los Angeles'])
    
    return df
```

## Phase 3: Service Layer Implementation

### Task 3.1: Implement RAG Service

**Critical Requirements**:
1. Implement California construction expert system prompt
2. Add topic filtering - ONLY construction queries
3. Enforce geographic restrictions
4. Configure Pinecone vector database
5. Set up OpenAI embeddings

System prompt MUST include:
```python
SYSTEM_PROMPT = """
You are a California residential construction expert AI assistant. 

EXPERTISE AREAS:
- Property zoning and feasibility analysis
- Residential design (economy, standard, luxury)
- California building codes and regulations
- Construction cost estimation
- Financing options
- Material selection and costs
- Permit requirements and processes
- ADU regulations
- Energy efficiency and Title 24 compliance

STRICT RULES:
1. ONLY discuss California residential construction topics
2. For non-California queries: "We currently serve California only"
3. For specific cost estimates: Only provide for San Diego and Los Angeles
4. REJECT non-construction queries
5. Always cite confidence levels for estimates
"""
```

### Task 3.2: Implement Chat Service

Requirements:
1. Query validation for construction topics
2. Geographic scope checking
3. Session management
4. Message history tracking

Implement validation pattern:
```python
async def process_chat_message(message: str, session_id: str):
    # 1. Validate query scope
    if not is_construction_related(message):
        return CONSTRUCTION_ONLY_RESPONSE
    
    # 2. Check geographic constraints
    location = extract_location(message)
    if location and not is_california(location):
        return OUT_OF_STATE_RESPONSE
    
    # 3. Process valid construction query
    return await rag_service.get_response(message)
```

### Task 3.3: Implement Estimate Service

Requirements:
1. Project detail validation
2. Cost calculation with breakdown (40/35/5/20)
3. LA pricing adjustment (+12%)
4. Timeline calculation
5. Similar project retrieval

### Task 3.4: Implement PDF Service

Requirements:
1. Professional PDF layout
2. Cost breakdown tables
3. Timeline visualization
4. 30-day validity period

## Phase 4: API Implementation

### Task 4.1: Implement API Endpoints

Create all API endpoints following the exact specifications:

**Chat Endpoints**:
- POST /api/v1/chat
- GET /api/v1/chat/sessions/{session_id}/history

**Estimate Endpoints**:
- POST /api/v1/estimate
- GET /api/v1/estimate/{estimate_id}

**Export Endpoints**:
- POST /api/v1/export
- GET /api/v1/export/download/{estimate_id}

### Task 4.2: Implement Main Application

Create main.py with:
1. FastAPI initialization
2. CORS configuration
3. Router registration
4. Health endpoints

## Phase 5: Data Integration

### Task 5.1: Implement Data Loading Script

Create scripts/load_data.py to:
1. Load CSV data (888 projects)
2. Preprocess and standardize data
3. Create embeddings
4. Store in Pinecone with proper metadata
5. Verify data integrity

**Data Preprocessing Steps**:
```python
def preprocess_data(self, df):
    # 1. Standardize locations
    df['Location'] = df['Location'].apply(self.standardize_location)
    
    # 2. Standardize project types
    df['Remodel Type'] = df['Remodel Type'].apply(self.standardize_project_type)
    
    # 3. Clean cost data
    df['Average Cost (High)'] = df['Average Cost (High)'].astype(float)
    
    # 4. Add metadata flags
    df['is_california'] = df['Location'].isin(['San Diego', 'Los Angeles'])
    
    return df

def prepare_documents(self, df):
    documents = []
    
    for idx, row in df.iterrows():
        # Create document with location metadata
        doc = {
            'id': f'doc_{idx}',
            'content': self.format_content(row),
            'metadata': {
                'location': row['Location'],
                'is_california': row['is_california'],
                'is_cost_eligible': row['Location'] in ['San Diego', 'Los Angeles'],
                # ... other metadata
            }
        }
        documents.append(doc)
    
    return documents
```

**Important**: Use metadata filters in Pinecone to ensure only SD/LA projects are used for specific cost estimates, while allowing all projects for general construction knowledge.

## Phase 6: Testing

### Task 6.1: Create Test Scripts

Implement test_api.py with tests for:
1. Chat functionality
2. Estimate generation
3. PDF export
4. Error handling

## Phase 7: Frontend Integration

### Task 7.1: Update API Endpoints

**DO NOT MODIFY UI COMPONENTS**

Only update:
1. API base URL configuration
2. Endpoint paths to match backend
3. Request/response handling

## Implementation Order

1. **Day 1**: Project setup and configuration
2. **Day 2**: RAG service implementation
3. **Day 3**: Service layer completion
4. **Day 4**: API endpoints
5. **Day 5**: Data integration
6. **Day 6**: Testing and debugging
7. **Day 7**: Frontend integration

## Critical Validation Points

1. **Geographic Validation**:
   - Only San Diego and Los Angeles for estimates
   - California-wide for general advice
   - Reject all other locations

2. **Topic Validation**:
   - Only residential construction topics
   - Reject medical, weather, news, trivia
   - Polite redirection for off-topic

3. **Frontend Preservation**:
   - NO changes to UI components
   - NO style modifications
   - Only API integration changes

## Error Handling Requirements

1. Implement proper error messages
2. Log all errors with context
3. Graceful degradation for external API failures
4. User-friendly error responses

## Security Requirements

1. Environment variable management
2. Input validation on all endpoints
3. Rate limiting implementation
4. CORS configuration

## Performance Requirements

1. Response times: Chat < 2s, Estimate < 5s, PDF < 3s
2. Caching for material prices
3. Session management optimization

## Deployment Preparation

1. Create vercel.json
2. Update environment variables
3. Remove debug code
4. Test all endpoints

## Final Checklist

- [ ] All services implemented with proper validation
- [ ] API endpoints match specification exactly
- [ ] Frontend unchanged except API connections
- [ ] Geographic restrictions enforced
- [ ] Topic filtering active
- [ ] PDF generation working
- [ ] Error handling comprehensive
- [ ] Tests passing
- [ ] Ready for deployment