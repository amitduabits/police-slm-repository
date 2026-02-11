# Gujarat Police AI Investigation Support System

A comprehensive on-premise investigation support platform leveraging Retrieval-Augmented Generation (RAG) and fine-tuned Small Language Models (SLM) to enhance criminal investigation efficiency across Gujarat Police.

## Overview

This system provides three core capabilities for investigation officers:

1. **SOP Assistant** - Procedural guidance for investigation workflows
2. **Chargesheet Reviewer** - Automated completeness checks and quality assurance
3. **Case Search** - Semantic search across court rulings, precedents, and legal documents

### Key Features

- **On-Premise & Air-Gapped** - Complete data sovereignty with no external API calls
- **Multi-Lingual Support** - English, Hindi, and Gujarati language processing
- **Dual Criminal Code Support** - Seamless IPC↔BNS and CrPC↔BNSS translation
- **Citation-Based Responses** - Every answer includes verifiable source references
- **Role-Based Access Control** - Hierarchical permissions from viewer to admin
- **Comprehensive Audit Trail** - Tamper-proof logging for compliance

## Architecture

```
┌─────────────────┐
│ React Dashboard │ (Port 3000)
│   TypeScript    │
└────────┬────────┘
         │
    ┌────▼────┐
    │  Nginx  │ Reverse Proxy
    └────┬────┘
         │
┌────────▼────────┐
│  FastAPI Server │ (Port 8000)
│    Python 3.11  │
└───┬─────────┬───┘
    │         │
    │    ┌────▼────────┐
    │    │ RAG Pipeline│
    │    └─┬─────────┬─┘
    │      │         │
┌───▼───┐ ┌▼────────▼┐ ┌──────────┐
│Redis  │ │PostgreSQL│ │ ChromaDB │
│Cache  │ │  + JSONB │ │  Vector  │
└───────┘ └──────────┘ └─────┬────┘
                              │
                    ┌─────────▼─────────┐
                    │   Mistral 7B      │
                    │   (llama.cpp)     │
                    │   Port 8080       │
                    └───────────────────┘
```

## Technology Stack

### Backend
- **Python 3.11+** - Core application language
- **FastAPI** - High-performance async web framework
- **SQLAlchemy 2.0** - Database ORM with async support
- **Pydantic V2** - Data validation and serialization
- **PostgreSQL 16** - Primary relational database
- **ChromaDB** - Vector database for embeddings
- **Redis 7** - Caching and session management

### Machine Learning
- **Mistral 7B Instruct** - Base language model (QLoRA fine-tuned)
- **llama.cpp** - Efficient model inference engine
- **sentence-transformers** - Multilingual embeddings
- **PyTorch 2.4** - Deep learning framework
- **PEFT + QLoRA** - Parameter-efficient fine-tuning
- **bitsandbytes** - 4-bit quantization

### Document Processing
- **Tesseract OCR** - Primary OCR engine (English/Hindi)
- **PaddleOCR** - Fallback OCR (Gujarati support)
- **pdf2image** - PDF to image conversion
- **python-docx** - Word document processing
- **pdfplumber** - PDF text extraction

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Component library
- **Vite** - Build tool

### Infrastructure
- **Docker & Docker Compose** - Container orchestration
- **Nginx** - Reverse proxy and load balancing
- **Prometheus** - Metrics collection
- **Grafana** - Monitoring dashboards

## Quick Start

### Prerequisites
- Python 3.11 or higher
- Docker & Docker Compose
- 16GB RAM minimum (32GB recommended)
- 100GB disk space

### Installation

```bash
# Clone repository
git clone <repository-url> gujpol-slm
cd gujpol-slm

# Setup environment
chmod +x scripts/*.sh
bash scripts/setup_env.sh

# Configure environment variables
cp .env.example .env
nano .env  # Edit with your settings

# Install dependencies
make install

# Create directory structure and save section mappings
make setup
```

### Running the System

```bash
# Start all services (PostgreSQL, ChromaDB, Redis, API, Frontend)
make docker-up

# Verify all services are healthy
make health

# Access the application
# Dashboard: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Monitoring: http://localhost:3001 (Grafana)
```

### Initial Data Collection

