Below is an **updated, comprehensive PRD** that merges your existing document with additional details for alignment, clarity on tasks, and references to example code/responses. **No new code** is included—only references to code snippets you've already provided in prior documentation.

---

# RemodelAI Product Requirements Document (PRD)

## 1. Project Overview

We are building an AI-powered construction cost estimation platform for **San Diego and Los Angeles** markets. The system leverages **888+ real remodeling projects** via a **Retrieval-Augmented Generation (RAG)** approach, providing instant cost estimates and project insights. Users interact with an AI assistant through a conversational UI, can view a detailed cost breakdown, and export professional PDFs.

### 1.1 Key Objectives

1. **Accurate Cost Estimation**

   * Leverage real historical data (888 projects).
   * Restrict location to SD and LA for MVP.
   * Return cost breakdown, confidence score, timeline.

2. **User-Friendly Chat & UI**

   * Frontend chat interface (Next.js 14 + Shadcn UI).
   * Seamless "Question -> Estimate -> PDF" flow.
   * Minimal friction for user input (city validation, etc.).

3. **Scalable & Extensible**

   * Ready to expand to more regions post-MVP.
   * Fine-tuning & iterative improvements via RAGAS.
   * Future contractor matching, advanced analytics, etc.

---

## 2. Technology Stack

* **Frontend**: Next.js 14 (already built), Shadcn UI, Tailwind CSS
* **Backend**: FastAPI (Python 3.9+), Deployed via Vercel
* **AI & Data**:

  * **LangChain** for RAG orchestration
  * **OpenAI GPT-4o-mini** for generative responses
  * **Pinecone** as the vector store (1536-d embeddings)
  * **SerpAPI** for real-time material pricing
  * **RAGAS** for retrieval QA evaluation
* **Data Processing**: Pandas, NumPy
* **PDF Generation**: ReportLab (or any PDF library)
* **Monitoring**: LangSmith for usage analytics
* **Testing**: Pytest + RAGAS baseline metrics

---

## 3. High-Level Tasks & Phases

The development plan is split into **7 phases**, aligning with 5 specific tasks you must complete.

1. **Phase 1** – Initial Setup (Basic project structure, environment)
2. **Phase 2** – Data Collection (Task 1)
3. **Phase 3** – RAG Application (Task 2)
4. **Phase 4** – RAGAS Baseline Evaluation (Task 3)
5. **Phase 5** – Fine-Tuning & Embeddings (Task 4)
6. **Phase 6** – Performance Assessment (Task 5)
7. **Phase 7** – Deployment & Testing

Where each task maps to:

* **Task 1**: Data Collection & API Selection (Phases 1–2)
* **Task 2**: Build RAG Application (Phase 3)
* **Task 3**: RAGAS Baseline Evaluation (Phase 4)
* **Task 4**: Fine-tune Embeddings (Phase 5)
* **Task 5**: Performance Assessment (Phase 6)

**Deployment** (Phase 7) is the final step to push everything to Vercel once you've validated performance.

---

## 4. Core Functionalities

### 4.1 Chat Interface

**Conversational AI Assistant**

* **Expert Scope**: California residential construction expert ONLY
* **Knowledge Areas**:
  - Property zoning and feasibility assessment
  - Design options (economy, standard, luxury)
  - Permitting requirements and processes
  - Cost estimation and budgeting
  - Financing options (construction loans, HELOCs, etc.)
  - Material selection and pricing
  - Space planning based on lot size and zoning
  - ADU regulations and requirements
  - Energy efficiency and California building codes
  - Timeline planning and project phases

* **Geographic Restriction**:
  - ONLY serves California residents
  - For out-of-state queries: "We're not available in [state] yet, but we're expanding soon!"
  - Focus cities: San Diego and Los Angeles (for cost estimates)
  - General California construction knowledge (for advisory)

* **Topic Boundaries**:
  - STRICTLY residential construction topics only
  - NO responses to: medical, weather, trivia, general knowledge, news, etc.
  - Default response for off-topic: "I'm specifically trained in California residential construction. I can help with remodeling, additions, ADUs, permits, costs, and financing. What construction questions can I answer for you?"

