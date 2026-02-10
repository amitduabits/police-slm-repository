Check the complete status of the Gujarat Police SLM project.

Run these checks and report results:

## 1. Environment
- Python version
- Poetry/pip packages installed
- Docker services status (docker ps)
- Disk usage for data/ and models/

## 2. Data Pipeline
- Documents in data/sources/ (count per source)
- Documents in data/processed/ (OCR, structured, cleaned counts)
- Section mapping files in configs/ (exist? entry counts?)

## 3. Vector Store
- ChromaDB status (is it running?)
- Collection counts (firs, chargesheets, court_rulings, etc.)
- Total embedded chunks

## 4. Model
- Is llama.cpp model server running?
- Model file in models/ directory?
- Fine-tuning status (checkpoints exist?)

## 5. API
- Is FastAPI running? Test /health endpoint
- How many endpoints are implemented vs stubs?

## 6. Frontend
- Is dashboard built? (src/dashboard/dist/ exists?)
- Node modules installed?

## 7. Tests
- Run: pytest tests/ --tb=no -q (quick summary)

## 8. Summary
Print a table:
| Component | Status | Next Step |
|-----------|--------|-----------|
| Data Sources | X/6 complete | ... |
| Ingestion | ... | ... |
| Embeddings | ... | ... |
| RAG | ... | ... |
| Model | ... | ... |
| API | ... | ... |
| Dashboard | ... | ... |
| Security | ... | ... |
| Docker | ... | ... |
| Tests | ... | ... |

Recommend what to work on next based on the current state.
