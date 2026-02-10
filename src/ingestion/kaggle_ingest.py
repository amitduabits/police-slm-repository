"""
Kaggle SC Judgments Ingestion Pipeline
======================================
Downloads and ingests Supreme Court judgments (1950-2024) into ChromaDB
for the Gujarat Police AI Investigation Support System.

Dataset: https://www.kaggle.com/datasets/adarshsingh0903/legal-dataset-sc-judgments-india-19502024

Usage:
  1. Download dataset from Kaggle and extract to data/kaggle_sc_judgments/
  2. Run: python -m src.ingestion.kaggle_ingest
"""

import os
import re
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================
DATA_DIR = os.environ.get("KAGGLE_DATA_DIR", "data/kaggle_sc_judgments")
CHROMA_COLLECTION = "sc_judgments"
CHUNK_SIZE = 512          # words per chunk
CHUNK_OVERLAP = 64        # overlapping words
BATCH_SIZE = 100          # ChromaDB upsert batch size
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ============================================================
# TEXT CLEANING
# ============================================================
def clean_judgment_text(text: str) -> str:
    """Clean and normalize judgment text."""
    if not isinstance(text, str):
        return ""

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove common boilerplate (first occurrence only)
    boilerplate = [
        r'REPORTABLE\s*',
        r'NON-REPORTABLE\s*',
        r'IN THE SUPREME COURT OF INDIA\s*',
        r'CIVIL APPELLATE JURISDICTION\s*',
        r'CRIMINAL APPELLATE JURISDICTION\s*',
    ]
    for pattern in boilerplate:
        text = re.sub(pattern, '', text, count=1)

    return text.strip()


# ============================================================
# CHUNKING
# ============================================================
def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    metadata: Optional[Dict] = None
) -> List[Dict]:
    """
    Sentence-aware chunking with overlap.
    Splits on sentence boundaries for better coherence.
    """
    if not text or len(text.split()) < 30:
        return []

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_sentences: List[str] = []
    current_word_count = 0

    for sentence in sentences:
        word_count = len(sentence.split())

        if current_word_count + word_count > chunk_size and current_sentences:
            # Save current chunk
            chunk_text_str = ' '.join(current_sentences)
            chunk_id = hashlib.md5(chunk_text_str[:200].encode()).hexdigest()

            chunks.append({
                "id": chunk_id,
                "text": chunk_text_str,
                "word_count": current_word_count,
                **(metadata or {})
            })

            # Keep overlap: remove oldest sentences until under overlap threshold
            while current_word_count > overlap and current_sentences:
                removed = current_sentences.pop(0)
                current_word_count -= len(removed.split())

        current_sentences.append(sentence)
        current_word_count += word_count

    # Final chunk
    if current_sentences and current_word_count >= 20:
        chunk_text_str = ' '.join(current_sentences)
        chunk_id = hashlib.md5(chunk_text_str[:200].encode()).hexdigest()
        chunks.append({
            "id": chunk_id,
            "text": chunk_text_str,
            "word_count": current_word_count,
            **(metadata or {})
        })

    return chunks


# ============================================================
# DATASET LOADING
# ============================================================
def load_dataset(data_dir: str = DATA_DIR) -> pd.DataFrame:
    """Load all CSV files from the Kaggle dataset directory."""
    data_path = Path(data_dir)

    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset directory not found: {data_dir}\n"
            f"Please download from Kaggle and extract to {data_dir}\n"
            f"  kaggle datasets download -d adarshsingh0903/legal-dataset-sc-judgments-india-19502024\n"
            f"  unzip legal-dataset-sc-judgments-india-19502024.zip -d {data_dir}"
        )

    all_frames = []
    for f in sorted(data_path.glob("*.csv")):
        logger.info(f"Loading {f.name}...")
        try:
            df = pd.read_csv(f, on_bad_lines='skip', low_memory=False)
            all_frames.append(df)
            logger.info(f"  → {len(df)} rows, columns: {list(df.columns)}")
        except Exception as e:
            logger.warning(f"  → Failed to load {f.name}: {e}")

    # Also check for .txt or .json files
    for f in sorted(data_path.glob("*.json")):
        logger.info(f"Loading {f.name}...")
        try:
            df = pd.read_json(f, lines=True)
            all_frames.append(df)
            logger.info(f"  → {len(df)} rows")
        except Exception:
            try:
                df = pd.read_json(f)
                all_frames.append(df)
                logger.info(f"  → {len(df)} rows")
            except Exception as e:
                logger.warning(f"  → Failed to load {f.name}: {e}")

    if not all_frames:
        raise FileNotFoundError(f"No CSV/JSON files found in {data_dir}")

    combined = pd.concat(all_frames, ignore_index=True)
    logger.info(f"Total loaded: {len(combined)} judgments")
    return combined


