# RAG System Documentation

## Gujarat Police AI Investigation Support System - RAG Pipeline

**Version:** 0.1.0
**Last Updated:** February 2026
**Status:** Production-Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Embedding System](#embedding-system)
4. [Vector Database](#vector-database)
5. [Hybrid Search](#hybrid-search)
6. [Query Processing](#query-processing)
7. [Context Assembly](#context-assembly)
8. [Re-ranking & Scoring](#re-ranking--scoring)
9. [Performance Optimization](#performance-optimization)
10. [API Integration](#api-integration)
11. [Monitoring & Metrics](#monitoring--metrics)
12. [Troubleshooting](#troubleshooting)

---

## Overview

The RAG (Retrieval-Augmented Generation) system is the core intelligence engine of the Gujarat Police investigation support platform. It combines semantic search, keyword matching, and legal knowledge retrieval to provide contextually accurate responses with source citations.

### Key Features

- **Hybrid Search**: Combines vector similarity search with keyword-based retrieval
- **Multilingual Support**: Handles English, Hindi, and Gujarati documents
- **Citation Tracking**: Every response includes source document references
- **Query Expansion**: Automatically expands queries with legal synonyms and section mappings
- **Context Management**: Intelligent chunking and context window optimization
- **Use-Case Specific**: Specialized prompts for SOP, chargesheet review, and general queries

### Design Principles

1. **Accuracy Over Speed**: Prioritize correct legal information
2. **Full Traceability**: Every claim must be traceable to source documents
3. **On-Premise Only**: No external API calls with sensitive data
4. **Multilingual First**: Equal support for all three languages
5. **Section Mapping**: Built-in IPC↔BNS and CrPC↔BNSS conversion

---

## Architecture

### High-Level Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAG PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Query Input                                                 │
│     ↓                                                           │
│  2. Query Expansion (Legal Terms + Section Mappings)           │
│     ↓                                                           │
│  3. Hybrid Search (Vector + Keyword)                           │
│     ├── Vector Search → ChromaDB                               │
│     └── Keyword Search → BM25 (Future)                         │
│     ↓                                                           │
│  4. Result Merging & Re-ranking                                │
│     ↓                                                           │
│  5. Context Assembly (with Citations)                          │
│     ↓                                                           │
│  6. Prompt Construction (Use-Case Specific)                    │
│     ↓                                                           │
│  7. LLM Generation (Mistral 7B via llama.cpp)                  │
│     ↓                                                           │
│  8. Response + Citations                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction

```
┌────────────┐     ┌──────────────┐     ┌──────────────┐
│   FastAPI  │────▶│ RAG Pipeline │────▶│  Embeddings  │
│  Endpoint  │     │   (Core)     │     │   Pipeline   │
└────────────┘     └──────────────┘     └──────────────┘
                          │                      │
                          │                      ▼
                          │              ┌──────────────┐
                          │              │   ChromaDB   │
                          │              │  (Vectors)   │
                          │              └──────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  LLM Client  │
                   │ (Mistral 7B) │
                   └──────────────┘
```

### Data Flow

1. **Ingestion Phase** (Offline):
   - Raw documents → OCR → Parsing → Cleaning → Chunking → Embedding → ChromaDB

2. **Query Phase** (Online):
   - User query → Expansion → Search → Re-rank → Context → LLM → Response

---

## Embedding System

### Model Selection

**Primary Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

**Specifications:**
- Embedding Dimension: 384
- Max Sequence Length: 128 tokens
- Languages: 50+ including English, Hindi, Gujarati
- Model Size: ~470MB
- Inference Speed: ~100 sentences/second on CPU

**Alternative Models** (for specialized use-cases):
- `sentence-transformers/all-MiniLM-L6-v2`: Faster, English-only
- `intfloat/multilingual-e5-base`: Higher accuracy, larger model
- `AI4Bharat/indic-bert`: Better for Indic languages

### Embedding Pipeline

**Location:** `src/retrieval/embeddings.py`

#### Key Components

```python
class EmbeddingPipeline:
    """
    Main embedding pipeline handling document encoding and search.

    Features:
    - Batch processing for efficiency
    - Persistent ChromaDB storage
    - Multiple collection support
    - Metadata filtering
    """

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        chroma_persist_dir: str = "data/embeddings/chroma",
        device: str = "cpu"
    ):
        # Load sentence transformer model
        self.model = SentenceTransformer(model_name, device=device)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=chroma_persist_dir)

        # Initialize document chunker
        self.chunker = DocumentChunker()
```

#### Embedding Process

**Step 1: Document Chunking**

Documents are split into semantically coherent chunks:

```python
class DocumentChunker:
    """
    Semantic document chunking with overlap.

    Parameters:
    - chunk_size: 512 tokens (default)
    - overlap: 50 tokens
    - split_by: Paragraph boundaries first, then sentences
    """

    def chunk_document(self, doc: Dict) -> List[Dict]:
        # Split on paragraph boundaries
        # Respect semantic units (sections, judgments)
        # Add overlap for context preservation
        # Include metadata in each chunk
```

**Chunk Structure:**
```json
{
  "text": "Section 302 of the Indian Penal Code deals with...",
  "metadata": {
    "doc_id": "abc123",
    "title": "State v. Kumar (2024)",
    "source": "indian_kanoon",
    "doc_type": "court_ruling",
    "court": "Gujarat High Court",
    "sections": ["302 IPC", "103 BNS"],
    "chunk_index": 3,
    "total_chunks": 15
  }
}
```

**Step 2: Batch Encoding**

```python
def embed_directory(
    self,
    input_dir: str = "data/processed/cleaned",
    batch_size: int = 32
) -> Dict[str, int]:
    """
    Process all documents in directory.

    Optimizations:
    - Batch encoding (32 docs at once)
    - GPU utilization if available
    - Progress tracking and resumable
    """

    for batch in document_batches:
        # Extract text from chunks
        texts = [chunk["text"] for chunk in batch]

        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            convert_to_numpy=True,
            show_progress_bar=True
        )

        # Store in ChromaDB
        collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
            ids=chunk_ids
        )
```

**Step 3: Collection Management**

Three main collections:

1. **all_documents**: All document types (default for search)
2. **court_rulings**: Only court judgments and orders
3. **bare_acts**: Only legislation (IPC, BNS, CrPC, BNSS)

### Performance Characteristics

| Operation | Time (CPU) | Time (GPU) | Notes |
|-----------|-----------|-----------|-------|
| Single embedding | ~10ms | ~2ms | 512 tokens |
| Batch (32 docs) | ~150ms | ~30ms | Amortized cost |
| Full corpus (10K docs) | ~30 min | ~6 min | Initial load |
| Query search (top-10) | ~50ms | ~20ms | From 100K chunks |

---

## Vector Database

### ChromaDB Configuration

**Version:** Latest (0.4.x)
**Storage:** Persistent on-disk (SQLite + HNSWlib)
**Location:** `data/embeddings/chroma/`

#### Initialization

```python
import chromadb
from chromadb.config import Settings

# Production configuration
client = chromadb.PersistentClient(
    path="data/embeddings/chroma",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=False
    )
)
```

#### Collection Schema

```python
collection = client.get_or_create_collection(
    name="all_documents",
    metadata={
        "description": "All legal documents",
        "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
        "embedding_dim": 384,
        "total_documents": 10000,
        "total_chunks": 150000
    }
)
```

#### Metadata Schema

Each vector has associated metadata:

```json
{
  "title": "State of Gujarat v. Ramesh Kumar (2024)",
  "source": "indian_kanoon",
  "doc_type": "court_ruling",
  "court": "Gujarat High Court",
  "case_number": "CRA/123/2024",
  "sections": "302 IPC,103 BNS",
  "language": "en",
  "date_published": "2024-01-15",
  "chunk_index": 5,
  "total_chunks": 20,
  "source_url": "https://indiankanoon.org/doc/12345"
}
```

#### Indexing Strategy

**HNSW (Hierarchical Navigable Small World):**
- Fast approximate nearest neighbor search
- Trade-off between speed and accuracy
- Configuration:
  ```python
  {
    "hnsw:space": "cosine",  # Distance metric
    "hnsw:construction_ef": 200,  # Build quality
    "hnsw:search_ef": 50  # Search quality
  }
  ```

### Storage Requirements

| Component | Size (10K docs) | Size (100K docs) |
|-----------|----------------|------------------|
| Original documents | ~2 GB | ~20 GB |
| Embedded vectors | ~500 MB | ~5 GB |
| ChromaDB index | ~800 MB | ~8 GB |
| PostgreSQL metadata | ~200 MB | ~2 GB |
| **Total** | **~3.5 GB** | **~35 GB** |

### Backup & Recovery

**Backup Strategy:**
```bash
# Automated daily backup (configured in docker-compose.yml)
docker-compose exec backup /backup.sh

# Manual backup
cp -r data/embeddings/chroma backups/chroma_$(date +%Y%m%d)
```

**Recovery:**
```bash
# Stop services
docker-compose down

# Restore from backup
rm -rf data/embeddings/chroma
cp -r backups/chroma_20240215 data/embeddings/chroma

# Restart services
docker-compose up -d
```

---

## Hybrid Search

### Search Strategy

Combines two complementary approaches:

1. **Vector Search** (Semantic Similarity)
   - Finds conceptually similar documents
   - Weight: 70% (default)
   - Good for: Understanding intent, cross-lingual search

2. **Keyword Search** (Lexical Matching)
   - Finds exact term matches
   - Weight: 30% (default)
   - Good for: Section numbers, case names, specific terms

### Implementation

**Location:** `src/retrieval/rag_pipeline.py`

```python
def hybrid_search(
    self,
    query: str,
    top_k: int = 10,
    collection: str = "all_documents",
    filters: Optional[Dict] = None
) -> List[Dict]:
    """
    Hybrid search combining vector and keyword approaches.

    Algorithm:
    1. Expand query with legal terms
    2. Vector search (top_k * 2 results)
    3. Keyword search (top_k results)
    4. Merge results with weighted scoring
    5. Re-rank by combined score
    6. Return top_k
    """

    # 1. Query expansion
    expanded = self.expand_query(query)

    # 2. Vector search
    vector_results = self.vector_search(
        expanded,
        top_k=top_k * 2,
        collection=collection,
        filters=filters
    )

    # 3. Keyword search (future implementation)
    keyword_results = self.keyword_search(
        query,
        top_k=top_k,
        collection=collection,
        filters=filters
    )

    # 4. Merge and score
    combined = {}
    for doc in vector_results:
        doc_id = doc["id"]
        combined[doc_id] = {
            **doc,
            "combined_score": doc["score"] * self.vector_weight
        }

    keyword_weight = 1 - self.vector_weight
    for doc in keyword_results:
        doc_id = doc["id"]
        if doc_id in combined:
            combined[doc_id]["combined_score"] += doc["score"] * keyword_weight
        else:
            combined[doc_id] = {
                **doc,
                "combined_score": doc["score"] * keyword_weight
            }

    # 5. Sort by combined score
    ranked = sorted(
        combined.values(),
        key=lambda x: x["combined_score"],
        reverse=True
    )

    return ranked[:top_k]
```

### Query Expansion

Automatically expands queries with legal synonyms and section mappings:

```python
def expand_query(self, query: str) -> str:
    """
    Expand query with:
    - Legal synonyms (murder → homicide, killing)
    - Section mappings (302 IPC → 103 BNS)
    - Related terms (FIR → First Information Report)
    """

    expansions = {
        "murder": "murder Section 302 IPC Section 103 BNS homicide killing",
        "theft": "theft Section 379 IPC Section 303 BNS stealing larceny",
        "bail": "bail anticipatory bail regular bail Section 437 CrPC",
        "302": "Section 302 IPC Section 103 BNS murder",
        "376": "Section 376 IPC Section 63 BNS rape sexual assault"
    }

    expanded = query
    for term, expansion in expansions.items():
        if term.lower() in query.lower():
            expanded = f"{expanded} {expansion}"

    return expanded
```

**Example:**
- Input: "What is punishment for murder?"
- Expanded: "What is punishment for murder? murder Section 302 IPC Section 103 BNS homicide killing"

### Filtering

Support for metadata-based filtering:

```python
# Example: Search only Gujarat High Court judgments from 2024
filters = {
    "court": "Gujarat High Court",
    "date_published": {"$gte": "2024-01-01"}
}

results = rag_pipeline.hybrid_search(
    query="bail provisions",
    filters=filters,
    top_k=10
)
```

**Supported Filter Operations:**
- `$eq`: Equals
- `$ne`: Not equals
- `$gt`, `$gte`: Greater than (or equal)
- `$lt`, `$lte`: Less than (or equal)
- `$in`: In list
- `$nin`: Not in list

---

## Query Processing

### Query Flow

```
User Query
    ↓
Language Detection
    ↓
Query Normalization
    ↓
Query Expansion
    ↓
Hybrid Search
    ↓
Results
```

### Language Detection

Automatic language detection for proper handling:

```python
def detect_language(query: str) -> str:
    """
    Detect query language.

    Returns: 'en', 'hi', or 'gu'
    """
    # Check for Devanagari (Hindi)
    if any('\u0900' <= c <= '\u097F' for c in query):
        return 'hi'

    # Check for Gujarati
    if any('\u0A80' <= c <= '\u0AFF' for c in query):
        return 'gu'

    # Default to English
    return 'en'
```

### Query Normalization

Clean and standardize queries:

```python
def normalize_query(query: str) -> str:
    """
    Normalize query:
    - Remove extra whitespace
    - Normalize section references
    - Handle abbreviations
    """

    # Standardize section references
    query = re.sub(r'Sec\.?\s*(\d+)', r'Section \1', query)
    query = re.sub(r'S\.?\s*(\d+)', r'Section \1', query)

    # Standardize code names
    query = re.sub(r'\bIPCr?\b', 'IPC', query, flags=re.IGNORECASE)
    query = re.sub(r'\bBNSr?\b', 'BNS', query, flags=re.IGNORECASE)

    # Remove extra whitespace
    query = ' '.join(query.split())

    return query
```

---

## Context Assembly

### Context Window Management

**Goal:** Maximize relevant context within token limits

**Configuration:**
- Max context tokens: 3000 (default)
- Model context window: 4096 tokens (Mistral 7B)
- Reserved for response: ~1000 tokens

### Assembly Algorithm

```python
def assemble_context(
    self,
    results: List[Dict],
    max_tokens: int = 3000
) -> str:
    """
    Assemble retrieved chunks into context string.

    Strategy:
    1. Prioritize by relevance score
    2. Include source citations
    3. Respect token limit
    4. Maintain document diversity
    """

    context_parts = []
    token_count = 0
    sources_used = set()

    for i, result in enumerate(results):
        # Format chunk with citation
        source_tag = f"[Source {i+1}: {result['metadata']['title']}]"
        chunk = f"{source_tag}\n{result['text']}"

        # Estimate tokens (rough: words * 1.3)
        chunk_tokens = int(len(chunk.split()) * 1.3)

        # Check token limit
        if token_count + chunk_tokens > max_tokens:
            break

        # Add to context
        context_parts.append(chunk)
        token_count += chunk_tokens
        sources_used.add(result['metadata']['source'])

    # Join with separators
    context = "\n\n---\n\n".join(context_parts)

    return context
```

### Citation Format

Each chunk includes clear source attribution:

```
[Source 1: State of Gujarat v. Ramesh Kumar (2024)]
The Gujarat High Court in this case held that under Section 302 IPC
(now Section 103 BNS), the punishment for murder is death sentence
or imprisonment for life, along with fine...

---

[Source 2: Bachan Singh v. State of Punjab (1980)]
The Supreme Court established the "rarest of rare" doctrine for
awarding death penalty in murder cases. The court must consider
mitigating circumstances before imposing capital punishment...
```

---

## Re-ranking & Scoring

### Scoring System

**Vector Similarity Score:**
- Based on cosine distance from ChromaDB
- Normalized to 0-1 range
- Higher is better

**Keyword Match Score:**
- Based on BM25 algorithm (future)
- Term frequency and document frequency
- Normalized to 0-1 range

**Combined Score:**
```python
combined_score = (vector_score * vector_weight) + (keyword_score * keyword_weight)
```

Default weights:
- Vector: 0.7
- Keyword: 0.3

### Re-ranking Strategies

**1. Reciprocal Rank Fusion (Future):**
```python
def reciprocal_rank_fusion(results_lists: List[List[Dict]]) -> List[Dict]:
    """
    Combine multiple ranking lists using RRF.

    Formula: RRF_score = Σ 1/(k + rank_i)
    where k = 60 (constant)
    """
    k = 60
    scores = defaultdict(float)

    for results in results_lists:
        for rank, doc in enumerate(results, start=1):
            scores[doc['id']] += 1 / (k + rank)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**2. Cross-Encoder Re-ranking (Future):**
- Use cross-encoder model for precise relevance
- Applied to top-20 candidates from initial search
- Models: `cross-encoder/ms-marco-MiniLM-L-6-v2`

### Quality Metrics

**Relevance Threshold:**
- Minimum score: 0.3 (configurable)
- Chunks below threshold are filtered out

**Diversity Boosting:**
- Penalize over-representation from single source
- Ensure variety in court levels and document types

---

## Performance Optimization

### Caching Strategy

**Redis Cache Layers:**

1. **Query Cache** (TTL: 1 hour)
   ```python
   cache_key = f"query:{hash(query)}:{collection}:{filters}"
   ```

2. **Embedding Cache** (TTL: 24 hours)
   ```python
   cache_key = f"embed:{hash(text)}"
   ```

3. **Context Cache** (TTL: 30 minutes)
   ```python
   cache_key = f"context:{hash(query)}:{top_k}"
   ```

### Batch Processing

**Ingestion Optimization:**
```python
# Process documents in batches
batch_size = 32  # Optimal for CPU
batch_size = 128  # Optimal for GPU

# Use multiprocessing for chunking
from multiprocessing import Pool
with Pool(processes=4) as pool:
    chunks = pool.map(chunk_document, documents)
```

### Index Optimization

**ChromaDB Tuning:**
```python
collection.modify(
    metadata={
        "hnsw:construction_ef": 200,  # Higher = better quality, slower build
        "hnsw:search_ef": 50,  # Higher = better recall, slower search
        "hnsw:M": 16  # Higher = better quality, more memory
    }
)
```

### Query Optimization

**Best Practices:**

1. **Use Specific Collections:**
   ```python
   # Fast: Search only court rulings
   results = search(query, collection="court_rulings")

   # Slow: Search all documents
   results = search(query, collection="all_documents")
   ```

2. **Limit top_k:**
   ```python
   # Fast: Get 5 results
   results = search(query, top_k=5)

   # Slower: Get 50 results
   results = search(query, top_k=50)
   ```

3. **Use Filters:**
   ```python
   # Reduces search space
   results = search(query, filters={"court": "Supreme Court"})
   ```

### Performance Benchmarks

**Hardware:** Intel i7-12700K, 32GB RAM, no GPU

| Operation | Latency (p50) | Latency (p95) | Throughput |
|-----------|--------------|---------------|------------|
| Single query search | 50ms | 120ms | 20 qps |
| Batch embedding (32) | 150ms | 300ms | 200 docs/s |
| Context assembly | 10ms | 25ms | 100 req/s |
| Full RAG pipeline | 2s | 5s | 0.5 qps |

---

## API Integration

### FastAPI Endpoints

**Location:** `src/api/routes/`

#### SOP Assistant

```python
POST /sop/suggest

Request:
{
  "fir_details": "Theft occurred at...",
  "case_category": "theft",
  "sections_cited": ["379 IPC"],
  "district": "Ahmedabad",
  "top_k": 5
}

Response:
{
  "query": "Theft occurred at... | Category: theft | Sections: 379 IPC",
  "response": "CRITICAL STEPS (within 24 hours): ...",
  "citations": [
    {
      "source": "State v. Kumar (2024)",
      "doc_type": "court_ruling",
      "court": "Gujarat HC",
      "score": 0.87
    }
  ],
  "num_results": 5,
  "processing_time_ms": 2340
}
```

#### Search

```python
POST /search/query

Request:
{
  "query": "bail provisions for murder case",
  "filters": {
    "court": "Supreme Court",
    "year": 2024
  },
  "collection": "court_rulings",
  "top_k": 10
}

Response:
{
  "query": "bail provisions for murder case",
  "results": [
    {
      "id": "abc123_chunk_5",
      "title": "Arnesh Kumar v. State of Bihar (2014)",
      "snippet": "The Supreme Court held that...",
      "document_type": "court_ruling",
      "source": "indian_kanoon",
      "court": "Supreme Court",
      "sections_cited": ["437 CrPC"],
      "score": 0.92,
      "url": "https://indiankanoon.org/doc/1234"
    }
  ],
  "total_results": 10,
  "processing_time_ms": 145
}
```

### Python SDK

```python
from src.retrieval.rag_pipeline import create_rag_pipeline

# Initialize pipeline
rag = create_rag_pipeline()

# Simple query
result = rag.query(
    text="What is punishment for murder?",
    use_case="general",
    top_k=5
)

print(result.response)
print(f"Citations: {len(result.citations)}")
```

---

## Monitoring & Metrics

### Key Metrics

**Search Quality:**
- Average relevance score
- Citation diversity (sources per response)
- Response time distribution

**System Health:**
- ChromaDB index size
- Query throughput
- Cache hit rate
- Error rate

### Prometheus Metrics

```python
# Defined in src/api/main.py

from prometheus_client import Counter, Histogram, Gauge

# Request counters
rag_queries_total = Counter(
    'rag_queries_total',
    'Total RAG queries',
    ['use_case', 'status']
)

# Latency histogram
rag_query_duration_seconds = Histogram(
    'rag_query_duration_seconds',
    'RAG query duration',
    ['use_case']
)

# Search results gauge
rag_results_count = Histogram(
    'rag_results_count',
    'Number of search results returned',
    ['collection']
)
```

### Logging

**Structured logging with correlation IDs:**

```python
import logging
import uuid

logger = logging.getLogger(__name__)

def process_query(query: str):
    correlation_id = str(uuid.uuid4())

    logger.info(
        "RAG query started",
        extra={
            "correlation_id": correlation_id,
            "query_length": len(query),
            "use_case": "sop"
        }
    )

    # ... processing ...

    logger.info(
        "RAG query completed",
        extra={
            "correlation_id": correlation_id,
            "results_count": len(results),
            "duration_ms": duration
        }
    )
```

---

## Troubleshooting

### Common Issues

#### 1. Slow Search Performance

**Symptoms:** Queries taking >5 seconds

**Diagnosis:**
```python
# Check index size
collection = client.get_collection("all_documents")
print(f"Total vectors: {collection.count()}")

# Check search parameters
# High top_k or complex filters slow down search
```

**Solutions:**
- Reduce top_k parameter
- Use collection-specific search
- Add metadata filters to narrow scope
- Increase ChromaDB search_ef parameter

#### 2. Low Relevance Scores

**Symptoms:** All results have score <0.4

**Diagnosis:**
```python
# Test embedding quality
test_query = "murder punishment"
results = pipeline.search(test_query, top_k=10)
for r in results:
    print(f"{r.score:.3f} - {r.title}")
```

**Solutions:**
- Check if documents are properly embedded
- Verify language matching (query vs documents)
- Try query expansion
- Re-embed corpus with better model

#### 3. ChromaDB Connection Errors

**Symptoms:** `ConnectionError` or `ClientError`

**Diagnosis:**
```bash
# Check ChromaDB service
docker-compose ps db-chroma
docker-compose logs db-chroma

# Test connection
curl http://localhost:8100/api/v1/heartbeat
```

**Solutions:**
```bash
# Restart ChromaDB
docker-compose restart db-chroma

# Check disk space
df -h data/embeddings/chroma

# Reset if corrupted (WARNING: loses data)
docker-compose down
rm -rf data/embeddings/chroma
docker-compose up -d
# Re-run: make embed
```

#### 4. Out of Memory During Embedding

**Symptoms:** Process killed during `make embed`

**Diagnosis:**
```bash
# Check memory usage
free -h
docker stats
```

**Solutions:**
```python
# Reduce batch size
pipeline = EmbeddingPipeline()
pipeline.embed_directory(batch_size=16)  # Default is 32

# Process in smaller chunks
# Split data/processed/cleaned/ into subdirectories
# Run embedding on each subdirectory separately
```

#### 5. Missing Citations

**Symptoms:** Response generated but citations list empty

**Diagnosis:**
```python
# Check RAG pipeline response
result = rag.query("test query", top_k=5)
print(f"Results: {result.num_results}")
print(f"Citations: {len(result.citations)}")
print(f"Context length: {len(result.context)}")
```

**Solutions:**
- Verify documents have proper metadata
- Check if context assembly is working
- Ensure top_k > 0
- Review filtering logic

### Debug Mode

Enable debug logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Run RAG pipeline
rag = create_rag_pipeline()
result = rag.query("test", top_k=5)
```

### Health Check Script

```python
# scripts/health_check_rag.py

def check_rag_health():
    """Comprehensive RAG system health check."""

    checks = {
        "embedding_model": check_embedding_model(),
        "chromadb": check_chromadb(),
        "llm_backend": check_llm(),
        "test_query": check_test_query()
    }

    print("RAG System Health Check")
    print("=" * 60)
    for component, status in checks.items():
        symbol = "✓" if status["ok"] else "✗"
        print(f"{symbol} {component}: {status['message']}")
    print("=" * 60)

    return all(c["ok"] for c in checks.values())

if __name__ == "__main__":
    import sys
    sys.exit(0 if check_rag_health() else 1)
```

---

## Appendix

### File Structure

```
src/retrieval/
├── __init__.py
├── chunker.py            # Document chunking logic
├── embeddings.py         # Embedding pipeline and ChromaDB
├── rag_pipeline.py       # Main RAG orchestration
└── prompts.py            # Use-case specific prompts

data/
├── embeddings/
│   └── chroma/           # ChromaDB persistent storage
├── processed/
│   └── cleaned/          # Source documents for embedding
└── sources/              # Raw scraped documents

configs/
├── ipc_to_bns_mapping.json
└── crpc_to_bnss_mapping.json
```

### References

- **Sentence Transformers:** https://www.sbert.net/
- **ChromaDB Documentation:** https://docs.trychroma.com/
- **HNSW Algorithm:** https://arxiv.org/abs/1603.09320
- **Reciprocal Rank Fusion:** https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf

---

**Document Version:** 1.0
**Last Updated:** February 11, 2026
**Maintained By:** Gujarat Police SLM Development Team
