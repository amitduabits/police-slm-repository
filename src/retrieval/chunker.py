"""
Document Chunker for RAG pipeline.
Chunks documents into semantically meaningful segments with metadata.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Chunk documents for embedding, respecting structure boundaries."""

    def __init__(self, chunk_size=500, overlap=100, max_chunk_size=1000):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.max_chunk_size = max_chunk_size

    def chunk_document(self, doc: dict) -> list[dict]:
        """Chunk a processed document based on its type."""
        doc_type = doc.get("document_type", "generic")
        content = doc.get("content", "")
        metadata = {
            "document_id": doc.get("id") or doc.get("document_id", ""),
            "document_type": doc_type,
            "source": doc.get("source", ""),
            "language": doc.get("language", "en"),
            "date": doc.get("date_published", ""),
            "district": doc.get("district", ""),
            "sections_cited": doc.get("sections_cited", []),
            "title": doc.get("title", ""),
        }

        if doc_type == "fir":
            return self._chunk_fir(content, metadata)
        elif doc_type == "chargesheet":
            return self._chunk_chargesheet(content, metadata)
        elif doc_type == "court_ruling":
            return self._chunk_ruling(content, metadata)
        else:
            return self._chunk_generic(content, metadata)

    def _chunk_fir(self, text: str, base_meta: dict) -> list[dict]:
        """Chunk FIR by sections."""
        sections = {
            "complainant": r"(?:complainant|informant|first information).*?(?=\n(?:accused|incident|offence|section)|\Z)",
            "incident": r"(?:incident|occurrence|offence committed).*?(?=\n(?:accused|evidence|action taken)|\Z)",
            "evidence": r"(?:evidence|property|exhibit|seized).*?(?=\n(?:action|recommendation|signature)|\Z)",
            "accused": r"(?:accused|suspect).*?(?=\n(?:evidence|action|signature)|\Z)",
        }
        chunks = []
        used_text = set()

        for section_name, pattern in sections.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section_text = match.group(0).strip()
                if section_text and section_text not in used_text:
                    meta = {**base_meta, "section_name": section_name}
                    chunks.extend(self._split_text(section_text, meta))
                    used_text.add(section_text)

        # Catch any remaining text
        if not chunks:
            chunks = self._chunk_generic(text, base_meta)

        return chunks

    def _chunk_chargesheet(self, text: str, base_meta: dict) -> list[dict]:
        """Chunk chargesheet by sections."""
        sections = {
            "accused_details": r"(?:accused|person charged).*?(?=\n(?:witness|evidence|investigation)|\Z)",
            "evidence": r"(?:evidence|exhibit|forensic|report).*?(?=\n(?:witness|chronology|recommendation)|\Z)",
            "witnesses": r"(?:witness|deposition|statement).*?(?=\n(?:evidence|chronology|conclusion)|\Z)",
            "investigation": r"(?:investigation|chronology|inquiry).*?(?=\n(?:conclusion|recommendation|prayer)|\Z)",
        }
        chunks = []
        for section_name, pattern in sections.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                meta = {**base_meta, "section_name": section_name}
                chunks.extend(self._split_text(match.group(0).strip(), meta))

        if not chunks:
            chunks = self._chunk_generic(text, base_meta)
        return chunks

    def _chunk_ruling(self, text: str, base_meta: dict) -> list[dict]:
        """Chunk court ruling by paragraphs, keep reasoning larger."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        chunks = []

        for i, para in enumerate(paragraphs):
            is_reasoning = any(kw in para.lower() for kw in [
                "held that", "we hold", "in our opinion", "we are of the view",
                "considering the", "it is established", "the evidence shows",
                "accordingly", "therefore", "thus we conclude",
            ])
            max_size = self.max_chunk_size if is_reasoning else self.chunk_size
            meta = {**base_meta, "section_name": "reasoning" if is_reasoning else f"para_{i}",
                    "is_key_reasoning": is_reasoning}
            chunks.extend(self._split_text(para, meta, max_chunk=max_size))

        return chunks

    def _chunk_generic(self, text: str, base_meta: dict) -> list[dict]:
        """Generic chunking by paragraphs with overlap."""
        return self._split_text(text, base_meta)

    def _split_text(self, text: str, metadata: dict, max_chunk: int = None) -> list[dict]:
        """Split text into chunks respecting word boundaries."""
        max_size = max_chunk or self.chunk_size
        words = text.split()
        if not words:
            return []

        chunks = []
        start = 0
        while start < len(words):
            end = min(start + max_size, len(words))
            chunk_text = ' '.join(words[start:end])

            chunks.append({
                "text": chunk_text,
                "metadata": {**metadata, "chunk_index": len(chunks)},
                "word_count": end - start,
            })

            if end >= len(words):
                break
            start = end - self.overlap  # Overlap

        return chunks
