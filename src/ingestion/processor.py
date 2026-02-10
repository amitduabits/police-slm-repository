"""
Document Processor - Prepare scraped documents for embedding.

Takes raw scraped documents from data/sources/ and:
1. Normalizes section references (IPC→BNS mappings)
2. Detects language per paragraph
3. Cleans and structures content
4. Saves to data/processed/cleaned/
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass

from src.ingestion.section_normalizer import SectionNormalizer
from src.data_sources.base import ScrapedDocument, DocumentType, SourceName

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Statistics from document processing."""
    total_processed: int = 0
    total_failed: int = 0
    by_source: Dict[str, int] = None
    by_type: Dict[str, int] = None

    def __post_init__(self):
        if self.by_source is None:
            self.by_source = {}
        if self.by_type is None:
            self.by_type = {}


class DocumentProcessor:
    """Process scraped documents into embedding-ready format."""

    def __init__(self, section_normalizer: Optional[SectionNormalizer] = None):
        """
        Initialize document processor.

        Args:
            section_normalizer: Optional SectionNormalizer instance.
                              If None, creates a new one.
        """
        self.normalizer = section_normalizer or SectionNormalizer()
        self.stats = ProcessingStats()

    def process_source_dir(
        self,
        source_dir: str = "data/sources",
        output_dir: str = "data/processed/cleaned"
    ) -> ProcessingStats:
        """
        Read all JSON docs from source scrapers, normalize, output cleaned JSONs.

        Args:
            source_dir: Directory containing raw scraped documents
            output_dir: Directory to save cleaned documents

        Returns:
            ProcessingStats with counts and breakdowns
        """
        source_path = Path(source_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Processing documents from {source_dir}")
        logger.info(f"Output directory: {output_dir}")

        # Reset stats
        self.stats = ProcessingStats()

        # Walk directory tree looking for JSON files
        for json_file in source_path.rglob("*.json"):
            # Skip state files and hidden files
            if json_file.name.startswith("."):
                continue

            try:
                # Load and process document
                cleaned_doc = self._process_document(json_file)

                if cleaned_doc:
                    # Save cleaned document
                    self._save_cleaned_document(cleaned_doc, output_path)

                    # Update stats
                    self.stats.total_processed += 1
                    source = cleaned_doc.get("source", "unknown")
                    doc_type = cleaned_doc.get("document_type", "unknown")

                    self.stats.by_source[source] = self.stats.by_source.get(source, 0) + 1
                    self.stats.by_type[doc_type] = self.stats.by_type.get(doc_type, 0) + 1

                    logger.info(f"Processed: {json_file.name} ({source}/{doc_type})")
                else:
                    self.stats.total_failed += 1
                    logger.warning(f"Failed to process: {json_file}")

            except Exception as e:
                self.stats.total_failed += 1
                logger.error(f"Error processing {json_file}: {e}")

        # Print summary
        self._print_stats()
        return self.stats

    def _process_document(self, json_file: Path) -> Optional[Dict]:
        """
        Process a single document.

        Args:
            json_file: Path to JSON file containing ScrapedDocument

        Returns:
            Cleaned document dict or None if processing failed
        """
        # Load document
        with open(json_file, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)

        # Reconstruct ScrapedDocument (or just work with dict)
        content = doc_data.get("content", "")
        if not content or len(content) < 50:
            logger.warning(f"Document too short or empty: {json_file.name}")
            return None

        # Normalize section references in content
        normalized_content = self._normalize_sections(content)

        # Detect language (simple heuristic for now)
        language = self._detect_language(content)

        # Extract normalized sections cited
        normalized_sections = self._extract_and_normalize_sections(content)

        # Build cleaned document
        cleaned = {
            "source": doc_data.get("source"),
            "source_url": doc_data.get("source_url"),
            "document_type": doc_data.get("document_type"),
            "title": doc_data.get("title", ""),
            "content": normalized_content,
            "language": language,
            "date_published": doc_data.get("date_published"),
            "case_number": doc_data.get("case_number"),
            "court": doc_data.get("court"),
            "sections_cited": normalized_sections,
            "judges": doc_data.get("judges", []),
            "parties": doc_data.get("parties", []),
            "metadata": doc_data.get("metadata", {}),
            "content_hash": doc_data.get("content_hash", ""),
            "processed": True,
        }

        return cleaned

    def _normalize_sections(self, text: str) -> str:
        """
        Normalize section references in text.
        For now, just returns original text.
        Full implementation would do regex replacement.

        Args:
            text: Original text with section references

        Returns:
            Text with normalized section references
        """
        # For POC, return as-is
        # Full implementation: regex find Section XXX IPC, replace with both IPC and BNS
        return text

    def _extract_and_normalize_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Extract section references and normalize them.

        Args:
            text: Document text

        Returns:
            List of dicts with original and normalized sections
        """
        # For POC, return empty list
        # Full implementation would use regex to find sections and normalize them
        return []

    def _detect_language(self, text: str) -> str:
        """
        Detect language of document.
        Simple heuristic: check for Devanagari script or Gujarati script.

        Args:
            text: Document text

        Returns:
            Language code: 'en', 'hi', 'gu'
        """
        # Simple heuristic: check for unicode ranges
        # Devanagari: 0900–097F
        # Gujarati: 0A80–0AFF

        sample = text[:1000]  # Check first 1000 chars

        devanagari_count = sum(1 for c in sample if '\u0900' <= c <= '\u097F')
        gujarati_count = sum(1 for c in sample if '\u0A80' <= c <= '\u0AFF')

        if gujarati_count > 10:
            return "gu"
        elif devanagari_count > 10:
            return "hi"
        else:
            return "en"

    def _save_cleaned_document(self, doc: Dict, output_dir: Path):
        """
        Save cleaned document to output directory.

        Args:
            doc: Cleaned document dict
            output_dir: Output directory path
        """
        # Organize by source/type/year
        source = doc.get("source", "unknown")
        doc_type = doc.get("document_type", "unknown")
        year = "unknown"

        if doc.get("date_published"):
            try:
                year = doc["date_published"][:4]
            except (IndexError, TypeError):
                pass

        subdir = output_dir / source / doc_type / year
        subdir.mkdir(parents=True, exist_ok=True)

        # Use content_hash for filename
        content_hash = doc.get("content_hash", "unknown")
        filename = f"{content_hash[:16]}.json"
        filepath = subdir / filename

        # Save
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)

    def _print_stats(self):
        """Print processing statistics."""
        logger.info("=" * 60)
        logger.info("Document Processing Statistics:")
        logger.info(f"  Total processed: {self.stats.total_processed}")
        logger.info(f"  Total failed: {self.stats.total_failed}")
        logger.info(f"  By source: {dict(self.stats.by_source)}")
        logger.info(f"  By type: {dict(self.stats.by_type)}")
        logger.info("=" * 60)


def create_processor() -> DocumentProcessor:
    """Factory function to create a DocumentProcessor."""
    return DocumentProcessor()


if __name__ == "__main__":
    # Test the processor
    logging.basicConfig(level=logging.INFO)
    processor = create_processor()
    stats = processor.process_source_dir()
    print(f"\nProcessed {stats.total_processed} documents")
