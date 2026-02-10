"""
Embedding Pipeline - Create and search vector embeddings.

Uses sentence-transformers for multilingual embeddings (English/Hindi/Gujarati)
and ChromaDB for vector storage.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Please install sentence-transformers: pip install sentence-transformers")
    raise

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("Please install chromadb: pip install chromadb")
    raise

from src.retrieval.chunker import DocumentChunker

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with document chunk and relevance score."""
    chunk_text: str
    doc_id: str
    title: str
    source: str
    court: Optional[str]
    sections: List[str]
    score: float
    metadata: Dict


class EmbeddingPipeline:
    """
    Embedding pipeline for document chunks.

    Features:
    - Multilingual embeddings (En/Hi/Gu)
    - ChromaDB persistent storage
    - Multiple collections (bare_acts, court_rulings, all_documents)
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        chroma_persist_dir: str = "data/embeddings/chroma",
        device: str = "cpu"
    ):
        """
        Initialize embedding pipeline.

        Args:
            model_name: Sentence transformer model name
            chroma_persist_dir: Directory to persist ChromaDB
            device: 'cpu' or 'cuda'
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)
        logger.info(f"Model loaded. Embedding dim: {self.model.get_sentence_embedding_dimension()}")

        # Initialize ChromaDB client
        persist_path = Path(chroma_persist_dir)
        persist_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(persist_path))
        logger.info(f"ChromaDB initialized at: {persist_path}")

        # Initialize chunker
        self.chunker = DocumentChunker()

        # Collection names
        self.collections = {
            "all_documents": None,
            "court_rulings": None,
            "bare_acts": None,
        }

    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        if self.collections[name] is None:
            self.collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"description": f"Collection for {name}"}
            )
            logger.info(f"Collection '{name}' ready (count: {self.collections[name].count()})")
        return self.collections[name]

    def embed_directory(
        self,
        input_dir: str = "data/processed/cleaned",
        batch_size: int = 32
    ) -> Dict[str, int]:
        """
        Chunk and embed all documents in directory.

        Args:
            input_dir: Directory containing processed JSON documents
            batch_size: Batch size for embedding

        Returns:
            Dict with stats (total_docs, total_chunks, etc.)
        """
        input_path = Path(input_dir)
        logger.info(f"Embedding documents from: {input_path}")

        stats = {
            "total_docs": 0,
            "total_chunks": 0,
            "by_collection": {},
        }

        # Collect all JSON files
        json_files = list(input_path.rglob("*.json"))
        logger.info(f"Found {len(json_files)} documents to embed")

        for json_file in json_files:
            try:
                # Load document
                with open(json_file, 'r', encoding='utf-8') as f:
                    doc = json.load(f)

                # Skip if no content
                if not doc.get("content"):
                    logger.warning(f"Skipping {json_file.name}: no content")
                    continue

                # Chunk document (pass whole doc dict)
                chunks = self.chunker.chunk_document(doc)

                if not chunks:
                    logger.warning(f"No chunks generated for {json_file.name}")
                    continue

                # Embed and store chunks
                self._embed_and_store_chunks(doc, chunks)

                stats["total_docs"] += 1
                stats["total_chunks"] += len(chunks)

                if stats["total_docs"] % 10 == 0:
                    logger.info(f"Processed {stats['total_docs']} documents, {stats['total_chunks']} chunks")

            except Exception as e:
                logger.error(f"Error processing {json_file}: {e}")

        logger.info("=" * 60)
        logger.info("Embedding Statistics:")
        logger.info(f"  Total documents: {stats['total_docs']}")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        logger.info(f"  Avg chunks/doc: {stats['total_chunks'] / stats['total_docs'] if stats['total_docs'] > 0 else 0:.1f}")
        logger.info("=" * 60)

        return stats

    def _embed_and_store_chunks(self, doc: Dict, chunks: List[Dict]):
        """
        Embed chunks and store in ChromaDB.

        Args:
            doc: Original document dict
            chunks: List of chunk dicts from chunker
        """
        # Extract texts and metadata
        texts = [chunk["text"] for chunk in chunks]

        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True).tolist()

        # Prepare for ChromaDB
        ids = [f"{doc.get('content_hash', 'unknown')[:16]}_chunk_{i}" for i in range(len(chunks))]

        metadatas = []
        for i, chunk in enumerate(chunks):
            metadatas.append({
                "title": doc.get("title", "")[:500],  # Limit length
                "source": doc.get("source", ""),
                "doc_type": doc.get("document_type", ""),
                "court": doc.get("court", "")[:200] if doc.get("court") else "",
                "case_number": doc.get("case_number", "")[:200] if doc.get("case_number") else "",
                "sections": ",".join(doc.get("sections_cited", []))[:500],
                "language": doc.get("language", "en"),
                "date_published": doc.get("date_published", "")[:20],
                "chunk_index": i,
                "total_chunks": len(chunks),
                "source_url": doc.get("source_url", "")[:500],
            })

        # Add to appropriate collections
        doc_type = doc.get("document_type", "")

        # All documents collection
        all_coll = self._get_or_create_collection("all_documents")
        all_coll.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

        # Type-specific collection
        if "court_ruling" in doc_type.lower():
            coll = self._get_or_create_collection("court_rulings")
            coll.add(embeddings=embeddings, documents=texts, metadatas=metadatas, ids=ids)
        elif "bare_act" in doc_type.lower():
            coll = self._get_or_create_collection("bare_acts")
            coll.add(embeddings=embeddings, documents=texts, metadatas=metadatas, ids=ids)

    def search(
        self,
        query: str,
        collection: str = "all_documents",
        top_k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Search embedded documents.

        Args:
            query: Search query text
            collection: Collection name to search
            top_k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            List of SearchResult objects
        """
        # Get collection
        coll = self._get_or_create_collection(collection)

        # Embed query
        query_embedding = self.model.encode([query], convert_to_numpy=True).tolist()[0]

        # Search
        results = coll.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_dict if filter_dict else None
        )

        # Parse results
        search_results = []
        if results and results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if 'distances' in results else 0.0

                # Convert distance to similarity score (1 - normalized_distance)
                # For L2 distance, normalize and invert
                score = max(0.0, 1.0 - (distance / 2.0))  # Simple normalization

                search_results.append(SearchResult(
                    chunk_text=results['documents'][0][i],
                    doc_id=results['ids'][0][i],
                    title=metadata.get('title', ''),
                    source=metadata.get('source', ''),
                    court=metadata.get('court'),
                    sections=metadata.get('sections', '').split(',') if metadata.get('sections') else [],
                    score=score,
                    metadata=metadata
                ))

        return search_results


def create_embedding_pipeline(chroma_dir: str = "data/embeddings/chroma") -> EmbeddingPipeline:
    """Factory function to create an EmbeddingPipeline."""
    return EmbeddingPipeline(chroma_persist_dir=chroma_dir)


if __name__ == "__main__":
    # Test the pipeline
    logging.basicConfig(level=logging.INFO)

    pipeline = create_embedding_pipeline()
    stats = pipeline.embed_directory("data/processed/cleaned")

    print(f"\nEmbedded {stats['total_docs']} documents into {stats['total_chunks']} chunks")

    # Test search
    results = pipeline.search("murder Section 302", top_k=3)
    print(f"\nTest search results ({len(results)}):")
    for r in results:
        print(f"  Score: {r.score:.3f} | {r.title[:80]}")
