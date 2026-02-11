# Development Guide

## Gujarat Police AI Investigation Support System - Developer Documentation

**Version:** 0.1.0
**Last Updated:** February 2026
**Target Audience:** Developers, Contributors

---

## Table of Contents

1. [Overview](#overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Project Structure](#project-structure)
4. [Code Architecture](#code-architecture)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Git Workflow](#git-workflow)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Debugging](#debugging)
10. [Contributing](#contributing)
11. [Code Review Process](#code-review-process)

---

## Overview

This document provides comprehensive guidance for developers working on the Gujarat Police AI Investigation Support System. It covers everything from setting up your development environment to submitting pull requests.

### Technology Stack

**Backend:**
- Python 3.11+
- FastAPI 0.104+
- SQLAlchemy 2.0 (async)
- Pydantic v2
- PostgreSQL 16
- ChromaDB
- Redis 7

**Frontend:**
- React 18
- TypeScript 5
- Tailwind CSS
- shadcn/ui components
- Vite

**AI/ML:**
- Sentence Transformers
- llama.cpp (C++)
- Mistral 7B (quantized)
- Transformers library

**DevOps:**
- Docker & Docker Compose
- Poetry (dependency management)
- pytest (testing)
- Ruff (linting)
- Black (formatting)
- MyPy (type checking)

### Development Principles

1. **Type Safety**: Use type hints everywhere
2. **Test Coverage**: Minimum 80% code coverage
3. **Documentation**: Docstrings for all public APIs
4. **Security First**: No secrets in code, validate all input
5. **Performance**: Profile before optimizing
6. **Maintainability**: Clear, readable code over clever code

---

## Development Environment Setup

### Prerequisites

**Required Software:**
- Python 3.11 or newer
- Node.js 18+ and npm
- Docker Desktop or Docker Engine
- Git 2.30+
- Poetry 1.7+
- VS Code or PyCharm (recommended)

**Optional but Recommended:**
- PostgreSQL client (psql)
- Redis CLI
- Postman or Insomnia (API testing)

### Initial Setup

**1. Clone Repository:**

```bash
git clone https://github.com/your-org/gujpol-slm.git
cd gujpol-slm
```

**2. Create Virtual Environment:**

```bash
# Using Poetry (recommended)
poetry install

# Or using venv
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Install Development Dependencies:**

```bash
# With Poetry
poetry install --with dev

# Or with pip
pip install -r requirements-dev.txt
```

**4. Setup Pre-commit Hooks:**

```bash
poetry run pre-commit install
```

**5. Configure Environment:**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with development values
# For development, you can use simple passwords
```

Example `.env` for development:

```bash
APP_ENV=development

# Database (use Docker container)
DATABASE_URL=postgresql://gujpol:gujpol@localhost:5432/gujpol_dev
POSTGRES_DB=gujpol_dev
POSTGRES_USER=gujpol
POSTGRES_PASSWORD=gujpol

# Redis
REDIS_URL=redis://:redispass@localhost:6379/0
REDIS_PASSWORD=redispass

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8100

# Model Server
MODEL_SERVER_HOST=localhost
MODEL_SERVER_PORT=8080

# Security (dev keys - NEVER use in production)
JWT_SECRET_KEY=dev-secret-key-change-in-production
ENCRYPTION_KEY=dev-encryption-key-change-in-production

# LLM Backend (use 'claude' for dev if you have API key)
LLM_BACKEND=claude
ANTHROPIC_API_KEY=your-key-here
```

**6. Start Development Services:**

```bash
# Start only database and cache services
docker compose up -d db-postgres cache-redis db-chroma

# Verify services are running
docker compose ps
```

**7. Initialize Database:**

```bash
# Run migrations
poetry run alembic upgrade head

# Create test user
poetry run python -m src.cli users create \
  --username dev_user \
  --password dev123 \
  --email dev@test.com \
  --full-name "Dev User" \
  --role admin
```

**8. Run Development Server:**

```bash
# Backend API
poetry run python -m src.api.main
# Or
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (in separate terminal)
cd src/dashboard
npm install
npm run dev
```

**9. Verify Installation:**

```bash
# Test API
curl http://localhost:8000/health

# Run tests
poetry run pytest

# Check code quality
poetry run ruff check src/
poetry run mypy src/
```

### IDE Configuration

**VS Code Settings (`.vscode/settings.json`):**

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "editor.formatOnSave": true,
  "editor.rulers": [100],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true
  }
}
```

**PyCharm Configuration:**

1. Set Python interpreter to Poetry venv
2. Enable pytest as test runner
3. Configure Ruff as external linter
4. Set line length to 100
5. Enable type checking with MyPy

---

## Project Structure

### Directory Layout

```
gujpol-slm/
├── src/                          # Source code
│   ├── api/                      # FastAPI backend
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── auth.py              # JWT authentication
│   │   ├── database.py          # Database connection
│   │   ├── dependencies.py      # Dependency injection
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   └── routes/              # API route modules
│   │       ├── __init__.py
│   │       ├── auth_routes.py   # /auth endpoints
│   │       ├── sop_routes.py    # /sop endpoints
│   │       ├── chargesheet_routes.py  # /chargesheet endpoints
│   │       ├── search_routes.py # /search endpoints
│   │       └── utils_routes.py  # /utils endpoints
│   │
│   ├── data_sources/            # Data collection scrapers
│   │   ├── __init__.py
│   │   ├── base.py             # Base scraper class
│   │   ├── indian_kanoon.py    # Indian Kanoon scraper
│   │   ├── ecourts.py          # eCourts scraper
│   │   ├── gujarat_hc.py       # Gujarat HC scraper
│   │   ├── supreme_court.py    # Supreme Court scraper
│   │   ├── india_code.py       # India Code (bare acts)
│   │   ├── ncrb.py             # NCRB data
│   │   └── orchestrator.py     # Scraper orchestration
│   │
│   ├── ingestion/               # Document processing
│   │   ├── __init__.py
│   │   ├── ocr_pipeline.py     # OCR processing
│   │   ├── processor.py        # Document cleaning
│   │   ├── section_normalizer.py  # Section mapping
│   │   └── kaggle_ingest.py    # Kaggle dataset import
│   │
│   ├── retrieval/               # RAG system
│   │   ├── __init__.py
│   │   ├── embeddings.py       # Embedding pipeline
│   │   ├── chunker.py          # Document chunking
│   │   ├── rag_pipeline.py     # Main RAG orchestration
│   │   └── prompts.py          # Prompt templates
│   │
│   ├── model/                   # LLM inference
│   │   ├── __init__.py
│   │   └── inference.py        # LLM client (llama.cpp/Ollama)
│   │
│   ├── security/                # Security utilities
│   │   └── __init__.py
│   │
│   ├── dashboard/               # React frontend
│   │   ├── public/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── lib/
│   │   │   └── App.tsx
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   └── cli.py                   # CLI commands
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── unit/                   # Unit tests
│   │   ├── test_embeddings.py
│   │   ├── test_rag_pipeline.py
│   │   ├── test_auth.py
│   │   └── ...
│   └── integration/            # Integration tests
│       ├── test_api_endpoints.py
│       ├── test_rag_e2e.py
│       └── ...
│
├── configs/                     # Configuration files
│   ├── ipc_to_bns_mapping.json
│   ├── crpc_to_bnss_mapping.json
│   └── ...
│
├── docker/                      # Docker configuration
│   ├── Dockerfile.api
│   ├── Dockerfile.frontend
│   ├── Dockerfile.model
│   ├── Dockerfile.backup
│   ├── prometheus.yml
│   └── grafana-datasources.yml
│
├── scripts/                     # Utility scripts
│   ├── backup.sh
│   ├── health_check.sh
│   └── ...
│
├── data/                        # Data storage (not in git)
│   ├── raw/                    # Raw documents
│   ├── processed/              # Processed documents
│   ├── embeddings/             # Vector embeddings
│   ├── sources/                # Scraped data
│   └── training/               # Training data
│
├── models/                      # Model files (not in git)
│   └── gujpol-mistral-7b-q4.gguf
│
├── logs/                        # Application logs (not in git)
├── backups/                     # Backup files (not in git)
│
├── docker-compose.yml           # Docker Compose config
├── Makefile                     # Common commands
├── pyproject.toml              # Poetry dependencies
├── poetry.lock                 # Locked dependencies
├── .env.example                # Example environment file
├── .gitignore                  # Git ignore rules
├── README.md                   # Project readme
├── CLAUDE.md                   # Project instructions
├── RAG_SYSTEM.md              # RAG documentation
├── API_REFERENCE.md           # API documentation
├── DEPLOYMENT.md              # Deployment guide
└── DEVELOPMENT.md             # This file
```

### Module Purposes

**`src/api/`** - FastAPI Backend
- Handles HTTP requests/responses
- Authentication and authorization
- Request validation
- Database interactions
- Coordinates RAG pipeline

**`src/data_sources/`** - Data Collection
- Web scrapers for legal data sources
- Handles rate limiting and retries
- Validates and normalizes scraped data
- Saves to standardized JSON format

**`src/ingestion/`** - Document Processing
- OCR for scanned documents
- Text extraction and cleaning
- Section normalization (IPC→BNS)
- Language detection
- Metadata extraction

**`src/retrieval/`** - RAG System
- Document chunking (semantic)
- Embedding generation
- Vector storage (ChromaDB)
- Hybrid search (vector + keyword)
- Context assembly with citations

**`src/model/`** - LLM Inference
- Interface to Mistral 7B
- Supports multiple backends (llama.cpp, Ollama)
- Prompt formatting
- Response parsing

**`src/security/`** - Security Utilities
- PII encryption/decryption
- Audit logging
- Access control helpers

**`src/dashboard/`** - Frontend
- React-based web interface
- Investigation guidance UI
- Chargesheet review UI
- Document search UI

---

## Code Architecture

### Backend Architecture

**Layered Architecture:**

```
┌─────────────────────────────────────┐
│         API Routes Layer            │  (HTTP endpoints)
│  - Request validation (Pydantic)    │
│  - Response formatting              │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│        Business Logic Layer         │  (Domain logic)
│  - RAG pipeline orchestration       │
│  - Search logic                     │
│  - Authentication                   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│        Data Access Layer            │  (Persistence)
│  - SQLAlchemy ORM                   │
│  - ChromaDB client                  │
│  - Redis cache                      │
└─────────────────────────────────────┘
```

**Dependency Injection:**

FastAPI's dependency injection system is used throughout:

```python
# src/api/dependencies.py

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.retrieval.rag_pipeline import RAGPipeline, create_rag_pipeline

# Database session dependency
async def get_db_session() -> AsyncSession:
    async with get_db() as session:
        yield session

# RAG pipeline singleton
_rag_pipeline_instance = None

def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline_instance
    if _rag_pipeline_instance is None:
        _rag_pipeline_instance = create_rag_pipeline()
    return _rag_pipeline_instance

# Type aliases for cleaner code
DBSession = Annotated[AsyncSession, Depends(get_db_session)]
RAGDep = Annotated[RAGPipeline, Depends(get_rag_pipeline)]
```

Usage in routes:

```python
@router.post("/search/query")
async def search(
    request: SearchRequest,
    db: DBSession,  # Auto-injected
    rag: RAGDep,    # Auto-injected
    current_user: User = Depends(get_current_user)  # Auth
):
    result = rag.query(request.query)
    # Log to database
    await db.add(SearchHistory(...))
    await db.commit()
    return result
```

### Database Schema

**Key Tables:**

```sql
-- Users and authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,  -- officer, supervisor, admin
    rank VARCHAR(100),
    badge_number VARCHAR(50),
    police_station VARCHAR(255),
    district VARCHAR(100),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents metadata
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type VARCHAR(50) NOT NULL,  -- court_ruling, bare_act, etc.
    source VARCHAR(100) NOT NULL,  -- indian_kanoon, ecourts, etc.
    title TEXT NOT NULL,
    content TEXT,  -- Full document text
    language VARCHAR(5) DEFAULT 'en',
    case_number VARCHAR(100),
    court VARCHAR(255),
    district VARCHAR(100),
    date_published DATE,
    processing_status VARCHAR(20) DEFAULT 'pending',
    ocr_confidence FLOAT,
    sections_cited JSONB,  -- Array of section references
    metadata JSONB,  -- Additional metadata
    content_hash VARCHAR(64) UNIQUE,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search history (audit trail)
CREATE TABLE search_history (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    query TEXT NOT NULL,
    filters TEXT,
    results_count INTEGER,
    top_result_id VARCHAR(255),
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit log
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    response_status INTEGER
);

-- Indexes for performance
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_source ON documents(source);
CREATE INDEX idx_documents_court ON documents(court);
CREATE INDEX idx_documents_date ON documents(date_published);
CREATE INDEX idx_documents_sections ON documents USING gin(sections_cited);
CREATE INDEX idx_search_history_user ON search_history(user_id);
CREATE INDEX idx_search_history_created ON search_history(created_at);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
```

### RAG Pipeline Flow

```python
# Simplified flow diagram

class RAGPipeline:
    """Main RAG orchestration."""

    def query(self, text: str, use_case: str, top_k: int = 5):
        # 1. Query expansion
        expanded = self.expand_query(text)
        # "murder" → "murder Section 302 IPC Section 103 BNS homicide"

        # 2. Hybrid search
        results = self.hybrid_search(expanded, top_k=top_k)
        # Combines vector search + keyword search

        # 3. Context assembly
        context = self.assemble_context(results)
        # Creates formatted context with citations

        # 4. Prompt construction
        prompt = get_prompt_template(use_case).format(
            context=context,
            query=text
        )

        # 5. LLM generation
        response = self.llm.generate(prompt, max_tokens=2048)

        # 6. Return with citations
        return RAGResponse(
            query=text,
            response=response,
            citations=[...],
            num_results=len(results)
        )
```

---

## Coding Standards

### Python Style Guide

**Follow PEP 8 with these specifics:**

- Line length: 100 characters (not 79)
- Use double quotes for strings
- Use trailing commas in multi-line structures
- Use f-strings for formatting

**Type Hints:**

Always use type hints:

```python
# Good
def process_document(doc: Dict[str, Any], max_chunks: int = 10) -> List[str]:
    """Process document into chunks."""
    chunks: List[str] = []
    # ...
    return chunks

# Bad
def process_document(doc, max_chunks=10):
    chunks = []
    # ...
    return chunks
```

**Docstrings:**

Use Google-style docstrings:

```python
def search_documents(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 10
) -> List[SearchResult]:
    """
    Search documents using hybrid search.

    Combines vector similarity search with keyword matching to find
    the most relevant documents for a given query.

    Args:
        query: Search query text
        filters: Optional metadata filters (e.g., {"court": "Supreme Court"})
        top_k: Maximum number of results to return

    Returns:
        List of SearchResult objects sorted by relevance

    Raises:
        ValueError: If query is empty or top_k is invalid
        ChromaDBError: If vector database is unavailable

    Example:
        >>> results = search_documents("bail provisions", top_k=5)
        >>> for r in results:
        ...     print(f"{r.title}: {r.score}")
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    # Implementation...
```

**Error Handling:**

Be specific with exceptions:

```python
# Good
try:
    document = load_document(path)
except FileNotFoundError:
    logger.error(f"Document not found: {path}")
    raise
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in {path}: {e}")
    raise ValueError(f"Malformed document: {path}") from e

# Bad
try:
    document = load_document(path)
except Exception as e:
    logger.error(f"Error: {e}")
    raise
```

**Logging:**

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

# Good
logger.info(
    "RAG query completed",
    extra={
        "query_length": len(query),
        "results_count": len(results),
        "duration_ms": duration,
        "user_id": user.id
    }
)

# Bad
logger.info(f"Query done: {len(results)} results in {duration}ms")
```

### Code Organization

**Class Structure:**

```python
class DocumentProcessor:
    """
    Process scraped documents for embedding.

    Attributes:
        normalizer: SectionNormalizer instance
        stats: ProcessingStats tracking processed documents
    """

    def __init__(self, section_normalizer: Optional[SectionNormalizer] = None):
        """Initialize document processor."""
        self.normalizer = section_normalizer or SectionNormalizer()
        self.stats = ProcessingStats()

    # Public methods first
    def process_source_dir(self, source_dir: str, output_dir: str) -> ProcessingStats:
        """Process all documents in directory."""
        # ...

    def process_document(self, doc_path: Path) -> Optional[Dict]:
        """Process single document."""
        # ...

    # Private methods last (prefixed with _)
    def _normalize_sections(self, text: str) -> str:
        """Normalize section references."""
        # ...

    def _detect_language(self, text: str) -> str:
        """Detect document language."""
        # ...
```

**Function Ordering:**

1. Public methods/functions (most important first)
2. Private methods/functions
3. Helper functions
4. Constants at module level

### Testing Standards

**Test Structure:**

```python
# tests/unit/test_embeddings.py

import pytest
from src.retrieval.embeddings import EmbeddingPipeline

@pytest.fixture
def embedding_pipeline():
    """Create test embedding pipeline."""
    return EmbeddingPipeline(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        chroma_persist_dir="/tmp/test_chroma"
    )

class TestEmbeddingPipeline:
    """Test suite for EmbeddingPipeline."""

    def test_initialization(self, embedding_pipeline):
        """Test pipeline initializes correctly."""
        assert embedding_pipeline.model is not None
        assert embedding_pipeline.client is not None

    def test_embed_single_document(self, embedding_pipeline, sample_document):
        """Test embedding a single document."""
        result = embedding_pipeline.embed_document(sample_document)

        assert result is not None
        assert "embeddings" in result
        assert len(result["embeddings"]) == 384  # Model dimension

    def test_search_returns_results(self, embedding_pipeline):
        """Test search returns expected results."""
        results = embedding_pipeline.search("test query", top_k=5)

        assert len(results) <= 5
        assert all(hasattr(r, "score") for r in results)
        assert all(0 <= r.score <= 1 for r in results)

    def test_empty_query_raises_error(self, embedding_pipeline):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            embedding_pipeline.search("", top_k=5)
```

**Test Coverage Requirements:**

- Minimum 80% overall coverage
- 100% coverage for critical paths (authentication, search, data access)
- All public APIs must have tests
- Edge cases and error conditions must be tested

---

## Testing Guidelines

### Running Tests

**Run all tests:**
```bash
poetry run pytest
```

**Run specific test file:**
```bash
poetry run pytest tests/unit/test_embeddings.py
```

**Run with coverage:**
```bash
poetry run pytest --cov=src --cov-report=html
```

**Run only fast tests (skip slow integration tests):**
```bash
poetry run pytest -m "not slow"
```

### Test Types

**1. Unit Tests (`tests/unit/`):**

Test individual functions/classes in isolation:

```python
def test_section_normalization():
    """Test IPC to BNS section conversion."""
    normalizer = SectionNormalizer()
    result = normalizer.normalize("Section 302 IPC")

    assert "Section 103 BNS" in result
    assert "murder" in result.lower()
```

**2. Integration Tests (`tests/integration/`):**

Test multiple components together:

```python
@pytest.mark.integration
async def test_rag_pipeline_e2e(db_session, chroma_client):
    """Test complete RAG pipeline flow."""
    # Setup: Add test documents to DB and ChromaDB
    test_docs = create_test_documents()
    await db_session.add_all(test_docs)
    await db_session.commit()

    # Execute: Run RAG query
    rag = create_rag_pipeline()
    result = rag.query("What is punishment for murder?", top_k=3)

    # Verify
    assert result.response is not None
    assert len(result.citations) > 0
    assert result.num_results == 3
```

**3. API Tests (`tests/integration/test_api_endpoints.py`):**

Test API endpoints:

```python
@pytest.mark.asyncio
async def test_sop_suggest_endpoint(client, auth_token):
    """Test /sop/suggest endpoint."""
    response = await client.post(
        "/sop/suggest",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "fir_details": "Theft of motorcycle",
            "case_category": "theft",
            "top_k": 5
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "citations" in data
    assert len(data["citations"]) > 0
```

### Test Fixtures

**Common fixtures in `tests/conftest.py`:**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    yield engine
    engine.dispose()

@pytest.fixture
async def db_session(test_db_engine):
    """Create test database session."""
    async with AsyncSession(test_db_engine) as session:
        yield session

@pytest.fixture
def client():
    """Create test API client."""
    from src.api.main import app
    return TestClient(app)

@pytest.fixture
def auth_token(client):
    """Get authentication token for tests."""
    response = client.post(
        "/auth/login",
        json={"username": "test_user", "password": "test123"}
    )
    return response.json()["access_token"]

@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "title": "Test Case v. State (2024)",
        "content": "Section 302 IPC - Murder case...",
        "source": "test",
        "document_type": "court_ruling"
    }
```

### Mocking

**Mock external dependencies:**

```python
from unittest.mock import Mock, patch

def test_llm_generation_with_mock():
    """Test RAG pipeline with mocked LLM."""
    with patch('src.model.inference.LLMClient') as mock_llm:
        # Configure mock
        mock_llm.return_value.generate.return_value = "Mocked response"

        # Test
        rag = RAGPipeline(llm_client=mock_llm())
        result = rag.query("test query")

        # Verify
        assert result.response == "Mocked response"
        mock_llm.return_value.generate.assert_called_once()
```

---

## Git Workflow

### Branch Strategy

**Main Branches:**
- `main` - Production-ready code
- `develop` - Integration branch for features

**Feature Branches:**
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

**Format:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(rag): add query expansion with legal synonyms

Implement query expansion to automatically add legal terms
and section mappings (IPC↔BNS) to improve search recall.

Closes #123
```

```
fix(api): handle empty search results gracefully

Previously raised unhandled exception when no results found.
Now returns empty results list with appropriate message.

Fixes #456
```

### Pull Request Process

**1. Create Feature Branch:**

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

**2. Make Changes:**

```bash
# Write code
# Write tests
# Update documentation

# Run tests
poetry run pytest

# Check code quality
poetry run ruff check src/
poetry run mypy src/
```

**3. Commit Changes:**

```bash
git add .
git commit -m "feat(scope): description"
```

**4. Push and Create PR:**

```bash
git push origin feature/your-feature-name
```

Then create pull request on GitHub/GitLab.

**5. PR Checklist:**

- [ ] Tests pass locally
- [ ] Code follows style guide
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] PR description explains changes
- [ ] Related issues linked

---

## CI/CD Pipeline

### GitHub Actions Workflow

**`.github/workflows/ci.yml`:**

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Install dependencies
        run: poetry install --with dev

      - name: Run linters
        run: |
          poetry run ruff check src/
          poetry run mypy src/

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
        run: poetry run pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  build:
    runs-on: ubuntu-latest
    needs: test

    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: docker compose build

      - name: Test Docker deployment
        run: |
          docker compose up -d
          sleep 30
          curl -f http://localhost:8000/health || exit 1
          docker compose down
```

### Pre-commit Hooks

**`.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

---

## Debugging

### Local Debugging

**VS Code Launch Configuration (`.vscode/launch.json`):**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Server",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.api.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false
    },
    {
      "name": "Pytest Current File",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v", "-s"],
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "CLI Command",
      "type": "python",
      "request": "launch",
      "module": "src.cli",
      "args": ["health"],
      "console": "integratedTerminal"
    }
  ]
}
```

**PyCharm Debug Configuration:**

1. Run → Edit Configurations
2. Add New Configuration → Python
3. Script path: `uvicorn`
4. Parameters: `src.api.main:app --reload`
5. Working directory: Project root

### Debugging Tips

**Enable Debug Logging:**

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or in .env
LOG_LEVEL=DEBUG
```

**Interactive Debugging:**

```python
# Add breakpoint in code
import pdb; pdb.set_trace()  # Python debugger

# Or use ipdb (better)
import ipdb; ipdb.set_trace()  # IPython debugger
```

**Profile Performance:**

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Your code here
    result = slow_function()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 slowest

    return result
```

**Debug RAG Pipeline:**

```python
# Enable verbose logging
import logging
logging.getLogger("src.retrieval").setLevel(logging.DEBUG)

# Test RAG with small dataset
rag = create_rag_pipeline()
result = rag.query("test query", top_k=3)

# Inspect intermediate results
print(f"Query expanded to: {rag.expand_query('test query')}")
print(f"Retrieved {len(result.citations)} documents")
print(f"Context length: {len(result.context)} chars")
```

---

## Contributing

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Write/update tests**
5. **Update documentation**
6. **Submit pull request**

### Contribution Guidelines

**Code Contributions:**

- Follow coding standards (see above)
- Include tests for new features
- Update documentation
- Keep commits atomic and focused
- Write clear commit messages

**Documentation Contributions:**

- Fix typos and improve clarity
- Add examples where helpful
- Keep documentation up-to-date with code
- Use proper Markdown formatting

**Bug Reports:**

Include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs/error messages

**Feature Requests:**

Include:
- Clear description of the feature
- Use case/rationale
- Proposed implementation (if applicable)
- Potential impact on existing features

### Code of Conduct

- Be respectful and professional
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions
- Follow the law and organizational policies

---

## Code Review Process

### Reviewer Checklist

**Functionality:**
- [ ] Code works as intended
- [ ] Edge cases handled
- [ ] Error handling appropriate
- [ ] No obvious bugs

**Code Quality:**
- [ ] Follows style guide
- [ ] Clear and readable
- [ ] Properly documented
- [ ] No unnecessary complexity

**Testing:**
- [ ] Tests included and passing
- [ ] Coverage acceptable
- [ ] Edge cases tested
- [ ] Integration points tested

**Security:**
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevented
- [ ] XSS prevention in place

**Performance:**
- [ ] No obvious performance issues
- [ ] Appropriate data structures
- [ ] Caching used where beneficial
- [ ] Database queries optimized

**Documentation:**
- [ ] Code comments where needed
- [ ] Docstrings present
- [ ] README updated if needed
- [ ] API docs updated if needed

### Review Process

**1. Author submits PR:**
- Ensure all CI checks pass
- Self-review changes
- Provide clear PR description

**2. Reviewer assigned:**
- Review within 24 hours
- Provide constructive feedback
- Approve or request changes

**3. Author addresses feedback:**
- Respond to all comments
- Make requested changes
- Mark conversations resolved

**4. Final approval:**
- Reviewer approves PR
- Author merges to target branch
- Delete feature branch

### Review Best Practices

**For Authors:**
- Keep PRs small and focused
- Provide context in description
- Respond to feedback promptly
- Don't take criticism personally

**For Reviewers:**
- Be constructive and specific
- Praise good work
- Ask questions rather than make demands
- Focus on important issues

---

## Appendix

### Useful Commands

**Development:**
```bash
# Start dev server
make serve

# Run tests
make test

# Lint code
make lint

# Format code
make format

# Generate embeddings
make embed

# Health check
make health
```

**Database:**
```bash
# Create migration
poetry run alembic revision --autogenerate -m "description"

# Run migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1

# Database shell
docker compose exec db-postgres psql -U gujpol_admin -d gujpol_slm
```

**Docker:**
```bash
# Build images
make docker-build

# Start services
make docker-up

# Stop services
make docker-down

# View logs
make docker-logs

# Shell into container
docker compose exec app-api bash
```

### Resources

**Documentation:**
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Pydantic: https://docs.pydantic.dev/
- Sentence Transformers: https://www.sbert.net/
- ChromaDB: https://docs.trychroma.com/

**Learning:**
- Python Type Hints: https://mypy.readthedocs.io/
- Async Python: https://docs.python.org/3/library/asyncio.html
- Testing: https://docs.pytest.org/
- Docker: https://docs.docker.com/

### FAQ

**Q: How do I add a new API endpoint?**

A:
1. Add route function to appropriate file in `src/api/routes/`
2. Define request/response schemas in `src/api/schemas.py`
3. Update API docs in `API_REFERENCE.md`
4. Write tests in `tests/integration/`

**Q: How do I add a new data source?**

A:
1. Create scraper class in `src/data_sources/` inheriting from `BaseScraper`
2. Implement `scrape()` method
3. Add to orchestrator in `src/data_sources/orchestrator.py`
4. Update data collection docs

**Q: How do I change the embedding model?**

A:
1. Update model name in `src/retrieval/embeddings.py`
2. Re-run embedding generation: `make embed`
3. Update documentation with new model specs

**Q: How do I debug a failing test?**

A:
```bash
# Run single test with verbose output
poetry run pytest tests/unit/test_file.py::test_function -v -s

# Add print statements or breakpoints
# Use pytest --pdb to drop into debugger on failure
poetry run pytest --pdb
```

---

**Document Version:** 1.0
**Last Updated:** February 11, 2026
**Maintained By:** Gujarat Police SLM Development Team
