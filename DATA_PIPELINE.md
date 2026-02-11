# Data Pipeline Documentation

This document describes the complete data collection, ingestion, and processing pipeline for the Gujarat Police AI Investigation Support System.

## Table of Contents

- [Overview](#overview)
- [Data Sources](#data-sources)
- [Collection Pipeline](#collection-pipeline)
- [Ingestion Pipeline](#ingestion-pipeline)
- [Processing Pipeline](#processing-pipeline)
- [Embedding Pipeline](#embedding-pipeline)
- [Quality Assurance](#quality-assurance)

## Overview

The data pipeline consists of four main stages:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Data Collection │ ──► │   OCR/Parsing    │ ──► │   Cleaning &     │ ──► │   Embedding &    │
│   (Scrapers)     │     │   (Extraction)   │     │   Normalization  │     │   Indexing       │
└──────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
        │                        │                        │                        │
        ▼                        ▼                        ▼                        ▼
  data/sources/          data/processed/ocr/    data/processed/cleaned/    ChromaDB + PostgreSQL
```

**Total Processing Time:** ~6-12 hours for full pipeline (depending on document volume)

## Data Sources

### 1. Indian Kanoon (indiankanoon.org)

**Type:** Court rulings and judgments
**Coverage:** Supreme Court, all High Courts, District Courts
**Estimated Documents:** 5,000-10,000 Gujarat-relevant cases

**Scraping Strategy:**
```python
# Key search queries
queries = [
    "Gujarat murder Section 302 IPC",
    "Gujarat bail Section 437 CrPC",
    "BNS Gujarat High Court",
    "chargesheet deficiency Gujarat",
    # ... 40+ domain-specific queries
]

# Courts covered
courts = [
    "gujarat_hc",          # Gujarat High Court
    "gujarat_district",    # District courts
    "supreme_court"        # Supreme Court (Gujarat-relevant)
]
```

**Rate Limiting:** 2-second delay between requests
**Data Format:** HTML → Parsed JSON
**Success Rate:** ~95% (some pages require JavaScript)

**Key Fields Extracted:**
- Case citation
- Court name and bench
- Judge names
- Parties involved
- Sections cited
- Judgment text (full)
- Judgment date
- Precedents cited

### 2. eCourts India (ecourts.gov.in)

**Type:** District court case data
**Coverage:** District and Taluka courts across Gujarat
**Estimated Documents:** 10,000-50,000 cases

**Districts Covered:**
- Ahmedabad, Surat, Vadodara, Rajkot, Gandhinagar
- Bhavnagar, Jamnagar, Junagadh, Anand
- All 33 districts (configurable)

**Data Format:** Web interface → Parsed JSON
**Challenges:** CAPTCHA, dynamic content, session management

**Key Fields Extracted:**
- Case number and type
- Filing date
- Current status
- Next hearing date
- Parties
- Sections
- Court orders (if available)

### 3. Gujarat High Court (gujarathighcourt.nic.in)

**Type:** High Court judgments
**Coverage:** Gujarat High Court (Civil & Criminal)
**Estimated Documents:** 2,000-5,000 judgments

**Access Methods:**
- Daily cause lists
- Judgment search by date/bench
- Case status by case number

**Data Format:** PDF/HTML → Parsed JSON

**Key Fields Extracted:**
- Case number and citation
- Bench composition
- Subject matter
- Appellant/Respondent
- Judgment summary
- Full judgment text

### 4. Supreme Court (main.sci.gov.in)

**Type:** Supreme Court judgments
**Coverage:** Constitutional and landmark criminal cases
**Estimated Documents:** 500-1,000 relevant cases

**Focus Areas:**
- Criminal procedure precedents
- Evidence law interpretations
- Constitutional matters affecting criminal law
- Landmark sentencing guidelines

**Data Format:** PDF → Parsed JSON

### 5. India Code (indiacode.nic.in)

**Type:** Bare acts (legislation)
**Coverage:** IPC, CrPC, IEA, BNS, BNSS, BSA
**Estimated Documents:** ~2,500 sections

**Section Mappings Generated:**
```json
{
  "IPC": {
    "302": {
      "title": "Punishment for murder",
      "bns_section": "103",
      "description": "Death or life imprisonment + fine"
    },
    "420": {
      "title": "Cheating and dishonestly inducing delivery of property",
      "bns_section": "318(4)",
      "description": "Imprisonment up to 7 years + fine"
    }
  }
}
```

**Files Generated:**
- `configs/ipc_to_bns_mapping.json` (IPC → BNS)
- `configs/crpc_to_bnss_mapping.json` (CrPC → BNSS)
- `configs/iea_to_bsa_mapping.json` (IEA → BSA)
- Reverse mappings for backward compatibility

### 6. NCRB (ncrb.gov.in)

**Type:** Crime statistics and data tables
**Coverage:** State and district-level crime data
**Estimated Documents:** 50-100 statistical reports

**Data Points:**
- Crime head-wise data
- Detection rates
- Conviction rates
- Pendency statistics
- Police station-wise data (if available)

### 7. Local Upload (Manual)

**Type:** Investigation documents (FIRs, chargesheets, etc.)
**Coverage:** Local police station documents
**Format:** PDF, JPG, PNG, DOCX

**Document Categories:**

```
data/raw/
├── firs/                    # First Information Reports
├── chargesheets/            # Final reports under CrPC 173
├── panchnamas/              # Scene of crime documentation
├── investigation_reports/   # IO reports
└── court_orders/            # Bail orders, remand orders, etc.
```

## Collection Pipeline

### Command Interface

```bash
# Collect all sources
make collect-all

# Individual sources
make collect-kanoon     # Indian Kanoon (~30 min)
make collect-ecourts    # eCourts (~45 min)
make collect-gujhc      # Gujarat HC (~20 min)
make collect-sci        # Supreme Court (~30 min)
make collect-acts       # Bare acts + mappings (~5 min)
make collect-ncrb       # NCRB statistics (~10 min)
```

### Orchestrator

**File:** `src/data_sources/orchestrator.py`

The orchestrator coordinates all scrapers with:
- Priority ordering (India Code first for mappings)
- Parallel execution (up to 3 concurrent scrapers)
- Rate limiting (configurable delays)
- Progress tracking
- Error handling and retry logic
- State persistence (resume from failure)

**Configuration:** `configs/ingestion_config.yaml`

```yaml
data_sources:
  scraper_delay_seconds: 2
  max_concurrent_scrapers: 3
  sources:
    india_code:
      enabled: true
      priority: 0  # Run first
    indian_kanoon:
      enabled: true
      priority: 1
      max_results_per_query: 50
    ecourts:
      enabled: true
      priority: 2
      districts: ["ahmedabad", "surat", "vadodara"]
    # ... more sources
```

### Output Format

All scrapers output standardized JSON:

```json
{
  "id": "unique-document-id",
  "document_type": "court_ruling",
  "source": "indian_kanoon",
  "source_url": "https://indiankanoon.org/doc/12345/",
  "title": "State of Gujarat vs. Accused Name",
  "content": "Full judgment text...",
  "metadata": {
    "court": "Gujarat High Court",
    "case_number": "Crl.A/123/2023",
    "judges": ["Justice A", "Justice B"],
    "parties": {
      "appellant": "State of Gujarat",
      "respondent": "Accused Name"
    },
    "sections_cited": ["IPC 302", "IPC 120B", "CrPC 173"],
    "date_published": "2023-06-15",
    "bench": "Division Bench"
  },
  "language": "en",
  "scraped_at": "2024-02-10T10:30:00Z"
}
```

**Saved to:** `data/sources/<source_name>/<date>/<doc_id>.json`

## Ingestion Pipeline

The ingestion pipeline processes uploaded documents (FIRs, chargesheets, etc.) through OCR and parsing.

### Stage 1: OCR Extraction

**Command:** `make ingest-ocr`

**Primary Engine:** Tesseract OCR
**Fallback Engine:** PaddleOCR (for Gujarati/complex scripts)

**Configuration:** `configs/ingestion_config.yaml`

```yaml
ocr:
  primary_engine: "tesseract"
  fallback_engine: "paddleocr"
  languages: ["eng", "hin", "guj"]
  confidence_threshold: 0.80
  preprocessing:
    deskew: true          # Correct skewed scans
    denoise: true         # Remove noise
    binarize: true        # Convert to B&W
    remove_stamps: true   # Remove official stamps
    dpi: 300              # Target DPI
  batch_size: 50
  max_concurrent: 2
  flag_low_confidence: true
```

**Process Flow:**

```
Input: data/raw/firs/FIR_12345.pdf
   ↓
PDF → Images (pdf2image)
   ↓
Preprocessing:
- Deskew (correct rotation)
- Denoise (Gaussian filter)
- Binarize (Otsu thresholding)
- Enhance contrast
   ↓
Tesseract OCR (English/Hindi)
   ↓
Confidence check (>80%?)
   ↓ (if low)
PaddleOCR fallback (Gujarati support)
   ↓
Output: data/processed/ocr/FIR_12345.json
```

**OCR Output Format:**

```json
{
  "source_file": "FIR_12345.pdf",
  "document_type": "fir",
  "ocr_engine": "tesseract",
  "pages": [
    {
      "page_num": 1,
      "text": "Extracted text from page 1...",
      "confidence": 0.92,
      "language": "en"
    },
    {
      "page_num": 2,
      "text": "Extracted text from page 2...",
      "confidence": 0.88,
      "language": "hi"
    }
  ],
  "full_text": "Combined text from all pages...",
  "avg_confidence": 0.90,
  "processing_time_seconds": 12.3,
  "flags": []
}
```

### Stage 2: Document Parsing

**Command:** `make ingest-parse`

**Purpose:** Extract structured fields from OCR text

**Parsers by Document Type:**

#### FIR Parser

**Pattern Matching Rules:**
```python
patterns = {
    "fir_number": r"(?:FIR|F\.I\.R\.|First Information Report)\s*(?:No\.|Number|#)?\s*:?\s*(\d+/\d{4})",
    "date": r"(?:Date|Dated|On)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
    "police_station": r"(?:Police Station|P\.S\.|PS)\s*:?\s*([A-Za-z\s]+)",
    "sections": r"(?:Section|Sec\.|u/s|U/S)\s*(\d+[A-Z]?\s*(?:IPC|BNS|NDPS|POCSO)?)",
    # ... more patterns
}
```

**Extracted Fields:**
- FIR number
- Date and time
- Police station and district
- Complainant details (name, address, relation)
- Accused details (name, age, address, parentage)
- Sections cited
- Incident description
- Incident location and time
- Evidence mentioned
- Witnesses

#### Chargesheet Parser

**Complexity:** Higher (multi-page, structured sections)

**Extracted Fields:**
- Case number
- FIR reference
- Accused list (with details)
- Witnesses list (with examination summaries)
- Evidence inventory (material/documentary/forensic)
- Sections charged (with modifications)
- Investigation officer
- Investigation chronology (timeline of steps)
- Forensic reports
- Filing date and court

#### Court Ruling Parser

**Extracted Fields:**
- Case citation
- Judge names
- Court name and bench
- Charges considered
- Verdict (acquitted/convicted/partial)
- Reasoning (key legal points)
- Sentences imposed
- Precedents cited

**Parser Output:** `data/processed/structured/<doc_id>.json`

### Stage 3: Data Cleaning & Normalization

**Command:** `make ingest-clean`

**Operations:**

1. **Section Normalization**
   ```python
   # Convert old codes to new codes
   "IPC 302" → adds "BNS 103"
   "CrPC 173" → adds "BNSS 193"
   "IEA 27" → adds "BSA 27"
   ```

2. **Entity Normalization**
   ```python
   # Standardize names
   "AHMEDABAD" → "Ahmedabad"
   "Guj. High Court" → "Gujarat High Court"

   # Date formats
   "15-06-2023" → "2023-06-15" (ISO 8601)
   "15/6/23" → "2023-06-15"
   ```

3. **PII Handling**
   ```python
   # Detect PII patterns
   pii_patterns = {
       "aadhaar": r"\d{4}\s?\d{4}\s?\d{4}",
       "phone": r"[6-9]\d{9}",
       "email": r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}",
       "pan": r"[A-Z]{5}\d{4}[A-Z]"
   }

   # Tag and encrypt
   if pii_detected:
       encrypted = encrypt_aes256(value, ENCRYPTION_KEY)
       metadata["contains_pii"] = True
   ```

4. **Deduplication**
   ```python
   # Content-based hashing
   content_hash = hashlib.sha256(content.encode()).hexdigest()

   # Check if exists
   if hash_exists_in_db(content_hash):
       skip_document()
   ```

5. **Quality Flags**
   ```yaml
   flags:
     - "low_ocr_confidence"  # <80% confidence
     - "missing_required_field"  # FIR without case number
     - "date_inconsistency"  # FIR date after chargesheet
     - "section_not_found"  # Section not in mappings
   ```

**Output:** `data/processed/cleaned/<doc_id>.json`

```json
{
  "id": "doc-12345",
  "document_type": "fir",
  "source": "upload",
  "title": "FIR 123/2023 - Theft Case",
  "content": "Normalized full text...",
  "content_hash": "a1b2c3...",
  "language": "en",
  "metadata": {
    "fir_number": "123/2023",
    "date": "2023-06-15",
    "police_station": "City Police Station",
    "district": "Ahmedabad",
    "sections_cited": ["IPC 379", "BNS 303"],
    "contains_pii": true,
    "ocr_confidence": 0.92,
    "processing_flags": []
  },
  "structured_data": {
    "complainant": {
      "name": "[ENCRYPTED]",
      "address": "[ENCRYPTED]",
      "relation": "Self"
    },
    "accused": [
      {
        "name": "[ENCRYPTED]",
        "age": 28,
        "address": "[ENCRYPTED]"
      }
    ],
    "incident": {
      "description": "...",
      "location": "...",
      "date": "2023-06-14",
      "time": "22:30:00"
    }
  },
  "quality_score": 0.95
}
```

## Processing Pipeline

### Database Ingestion

**Command:** `python -m src.cli ingest save-to-db`

**Process:**

```python
# For each cleaned document:
1. Load JSON from data/processed/cleaned/
2. Create Document record (PostgreSQL)
3. Create specific record (FIR/Chargesheet/CourtRuling table)
4. Commit transaction
```

**Database Tables Populated:**
- `documents` (main table with full text)
- `firs` (structured FIR data)
- `chargesheets` (structured chargesheet data)
- `court_rulings` (structured ruling data)
- `section_mappings` (from India Code)

### Validation

**Command:** `make validate-data`

**Checks:**

1. **Completeness**
   - All required fields present
   - No NULL values in mandatory columns
   - Foreign key integrity

2. **Consistency**
   - FIR date < Chargesheet filing date
   - Section codes valid (exist in mappings)
   - Court names standardized

3. **Quality**
   - OCR confidence >= threshold
   - No duplicate content hashes
   - PII properly encrypted

**Output:** Validation report with pass/fail counts

## Embedding Pipeline

### Command

```bash
make embed
```

### Process

**File:** `src/retrieval/embeddings.py`

```
For each document in PostgreSQL (is_indexed=false):
   ↓
1. Chunk text (500 tokens, 100 overlap)
   ↓
2. Generate embeddings (sentence-transformers)
   ↓
3. Store in ChromaDB with metadata
   ↓
4. Mark as indexed (is_indexed=true)
```

### Chunking Strategy

**Configuration:** `configs/ingestion_config.yaml`

```yaml
chunking:
  default_chunk_size: 500  # tokens
  chunk_overlap: 100       # overlap between chunks
  respect_paragraphs: true
  respect_sections: true

  # Document-specific strategies
  fir:
    chunk_by: "section"
    sections: ["complainant", "incident", "evidence", "accused"]

  chargesheet:
    chunk_by: "section"
    sections: ["accused", "evidence", "witnesses", "investigation"]

  court_ruling:
    chunk_by: "paragraph"
    keep_reasoning_large: true
    max_chunk_size: 1000
```

**Example Chunking:**

```
Document: 5000 words → ~6500 tokens

Chunks:
1. Tokens 0-500 (metadata: doc_id, chunk_idx=0, section="introduction")
2. Tokens 400-900 (overlap 100, metadata: doc_id, chunk_idx=1, section="facts")
3. Tokens 800-1300
...
14. Tokens 6000-6500 (metadata: doc_id, chunk_idx=13, section="conclusion")
```

### Embedding Generation

**Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
**Dimension:** 384
**Languages:** English, Hindi, Gujarati (100+ languages supported)

**Process:**

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Batch processing for efficiency
chunks = [chunk1, chunk2, ..., chunk64]  # Batch size = 64
embeddings = model.encode(chunks, batch_size=64, show_progress_bar=True)

# Shape: (64, 384)
```

### ChromaDB Storage

**Collections:**

```python
collections = [
    "firs",              # FIR documents only
    "chargesheets",      # Chargesheet documents only
    "court_rulings",     # Court judgments only
    "panchnamas",        # Panchnama documents only
    "bare_acts",         # Legal code sections
    "all_documents"      # Unified collection (default)
]
```

**Storage Format:**

```python
collection.add(
    ids=[f"{doc_id}_chunk_{idx}" for idx in range(num_chunks)],
    embeddings=embeddings,  # (N, 384) array
    documents=[chunk_text for chunk_text in chunks],
    metadatas=[
        {
            "doc_id": doc_id,
            "chunk_idx": idx,
            "doc_type": "fir",
            "source": "upload",
            "title": "FIR 123/2023",
            "district": "Ahmedabad",
            "date": "2023-06-15",
            "sections": ["IPC 379", "BNS 303"],
            # ... more metadata
        }
        for idx, chunk in enumerate(chunks)
    ]
)
```

**Indexing Performance:**
- ~1000 documents/hour (CPU)
- ~5000 documents/hour (GPU)
- Total time: 2-6 hours for 10,000 documents

## Quality Assurance

### Data Quality Metrics

```python
metrics = {
    "total_documents": 15234,
    "by_source": {
        "indian_kanoon": 8234,
        "ecourts": 4500,
        "upload": 2500
    },
    "by_type": {
        "court_ruling": 8234,
        "fir": 1200,
        "chargesheet": 800,
        "panchnama": 500
    },
    "avg_ocr_confidence": 0.89,
    "pii_encrypted": 3400,
    "quality_flags": {
        "low_confidence": 234,
        "missing_required": 45,
        "date_inconsistency": 12
    },
    "indexed_documents": 15100,  # 99.1%
    "avg_chunks_per_doc": 8.5
}
```

### Validation Queries

```sql
-- Documents with quality issues
SELECT document_type, COUNT(*)
FROM documents
WHERE ocr_confidence < 0.80 OR processing_status = 'failed'
GROUP BY document_type;

-- Documents not yet indexed
SELECT COUNT(*) FROM documents WHERE is_indexed = false;

-- Duplicate content check
SELECT content_hash, COUNT(*) as count
FROM documents
GROUP BY content_hash
HAVING COUNT(*) > 1;

-- Section citation coverage
SELECT
    UNNEST(sections_cited) as section,
    COUNT(*) as occurrences
FROM documents
WHERE sections_cited IS NOT NULL
GROUP BY section
ORDER BY occurrences DESC
LIMIT 20;
```

### Manual Review Process

1. **Sample Review** (5% random sampling)
   - OCR accuracy check
   - Field extraction accuracy
   - Section normalization correctness

2. **Error Analysis**
   - Review documents with quality flags
   - Identify common OCR errors
   - Improve parsers based on findings

3. **Continuous Monitoring**
   - Track new documents added
   - Monitor ingestion failure rates
   - Update patterns/mappings as needed

---

**Next:** See [RAG_SYSTEM.md](./RAG_SYSTEM.md) for how this data is used in retrieval.