def detect_text_column(df: pd.DataFrame) -> str:
    """Auto-detect which column contains the judgment text."""
    candidates = [
        'judgment_text', 'text', 'content', 'judgment', 'full_text',
        'Text', 'Content', 'Judgment', 'body', 'document_text',
    ]
    for col in candidates:
        if col in df.columns:
            logger.info(f"Using text column: '{col}'")
            return col

    # Fallback: find the column with longest average string length
    str_cols = df.select_dtypes(include='object').columns
    if len(str_cols) == 0:
        raise ValueError(f"No text columns found. Columns: {list(df.columns)}")

    best_col = max(str_cols, key=lambda c: df[c].astype(str).str.len().mean())
    logger.info(f"Auto-detected text column: '{best_col}' (longest avg string)")
    return best_col


def extract_metadata(row: pd.Series, df_columns: List[str]) -> Dict:
    """Extract available metadata from a row."""
    metadata: Dict[str, str] = {
        "source": "kaggle_sc_judgments",
        "document_type": "supreme_court_judgment",
    }

    # Case name/title
    for col in ['case_name', 'case_title', 'title', 'Title', 'case', 'Case']:
        if col in df_columns and pd.notna(row.get(col)):
            metadata['case_name'] = str(row[col])[:500]
            break

    # Petitioner / Respondent
    for col in ['petitioner', 'Petitioner']:
        if col in df_columns and pd.notna(row.get(col)):
            metadata['petitioner'] = str(row[col])[:300]
    for col in ['respondent', 'Respondent']:
        if col in df_columns and pd.notna(row.get(col)):
            metadata['respondent'] = str(row[col])[:300]

    # Date
    for col in ['date', 'judgment_date', 'decided_on', 'Date', 'judgment_date_str']:
        if col in df_columns and pd.notna(row.get(col)):
            metadata['judgment_date'] = str(row[col])[:50]
            break

    # Bench / Judges
    for col in ['bench', 'judges', 'coram', 'Bench', 'Judge']:
        if col in df_columns and pd.notna(row.get(col)):
            metadata['bench'] = str(row[col])[:500]
            break

    # Category
    for col in ['category', 'case_type', 'type', 'Category']:
        if col in df_columns and pd.notna(row.get(col)):
            metadata['category'] = str(row[col])[:100]
            break

    return metadata


# ============================================================
# EMBEDDING + STORAGE
# ============================================================
def create_embeddings_and_store(chunks: List[Dict]):
    """Embed all chunks and upsert into ChromaDB."""
    try:
        from sentence_transformers import SentenceTransformer
        import chromadb
    except ImportError:
        logger.error(
            "Missing dependencies. Install with:\n"
            "  pip install sentence-transformers chromadb --break-system-packages"
        )
        return

    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    logger.info("Connecting to ChromaDB...")
    chroma_path = os.environ.get("CHROMA_PATH", "data/chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        metadata={"description": "Supreme Court Judgments 1950-2024"}
    )

    total = len(chunks)
    logger.info(f"Embedding and storing {total} chunks in batches of {BATCH_SIZE}...")

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]

        texts = [c["text"] for c in batch]
        ids = [c["id"] for c in batch]
        metadatas = [
            {k: v for k, v in c.items() if k not in ("text", "id", "word_count")}
            for c in batch
        ]

        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        done = min(i + BATCH_SIZE, total)
        if done % 500 == 0 or done == total:
            logger.info(f"  Progress: {done}/{total} chunks ({done*100//total}%)")

    logger.info(f"✅ Stored {total} chunks in ChromaDB collection '{CHROMA_COLLECTION}'")
    logger.info(f"   Collection now has {collection.count()} total chunks")


# ============================================================
# MAIN PIPELINE
# ============================================================
def run():
    """Full pipeline: Load → Clean → Chunk → Embed → Store"""
    logger.info("=" * 60)
    logger.info("KAGGLE SC JUDGMENTS INGESTION PIPELINE")
    logger.info("=" * 60)

    # 1. Load dataset
    df = load_dataset()

    # 2. Detect text column
    text_col = detect_text_column(df)
    columns = list(df.columns)

    # 3. Chunk all judgments
    all_chunks: List[Dict] = []
    skipped = 0

    for idx, row in df.iterrows():
        raw_text = str(row.get(text_col, ''))
        text = clean_judgment_text(raw_text)

        if len(text) < 100:
            skipped += 1
            continue

        metadata = extract_metadata(row, columns)
        chunks = chunk_text(text, metadata=metadata)
        all_chunks.extend(chunks)

        if (idx + 1) % 1000 == 0:
            logger.info(
                f"  Processed {idx + 1}/{len(df)} judgments → "
                f"{len(all_chunks)} chunks (skipped {skipped})"
            )

    logger.info(f"\nChunking complete:")
    logger.info(f"  Judgments processed: {len(df) - skipped}")
    logger.info(f"  Judgments skipped (too short): {skipped}")
    logger.info(f"  Total chunks: {len(all_chunks)}")

    if not all_chunks:
        logger.error("No chunks generated! Check your data.")
        return

    # 4. Embed and store
    create_embeddings_and_store(all_chunks)

    logger.info("\n" + "=" * 60)
    logger.info("✅ INGESTION COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