* **Initial Greeting**:
  `"Hello! I'm your California residential construction expert. I can help with remodeling projects, cost estimates, permits, zoning, design options, and financing. I specialize in San Diego and Los Angeles markets. What's your construction project?"

* **Example System Prompt for GPT-4o-mini**:
  ```
  You are an expert in California residential construction. Your knowledge includes:
  - Zoning laws and property feasibility
  - Design (economy to luxury)
  - Permitting and regulations
  - Cost estimation
  - Construction financing options
  - California building codes
  - ADU requirements
  - Material costs and selection
  
  IMPORTANT RULES:
  1. ONLY discuss residential construction in California
  2. For non-California locations: "We're not available in [location] yet, but we're expanding soon!"
  3. For cost estimates: Only provide specific numbers for San Diego and Los Angeles
  4. NEVER discuss topics outside construction (medical, weather, news, etc.)
  5. If asked about non-construction topics, respond: "I'm specifically trained in California residential construction..."
  ```

* **Frontend Code**: Unchanged from V0 export

**Project Details Collection**

* Modal or sidebar form from Shadcn UI
* Fields: `project_type`, `city`, `state`, `square_footage`, `additional_details`
* Validations with React Hook Form + Zod
* **Example Code**:

  ```tsx
  // ProjectDetailsModal with form fields
  // ...
  ```

### 4.2 Location Validation

* Only serve **San Diego** and **Los Angeles** (plus accepted synonyms "LA", "SD").
* Return error if user attempts other locations:
  *"We're not available in \[city] yet, but we're expanding soon!"*
* Validate at multiple levels (frontend form, schema, backend checks).

### 4.3 Cost Estimation Engine

**RAG-Based Approach**

* 5 relevant projects from Pinecone
* Base cost derived from those matches
* Adjust for location (LA \~12% higher)
* Incorporate material pricing from SerpAPI
* **Example Pseudocode** (from earlier references):

  ```python
  # def estimate_service(project_details):
  #   similar_projects = find_similar_projects(query)
  #   base_cost = average(similar_projects)
  #   if city == 'Los Angeles': base_cost *= 1.12
  #   # ...
  #   return final_estimate
  ```

**Cost Breakdown**

* Materials: 40%
* Labor: 35%
* Permits: 5%
* Other costs: 20%
* Return a confidence score, timeline, similar projects array.

### 4.4 External API Integration

**Material Pricing (SerpAPI)**

* Home Depot Product Search API for real-time prices
* Location-based pricing using ZIP codes
* Product availability and inventory status
* Structured product data extraction
* **Implementation Details**:
  - Use 'home_depot' engine
  - Pass ZIP code for accurate local pricing
  - Extract price, unit, availability
  - Cache results for performance

**Example API Call**:
```python
params = {
    'engine': 'home_depot',
    'q': 'kitchen cabinets',
    'lowe's_zip': '92101',  # San Diego ZIP
    'api_key': api_key
}
```

**GPT-4o-mini Integration**

* Powers natural language Q\&A
* Summarizes, clarifies, or extracts project info from user input
* Connects to the RAG pipeline for contextual answers

### 4.5 PDF Export

**Professional Estimate Report**

* Triggered from frontend "Download" button
* Returns a PDF with cost breakdown, timeline, confidence, relevant disclaimers
* Should be valid for 30 days
* **Example Layout** (from earlier references):

  ```python
  # generate_pdf_report(estimate_data):
  #   doc = ...
  #   story.append(...)
  #   doc.build(story)
  ```

### 4.6 Monitoring & Analytics

**LangSmith Integration**

* Track usage, requests, and model performance
* Provide debug logs for RAG steps

**RAGAS Evaluation**

* Evaluate context relevancy and factual correctness
* Baseline established in "Task 3"
* Fine-tuning improvements measured in "Task 5"

### 4.7 Chatbot Learning & Expansion

**Progressive Knowledge Enhancement**

* **Current State**: GPT-4o-mini with 888 project dataset
* **Future Learning Sources**:
  - Real-time material costs from multiple APIs
  - Contractor quotes database
  - Permit requirements per city/county
  - Zoning regulations database
  - Building code updates
  - Energy efficiency regulations
  - California construction law changes

* **Learning Pipeline**:
  1. Collect new data sources (quotes, APIs, regulations)
  2. Process and validate information
  3. Update RAG knowledge base
  4. Re-evaluate with RAGAS
  5. Deploy improved model

* **Knowledge Domains to Expand**:
  - County-specific permit requirements
  - Material cost variations by region
  - Labor cost databases
  - Financing institution partnerships
  - Green building incentives
  - Seismic retrofit requirements
  - Fire safety regulations
  - Water conservation mandates

---

## 5. Documentation & Examples

### 5.1 API Endpoints

1. **`POST /api/v1/chat`**

   * **Request**:

     ```json
     {
       "content": "I need a kitchen remodel",
       "role": "user",
       "session_id": "optional"
     }
     ```
   * **Response**:

     ```json
     {
       "message": "Sure! Which city are you located in?",
       "type": "text",
       "metadata": { "session_id": "session-123" }
     }
     ```

2. **`POST /api/v1/estimate`**

   * **Request**:

     ```json
     {
       "project_details": {
         "project_type": "kitchen_remodel",
         "city": "San Diego",
         "state": "CA",
         "square_footage": 200,
         "additional_details": "Modern with granite countertops"
       }
     }
     ```
   * **Response**:

     ```json
     {
       "estimate_id": "est_abc123",
       "total_cost": 45000.00,
       "cost_breakdown": {
         "materials": 18000.00,
         "labor": 15750.00,
         "permits": 2250.00,
         "other": 9000.00,
         "total": 45000.00
       },
       "confidence_score": 0.87,
       "timeline_days": 30,
       "similar_projects": []
     }
     ```

3. **`GET /api/v1/export/{estimate_id}`**

   * Returns **PDF file**
   * Content-Type: `application/pdf`

### 5.2 Location Validation Implementation

**Example** (reference code, no modification needed):

```python
@validator('city')
def validate_city(cls, v):
    allowed_cities = ["San Diego", "Los Angeles", "LA", "SD"]
    if v.upper() == "LA": return "Los Angeles"
    if v.upper() == "SD": return "San Diego"
    if v.title() not in allowed_cities:
        raise ValueError("We currently only serve San Diego and Los Angeles")
    return v.title()
