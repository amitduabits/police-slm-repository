# Gujarat Police SLM — Complete Upgrade Plan

## Two Major Upgrades

### 1. RAG Pipeline Improvement (Kaggle SC Judgments Dataset)
### 2. Complete UI/UX Redesign

---

## PART 1: RAG IMPROVEMENT WITH KAGGLE DATASET

### Dataset: SC Judgments India (1950–2024)
- **Source**: https://www.kaggle.com/datasets/adarshsingh0903/legal-dataset-sc-judgments-india-19502024
- **Content**: Supreme Court judgment texts from Indian Kanoon, 98%+ coverage
- **Format**: CSV/text with judgment full text, metadata (date, bench, petitioner, respondent)

### Step-by-Step Integration

#### Step 1: Download & Prepare Data
```bash
# Download from Kaggle (requires kaggle CLI)
pip install kaggle --break-system-packages
kaggle datasets download -d adarshsingh0903/legal-dataset-sc-judgments-india-19502024
unzip legal-dataset-sc-judgments-india-19502024.zip -d data/kaggle_sc_judgments/
```

#### Step 2: Create Kaggle Dataset Ingestion Script
Create `src/ingestion/kaggle_ingest.py`:

```python
"""
Ingest Kaggle SC Judgments into the RAG pipeline.
Handles: CSV parsing → Chunking → Embedding → ChromaDB storage
"""
import pandas as pd
import os
import hashlib
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Assuming your existing embedding pipeline is in src/rag/
from src.rag.embedder import get_embedding_model
from src.rag.vector_store import get_chroma_collection


def load_kaggle_dataset(data_dir: str = "data/kaggle_sc_judgments") -> pd.DataFrame:
    """Load all CSV/text files from the Kaggle dataset directory."""
    all_data = []
    data_path = Path(data_dir)

    for csv_file in data_path.glob("*.csv"):
        df = pd.read_csv(csv_file, on_bad_lines='skip')
        all_data.append(df)

    if not all_data:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    combined = pd.concat(all_data, ignore_index=True)
    print(f"Loaded {len(combined)} judgments from Kaggle dataset")
    return combined


def clean_judgment_text(text: str) -> str:
    """Clean and normalize judgment text."""
    if not isinstance(text, str):
        return ""

    # Remove excessive whitespace
    import re
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove common boilerplate patterns
    text = re.sub(r'REPORTABLE\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'IN THE SUPREME COURT OF INDIA', '', text, count=1)

    return text.strip()


def chunk_judgment(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    metadata: dict = None
) -> List[Dict]:
    """
    Chunk a judgment into overlapping segments.
    Uses sentence-aware splitting for better coherence.
    """
    if not text or len(text) < 50:
        return []

    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        words = sentence.split()
        sentence_len = len(words)

        if current_length + sentence_len > chunk_size and current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_id = hashlib.md5(chunk_text[:200].encode()).hexdigest()

            chunk_data = {
                "id": chunk_id,
                "text": chunk_text,
                "word_count": current_length,
                **(metadata or {})
            }
            chunks.append(chunk_data)

            # Keep overlap
            overlap_words = chunk_size - chunk_overlap
            while current_length > chunk_overlap and current_chunk:
                removed = current_chunk.pop(0)
                current_length -= len(removed.split())

        current_chunk.append(sentence)
        current_length += sentence_len

    # Final chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunk_id = hashlib.md5(chunk_text[:200].encode()).hexdigest()
        chunks.append({
            "id": chunk_id,
            "text": chunk_text,
            "word_count": current_length,
            **(metadata or {})
        })

    return chunks


def ingest_to_chroma(
    chunks: List[Dict],
    collection_name: str = "sc_judgments",
    batch_size: int = 100
):
    """Embed chunks and store in ChromaDB."""
    model = get_embedding_model()
    collection = get_chroma_collection(collection_name)

    total = len(chunks)
    for i in range(0, total, batch_size):
        batch = chunks[i:i + batch_size]

        texts = [c["text"] for c in batch]
        ids = [c["id"] for c in batch]
        metadatas = [{k: v for k, v in c.items() if k not in ("text", "id")}
                     for c in batch]

        embeddings = model.encode(texts).tolist()

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        print(f"  Ingested {min(i + batch_size, total)}/{total} chunks")

    print(f"✅ Total {total} chunks stored in '{collection_name}'")


def run_full_ingestion(data_dir: str = "data/kaggle_sc_judgments"):
    """Full pipeline: Load → Clean → Chunk → Embed → Store"""
    print("=" * 60)
    print("KAGGLE SC JUDGMENTS INGESTION")
    print("=" * 60)

    # 1. Load
    df = load_kaggle_dataset(data_dir)

    # 2. Identify text column (dataset may vary)
    text_col = None
    for candidate in ['judgment_text', 'text', 'content', 'judgment', 'full_text']:
        if candidate in df.columns:
            text_col = candidate
            break

    if text_col is None:
        print(f"Available columns: {list(df.columns)}")
        # Fallback: use the longest text column
        text_col = max(df.columns, key=lambda c: df[c].astype(str).str.len().mean())
        print(f"Using column: {text_col}")

    # 3. Chunk all judgments
    all_chunks = []
    for idx, row in df.iterrows():
        text = clean_judgment_text(str(row[text_col]))
        if len(text) < 100:
            continue

        metadata = {
            "source": "kaggle_sc_judgments",
            "document_type": "supreme_court_judgment",
        }

        # Extract available metadata
        for col in ['case_name', 'case_title', 'title', 'petitioner', 'respondent']:
            if col in df.columns and pd.notna(row.get(col)):
                metadata[col] = str(row[col])[:500]

        for col in ['date', 'judgment_date', 'decided_on']:
            if col in df.columns and pd.notna(row.get(col)):
                metadata['judgment_date'] = str(row[col])

        for col in ['bench', 'judges', 'coram']:
            if col in df.columns and pd.notna(row.get(col)):
                metadata['bench'] = str(row[col])[:500]

        chunks = chunk_judgment(text, chunk_size=512, chunk_overlap=64, metadata=metadata)
        all_chunks.extend(chunks)

        if (idx + 1) % 500 == 0:
            print(f"  Processed {idx + 1}/{len(df)} judgments → {len(all_chunks)} chunks")

    print(f"\nTotal: {len(all_chunks)} chunks from {len(df)} judgments")

    # 4. Ingest into ChromaDB
    ingest_to_chroma(all_chunks)

    print("\n✅ INGESTION COMPLETE")
    return len(all_chunks)


if __name__ == "__main__":
    run_full_ingestion()
```