```bash
# Collect bare acts and section mappings (required first)
make collect-acts

# Scrape verified legal data sources
make collect-kanoon    # Indian Kanoon court rulings
make collect-ecourts   # District court data
make collect-gujhc     # Gujarat High Court judgments
make collect-sci       # Supreme Court judgments

# Or collect all sources
make collect-all
```

### Document Ingestion

```bash
# Place your documents in data/raw/
# - FIRs → data/raw/firs/
# - Chargesheets → data/raw/chargesheets/
# - Panchnamas → data/raw/panchnamas/

# Run full ingestion pipeline (OCR → Parse → Clean)
make ingest-all

# Create vector embeddings
make embed
```

## Data Sources

All data sources are official and verified:

| Source | URL | Content | Status |
|--------|-----|---------|--------|
| **Indian Kanoon** | indiankanoon.org | Court rulings (full text) | ✓ Implemented |
| **eCourts India** | ecourts.gov.in | District court orders | ✓ Implemented |
| **Gujarat High Court** | gujarathighcourt.nic.in | HC judgments | ✓ Implemented |
| **Supreme Court** | main.sci.gov.in | SC judgments | ✓ Implemented |
| **India Code** | indiacode.nic.in | Bare acts (IPC/BNS/CrPC/BNSS) | ✓ Implemented |
| **NCRB** | ncrb.gov.in | Crime statistics | ✓ Implemented |
| **Local Upload** | Manual | FIRs, Chargesheets, Panchnamas | ✓ Supported |

## Section Code Conversion

The system supports both old and new criminal codes:

```bash
# Command line conversion
make convert S=302 FROM=IPC TO=BNS
# Output: IPC Section 302 → BNS Section 103 (Murder)

make convert S=420 FROM=IPC TO=BNS
# Output: IPC Section 420 → BNS Section 318(4) (Cheating)

# API endpoint
curl http://localhost:8000/utils/convert-section/302?from_code=IPC&to_code=BNS
```

Mappings are automatically generated from India Code and stored in:
- `configs/ipc_to_bns_mapping.json`
- `configs/crpc_to_bnss_mapping.json`
- `configs/iea_to_bsa_mapping.json`

## Core Features

### 1. SOP Assistant

Provides step-by-step procedural guidance for investigation tasks:
- Crime scene preservation
- Evidence collection protocols
- Witness examination procedures
- FIR registration guidelines
- Investigation report preparation

**API Endpoint:** `POST /sop/suggest`

### 2. Chargesheet Reviewer

Automated review of chargesheet documents:
- Completeness checks (required sections, evidence)
- Section citation validation
- Consistency checks between FIR and chargesheet
- Missing information flagging
- Quality scoring

**API Endpoint:** `POST /chargesheet/review`

### 3. Case Search

Semantic search across all indexed documents:
- Natural language queries
- Hybrid search (vector + keyword)
- Multi-lingual support
- Filter by court, date, district, section
- Similar case finding

**API Endpoint:** `POST /search/query`

## Security Features

### Data Protection
- **AES-256 Encryption** at rest for all sensitive data
- **TLS 1.3** for data in transit
- **PII Tagging & Encryption** for personally identifiable information
- **Air-Gapped Deployment** - No external API calls

### Authentication & Authorization
- **JWT-based Authentication** with refresh tokens
- **Role-Based Access Control** (Admin, Senior Officer, Officer, Viewer)
- **Account Lockout** after failed login attempts
- **Session Management** via Redis

### Audit & Compliance
- **Tamper-Proof Audit Logs** with chain hashing
- **Complete Request Logging** (query, response, user, timestamp)
- **No-Delete Policy** on audit logs (append-only)
- **90-Day Audit Retention** (configurable)

## Project Structure

