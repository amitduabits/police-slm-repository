# Gujarat Police SLM - Upgrade Instructions

## What You Have

✅ **25,735 Supreme Court judgment PDFs** in `archive/supreme_court_judgments/` (1950-2024)
✅ **New upgraded dashboard** in root `dashboard/` folder
✅ **kaggle_ingest.py** in `src/ingestion/`
✅ **Existing OCR pipeline** in `src/ingestion/ocr_pipeline.py`

## Important Discovery

⚠️ **MISMATCH IDENTIFIED:**
- `kaggle_ingest.py` expects **CSV/JSON files** with pre-extracted text
- But you have **PDF files** that need OCR processing first

## Solution: Two-Step Approach

### Option A: Use Existing RAG Pipeline (Recommended - Faster)

Your existing data sources already scrape Indian Kanoon, which has the same SC judgments as your archive. Instead of processing 25K PDFs with OCR:

```bash
# Use your existing data pipeline
python -m src.data_sources.orchestrator --sources supreme_court indian_kanoon
python -m src.ingestion.processor
python -m src.retrieval.embeddings
```

### Option B: Process Archive PDFs (Complete - Slower)

If you want to process the archive PDFs:

#### Step 1: Create PDF Ingestion Script

We need a new script that combines OCR + kaggle_ingest logic:

```bash
# Create src/ingestion/pdf_archive_ingest.py
```

```python
"""
PDF Archive Ingestion for SC Judgments
Processes PDFs → OCR → Chunk → Embed → ChromaDB
"""
import os
import logging
from pathlib import Path
from typing import List, Dict
import hashlib

from src.ingestion.ocr_pipeline import OCRPipeline
from sentence_transformers import SentenceTransformer
import chromadb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARCHIVE_PATH = "archive/supreme_court_judgments"
CHROMA_COLLECTION = "sc_judgments_archive"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
BATCH_SIZE = 50

def process_pdfs():
    """Process all PDFs in archive with OCR → Chunking → Embedding"""
    archive_path = Path(ARCHIVE_PATH)
    pdf_files = list(archive_path.rglob("*.PDF")) + list(archive_path.rglob("*.pdf"))

    logger.info(f"Found {len(pdf_files)} PDF files")

    # Initialize
    ocr = OCRPipeline()
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path="data/chroma")
    collection = client.get_or_create_collection(CHROMA_COLLECTION)

    all_chunks = []
    processed = 0

    for pdf_path in pdf_files:
        try:
            # Extract metadata from path
            year = pdf_path.parent.name
            case_name = pdf_path.stem.replace("_", " ")

            # OCR
            logger.info(f"[{processed+1}/{len(pdf_files)}] OCR: {pdf_path.name}")
            text = ocr.process_pdf(str(pdf_path))

            if not text or len(text.split()) < 50:
                logger.warning(f"  Skipping (too short)")
                continue

            # Chunk
            chunks = chunk_text(text, metadata={
                "source": "archive_sc_judgments",
                "document_type": "supreme_court_judgment",
                "year": year,
                "case_name": case_name,
                "file_path": str(pdf_path)
            })

            all_chunks.extend(chunks)
            processed += 1

            # Batch embed every 100 documents
            if len(all_chunks) >= BATCH_SIZE * 10:
                embed_and_store(all_chunks, collection, model)
                all_chunks = []

        except Exception as e:
            logger.error(f"  Error processing {pdf_path.name}: {e}")

    # Final batch
    if all_chunks:
        embed_and_store(all_chunks, collection, model)

    logger.info(f"✅ Processed {processed}/{len(pdf_files)} PDFs")

def chunk_text(text: str, metadata: Dict) -> List[Dict]:
    """Simple sentence-aware chunking"""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current = []
    word_count = 0

    for sent in sentences:
        words = len(sent.split())
        if word_count + words > CHUNK_SIZE and current:
            chunk_text = ' '.join(current)
            chunk_id = hashlib.md5(chunk_text[:200].encode()).hexdigest()
            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                **metadata
            })
            current = current[-(CHUNK_OVERLAP//10):]  # Keep overlap
            word_count = sum(len(s.split()) for s in current)

        current.append(sent)
        word_count += words

    if current:
        chunk_text = ' '.join(current)
        chunk_id = hashlib.md5(chunk_text[:200].encode()).hexdigest()
        chunks.append({"id": chunk_id, "text": chunk_text, **metadata})

    return chunks

def embed_and_store(chunks: List[Dict], collection, model):
    """Embed and store in ChromaDB"""
    logger.info(f"  Embedding {len(chunks)} chunks...")

    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    metadatas = [{k: v for k, v in c.items() if k not in ("id", "text")}
                 for c in chunks]

    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )
    logger.info(f"  ✅ Stored {len(chunks)} chunks")

if __name__ == "__main__":
    process_pdfs()
```

