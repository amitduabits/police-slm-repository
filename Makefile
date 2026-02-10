# Gujarat Police SLM - Makefile
# Common commands for development and deployment

.PHONY: help setup install dev collect ingest embed train serve test lint clean docker-up docker-down backup

# Default target
help:
	@echo "Gujarat Police SLM - Available Commands:"
	@echo ""
	@echo "  Setup & Install:"
	@echo "    make setup          - Full initial setup (install deps, create dirs, save mappings)"
	@echo "    make install        - Install Python dependencies via Poetry"
	@echo "    make install-dev    - Install with dev dependencies"
	@echo ""
	@echo "  Data Collection:"
	@echo "    make collect-all    - Run all data source scrapers"
	@echo "    make collect-kanoon - Scrape Indian Kanoon court rulings"
	@echo "    make collect-ecourts- Scrape eCourts district court data"
	@echo "    make collect-gujhc  - Scrape Gujarat High Court judgments"
	@echo "    make collect-sci    - Scrape Supreme Court judgments"
	@echo "    make collect-ncrb   - Download NCRB crime statistics"
	@echo "    make collect-acts   - Fetch bare acts and save section mappings"
	@echo "    make validate-data  - Validate collected data"
	@echo ""
	@echo "  Ingestion Pipeline:"
	@echo "    make ingest-ocr     - Run OCR on raw documents"
	@echo "    make ingest-parse   - Parse OCR output into structured data"
	@echo "    make ingest-clean   - Clean and normalize data"
	@echo "    make ingest-all     - Run full ingestion pipeline"
	@echo ""
	@echo "  Embedding & Search:"
	@echo "    make embed          - Create embeddings and store in ChromaDB"
	@echo "    make search Q='query'- Test search against vector store"
	@echo ""
	@echo "  Model:"
	@echo "    make train-data     - Prepare fine-tuning training data"
	@echo "    make train          - Fine-tune SLM with QLoRA"
	@echo "    make evaluate       - Evaluate fine-tuned model"
	@echo ""
	@echo "  Server:"
	@echo "    make serve          - Start FastAPI dev server"
	@echo "    make serve-prod     - Start production server"
	@echo ""
	@echo "  Docker:"
	@echo "    make docker-up      - Start all Docker services"
	@echo "    make docker-down    - Stop all Docker services"
	@echo "    make docker-logs    - View Docker logs"
	@echo "    make docker-build   - Build Docker images"
	@echo ""
	@echo "  Testing & Quality:"
	@echo "    make test           - Run all tests"
	@echo "    make lint           - Run linter"
	@echo "    make format         - Format code"
	@echo ""
	@echo "  Utilities:"
	@echo "    make convert S=302 FROM=IPC TO=BNS  - Convert section number"
	@echo "    make stats          - Show system statistics"
	@echo "    make health         - Check system health"
	@echo "    make backup         - Run manual backup"
	@echo "    make clean          - Clean temporary files"

# ============================================
# Setup
# ============================================
setup: install
	@mkdir -p data/{raw/{firs,chargesheets,rulings,panchnamas,investigation_reports},processed/{ocr,structured,cleaned},embeddings,training,sources}
	@mkdir -p configs logs backups models
	@cp -n .env.example .env 2>/dev/null || true
	@python -m src.cli collect save-mappings
	@echo "✅ Setup complete! Edit .env with your configuration."

install:
	poetry install --no-dev

install-dev:
	poetry install
	pre-commit install 2>/dev/null || true

# ============================================
# Data Collection
# ============================================
collect-all:
	python -m src.cli collect run --source all

collect-kanoon:
	python -m src.cli collect run --source indian_kanoon --max-results 100

collect-ecourts:
	python -m src.cli collect run --source ecourts --max-results 50

collect-gujhc:
	python -m src.cli collect run --source gujarat_hc --max-results 50

collect-sci:
	python -m src.cli collect run --source supreme_court --max-results 30

collect-ncrb:
	python -m src.cli collect run --source ncrb

collect-acts:
	python -m src.cli collect run --source india_code
	python -m src.cli collect save-mappings

validate-data:
	python -m src.cli collect validate

# ============================================
# Ingestion
# ============================================
ingest-ocr:
	python -m src.cli ingest ocr --input-dir data/raw --output-dir data/processed/ocr

ingest-parse:
	python -m src.cli ingest parse --input-dir data/processed/ocr --output-dir data/processed/structured

ingest-clean:
	python -m src.cli ingest clean --input-dir data/processed/structured --output-dir data/processed/cleaned

ingest-all: ingest-ocr ingest-parse ingest-clean

# ============================================
# Embedding
# ============================================
embed:
	python -m src.cli embed create --input-dir data/processed/cleaned

search:
	python -m src.cli embed search "$(Q)" --top-k 5

# ============================================
# Model
# ============================================
train-data:
	python -m src.cli model prepare-data

train:
	python -m src.cli model train

evaluate:
	python -m src.cli model evaluate

# ============================================
# Server
# ============================================
serve:
	python -m src.cli serve --reload

serve-prod:
	python -m src.cli serve --host 0.0.0.0 --port 8000

# ============================================
# Docker
# ============================================
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

# ============================================
# Testing
# ============================================
test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

# ============================================
# Utilities
# ============================================
convert:
	python -m src.cli convert-section $(S) --from $(FROM) --to $(TO)

stats:
	python -m src.cli stats

health:
	python -m src.cli health

backup:
	./scripts/backup.sh

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov 2>/dev/null || true
