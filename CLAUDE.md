# Gujarat Police AI-Powered Investigation Support System

## Project Overview
On-premise, air-gapped RAG + Fine-tuned SLM (Mistral 7B) system for Gujarat Police.
3 core features: **SOP Assistant**, **Chargesheet Reviewer**, **Case Search**.
Team: 3 members | Timeline: 6 months | Budget: ~50K INR/month

## Architecture
```
User → React Dashboard → FastAPI → RAG Pipeline → ChromaDB + PostgreSQL → Mistral 7B (llama.cpp) → Response + Citations
```

## Tech Stack
- Python 3.11+, FastAPI, SQLAlchemy, Pydantic
- React 18 + TypeScript + Tailwind + shadcn/ui
- PostgreSQL 16, ChromaDB, Redis
- Mistral 7B (QLoRA fine-tuned), sentence-transformers, llama.cpp
- Tesseract + PaddleOCR (Gujarati/Hindi/English)
- Docker Compose (8 services)

## Data Sources (Verified Official)
1. **Indian Kanoon** (indiankanoon.org) - Court rulings full text
2. **eCourts India** (ecourts.gov.in) - Court orders, case status
3. **Gujarat High Court** (gujarathighcourt.nic.in) - HC judgments
4. **Supreme Court** (main.sci.gov.in) - SC judgments
5. **India Code** (indiacode.nic.in) - Bare acts (IPC, BNS, CrPC, BNSS)
6. **NCRB** (ncrb.gov.in) - Crime statistics
7. **Local Upload** - FIRs, Chargesheets, Panchnamas, Investigation Reports

## Critical Rules
1. **NEVER send police data to external APIs** - Everything on-premise
2. **Always encrypt PII** - Names, addresses, Aadhaar numbers
3. **Always include citations** - Every AI response references source documents
4. **Log everything** - Every query, response, access for audit trail
5. **Test in all 3 languages** - English, Hindi, Gujarati
6. **Support both old AND new codes** - IPC↔BNS, CrPC↔BNSS mappings built-in

## Key Commands
```bash
make setup          # Initial setup
make collect-all    # Scrape all verified data sources
make ingest-all     # OCR → Parse → Clean pipeline
make embed          # Create vector embeddings
make train          # QLoRA fine-tuning
make serve          # Start API server
make docker-up      # Start all services
make test           # Run tests
make health         # System health check
```

## Project Structure
- `src/data_sources/` - Scrapers for verified legal data
- `src/ingestion/` - OCR, document parsing, cleaning, normalization
- `src/retrieval/` - RAG pipeline with hybrid search + re-ranking
- `src/model/` - SLM fine-tuning and inference via llama.cpp
- `src/api/` - FastAPI backend with RBAC and audit
- `src/security/` - Encryption, JWT auth, audit logging
- `configs/` - YAML configs and section mapping JSONs
- `docker/` - Dockerfiles and compose config