```

### 5.3 RAG Implementation with Pinecone

**Example** (reference code snippet, no changes):

```python
# RAGService uses Pinecone + OpenAIEmbeddings
# ...
```

**System Prompt Configuration**:

```python
SYSTEM_PROMPT = """
You are a California residential construction expert AI assistant. 

EXPERTISE AREAS:
- Property zoning and feasibility analysis
- Residential design (economy, standard, luxury)
- California building codes and regulations
- Construction cost estimation
- Financing options (construction loans, HELOCs, cash-out refinancing)
- Material selection and costs
- Permit requirements and processes
- ADU (Accessory Dwelling Unit) regulations
- Energy efficiency and Title 24 compliance
- Seismic and fire safety requirements

STRICT RULES:
1. ONLY discuss California residential construction topics
2. For non-California queries: "We currently serve California only, but we're expanding to [state] soon!"
3. For specific cost estimates: Only provide for San Diego and Los Angeles
4. REJECT non-construction queries with: "I'm specialized in California residential construction. How can I help with your construction project?"
5. Always cite confidence levels for estimates
6. Reference similar projects when providing estimates

KNOWLEDGE BOUNDARIES:
- YES: Remodeling, additions, ADUs, permits, zoning, costs, financing, materials, codes
- NO: Commercial construction, medical, weather, news, entertainment, general trivia
"""
```

**Example Chat Service Enhancement**:

```python
def validate_query_scope(query: str) -> bool:
    """Validate if query is within construction scope"""
    construction_keywords = [
        'remodel', 'addition', 'adu', 'permit', 'cost', 
        'build', 'construction', 'contractor', 'design',
        'zoning', 'finance', 'loan', 'kitchen', 'bathroom'
    ]
    # Implementation to check if query relates to construction
    return any(keyword in query.lower() for keyword in construction_keywords)
```

### 5.4 Material Price Fetching with SerpAPI

**Example** (reference code snippet):

```python
# MaterialPriceService with get_home_depot_prices
# ...
```

### 5.5 Example Frontend Implementations

**Chat Interface**:

```tsx
// ChatInterface with Shadcn UI
// ...
```

**Project Details Form**:

```tsx
// ProjectDetailsModal
// ...
```

*(These remain unchanged in the final MVP frontend.)*

---

## 6. Implementation Guidelines

### 6.1 File Structure

A consolidated layout for quick reference:

```
remodel-ai/
├── remodel-ai-frontend/      # (V0 export - UI/UX final, do not modify)
├── remodel-ai-backend/
│   ├── main.py               # FastAPI entry point
│   ├── config.py             # Environment variables (API keys, etc.)
│   ├── schemas.py            # Pydantic models (requests/responses)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── estimate.py
│   │   └── export.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_service.py
│   │   ├── estimate_service.py
│   │   ├── rag_service.py
│   │   └── pdf_service.py
│   ├── scripts/
│   │   ├── collection/       # Data collection scripts (Task 1)
│   │   ├── evaluation/       # RAGAS baseline (Task 3)
│   │   ├── training/         # Fine-tuning data (Task 4)
│   │   └── load_data.py
│   ├── requirements.txt      # Python deps (fastapi, pinecone, etc.)
│   └── vercel.json           # Deployment config for Vercel
└── remodel-ai-data/
    ├── raw/
    ├── processed/
    └── cleaned_remodeling_data_1000.csv
