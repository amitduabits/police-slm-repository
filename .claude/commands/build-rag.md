Build the complete RAG (Retrieval-Augmented Generation) pipeline.

## 1. Embedding Pipeline (`src/retrieval/embeddings.py`)

Embedding model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
(supports Hindi, Gujarati, English - runs locally, no API calls)

**Chunking strategy** (`src/retrieval/chunker.py`):
- Default: ~500 tokens with 100 token overlap
- Never split mid-paragraph or mid-section
- FIRs: chunk by section (complainant, incident, evidence, accused)
- Chargesheets: chunk by section (accused, evidence, witnesses, investigation)
- Court Rulings: chunk by paragraph, keep reasoning as larger chunks (up to 1000 tokens)
- Each chunk gets metadata: document_type, document_id, section_name, language, date, district, sections_cited

**Vector Store** (ChromaDB):
- Collections: firs, chargesheets, court_rulings, panchnamas, bare_acts, all_documents
- Metadata filtering capability
- Incremental indexing (add new docs without re-indexing all)
- Batch embedding (process 10K+ documents)

Wire up: `python -m src.cli embed create --input-dir data/processed/cleaned`

## 2. Hybrid Search (`src/retrieval/search.py`)

Architecture:
```
Query → Query Expansion → [Vector Search + Keyword Search] → Re-ranking → Context Assembly → Response
```

**Query Expansion**:
- Translate query to all 3 languages (use simple dictionary-based for legal terms)
- Expand legal terms: "murder" → ["murder", "homicide", "Section 302", "Section 103 BNS", "hatya", "ખૂન"]
- Add synonyms from legal glossary

**Hybrid Search**:
- Vector similarity search (ChromaDB) - semantic matching
- Keyword search (PostgreSQL full-text with pg_trgm) - exact term matching
- Combined score: 0.7 × vector_score + 0.3 × keyword_score
- Return top-20 candidates

**Re-ranking**:
- Use cross-encoder `cross-encoder/ms-marco-MiniLM-L-6-v2` to re-rank top-20
- Filter by metadata (date range, district, document type)
- Return top-5 most relevant chunks

**Context Assembly** (`src/retrieval/context.py`):
- Concatenate top-5 chunks with source metadata
- Max 4000 tokens total context
- Format: "[Source: FIR-2023-AHM-1234, Ahmedabad, 2023-05-15] {chunk text}"
- Merge chunks from same document

## 3. Prompt Templates (`src/retrieval/prompts.py`)

Create prompt templates for each use case:

**SOP Assistant**:
```
Given this FIR: {fir_context}
Suggest investigation next steps based on these similar past cases: {retrieved_cases}
Provide steps in priority order with source references.
```

**Chargesheet Reviewer**:
```
Review this draft chargesheet: {chargesheet}
Compare against these successful chargesheets: {good_examples}
Identify: missing elements, weak points, and strengths.
Score completeness 0-100%.
```

**General Q&A**:
```
Based on the following case documents: {context}
Answer this question: {query}
Always cite your sources.
```

## 4. RAG Pipeline (`src/retrieval/rag_pipeline.py`)

Main class `RAGPipeline` that ties everything together:
- `query(text, use_case, filters)` → returns answer + citations
- `search(text, top_k, filters)` → returns relevant documents
- Response streaming for long answers
- Citation tracking (which source documents contributed to answer)

## 5. Test
Wire up: `python -m src.cli embed search "murder bail conditions Gujarat" --top-k 5`
Create tests/unit/test_rag.py with test queries in all 3 languages.
