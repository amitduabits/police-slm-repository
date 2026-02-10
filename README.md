# Gujarat Police AI Investigation Support System

> On-premise, air-gapped AI system for investigation guidance, chargesheet review, and case search.

## Quick Start (Day 1)

```bash
# 1. Clone and setup
git clone <repo-url> gujpol-slm && cd gujpol-slm
chmod +x scripts/*.sh
bash scripts/setup_env.sh

# 2. Edit configuration
cp .env.example .env
nano .env  # Set passwords, keys

# 3. Start database services
make docker-up

# 4. Save IPC↔BNS section mappings
make collect-acts

# 5. Start collecting court rulings (runs in background)
make collect-kanoon &

# 6. Start API server
make serve
```

## Architecture

```
[Officer Browser] → [React Dashboard :3000]
                         ↓
                    [Nginx Reverse Proxy]
                         ↓
                    [FastAPI Backend :8000]
                     ↙        ↘
          [RAG Pipeline]   [Auth + Audit]
            ↙      ↘            ↓
  [ChromaDB]  [PostgreSQL]  [Redis Cache]
       ↓
  [Mistral 7B via llama.cpp :8080]
       ↓
  [Response + Citations]
```

## Data Sources (Verified/Official)

| Source | URL | Data Type | Status |
|--------|-----|-----------|--------|
| Indian Kanoon | indiankanoon.org | Court rulings (full text) | ✅ Scraper built |
| eCourts India | ecourts.gov.in | District court orders, case data | ✅ Scraper built |
| Gujarat High Court | gujarathighcourt.nic.in | HC judgments | ✅ Scraper built |
| Supreme Court | main.sci.gov.in | SC judgments (precedents) | ✅ Scraper built |
| India Code | indiacode.nic.in | Bare acts (IPC, BNS, CrPC, BNSS) | ✅ Scraper built |
| NCRB | ncrb.gov.in | Crime statistics | ✅ Scraper built |
| Local Upload | — | FIRs, Chargesheets, Panchnamas | 📁 Manual upload |

## Section Mapping (IPC ↔ BNS)

The system handles both old (IPC/CrPC) and new (BNS/BNSS) criminal codes:

```bash
# Convert section numbers
make convert S=302 FROM=IPC TO=BNS     # → BNS 103
make convert S=420 FROM=IPC TO=BNS     # → BNS 318(4)
make convert S=173 FROM=CrPC TO=BNSS   # → BNSS 193

# API endpoint
curl http://localhost:8000/utils/convert-section/302?from_code=IPC&to_code=BNS
```

## Project Structure

```
gujpol-slm/
├── CLAUDE.md                   # Claude Code instructions
├── .claude/settings.json       # Claude Code permissions
├── .env.example                # Environment template
├── pyproject.toml              # Python dependencies (Poetry)
├── docker-compose.yml          # All services
├── Makefile                    # Command shortcuts
├── configs/
│   ├── model_config.yaml       # SLM + embedding config
│   ├── ingestion_config.yaml   # OCR + parsing + chunking config
│   ├── ipc_to_bns_mapping.json # Generated mapping
│   └── crpc_to_bnss_mapping.json
├── src/
│   ├── data_sources/           # Verified legal data scrapers
│   │   ├── base.py             # Base scraper class
│   │   ├── indian_kanoon.py    # Court rulings
│   │   ├── ecourts.py          # eCourts district data
│   │   ├── gujarat_hc.py       # Gujarat HC judgments
│   │   ├── supreme_court.py    # SC judgments
│   │   ├── india_code.py       # Bare acts + section mappings
│   │   ├── ncrb.py             # Crime statistics
│   │   └── orchestrator.py     # Manages all sources
│   ├── ingestion/              # OCR, parsing, cleaning
│   ├── retrieval/              # RAG pipeline
│   ├── model/                  # Fine-tuning (QLoRA)
│   ├── api/main.py             # FastAPI backend
│   ├── dashboard/              # React frontend
│   ├── security/               # Auth, encryption, audit
│   ├── feedback/               # User feedback system
│   └── cli.py                  # Command-line interface
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.model
│   ├── Dockerfile.frontend
│   ├── Dockerfile.backup
│   ├── init-db.sql             # Database schema
│   ├── nginx.conf
│   └── prometheus.yml
├── scripts/
│   ├── setup_env.sh            # Full environment setup
│   └── backup.sh               # Backup script
├── data/
│   ├── raw/                    # Upload local docs here
│   ├── processed/              # OCR → Structured → Cleaned
│   ├── embeddings/             # ChromaDB vectors
│   ├── training/               # Fine-tuning data
│   └── sources/                # Scraped verified data
└── tests/
```

## Common Commands

```bash
# Data Collection
make collect-all              # All sources
make collect-kanoon           # Indian Kanoon court rulings
make validate-data            # Check data quality

# Ingestion
make ingest-all               # Full OCR → Parse → Clean pipeline

# Embedding & Search
make embed                    # Create vector embeddings
make search Q="murder bail Gujarat"

# Model Training
make train-data               # Prepare fine-tuning data
make train                    # QLoRA fine-tuning

# Development
make serve                    # Start API (dev mode)
make test                     # Run tests
make health                   # System health check

# Docker (Production)
make docker-build             # Build all images
make docker-up                # Start everything
make docker-logs              # View logs
make backup                   # Manual backup
```

## Team Allocation (6-Month POC)

| Phase | Weeks | Lead | Member 1 | Member 2 |
|-------|-------|------|----------|----------|
| 1: Data Pipeline | 1-4 | Architecture | OCR/Extraction | Cleaning/Structure |
| 2: RAG + SLM | 5-12 | RAG Pipeline | Fine-tuning | Evaluation |
| 3: Dashboard | 13-20 | Security/Deploy | Backend API | Frontend |
| 4: Training | 21-24 | Strategy | Tech Docs | Content |

## Security

- **Air-gapped**: No police data leaves the network
- **Encrypted**: AES-256 at rest, TLS 1.3 in transit
- **RBAC**: Admin → Senior Officer → Officer → Viewer
- **Audit**: Every action logged with tamper-proof chain
- **PII**: Tagged, encrypted with separate key

## License

Internal use only - Gujarat Police.