```
gujpol-slm/
├── configs/                    # Configuration files
│   ├── model_config.yaml       # SLM training & inference config
│   ├── ingestion_config.yaml   # OCR, parsing, chunking config
│   └── *_mapping.json          # Section code mappings
├── data/
│   ├── raw/                    # Uploaded documents (FIR, chargesheet, etc.)
│   ├── processed/              # OCR → Structured → Cleaned
│   ├── embeddings/             # ChromaDB vector storage
│   ├── training/               # Fine-tuning datasets
│   └── sources/                # Scraped legal documents
├── docker/                     # Docker configurations
│   ├── Dockerfile.*            # Service-specific Dockerfiles
│   ├── init-db.sql             # PostgreSQL schema
│   └── nginx.conf              # Reverse proxy config
├── models/                     # Fine-tuned model weights
├── scripts/                    # Deployment & maintenance scripts
├── src/
│   ├── api/                    # FastAPI backend
│   │   ├── main.py             # Application entry point
│   │   ├── routes/             # API route handlers
│   │   ├── models.py           # Database models (SQLAlchemy)
│   │   ├── schemas.py          # Request/response schemas
│   │   └── auth.py             # Authentication logic
│   ├── data_sources/           # Web scrapers for legal data
│   │   ├── indian_kanoon.py    # Court rulings scraper
│   │   ├── ecourts.py          # eCourts scraper
│   │   ├── india_code.py       # Bare acts & mappings
│   │   └── orchestrator.py     # Scraping coordinator
│   ├── ingestion/              # Document processing pipeline
│   │   ├── ocr_pipeline.py     # OCR processing
│   │   ├── processor.py        # Document parsing
│   │   └── section_normalizer.py # Section code normalization
│   ├── retrieval/              # RAG pipeline
│   │   ├── rag_pipeline.py     # End-to-end RAG
│   │   ├── embeddings.py       # Vector search
│   │   ├── chunker.py          # Text chunking
│   │   └── prompts.py          # Prompt templates
│   ├── model/                  # SLM training & inference
│   │   └── inference.py        # llama.cpp integration
│   ├── security/               # Security utilities
│   └── cli.py                  # Command-line interface
└── tests/                      # Test suites

```

## Common Commands

```bash
# Development
make serve          # Start API server (development mode)
make test           # Run test suite
make lint           # Code quality checks
make format         # Auto-format code

# Data Pipeline
make collect-all    # Scrape all verified sources
make ingest-all     # OCR → Parse → Clean pipeline
make embed          # Create vector embeddings
make search Q="your query here"

# Model Training
make train-data     # Prepare training datasets
make train          # QLoRA fine-tuning
make evaluate       # Model evaluation

# Docker Operations
make docker-build   # Build all Docker images
make docker-up      # Start all services
make docker-down    # Stop all services
make docker-logs    # View service logs

# Maintenance
make backup         # Manual backup
make health         # System health check
make stats          # Usage statistics
```

## Performance Benchmarks

Target metrics for system evaluation:

| Metric | Target | Description |
|--------|--------|-------------|
| **Recall@5** | ≥80% | Top 5 results contain relevant answer |
| **Precision@5** | ≥70% | Top 5 results are relevant |
| **Response Time** | <10s | End-to-end query response |
| **Expert Rating** | ≥3.5/5 | Average rating by domain experts |
| **Hallucination Rate** | <5% | Responses with unsupported claims |

## Deployment

For production deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md).

For detailed architecture documentation, see [ARCHITECTURE.md](./ARCHITECTURE.md).

For API reference, see [API_REFERENCE.md](./API_REFERENCE.md).

## Support & Maintenance

### System Requirements
- **CPU:** 8 cores minimum (16 recommended)
- **RAM:** 16GB minimum (32GB recommended)
- **GPU:** Optional (NVIDIA with CUDA support) for faster inference
- **Storage:** 100GB minimum (500GB recommended for production)

### Backup Schedule
- **Database:** Automated daily backups (2 AM)
- **Vector Store:** Weekly backups
- **Model Weights:** Manual backup after training
- **Retention:** 90 days (configurable)

### Monitoring
- **Prometheus:** Metrics collection (port 9090)
- **Grafana:** Visualization dashboards (port 3001)
- **Health Check:** `GET /utils/health`

## License

Internal use only - Gujarat Police Department.

This system contains sensitive law enforcement data and is restricted to authorized personnel only.

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture and design
- [SETUP.md](./SETUP.md) - Detailed setup instructions
- [DATA_PIPELINE.md](./DATA_PIPELINE.md) - Data collection and processing
- [RAG_SYSTEM.md](./RAG_SYSTEM.md) - RAG pipeline documentation
- [API_REFERENCE.md](./API_REFERENCE.md) - API endpoint reference
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Production deployment guide
- [DEVELOPMENT.md](./DEVELOPMENT.md) - Developer guidelines
