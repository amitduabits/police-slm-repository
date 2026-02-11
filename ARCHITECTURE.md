# System Architecture

This document describes the technical architecture of the Gujarat Police AI Investigation Support System.

## Table of Contents

- [Overview](#overview)
- [Architecture Diagram](#architecture-diagram)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Database Schema](#database-schema)
- [RAG Pipeline](#rag-pipeline)
- [Security Architecture](#security-architecture)
- [Deployment Architecture](#deployment-architecture)

## Overview

The system follows a **microservices architecture** with **8 containerized services** orchestrated via Docker Compose. It implements a **Retrieval-Augmented Generation (RAG)** pattern combining vector search with a fine-tuned Small Language Model (SLM) for domain-specific responses.

### Design Principles

1. **On-Premise First** - No external API dependencies, complete air-gapped operation
2. **Data Sovereignty** - All sensitive data stays within Gujarat Police infrastructure
3. **Audit Trail** - Every action logged with tamper-proof chain hashing
4. **Horizontal Scalability** - Stateless API servers, shared cache layer
5. **Fail-Safe** - Graceful degradation when model server unavailable

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                          User Access Layer                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Web Browser (Officers)                                      │       │
│  │  - Chrome/Firefox/Edge                                       │       │
│  │  - Minimum 1920x1080 resolution                             │       │
│  └──────────────────────┬──────────────────────────────────────┘       │
│                         │ HTTPS (TLS 1.3)                              │
└─────────────────────────┼────────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────────┐
│                     Presentation Layer                                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  React Dashboard (Port 3000)                                 │       │
│  │  - TypeScript + React 18                                     │       │
│  │  - Tailwind CSS + shadcn/ui                                  │       │
│  │  - Vite build system                                         │       │
│  │  - JWT token storage & management                            │       │
│  └──────────────────────┬──────────────────────────────────────┘       │
│                         │                                               │
└─────────────────────────┼────────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────────┐
│                      Proxy Layer                                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  Nginx Reverse Proxy                                         │       │
│  │  - SSL/TLS termination                                       │       │
│  │  - Load balancing (future: multiple API instances)          │       │
│  │  - Request rate limiting                                     │       │
│  │  - Static file serving                                       │       │
│  └──────────────────────┬──────────────────────────────────────┘       │
│                         │                                               │
└─────────────────────────┼────────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────────┐
│                   Application Layer                                    │
├────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  FastAPI Backend (Port 8000)                                 │       │
│  │  ┌─────────────────────────────────────────────────────┐    │       │
│  │  │  API Routes                                          │    │       │
│  │  │  - /auth/*      → Authentication                     │    │       │
│  │  │  - /sop/*       → SOP suggestions                    │    │       │
│  │  │  - /chargesheet/* → Review & validation             │    │       │
│  │  │  - /search/*    → Case search                        │    │       │
│  │  │  - /utils/*     → Section conversion, health         │    │       │
│  │  └─────────────────────────────────────────────────────┘    │       │
│  │  ┌─────────────────────────────────────────────────────┐    │       │
│  │  │  Middleware                                          │    │       │
│  │  │  - CORS handling                                     │    │       │
│  │  │  - JWT validation                                    │    │       │
│  │  │  - Request timing                                    │    │       │
│  │  │  - Audit logging                                     │    │       │
│  │  │  - Error handling                                    │    │       │
│  │  └─────────────────────────────────────────────────────┘    │       │
│  └────────┬──────────────────┬──────────────────┬───────────────┘       │
│           │                  │                  │                       │
└───────────┼──────────────────┼──────────────────┼──────────────────────┘
            │                  │                  │
            │                  │                  │
┌───────────▼──────┐  ┌────────▼────────┐  ┌─────▼──────────────────────┐
│  Cache Layer     │  │  Data Layer     │  │   Intelligence Layer       │
├──────────────────┤  ├─────────────────┤  ├────────────────────────────┤
│                  │  │                 │  │                            │
│ ┌──────────────┐ │  │ ┌─────────────┐ │  │ ┌────────────────────────┐ │
│ │ Redis Cache  │ │  │ │ PostgreSQL  │ │  │ │   RAG Pipeline         │ │
│ │ (Port 6379)  │ │  │ │ (Port 5432) │ │  │ │  ┌──────────────────┐  │ │
│ │              │ │  │ │             │ │  │ │  │ Query Expansion  │  │ │
│ │ - Sessions   │ │  │ │ - Users     │ │  │ │  └────────┬─────────┘  │ │
│ │ - JWT tokens │ │  │ │ - Documents │ │  │ │           │            │ │
│ │ - Query cache│ │  │ │ - FIRs      │ │  │ │  ┌────────▼─────────┐  │ │
│ │ - Rate limits│ │  │ │ - Chargeshts│ │  │ │  │ Hybrid Search    │  │ │
│ └──────────────┘ │  │ │ - Rulings   │ │  │ │  │ - Vector (70%)   │  │ │
│                  │  │ │ - Audit log │ │  │ │  │ - Keyword (30%)  │  │ │
│                  │  │ │ - Feedback  │ │  │ │  └────────┬─────────┘  │ │
│                  │  │ └─────────────┘ │  │ │           │            │ │
│                  │  │                 │  │ │  ┌────────▼─────────┐  │ │
│                  │  │ ┌─────────────┐ │  │ │  │ Context Assembly │  │ │
│                  │  │ │  ChromaDB   │ │  │ │  │ + Citations      │  │ │
│                  │  │ │ (Port 8100) │ │  │ │  └────────┬─────────┘  │ │
│                  │  │ │             │ │  │ │           │            │ │
│                  │  │ │ - Embeddings│◄─┼──┼─┼───────────┘            │ │
│                  │  │ │ - Collections│ │  │ │           │            │ │
│                  │  │ │   * firs    │ │  │ │  ┌────────▼─────────┐  │ │
│                  │  │ │   * sheets  │ │  │ │  │ LLM Generation   │  │ │
│                  │  │ │   * rulings │ │  │ │  └────────┬─────────┘  │ │
│                  │  │ │   * acts    │ │  │ │           │            │ │
│                  │  │ └─────────────┘ │  │ └───────────┼────────────┘ │
│                  │  │                 │  │             │              │
└──────────────────┘  └─────────────────┘  └─────────────┼──────────────┘
                                                          │
                                           ┌──────────────▼───────────────┐
                                           │  Model Server (Port 8080)    │
                                           ├──────────────────────────────┤
                                           │  llama.cpp                   │
                                           │  - Mistral 7B (4-bit GGUF)   │
                                           │  - 4096 token context        │
                                           │  - GPU acceleration (opt)    │
                                           └──────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        Monitoring Layer                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────┐         ┌────────────────────────────┐        │
│  │  Prometheus          │────────►│  Grafana                   │        │
│  │  (Port 9090)         │         │  (Port 3001)               │        │
│  │  - Metrics collection│         │  - Dashboards              │        │
│  │  - Time-series DB    │         │  - Alerts                  │        │
│  └──────────────────────┘         └────────────────────────────┘        │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        Backup Layer                                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────────────────────────────────────────────┐         │
│  │  Backup Service (Cron: 2 AM daily)                         │         │
│  │  - PostgreSQL dump (pg_dump)                               │         │
│  │  - ChromaDB snapshot                                       │         │
│  │  - 90-day retention                                        │         │
│  │  - Encrypted storage                                       │         │
│  └────────────────────────────────────────────────────────────┘         │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

## System Components

### 1. Frontend Service (app-frontend)

**Container:** `gujpol-frontend`
**Port:** 3000
**Technology:** React 18 + TypeScript + Vite

**Responsibilities:**
- User interface for all three features (SOP, Chargesheet, Search)
- JWT token management
- Form validation
- Real-time feedback display
- Multi-language support (EN/HI/GU)

**Build Output:**
- Static files served via Nginx
- Code splitting for optimal loading
- Service worker for offline capability (future)

### 2. API Service (app-api)

**Container:** `gujpol-api`
**Port:** 8000
**Technology:** FastAPI + Python 3.11

**Responsibilities:**
- Request authentication & authorization
- Business logic orchestration
- RAG pipeline invocation
- Database operations
- Audit logging
- Response formatting

**Resource Limits:**
- Memory: 4GB
- CPU: 2 cores

**Health Check:** `GET /health` (30s interval)

### 3. PostgreSQL Database (db-postgres)

**Container:** `gujpol-postgres`
**Port:** 5432
**Technology:** PostgreSQL 16 Alpine

**Responsibilities:**
- Structured data storage
- Full-text search (pg_trgm extension)
- User management
- Audit trail (append-only)
- Session data

**Resource Limits:**
- Memory: 2GB
- CPU: 1 core

**Persistence:** Named volume `postgres_data`

**Extensions:**
- `uuid-ossp` - UUID generation
- `pgcrypto` - Cryptographic functions
- `pg_trgm` - Trigram matching for fuzzy search

### 4. ChromaDB Vector Store (db-chroma)

**Container:** `gujpol-chroma`
**Port:** 8100 (internal), 8000 (container)
**Technology:** ChromaDB latest

**Responsibilities:**
- Vector embedding storage
- Semantic similarity search
- Collection management
- Metadata filtering

**Collections:**
- `firs` - FIR documents
- `chargesheets` - Chargesheet documents
- `court_rulings` - Court judgments
- `panchnamas` - Panchnama documents
- `bare_acts` - Legal code sections
- `all_documents` - Unified collection

**Resource Limits:**
- Memory: 2GB
- CPU: 1 core

**Persistence:** Named volume `chroma_data`

### 5. Redis Cache (cache-redis)

**Container:** `gujpol-redis`
**Port:** 6379
**Technology:** Redis 7 Alpine

**Responsibilities:**
- Session storage
- JWT token caching
- Query result caching (15 min TTL)
- Rate limiting counters
- Distributed locks

**Configuration:**
- Max memory: 512MB
- Eviction policy: `allkeys-lru`
- Persistence: RDB snapshots

**Resource Limits:**
- Memory: 1GB
- CPU: 0.5 core

### 6. Model Server (model-server)

**Container:** `gujpol-model`
**Port:** 8080
**Technology:** llama.cpp + Python wrapper

**Responsibilities:**
- SLM inference (Mistral 7B)
- Prompt processing
- Token generation
- Context window management (4096 tokens)

**Model Specifications:**
- Base: Mistral 7B Instruct v0.3
- Fine-tuning: QLoRA adapters merged
- Quantization: 4-bit GGUF format
- File size: ~4GB
- VRAM usage: ~6GB (with GPU layers)

**Resource Limits:**
- Memory: 8GB
- CPU: 4 cores
- GPU: Optional NVIDIA GPU (35 layers offloaded)

**Health Check:** `GET /health` (30s interval, 60s start period)

### 7. Prometheus (prometheus)

**Container:** `gujpol-prometheus`
**Port:** 9090
**Technology:** Prometheus latest

**Responsibilities:**
- Time-series metrics storage
- API endpoint scraping
- Alert rule evaluation

**Metrics Collected:**
- Request count & latency
- Database connection pool stats
- Model inference time
- Cache hit rates
- System resource usage

**Resource Limits:**
- Memory: 512MB
- CPU: 0.5 core

### 8. Grafana (grafana)

**Container:** `gujpol-grafana`
**Port:** 3001
**Technology:** Grafana latest

**Responsibilities:**
- Visualization dashboards
- Alert notifications
- User analytics

**Dashboards:**
- System Overview (requests, errors, latency)
- Model Performance (inference time, queue depth)
- Database Health (connections, query time)
- User Activity (queries per user, feature usage)

**Resource Limits:**
- Memory: 512MB
- CPU: 0.5 core

### 9. Backup Service (backup)

**Container:** `gujpol-backup`
**Technology:** Alpine + cron + pg_dump

**Responsibilities:**
- Automated PostgreSQL backups (daily 2 AM)
- ChromaDB snapshots (weekly)
- Backup rotation (90-day retention)
- Backup encryption

**Schedule:** Configured via `BACKUP_SCHEDULE_CRON` env var

## Data Flow

### 1. Authentication Flow

```
User → Dashboard → POST /auth/login
                      ↓
              Validate credentials (PostgreSQL)
                      ↓
              Generate JWT access + refresh tokens
                      ↓
              Store refresh token (Redis)
                      ↓
              Return tokens to dashboard
                      ↓
              Dashboard stores in localStorage
                      ↓
              Subsequent requests include JWT in Authorization header
```

### 2. Query Flow (Search/SOP/Chargesheet)

```
User enters query → Dashboard
                      ↓
              POST /search/query (with JWT)
                      ↓
              API: Validate JWT → Extract user info
                      ↓
              API: Check Redis cache (key = query hash)
                      ↓ (cache miss)
              API: Invoke RAG Pipeline
                      ↓
         ┌────────────┴────────────┐
         ▼                         ▼
    Query Expansion        Metadata Filtering
         ↓                         ↓
    Hybrid Search ←────────────────┘
    (Vector 70% + Keyword 30%)
         ↓
    Retrieve top-k chunks from ChromaDB
         ↓
    Assemble context with citations
         ↓
    Build use-case specific prompt
         ↓
    POST to Model Server (llama.cpp)
         ↓
    Receive generated response
         ↓
    Format response + citations
         ↓
    Store in Redis cache (15 min TTL)
         ↓
    Log to audit_log table (PostgreSQL)
         ↓
    Return to dashboard
         ↓
    Dashboard displays answer + sources
```

### 3. Document Ingestion Flow

```
Upload PDF/Image → data/raw/ directory
                      ↓
              make ingest-ocr
                      ↓
         ┌────────────┴────────────┐
         ▼                         ▼
    Tesseract OCR           PaddleOCR (fallback)
         ↓                         ↓
    Extract text → data/processed/ocr/
         ↓
              make ingest-parse
                      ↓
    Document-type specific parser
    (FIR/Chargesheet/Ruling/Panchnama)
         ↓
    Extract structured fields
    - Case number, sections, dates, parties, etc.
         ↓
    Validate required fields
         ↓
    Save to data/processed/structured/
         ↓
              make ingest-clean
                      ↓
    Normalize section codes (IPC→BNS mapping)
         ↓
    Detect & encrypt PII
         ↓
    Deduplicate (content hash)
         ↓
    Save to PostgreSQL (documents table)
         ↓
    Save structured data (firs/chargesheets/court_rulings tables)
         ↓
              make embed
                      ↓
    Chunk documents (500 tokens, 100 overlap)
         ↓
    Generate embeddings (sentence-transformers)
         ↓
    Store in ChromaDB with metadata
         ↓
    Mark document as indexed (is_indexed=true)
```

### 4. Section Conversion Flow

```
User query contains "IPC 302" → API detects old code
                      ↓
              Load mapping from configs/ipc_to_bns_mapping.json
                      ↓
              Lookup: IPC 302 → BNS 103
                      ↓
              Enrich query with both codes
              "IPC 302 OR BNS 103 murder"
                      ↓
              Execute search with expanded query
                      ↓
              Return results covering both old & new code
```

## Technology Stack

### Backend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.11+ | Core application |
| **Web Framework** | FastAPI | 0.115+ | REST API |
| **ASGI Server** | Uvicorn | 0.30+ | Production server |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Validation** | Pydantic | 2.9+ | Data validation |
| **Database** | PostgreSQL | 16 | Relational data |
| **Vector DB** | ChromaDB | 0.5+ | Embeddings |
| **Cache** | Redis | 7 | Session & cache |
| **Task Queue** | Celery | 5.4+ | Background jobs |

### ML/NLP Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Base Model** | Mistral 7B Instruct | v0.3 | Language model |
| **Inference** | llama.cpp | Latest | Efficient inference |
| **Embeddings** | sentence-transformers | 3.1+ | Vector generation |
| **Specific Model** | paraphrase-multilingual-MiniLM-L12-v2 | - | Multilingual embeddings |
| **Fine-tuning** | PEFT + QLoRA | 0.13+ | Parameter-efficient tuning |
| **Framework** | PyTorch | 2.4+ | Deep learning |
| **Quantization** | bitsandbytes | 0.44+ | 4-bit quantization |

### OCR/Processing Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Primary OCR** | Tesseract | 5.x | English/Hindi OCR |
| **Fallback OCR** | PaddleOCR | 2.8+ | Gujarati/complex OCR |
| **PDF Processing** | pdf2image | 1.17+ | PDF to image |
| **Text Extraction** | pdfplumber | 0.11+ | PDF text extraction |
| **Document Parsing** | python-docx | 1.1+ | Word docs |
| **Image Processing** | Pillow | 10.4+ | Image manipulation |

### Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | React | 18 | UI library |
| **Language** | TypeScript | 5+ | Type safety |
| **Build Tool** | Vite | 5+ | Fast builds |
| **Styling** | Tailwind CSS | 3+ | Utility CSS |
| **Components** | shadcn/ui | Latest | Pre-built components |
| **HTTP Client** | Axios | 1+ | API requests |
| **State** | React Context | - | State management |

### Infrastructure Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Containerization** | Docker | 24+ | Container runtime |
| **Orchestration** | Docker Compose | 3.9 | Multi-container |
| **Reverse Proxy** | Nginx | Latest | Load balancing |
| **Monitoring** | Prometheus | Latest | Metrics |
| **Visualization** | Grafana | Latest | Dashboards |
| **Process Manager** | Systemd | - | Service management |

## Database Schema

### Core Tables

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'officer',  -- admin, senior_officer, officer, viewer
    rank VARCHAR(100),
    badge_number VARCHAR(50),
    police_station VARCHAR(200),
    district VARCHAR(100),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### documents
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_type VARCHAR(50) NOT NULL,  -- fir, chargesheet, court_ruling, panchnama, bare_act
    source VARCHAR(50) NOT NULL,  -- upload, indian_kanoon, ecourts, etc.
    source_url TEXT,
    title TEXT NOT NULL,
    content TEXT,  -- Full text content
    content_hash VARCHAR(64) UNIQUE,  -- SHA-256 for deduplication
    language VARCHAR(10) DEFAULT 'en',  -- en, hi, gu
    case_number VARCHAR(200),
    court VARCHAR(200),
    district VARCHAR(100),
    police_station VARCHAR(200),
    date_published DATE,
    date_ingested TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ocr_confidence FLOAT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    sections_cited TEXT[],  -- ["IPC 302", "IPC 120B", ...]
    judges TEXT[],
    parties TEXT[],
    is_indexed BOOLEAN DEFAULT false,  -- Embedded in ChromaDB?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_source ON documents(source);
CREATE INDEX idx_documents_district ON documents(district);
CREATE INDEX idx_documents_sections ON documents USING GIN(sections_cited);
CREATE INDEX idx_documents_content_trgm ON documents USING GIN(content gin_trgm_ops);
```

#### section_mappings
```sql
CREATE TABLE section_mappings (
    id SERIAL PRIMARY KEY,
    old_code VARCHAR(20) NOT NULL,  -- IPC, CrPC, IEA
    old_section VARCHAR(20) NOT NULL,  -- 302, 173, etc.
    new_code VARCHAR(20) NOT NULL,  -- BNS, BNSS, BSA
    new_section VARCHAR(20),  -- 103, 193, etc. (NULL if decriminalized)
    old_title TEXT,
    new_title TEXT,
    description TEXT,
    is_decriminalized BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(old_code, old_section, new_code)
);

CREATE INDEX idx_section_old ON section_mappings(old_code, old_section);
CREATE INDEX idx_section_new ON section_mappings(new_code, new_section);
```

#### firs
```sql
CREATE TABLE firs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    fir_number VARCHAR(100) NOT NULL,
    fir_date DATE,
    fir_time TIME,
    police_station VARCHAR(200),
    district VARCHAR(100),
    complainant_name VARCHAR(255),
    complainant_address TEXT,
    complainant_relation VARCHAR(100),
    accused_details JSONB DEFAULT '[]',  -- [{name, age, address, ...}, ...]
    sections_cited TEXT[],
    incident_description TEXT,
    incident_location TEXT,
    incident_date DATE,
    incident_time TIME,
    evidence_mentioned TEXT[],
    status VARCHAR(50) DEFAULT 'registered',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_firs_number ON firs(fir_number);
CREATE INDEX idx_firs_district ON firs(district);
CREATE INDEX idx_firs_ps ON firs(police_station);
CREATE INDEX idx_firs_date ON firs(fir_date);
```

#### chargesheets
```sql
CREATE TABLE chargesheets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    case_number VARCHAR(200),
    fir_reference VARCHAR(100),
    fir_id UUID REFERENCES firs(id),
    accused_list JSONB DEFAULT '[]',
    witnesses_list JSONB DEFAULT '[]',
    evidence_inventory JSONB DEFAULT '[]',
    sections_charged TEXT[],
    investigation_officer VARCHAR(255),
    investigation_chronology JSONB DEFAULT '[]',
    forensic_reports JSONB DEFAULT '[]',
    filing_date DATE,
    court_name VARCHAR(200),
    completeness_score FLOAT,  -- 0-1, calculated by review algorithm
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### court_rulings
```sql
CREATE TABLE court_rulings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    case_citation VARCHAR(500),
    case_number VARCHAR(200),
    court_name VARCHAR(200),
    bench VARCHAR(200),
    judges TEXT[],
    parties TEXT[],
    charges_considered TEXT[],
    verdict VARCHAR(50),  -- acquitted, convicted, partial, etc.
    verdict_details JSONB DEFAULT '{}',
    key_reasoning TEXT,
    sentences_imposed TEXT[],
    precedents_cited TEXT[],
    judgment_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rulings_court ON court_rulings(court_name);
CREATE INDEX idx_rulings_verdict ON court_rulings(verdict);
CREATE INDEX idx_rulings_date ON court_rulings(judgment_date);
```

#### audit_log (Tamper-Proof)
```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_id UUID REFERENCES users(id),
    username VARCHAR(100),
    action VARCHAR(100) NOT NULL,  -- login, query, review, export, etc.
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path TEXT,
    response_status INTEGER,
    prev_hash VARCHAR(64),  -- SHA-256 of previous entry (chain)
    entry_hash VARCHAR(64),  -- SHA-256 of current entry
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_action ON audit_log(action);

-- Make audit log append-only
CREATE OR REPLACE RULE audit_no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
CREATE OR REPLACE RULE audit_no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING;
```

### Relationships

```
users (1) ────────< (many) search_history
users (1) ────────< (many) feedback
users (1) ────────< (many) training_progress
users (1) ────────< (many) audit_log

documents (1) ────< (1) firs
documents (1) ────< (1) chargesheets
documents (1) ────< (1) court_rulings

firs (1) ─────────< (many) chargesheets
```

## RAG Pipeline

The Retrieval-Augmented Generation pipeline is the core intelligence component.

### Pipeline Stages

```
1. Query Expansion
   ↓
2. Hybrid Search (Vector + Keyword)
   ↓
3. Context Assembly
   ↓
4. Prompt Construction
   ↓
5. LLM Generation
   ↓
6. Response Formatting
```

### 1. Query Expansion

**Purpose:** Enrich user query with legal synonyms and section codes.

**Example:**
```
Input:  "murder bail in Gujarat"
Output: "murder Section 302 IPC Section 103 BNS homicide killing bail
         anticipatory bail regular bail Section 437 CrPC Gujarat"
```

**Implementation:** Dictionary-based expansion (see `src/retrieval/rag_pipeline.py::expand_query`)

### 2. Hybrid Search

**Vector Search (70% weight):**
- Embedding model: `paraphrase-multilingual-MiniLM-L12-v2`
- Dimension: 384
- Similarity: Cosine distance
- ChromaDB collection: `all_documents` or specific collection

**Keyword Search (30% weight):**
- Method: BM25 (to be implemented)
- Fallback: PostgreSQL full-text search with `pg_trgm`

**Fusion:** Reciprocal Rank Fusion (RRF) algorithm

### 3. Context Assembly

**Strategy:**
- Retrieve top-k chunks (default k=5)
- Respect token limit (3000 tokens)
- Include source citations for each chunk
- Format: `[Source 1: Title]\nContent\n\n[Source 2: Title]\nContent...`

### 4. Prompt Construction

**Templates by Use Case:**

**General Search:**
```
You are a legal assistant for Gujarat Police. Answer the question using ONLY the provided context.

CONTEXT:
{context}

QUESTION: {query}

INSTRUCTIONS:
- Answer in clear, professional language
- Cite specific sources using [Source N] notation
- If context doesn't contain answer, say "Insufficient information in available documents"
- Include relevant section numbers
```

**SOP Assistant:**
```
You are a police procedure expert. Provide step-by-step SOP guidance.

CONTEXT:
{context}

OFFICER QUESTION: {query}

Provide a numbered list of steps. Each step should be clear and actionable.
Cite relevant regulations using [Source N].
```

**Chargesheet Review:**
```
You are a chargesheet quality reviewer. Analyze the provided chargesheet.

CHARGESHEET CONTENT:
{context}

Check for:
1. Completeness (all required sections present)
2. Evidence inventory
3. Witness list
4. Section citations accuracy
5. Investigation chronology

Provide findings in structured format with completeness score (0-1).
```

### 5. LLM Generation

**Model:** Mistral 7B Instruct (4-bit quantized)
**Inference Engine:** llama.cpp
**Parameters:**
- `temperature`: 0.1 (factual, low creativity)
- `top_p`: 0.9
- `top_k`: 40
- `repeat_penalty`: 1.1
- `max_tokens`: 2048

**API Call:**
```python
response = llm_client.generate(
    prompt=prompt,
    max_tokens=2048,
    temperature=0.1
)
```

### 6. Response Formatting

**Output Structure:**
```json
{
  "query": "original user query",
  "use_case": "sop|chargesheet|general",
  "response": "generated answer text",
  "citations": [
    {
      "source": "Document Title",
      "doc_type": "court_ruling",
      "court": "Gujarat High Court",
      "score": 0.87
    }
  ],
  "num_results": 5,
  "metadata": {
    "vector_weight": 0.7,
    "max_context_tokens": 3000
  }
}
```

## Security Architecture

### Authentication

**Method:** JWT (JSON Web Tokens)

**Token Types:**
1. **Access Token** (15 min expiry)
   - Includes: user_id, username, role, district
   - Signed with HS256
   - Stored in memory (not localStorage)

2. **Refresh Token** (7 days expiry)
   - Stored in Redis with user_id key
   - Used to obtain new access token
   - Rotated on each use

**Flow:**
```
Login → Validate credentials → Generate tokens → Store refresh in Redis
     ↓
Subsequent requests include access token in Authorization header
     ↓
API validates token signature & expiry
     ↓
If expired, use refresh token to get new access token
```

### Authorization

**Role-Based Access Control (RBAC):**

| Role | Permissions |
|------|-------------|
| **admin** | All operations + user management + system config |
| **senior_officer** | All queries + export + review + manage officers |
| **officer** | All queries + review + limited export |
| **viewer** | Read-only access to public data |

**Implementation:** Decorator-based permission checks

```python
@requires_role("officer")
async def review_chargesheet(...):
    ...
```

### Encryption

**At Rest:**
- PII fields: AES-256-GCM encryption
- Encryption key: Stored in environment variable `ENCRYPTION_KEY`
- Database: PostgreSQL with encrypted volume (LUKS)

**In Transit:**
- TLS 1.3 for all HTTP connections
- Certificate: Self-signed (for air-gapped) or CA-signed

**PII Fields:**
- Names (complainant, accused, witnesses)
- Addresses
- Phone numbers
- ID numbers (Aadhaar, etc.)

### Audit Trail

**Every action logged:**
- User ID & username
- Timestamp
- Action type (login, query, export, etc.)
- Resource accessed
- IP address
- User agent
- Request/response

**Tamper-Proof Chain:**
- Each audit entry includes `prev_hash` (hash of previous entry)
- Any modification breaks the chain
- No UPDATE or DELETE allowed (database rules)

### Rate Limiting

**Implemented via Redis:**
- 100 requests per 15 minutes per user
- 10 login attempts per hour per IP
- Configurable per endpoint

## Deployment Architecture

### Production Deployment

```
┌─────────────────────────────────────────────────────────┐
│              Physical/Virtual Server                     │
│  Ubuntu Server 22.04 LTS                                 │
│  - 32GB RAM                                              │
│  - 16 CPU cores                                          │
│  - 500GB SSD                                             │
│  - Optional: NVIDIA GPU (RTX 3060 or better)             │
└─────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                                  │
┌───────▼──────┐                   ┌──────▼──────┐
│  Docker      │                   │  Systemd    │
│  Daemon      │                   │  Services   │
└───────┬──────┘                   └──────┬──────┘
        │                                  │
        │  ┌────────────────────────────┐ │
        └─►│  docker-compose.yml        │◄┘
           │  - 8 services              │
           │  - Named volumes           │
           │  - Bridge network          │
           └────────────────────────────┘
```

### Scaling Strategy

**Horizontal Scaling (Future):**
1. Multiple API server instances behind Nginx load balancer
2. Shared PostgreSQL (single writer, multiple readers via replicas)
3. Shared Redis cluster
4. Shared ChromaDB (distributed setup)
5. Multiple model servers with request queuing

**Vertical Scaling (Current):**
- Increase server resources
- GPU acceleration for model inference
- SSD for faster I/O

### High Availability

**Components:**
- API: Stateless, can run multiple instances
- Database: PostgreSQL replication (master-slave)
- Cache: Redis Sentinel for automatic failover
- Model Server: Multiple instances with load balancing

### Backup & Recovery

**Automated Backups:**
- PostgreSQL: Daily full dump + WAL archiving
- ChromaDB: Weekly snapshots
- Config files: Daily
- Model weights: Manual after training

**Retention:** 90 days

**Recovery Time Objective (RTO):** 2 hours
**Recovery Point Objective (RPO):** 24 hours

---

**Next:** See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.