#### Step 3: Update RAG Pipeline to Search Multiple Collections
In your existing RAG query function, update to search across both your original collection and the new `sc_judgments` collection:

```python
# In src/rag/pipeline.py — update the query function

async def query_rag(query: str, top_k: int = 5, collections: list = None):
    """Query across multiple ChromaDB collections and merge results."""
    if collections is None:
        collections = ["documents", "sc_judgments"]  # Both old + new

    all_results = []
    model = get_embedding_model()
    query_embedding = model.encode(query).tolist()

    for coll_name in collections:
        try:
            collection = get_chroma_collection(coll_name)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            for i, doc in enumerate(results["documents"][0]):
                all_results.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i],  # Convert distance to similarity
                    "collection": coll_name,
                })
        except Exception as e:
            print(f"Warning: Could not query {coll_name}: {e}")

    # Sort by score descending, return top_k
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:top_k]
```

#### Step 4: Run Ingestion
```bash
cd gujpol-slm-complete
python -m src.ingestion.kaggle_ingest
```

This should go from ~43 chunks → thousands of chunks, dramatically improving RAG quality.

---

## PART 2: UI/UX REDESIGN

The existing UI is basic Tailwind with no design language. The new UI features:

- **Dark theme** with Gujarat Police navy/gold branding
- **Glass morphism** cards with depth
- **Animated transitions** and micro-interactions
- **Professional dashboard** with stats, charts, activity feeds
- **Chat-style** SOP Assistant (conversational UX)
- **Step-by-step** chargesheet review with visual scoring
- **Faceted search** with filters and highlighted results
- **Responsive** mobile-first design

See the complete React app in the companion files.

---

## DEPLOYMENT CHECKLIST

1. Download Kaggle dataset → `data/kaggle_sc_judgments/`
2. Run `python -m src.ingestion.kaggle_ingest`
3. Replace `src/dashboard/` with new dashboard code
4. `cd src/dashboard && npm install && npm run dev`
5. Fix bcrypt issue: `pip install bcrypt==4.0.1 --break-system-packages`
6. Restart API: `python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000`
