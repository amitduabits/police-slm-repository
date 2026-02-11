"""
PDF Archive Ingestion for Supreme Court Judgments
==================================================
Processes archive PDFs → OCR → Chunk → Embed → ChromaDB
Handles the 25K+ Supreme Court judgment PDFs from Kaggle archive.

Usage:
    python -m src.ingestion.pdf_archive_ingest

⚠️  WARNING: This processes 25,000+ PDFs with OCR. Expected runtime: 10-15 hours
"""

import os
import re
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================
ARCHIVE_PATH = "archive/supreme_court_judgments"
CHROMA_COLLECTION = "sc_judgments_archive"
CHUNK_SIZE = 512          # words per chunk
CHUNK_OVERLAP = 64        # overlapping words
BATCH_SIZE = 50           # Process N documents before embedding
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ============================================================
# TEXT CLEANING
# ============================================================
def clean_text(text: str) -> str:
    """Clean and normalize OCR'd judgment text."""
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove common OCR artifacts
    text = re.sub(r'[^\x00-\x7F\u0900-\u097F]+', '', text)  # Keep ASCII + Devanagari

    # Remove boilerplate
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
    Returns list of chunk dictionaries with id, text, and metadata.
    """
    if not text or len(text.split()) < 30:
        return []

    # Split into sentences (handles ., !, ?)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_sentences: List[str] = []
    current_word_count = 0

    # Get source file for unique ID generation
    source_file = metadata.get("file_path", "unknown") if metadata else "unknown"

    for sentence in sentences:
        word_count = len(sentence.split())

        # Create chunk when size limit reached
        if current_word_count + word_count > chunk_size and current_sentences:
            chunk_text_str = ' '.join(current_sentences)
            # Generate unique ID using source file + chunk index + text hash
            chunk_idx = len(chunks)
            chunk_id = hashlib.md5(f"{source_file}_{chunk_idx}_{chunk_text_str[:200]}".encode()).hexdigest()

            chunks.append({
                "id": chunk_id,
                "text": chunk_text_str,
                "word_count": current_word_count,
                **(metadata or {})
            })

            # Keep overlap: remove oldest sentences
            while current_word_count > overlap and current_sentences:
                removed = current_sentences.pop(0)
                current_word_count -= len(removed.split())

        current_sentences.append(sentence)
        current_word_count += word_count

    # Final chunk
    if current_sentences and current_word_count >= 20:
        chunk_text_str = ' '.join(current_sentences)
        # Generate unique ID using source file + chunk index + text hash
        chunk_idx = len(chunks)
        chunk_id = hashlib.md5(f"{source_file}_{chunk_idx}_{chunk_text_str[:200]}".encode()).hexdigest()
        chunks.append({
            "id": chunk_id,
            "text": chunk_text_str,
            "word_count": current_word_count,
            **(metadata or {})
        })

    return chunks


# ============================================================
# PDF PROCESSING
# ============================================================
def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF (fast, no OCR needed for text PDFs)."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(str(pdf_path))
        text_parts = []

        for page in doc:
            text_parts.append(page.get_text())

        doc.close()
        full_text = "\n".join(text_parts)
        return clean_text(full_text)

    except Exception as e:
        logger.error(f"PDF extraction failed for {pdf_path.name}: {e}")
        return ""


def extract_metadata_from_path(pdf_path: Path) -> Dict:
    """Extract metadata from file path structure."""
    year = pdf_path.parent.name  # Folder name is year
    case_name = pdf_path.stem.replace("_", " ")

    # Try to parse case name components
    petitioner = ""
    respondent = ""
    date_str = ""

    # Pattern: "Name1 vs Name2 on DD Month YYYY"
    match = re.search(r'(.+?)\s+vs\s+(.+?)\s+on\s+(\d+\s+\w+\s+\d{4})', case_name, re.IGNORECASE)
    if match:
        petitioner = match.group(1).strip()
        respondent = match.group(2).strip()
        date_str = match.group(3).strip()

    return {
        "source": "archive_sc_judgments",
        "document_type": "supreme_court_judgment",
        "year": year,
        "case_name": case_name,
        "petitioner": petitioner or "Unknown",
        "respondent": respondent or "Unknown",
        "judgment_date": date_str or year,
        "file_path": str(pdf_path.relative_to(ARCHIVE_PATH)),
    }


# ============================================================
# EMBEDDING + STORAGE
# ============================================================
def embed_and_store(chunks: List[Dict]):
    """Embed chunks and upsert into ChromaDB."""
    if not chunks:
        return

    try:
        from sentence_transformers import SentenceTransformer
        import chromadb
    except ImportError:
        logger.error(
            "Missing dependencies. Install with:\n"
            "  pip install sentence-transformers chromadb --break-system-packages"
        )
        return

    logger.info(f"Embedding {len(chunks)} chunks...")

    # Load model (will cache after first load)
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Get ChromaDB collection
    client = chromadb.PersistentClient(path="data/chroma")
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        metadata={"description": "Supreme Court judgments from PDF archive"}
    )

    # Prepare data
    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    metadatas = [{k: v for k, v in c.items() if k not in ("id", "text", "word_count")}
                 for c in chunks]

    # Embed
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)

    # Store in batches
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        end = min(i + batch_size, len(chunks))
        collection.upsert(
            ids=ids[i:end],
            documents=texts[i:end],
            embeddings=embeddings[i:end].tolist(),
            metadatas=metadatas[i:end]
        )

    logger.info(f"✅ Stored {len(chunks)} chunks in ChromaDB")


# ============================================================
# MAIN PIPELINE
# ============================================================
def run_full_ingestion():
    """Full pipeline: Find PDFs → OCR → Chunk → Embed → Store"""
    logger.info("=" * 70)
    logger.info("PDF ARCHIVE INGESTION - SUPREME COURT JUDGMENTS")
    logger.info("=" * 70)

    # Find all PDFs
    archive_path = Path(ARCHIVE_PATH)
    if not archive_path.exists():
        logger.error(f"Archive path not found: {ARCHIVE_PATH}")
        return

    # Use set to avoid duplicates on Windows (case-insensitive filesystem)
    pdf_files = sorted(set(
        list(archive_path.rglob("*.PDF")) + list(archive_path.rglob("*.pdf"))
    ))
    total_pdfs = len(pdf_files)
    logger.info(f"Found {total_pdfs} PDF files")

    if total_pdfs == 0:
        logger.error("No PDF files found!")
        return

    # Estimate
    logger.info(f"⏱️  Estimated time: {total_pdfs * 2 / 60:.1f} hours (2 sec/PDF avg)")
    logger.info("🚀 Starting automatic processing (no confirmation needed)...")

    # Process PDFs
    all_chunks = []
    processed = 0
    skipped = 0
    start_time = datetime.now()

    for idx, pdf_path in enumerate(pdf_files, 1):
        try:
            # Extract metadata
            metadata = extract_metadata_from_path(pdf_path)

            # OCR
            logger.info(f"[{idx}/{total_pdfs}] Processing: {pdf_path.name}")
            text = extract_text_from_pdf(pdf_path)

            if not text or len(text.split()) < 50:
                logger.warning(f"  ⏭️  Skipping (too short or OCR failed)")
                skipped += 1
                continue

            # Chunk
            chunks = chunk_text(text, metadata=metadata)
            all_chunks.extend(chunks)
            processed += 1

            logger.info(f"  ✅ {len(chunks)} chunks | {len(all_chunks)} total queued")

            # Batch embed every N documents
            if len(all_chunks) >= BATCH_SIZE * 10:
                embed_and_store(all_chunks)
                all_chunks = []

        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Interrupted by user. Saving progress...")
            break
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            skipped += 1

        # Progress update every 100 files
        if idx % 100 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = elapsed / idx
            remaining = (total_pdfs - idx) * rate
            logger.info(f"\n📊 Progress: {idx}/{total_pdfs} | "
                       f"ETA: {remaining/3600:.1f}h | "
                       f"Rate: {rate:.1f}s/PDF\n")

    # Final batch
    if all_chunks:
        embed_and_store(all_chunks)

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("✅ INGESTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total PDFs: {total_pdfs}")
    logger.info(f"Processed: {processed}")
    logger.info(f"Skipped: {skipped}")
    logger.info(f"Success rate: {processed/total_pdfs*100:.1f}%")
    logger.info(f"Time taken: {(datetime.now() - start_time).total_seconds()/3600:.2f}h")
    logger.info(f"Collection: {CHROMA_COLLECTION}")
    logger.info("=" * 70)


if __name__ == "__main__":
    run_full_ingestion()