## Recommended Upgrade Steps

### STEP 1: Fix bcrypt (Required First)
```bash
cd "D:\projects\Ongoing\gujarat police\Implementation project\gujpol-slm-complete\gujpol-slm-complete"
pip install bcrypt==4.0.1 --break-system-packages
```

### STEP 2: Backup Old Dashboard
```bash
# Windows
move src\dashboard src\dashboard-backup-%date:~-4,4%%date:~-10,2%%date:~-7,2%

# OR manually rename src/dashboard to src/dashboard-old
```

### STEP 3: Install New Dashboard
```bash
# Move new dashboard from root to src/
move dashboard src\dashboard

# Install dependencies
cd src\dashboard
npm install
```

### STEP 4: Choose Your RAG Data Approach

**Option A - Use Existing Scrapers (Recommended):**
```bash
# Already has Indian Kanoon scraper that gets SC judgments
python -m src.data_sources.orchestrator
```

**Option B - Process Archive PDFs (If you prefer local data):**
```bash
# Create the pdf_archive_ingest.py script above, then:
python -m src.ingestion.pdf_archive_ingest
```

⏱️ **Time Estimate:**
- Option A: 2-4 hours (scraping + embedding)
- Option B: 10-15 hours (OCR 25K PDFs + embedding)

### STEP 5: Start Services

**Dashboard (Dev Mode):**
```bash
cd src\dashboard
npm run dev
```

**API Server:**
```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Full Docker Stack:**
```bash
docker-compose up -d
```

### STEP 6: Access the System
- **Dashboard:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Summary

| Component | Status | Action Required |
|-----------|--------|----------------|
| Dashboard | ✅ Ready | Move to `src/dashboard` + npm install |
| bcrypt | ⚠️ Needs fix | `pip install bcrypt==4.0.1` |
| RAG Data | ⚠️ Choose approach | Option A (scraper) or B (OCR PDFs) |
| Archive PDFs | ✅ Ready | 25,735 PDFs available if needed |
| kaggle_ingest.py | ⚠️ Expects CSV | Needs modification for PDFs |

## Recommendation

**Use Option A** (existing scrapers) because:
1. ✅ Much faster (hours vs days)
2. ✅ Already working code
3. ✅ Gets same data from Indian Kanoon
4. ✅ No OCR errors
5. ✅ Structured metadata included

Keep the archive PDFs as backup/offline source for future use.

## Quick Start (Recommended Path)

```bash
# 1. Fix bcrypt
pip install bcrypt==4.0.1 --break-system-packages

# 2. Install dashboard
move src\dashboard src\dashboard-old
move dashboard src\dashboard
cd src\dashboard && npm install && cd ..\..

# 3. Use existing data pipeline
python -m src.data_sources.orchestrator

# 4. Start services
# Terminal 1:
cd src\dashboard && npm run dev

# Terminal 2:
python -m uvicorn src.api.main:app --reload
```

Done! 🎉
