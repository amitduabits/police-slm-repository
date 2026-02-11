# Setup Guide

Complete installation and configuration guide for the Gujarat Police AI Investigation Support System.

## Table of Contents

- [System Requirements](#system-requirements)
- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Data Collection](#data-collection)
- [Testing Installation](#testing-installation)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

| Component | Specification |
|-----------|--------------|
| **OS** | Ubuntu 22.04 LTS (recommended) / Windows 10+ / macOS 12+ |
| **CPU** | 8 cores (x86_64) |
| **RAM** | 16GB |
| **Storage** | 100GB SSD |
| **Network** | Air-gapped or isolated network |

### Recommended Requirements

| Component | Specification |
|-----------|--------------|
| **OS** | Ubuntu 22.04 LTS Server |
| **CPU** | 16 cores (x86_64) |
| **RAM** | 32GB |
| **Storage** | 500GB NVMe SSD |
| **GPU** | NVIDIA RTX 3060 or better (optional, for faster inference) |
| **Network** | Air-gapped with 1Gbps internal network |

### GPU Requirements (Optional)

If using GPU acceleration:
- NVIDIA GPU with CUDA support
- CUDA Toolkit 12.0+
- NVIDIA Driver 525+
- Minimum 8GB VRAM

## Prerequisites

### 1. Install Docker & Docker Compose

**Ubuntu/Debian:**
```bash
# Update package index
sudo apt update

# Install dependencies
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Add current user to docker group (avoid using sudo)
sudo usermod -aG docker $USER
newgrp docker
```

**Windows:**
1. Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Enable WSL 2 backend
3. Restart system after installation

**macOS:**
1. Download and install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
2. Start Docker Desktop application

### 2. Install Python 3.11+

**Ubuntu/Debian:**
```bash
# Add deadsnakes PPA for Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Verify installation
python3.11 --version
```

**Windows:**
1. Download Python 3.11 from [python.org](https://www.python.org/downloads/)
2. Run installer, check "Add Python to PATH"
3. Verify: `python --version`

**macOS:**
```bash
# Using Homebrew
brew install python@3.11

# Verify
python3.11 --version
```

### 3. Install Poetry (Python Package Manager)

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Verify installation
poetry --version
```

### 4. Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt install -y tesseract-ocr tesseract-ocr-hin tesseract-ocr-guj
```

**Windows:**
1. Download installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install to `C:\Program Files\Tesseract-OCR`
3. Add to PATH: `C:\Program Files\Tesseract-OCR`

**macOS:**
```bash
brew install tesseract tesseract-lang
```

### 5. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    poppler-utils \
    libmagic1 \
    git \
    make
```

**Windows:**
- Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Install [Git for Windows](https://git-scm.com/download/win)

## Installation Steps

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url> gujpol-slm
cd gujpol-slm

# Make scripts executable (Linux/macOS)
chmod +x scripts/*.sh
```

### Step 2: Environment Setup

```bash
# Run automated setup script
bash scripts/setup_env.sh

# This script will:
# - Check Python version
# - Install Poetry dependencies
# - Create directory structure
# - Copy environment template
```

**Manual alternative:**
```bash
# Install Python dependencies
poetry install

# Create directory structure
mkdir -p data/{raw/{firs,chargesheets,rulings,panchnamas,investigation_reports},processed/{ocr,structured,cleaned},embeddings,training,sources}
mkdir -p configs logs backups models

# Copy environment template
cp .env.example .env
```

### Step 3: Configure Environment Variables

Edit `.env` file with your configuration:

```bash
nano .env  # or use any text editor
```

**Critical variables to configure:**

```bash
# Application
APP_ENV=production
DEBUG=false

# PostgreSQL
POSTGRES_USER=gujpol_admin
POSTGRES_PASSWORD=<strong-password-here>  # CHANGE THIS!
POSTGRES_DB=gujpol_slm
POSTGRES_HOST=db-postgres
POSTGRES_PORT=5432

# Redis
REDIS_PASSWORD=<strong-password-here>  # CHANGE THIS!
REDIS_HOST=cache-redis
REDIS_PORT=6379

# ChromaDB
CHROMA_HOST=db-chroma
CHROMA_PORT=8100

# Security
JWT_SECRET_KEY=<generate-random-string-here>  # CHANGE THIS!
ENCRYPTION_KEY=<32-byte-base64-encoded-key>   # CHANGE THIS!
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Model Server
MODEL_SERVER_HOST=model-server
MODEL_SERVER_PORT=8080
MODEL_PATH=/models/gujpol-mistral-7b-q4.gguf
MODEL_GPU_LAYERS=35  # Set to 0 if no GPU
MODEL_THREADS=4

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
GRAFANA_ADMIN_PASSWORD=<strong-password-here>  # CHANGE THIS!

# Backup
BACKUP_SCHEDULE_CRON="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS=90
```

**Generate secure keys:**

```bash
# Generate JWT secret (32 bytes)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate encryption key (32 bytes, base64 encoded)
python3 -c "import base64, secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

### Step 4: Download Model Weights

**Option A: Download Pre-quantized Model (Recommended)**

```bash
# Create models directory
mkdir -p models

# Download pre-quantized Mistral 7B model (4-bit GGUF)
# NOTE: This requires internet access. Download on a connected machine,
# then transfer to air-gapped server via USB/secure transfer

cd models

# Using wget (if available)
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/mistral-7b-instruct-v0.3.Q4_K_M.gguf \
     -O gujpol-mistral-7b-q4.gguf

# OR using curl
curl -L https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/mistral-7b-instruct-v0.3.Q4_K_M.gguf \
     -o gujpol-mistral-7b-q4.gguf

cd ..
```

**Option B: Fine-tune from Base Model (Advanced)**

```bash
# Download base model and fine-tune (requires GPU)
# See MODEL_TRAINING.md for detailed instructions
make train
```

### Step 5: Initialize Configuration

```bash
# Save section mappings (IPC↔BNS, CrPC↔BNSS)
make setup

# This will:
# - Create all necessary directories
# - Fetch section mappings from India Code
# - Save to configs/ directory
# - Create sample .env file
```

### Step 6: Start Services

```bash
# Build Docker images
make docker-build

# Start all services (database, cache, API, frontend, model server)
make docker-up

# Check service status
docker compose ps

# Expected output:
# NAME                 STATUS              PORTS
# gujpol-api           Up (healthy)        0.0.0.0:8000->8000/tcp
# gujpol-frontend      Up                  0.0.0.0:3000->80/tcp
# gujpol-postgres      Up (healthy)        0.0.0.0:5432->5432/tcp
# gujpol-chroma        Up                  0.0.0.0:8100->8000/tcp
# gujpol-redis         Up (healthy)        0.0.0.0:6379->6379/tcp
# gujpol-model         Up (healthy)        0.0.0.0:8080->8080/tcp
# gujpol-prometheus    Up                  0.0.0.0:9090->9090/tcp
# gujpol-grafana       Up                  0.0.0.0:3001->3000/tcp
```

**Wait for all services to be healthy (may take 1-2 minutes)**

```bash
# Watch service logs
make docker-logs

# Or follow logs for specific service
docker compose logs -f app-api
```

### Step 7: Verify Installation

```bash
# Check system health
make health

# Expected output:
# ✓ API Server: healthy
# ✓ PostgreSQL: healthy
# ✓ Redis: healthy
# ✓ ChromaDB: healthy
# ✓ Model Server: healthy
```

**Manual verification:**

```bash
# Test API
curl http://localhost:8000/health

# Test model server
curl http://localhost:8080/health

# Test database connection
docker compose exec db-postgres pg_isready -U gujpol_admin
```

## Configuration

### Model Configuration

Edit `configs/model_config.yaml`:

```yaml
# Base Model
base_model: "mistralai/Mistral-7B-Instruct-v0.3"

# Quantization (for inference)
quantization:
  method: "gguf"
  bits: 4
  group_size: 128

# QLoRA Fine-tuning
qlora:
  r: 64
  alpha: 16
  dropout: 0.1
  target_modules: ["q_proj", "v_proj", "k_proj", "o_proj"]

# Inference (llama.cpp)
inference:
  context_size: 4096
  gpu_layers: 35  # Set to 0 for CPU-only
  threads: 4
  temperature: 0.1
  top_p: 0.9
  max_tokens: 2048

# Embedding Model
embedding:
  model: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
  device: "cpu"  # or "cuda" if GPU available
  batch_size: 64
```

### Ingestion Configuration

Edit `configs/ingestion_config.yaml`:

```yaml
# OCR Pipeline
ocr:
  primary_engine: "tesseract"
  fallback_engine: "paddleocr"
  languages: ["eng", "hin", "guj"]
  confidence_threshold: 0.80
  preprocessing:
    deskew: true
    denoise: true
    binarize: true
    dpi: 300

# Chunking Strategy
chunking:
  default_chunk_size: 500  # tokens
  chunk_overlap: 100
  respect_paragraphs: true
  respect_sections: true

# Data Sources
data_sources:
  scraper_delay_seconds: 2
  sources:
    indian_kanoon:
      enabled: true
      max_results_per_query: 50
    ecourts:
      enabled: true
      districts: ["ahmedabad", "surat", "vadodara", "rajkot"]
    gujarat_hc:
      enabled: true
      max_per_combo: 50
```

## Database Setup

### Initialize Schema

The database schema is automatically initialized on first startup via `docker/init-db.sql`.

**Verify schema:**

```bash
# Connect to PostgreSQL
docker compose exec db-postgres psql -U gujpol_admin -d gujpol_slm

# List tables
\dt

# Expected tables:
# users, documents, firs, chargesheets, court_rulings,
# section_mappings, audit_log, feedback, search_history,
# training_progress, system_metrics

# Exit
\q
```

### Create Admin User

```bash
# Connect to database
docker compose exec db-postgres psql -U gujpol_admin -d gujpol_slm

# Create admin user (password: changeme)
INSERT INTO users (username, email, password_hash, full_name, role, district)
VALUES (
    'admin',
    'admin@gujpol.gov.in',
    '$2b$12$LQA4.zKz7zXb8hXqzLfzQeZ7UZ9qXjN8Rj7qF5Q3qF5Q3qF5Q3qF5',
    'System Administrator',
    'admin',
    'Gandhinagar'
);

# Exit
\q
```

**Change default password immediately after first login!**

### Backup Database

```bash
# Manual backup
make backup

# This creates:
# - backups/postgres_YYYYMMDD_HHMMSS.sql.gz
# - backups/chroma_YYYYMMDD_HHMMSS.tar.gz
```

## Data Collection

### Step 1: Collect Section Mappings (Required)

```bash
# Fetch bare acts and generate section mappings
make collect-acts

# This creates:
# - configs/ipc_to_bns_mapping.json
# - configs/crpc_to_bnss_mapping.json
# - configs/iea_to_bsa_mapping.json

# Verify mappings
ls -lh configs/*_mapping.json
```

### Step 2: Scrape Legal Data Sources

```bash
# Scrape all verified sources (takes 2-4 hours)
make collect-all

# Or scrape individual sources:
make collect-kanoon    # Indian Kanoon court rulings (~30 min)
make collect-ecourts   # eCourts district data (~45 min)
make collect-gujhc     # Gujarat HC judgments (~20 min)
make collect-sci       # Supreme Court judgments (~30 min)
make collect-ncrb      # NCRB statistics (~10 min)
```

**Monitor progress:**

```bash
# Check logs
tail -f logs/data_collection.log

# Check collected files
ls -lh data/sources/
```

### Step 3: Upload Local Documents

```bash
# Place documents in appropriate directories:

# FIRs (PDF/JPG/PNG)
cp /path/to/fir_documents/* data/raw/firs/

# Chargesheets
cp /path/to/chargesheet_documents/* data/raw/chargesheets/

# Panchnamas
cp /path/to/panchnama_documents/* data/raw/panchnamas/

# Investigation reports
cp /path/to/investigation_reports/* data/raw/investigation_reports/
```

### Step 4: Process Documents

```bash
# Run full ingestion pipeline (OCR → Parse → Clean)
make ingest-all

# This performs:
# 1. OCR extraction (Tesseract/PaddleOCR)
# 2. Document parsing (extract structured fields)
# 3. Data cleaning (normalization, PII encryption, deduplication)

# Monitor progress
tail -f logs/ingestion.log

# Check processed documents
ls -lh data/processed/cleaned/
```

**Process stages can be run individually:**

```bash
# Only OCR
make ingest-ocr

# Only parsing
make ingest-parse

# Only cleaning
make ingest-clean
```

### Step 5: Create Embeddings

```bash
# Generate vector embeddings and store in ChromaDB
make embed

# This takes ~2-4 hours depending on document count
# Monitor progress:
tail -f logs/embedding.log

# Verify embeddings
curl http://localhost:8100/api/v1/collections
```

### Step 6: Validate Data

```bash
# Run data quality checks
make validate-data

# This checks:
# - Document count in PostgreSQL vs ChromaDB
# - Required fields present
# - Section citations normalized
# - PII properly encrypted
# - No duplicate documents (by content hash)
```

## Testing Installation

### 1. Access Dashboard

Open web browser and navigate to:
```
http://localhost:3000
```

**Login credentials:**
- Username: `admin`
- Password: `changeme`

**Change password immediately after first login!**

### 2. Test API Endpoints

```bash
# Login and get JWT token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme"}' \
  | jq -r '.access_token')

# Test search endpoint
curl -X POST http://localhost:8000/search/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the punishment for murder under IPC 302?"}'

# Test SOP endpoint
curl -X POST http://localhost:8000/sop/suggest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scenario":"crime scene preservation"}'

# Test section conversion
curl "http://localhost:8000/utils/convert-section/302?from_code=IPC&to_code=BNS"
```

### 3. Run Test Suite

```bash
# Run all tests
make test

# Run specific test categories
make test-unit         # Unit tests only
make test-integration  # Integration tests only

# Generate coverage report
make test
# Coverage report: htmlcov/index.html
```

### 4. Check Monitoring

**Prometheus (Metrics):**
```
http://localhost:9090
```

**Grafana (Dashboards):**
```
http://localhost:3001
```
- Username: `admin`
- Password: (from GRAFANA_ADMIN_PASSWORD in .env)

### 5. Test Search Functionality

```bash
# Test vector search
make search Q="murder bail guidelines Gujarat"

# Expected output:
# Top 5 results:
# 1. [Court Ruling] ... (score: 0.87)
# 2. [Bare Act] Section 302 IPC ... (score: 0.82)
# ...
```

## Troubleshooting

### Issue: Docker services won't start

**Solution:**
```bash
# Check Docker daemon status
sudo systemctl status docker

# Start Docker daemon
sudo systemctl start docker

# Check for port conflicts
sudo netstat -tulpn | grep -E '8000|3000|5432|6379|8100'

# Stop conflicting services or change ports in .env
```

### Issue: Database connection failed

**Solution:**
```bash
# Check PostgreSQL container logs
docker compose logs db-postgres

# Verify PostgreSQL is running
docker compose ps db-postgres

# Test connection
docker compose exec db-postgres pg_isready -U gujpol_admin

# Check credentials in .env match docker-compose.yml
```

### Issue: Model server fails to start

**Solution:**
```bash
# Check if model file exists
ls -lh models/gujpol-mistral-7b-q4.gguf

# Check model server logs
docker compose logs model-server

# Reduce GPU layers if out of memory
# Edit .env: MODEL_GPU_LAYERS=0 (CPU only)
docker compose restart model-server

# Increase memory limit in docker-compose.yml
```

### Issue: OCR extraction fails

**Solution:**
```bash
# Check Tesseract installation
tesseract --version

# Check language data installed
tesseract --list-langs

# Install missing languages (Ubuntu)
sudo apt install tesseract-ocr-hin tesseract-ocr-guj

# Check image quality (must be >= 300 DPI)
identify -verbose data/raw/firs/sample.jpg | grep Resolution
```

### Issue: Embeddings not generated

**Solution:**
```bash
# Check ChromaDB is running
curl http://localhost:8100/api/v1/heartbeat

# Check embedding model downloaded
ls -lh ~/.cache/torch/sentence_transformers/

# Re-run embedding with verbose logging
python -m src.cli embed create --input-dir data/processed/cleaned --verbose

# Check disk space
df -h
```

### Issue: Search returns no results

**Solution:**
```bash
# Verify documents are indexed
curl http://localhost:8100/api/v1/collections/all_documents

# Check document count in PostgreSQL
docker compose exec db-postgres psql -U gujpol_admin -d gujpol_slm \
  -c "SELECT COUNT(*) FROM documents WHERE is_indexed = true;"

# Re-index if needed
make embed
```

### Issue: API responds slowly

**Solution:**
```bash
# Check resource usage
docker stats

# Increase cache TTL in .env
# CACHE_TTL_SECONDS=900

# Add more API replicas (advanced)
docker compose up -d --scale app-api=3

# Check model server GPU usage
nvidia-smi  # If using GPU
```

### Getting Help

**Check logs:**
```bash
# All services
make docker-logs

# Specific service
docker compose logs -f app-api
docker compose logs -f model-server

# Application logs
tail -f logs/api.log
tail -f logs/ingestion.log
```

**Health check:**
```bash
make health
```

**System statistics:**
```bash
make stats
```

## Next Steps

1. **Read API Documentation:** [API_REFERENCE.md](./API_REFERENCE.md)
2. **Configure Data Pipeline:** [DATA_PIPELINE.md](./DATA_PIPELINE.md)
3. **Learn RAG System:** [RAG_SYSTEM.md](./RAG_SYSTEM.md)
4. **Deploy to Production:** [DEPLOYMENT.md](./DEPLOYMENT.md)

---

**For production deployment, see [DEPLOYMENT.md](./DEPLOYMENT.md).**
