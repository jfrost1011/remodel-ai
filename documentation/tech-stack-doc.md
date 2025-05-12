# RemodelAI Technology Stack

## Overview

This document details the complete technology stack for the RemodelAI construction cost estimation platform, including frontend, backend, AI/ML components, infrastructure, and development tools.

## Frontend Stack

### Core Framework
- **Next.js 14**: React-based framework with App Router
- **React 19**: UI component library
- **TypeScript**: Type-safe JavaScript

### UI/Design
- **Shadcn UI**: Modern component library
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide Icons**: Icon library
- **Radix UI**: Headless UI primitives

### State Management & Forms
- **React Hook Form**: Form state management
- **Zod**: Schema validation
- **TanStack Query**: Data fetching and caching

### Build Tools
- **Vercel**: Deployment platform
- **PostCSS**: CSS processing
- **Autoprefixer**: CSS vendor prefixing

## Backend Stack

### Core Framework
- **FastAPI**: Modern Python web framework
- **Python 3.9+**: Programming language
- **Uvicorn**: ASGI server

### Data Validation
- **Pydantic**: Data validation using Python type annotations
- **Pydantic Settings**: Environment variable management

### AI/ML Components
- **OpenAI GPT-4o-mini**: Large language model for chat
- **LangChain**: RAG orchestration framework
- **Pinecone**: Vector database for embeddings
- **OpenAI Embeddings**: text-embedding-ada-002

### External APIs
- **SerpAPI**: Material pricing from Home Depot
  - Home Depot Product Search API
  - Location-based pricing with ZIP codes
  - Real-time inventory status
- **Google Search Results**: General search backup

### Data Processing
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **RAGAS**: RAG evaluation framework
- **Sentence Transformers**: Embedding models

### PDF Generation
- **ReportLab**: PDF creation library

### Testing
- **Pytest**: Python testing framework
- **Pytest-asyncio**: Async test support
- **RAGAS**: Retrieval evaluation metrics

## Database & Storage

### Vector Database
- **Pinecone**: Managed vector database
  - Index: `remodel-ai-mvp`
  - Dimension: 1536
  - Metric: Cosine similarity

### Data Storage
- **CSV Files**: Initial 888 project dataset
- **In-Memory Cache**: Session and estimate storage (MVP)

## Deployment & Infrastructure

### Hosting
- **Vercel**: Frontend and backend hosting
- **Vercel Functions**: Serverless backend

### Environment Management
- **Python-dotenv**: Environment variable loading
- **Vercel Environment Variables**: Production secrets

### Monitoring
- **LangSmith**: LLM usage analytics
- **Vercel Analytics**: Performance monitoring

## Development Tools

### Version Control
- **Git**: Source control
- **GitHub**: Code repository

### Package Management
- **npm/pnpm**: Frontend dependencies
- **pip**: Python dependencies
- **UV**: Fast Python package installer

### Code Quality
- **Black**: Python code formatter
- **isort**: Python import sorting
- **ESLint**: JavaScript/TypeScript linting
- **Prettier**: Code formatting

### API Testing
- **HTTPx**: HTTP client library
- **Postman**: API development environment

## Security

### Authentication
- **Session-based**: MVP authentication
- **JWT**: Future implementation

### API Security
- **CORS**: Cross-origin resource sharing
- **Rate Limiting**: API protection
- **Environment Variables**: Secret management

## External Services

### AI/ML Platforms
- **OpenAI**: GPT-4o-mini and embeddings
- **Hugging Face**: Model hosting and AutoTrain
- **Pinecone**: Vector search

### Data Sources
- **SerpAPI**: Material pricing
- **Home Depot**: Product pricing
- **Google Shopping**: Backup pricing

## Performance Optimization

### Caching
- **In-memory caching**: Session data
- **Vector caching**: Embedding results
- **API response caching**: Material prices

### Optimization Tools
- **Next.js Image Optimization**: Automatic image optimization
- **Vercel Edge Functions**: Low-latency compute

## Future Considerations

### Planned Additions
- **PostgreSQL**: Relational database
- **Redis**: Distributed caching
- **Celery**: Task queue
- **WebSockets**: Real-time updates

### Scaling Tools
- **Kubernetes**: Container orchestration
- **Docker**: Containerization
- **AWS S3**: File storage

## Version Information

### Key Versions
- Next.js: 14.0.0
- React: 19.0.0
- Python: 3.9+
- FastAPI: 0.104.1
- LangChain: 0.0.350
- OpenAI: 1.3.0

### API Versions
- OpenAI API: v1
- Pinecone API: v1
- SerpAPI: v1

## Development Environment

### Required Tools
- Node.js 18+
- Python 3.9+
- Git
- VS Code or similar IDE

### Recommended Extensions
- Python (VS Code)
- ESLint
- Prettier
- Tailwind CSS IntelliSense