```

**Note**:

* The `scripts/` folder holds all your **Task**-related code for data collection, fine-tuning, or RAGAS evaluation.
* The `api/` directory is for the **FastAPI routes**.
* The `services/` directory encloses the **business logic** (RAG, PDF, etc.).

### 6.2 Task Alignment

1. **Task 1: Data Collection & API Selection**

   * Scripts in `scripts/collection/` gather & clean data.
   * SerpAPI chosen for material pricing.

2. **Task 2: Build RAG Application**

   * `rag_service.py` integrates Pinecone, embeddings, GPT for retrieval.
   * Linking to the existing 888 projects dataset.

3. **Task 3: RAGAS Baseline Evaluation**

   * `scripts/evaluation/` for generating synthetic queries, measuring recall & accuracy.
   * RAGAS metrics used to set baseline.

4. **Task 4: Fine-tune Embeddings**

   * `scripts/training/` for generating positive/negative pairs, uploading to Hugging Face AutoTrain.
   * Replacing or augmenting default embeddings.

5. **Task 5: Performance Assessment**

   * Compare baseline vs. fine-tuned embeddings.
   * Document improvements & final results.

---

## 7. Performance Requirements

### 7.1 Response Times

* **Chat**: < 2 seconds
* **Estimate**: < 5 seconds
* **PDF Export**: < 3 seconds

### 7.2 Accuracy Targets

* **Confidence Score**: > 0.85
* **RAGAS**: Weighted average > 0.80

### 7.3 Scalability

* **Concurrent Users**: 100
* **Estimates per Day**: \~1000

---

## 8. Security & Testing

### 8.1 API Security

* Store keys in environment variables
* Minimal personal data stored (no user PII)
* Proper CORS & rate limiting

### 8.2 Testing Requirements

1. **Unit Tests**

   * Service functions & utility validation (schemas, city normalization)
2. **Integration Tests**

   * Endpoint calls (chat, estimate, export)
   * PDF generation consistency
3. **End-to-End Tests**

   * Entire user flow: from chat to PDF
   * RAGAS tests for accuracy

### 8.3 RAGAS & Monitoring

* Evaluate retrieval accuracy on \~50 synthetic queries
* Track improvements after fine-tuning
* Log usage data and performance with LangSmith

---

## 9. Deployment Checklist

1. **Vercel Configuration**

   * `vercel.json`
   * Build settings for Python + FastAPI
   * Environment variables for OpenAI, Pinecone, SerpAPI

2. **Production Pinecone Index**

   * Confirm dimension = 1536
   * Enough capacity for 888+ docs

3. **Environment Variables**

   * `OPENAI_API_KEY`, `PINECONE_API_KEY`, `SERP_API_KEY`
   * Optional: `HUGGINGFACE_TOKEN` for fine-tuned embedding updates

4. **Testing & Monitoring**

   * Validate performance with RAGAS final.
   * Confirm minimal latency from Vercel endpoint logs.

---

## 10. Future Enhancements

1. **Geographic Expansion**

   * Add Orange County, SF Bay Area, Sacramento.
   * Expand city validation logic.

2. **Advanced Features**

   * Contractor matching (bid system).
   * Real-time cost updates (material prices, labor).
   * ROI or payback period calculations.

3. **Integration Options**

   * QuickBooks / Xero for financial tracking.
   * Permit database checks.
   * Slack or MS Teams integration for contractor coordination.

---

## 11. Developer Notes

1. **Code Standards**

   * Python code: PEP 8.
   * TypeScript for any new frontend utilities.
   * Thorough docstrings for any public functions.

2. **Git Workflow**

   * Feature branches for each phase.
   * PR review required before merge.
   * Use conventional commits (e.g., `feat:`, `fix:`, `chore:`).

3. **Frontend UI**

   * **Do Not** alter the Next.js 14 + Shadcn UI design.
   * Any changes must be explicitly approved by Product.
   * Use only the provided form fields & chat components.

4. **Chatbot Implementation Requirements**

   * **CRITICAL**: Implement strict topic filtering in chat_service.py
   * Add query validation before processing
   * Log all off-topic queries for analysis
   * Maintain California-only geographic scope
   * Cost estimates ONLY for San Diego and Los Angeles
   * General construction advice for all California
   * Example implementation pattern:
   
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

5. **Knowledge Base Expansion**

   * Document all new data sources
   * Validate accuracy before adding to RAG
   * Test with RAGAS after each update
   * Maintain version control for knowledge base
   * Future API integrations must maintain scope

6. **Implementation Order**

   * Follow the day-by-day approach:

     1. Setup & data cleaning
     2. RAG building (with chatbot constraints)
     3. RAGAS evaluation
     4. Fine-tuning (HF AutoTrain)
     5. Performance check & final improvements
     6. Deploy to Vercel

---

# End of Document

This PRD **clearly aligns** each developer to the project scope, tasks, and file structure. It references prior **example code** and **API responses** for context, ensuring everyone understands the functional and technical requirements without modifying the established frontend UI.