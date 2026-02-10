"""
Base classes for all data sources.
Provides common functionality: rate limiting, retry, logging, storage.
"""

import hashlib
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Generator, Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    COURT_RULING = "court_ruling"
    FIR = "fir"
    CHARGESHEET = "chargesheet"
    PANCHNAMA = "panchnama"
    INVESTIGATION_REPORT = "investigation_report"
    BARE_ACT = "bare_act"
    CRIME_STATISTICS = "crime_statistics"
    LEGAL_COMMENTARY = "legal_commentary"


class SourceName(str, Enum):
    ECOURTS = "ecourts"
    INDIAN_KANOON = "indian_kanoon"
    GUJARAT_HC = "gujarat_hc"
    SUPREME_COURT = "supreme_court"
    INDIA_CODE = "india_code"
    NCRB = "ncrb"
    NJDG = "njdg"
    LOCAL_UPLOAD = "local_upload"


@dataclass
class DataSourceConfig:
    """Configuration for a data source scraper."""
    base_url: str
    output_dir: str
    delay_seconds: float = 2.0
    max_concurrent: int = 3
    max_retries: int = 3
    timeout: int = 30
    user_agent: str = "GujPolSLM-Research/1.0"
    proxy: Optional[str] = None
    verify_ssl: bool = True
    max_pages: int = 100
    state_file: Optional[str] = None  # For resume capability


@dataclass
class ScrapedDocument:
    """A document scraped from a verified source."""
    source: SourceName
    source_url: str
    document_type: DocumentType
    title: str
    content: str  # Raw text content
    html_content: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    language: str = "en"  # en, hi, gu
    date_scraped: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    date_published: Optional[str] = None
    case_number: Optional[str] = None
    court: Optional[str] = None
    sections_cited: list = field(default_factory=list)
    judges: list = field(default_factory=list)
    parties: list = field(default_factory=list)
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash and self.content:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ScrapedDocument":
        data = json.loads(json_str)
        data["source"] = SourceName(data["source"])
        data["document_type"] = DocumentType(data["document_type"])
        return cls(**data)


class BaseDataSource(ABC):
    """
    Abstract base class for all data source scrapers.

    Provides:
    - HTTP session with retries and rate limiting
    - State persistence for resume capability
    - Deduplication via content hashing
    - Structured logging
    - File storage with organized directory structure
    """

    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.session = self._create_session()
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._last_request_time = 0.0
        self._seen_hashes: set = set()
        self._stats = {
            "total_fetched": 0,
            "total_saved": 0,
            "total_skipped_duplicate": 0,
            "total_errors": 0,
            "start_time": None,
            "end_time": None,
        }
        self._load_state()
        self._load_seen_hashes()

    def _create_session(self) -> requests.Session:
        """Create an HTTP session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8,gu;q=0.7",
        })
        if self.config.proxy:
            session.proxies = {"http": self.config.proxy, "https": self.config.proxy}
        return session

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.config.delay_seconds:
            time.sleep(self.config.delay_seconds - elapsed)
        self._last_request_time = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    def fetch_page(self, url: str, params: dict = None) -> Optional[requests.Response]:
        """Fetch a page with rate limiting and retry."""
        self._rate_limit()
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
            response.raise_for_status()
            self._stats["total_fetched"] += 1
            logger.info(f"Fetched: {url} [{response.status_code}]")
            return response
        except requests.RequestException as e:
            self._stats["total_errors"] += 1
            logger.error(f"Error fetching {url}: {e}")
            raise

    def fetch_json(self, url: str, params: dict = None) -> Optional[dict]:
        """Fetch JSON data from a URL."""
        response = self.fetch_page(url, params)
        if response:
            return response.json()
        return None

    def save_document(self, doc: ScrapedDocument) -> Optional[Path]:
        """Save a scraped document to disk, skipping duplicates."""
        if doc.content_hash in self._seen_hashes:
            self._stats["total_skipped_duplicate"] += 1
            logger.debug(f"Skipping duplicate: {doc.title}")
            return None

        # Organize by source/type/year
        year = "unknown"
        if doc.date_published:
            try:
                year = doc.date_published[:4]
            except (IndexError, TypeError):
                pass

        subdir = self.output_dir / doc.source.value / doc.document_type.value / year
        subdir.mkdir(parents=True, exist_ok=True)

        # Filename from hash (avoids special chars)
        filename = f"{doc.content_hash[:16]}.json"
        filepath = subdir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(doc.to_json())

        self._seen_hashes.add(doc.content_hash)
        self._stats["total_saved"] += 1
        logger.info(f"Saved: {doc.title} -> {filepath}")
        return filepath

    def _load_seen_hashes(self):
        """Load previously seen content hashes for deduplication."""
        hash_file = self.output_dir / ".seen_hashes"
        if hash_file.exists():
            with open(hash_file, "r") as f:
                self._seen_hashes = set(f.read().splitlines())
            logger.info(f"Loaded {len(self._seen_hashes)} known document hashes")

    def _save_seen_hashes(self):
        """Persist seen hashes to disk."""
        hash_file = self.output_dir / ".seen_hashes"
        with open(hash_file, "w") as f:
            f.write("\n".join(self._seen_hashes))

    def _load_state(self):
        """Load scraper state for resume capability."""
        self._state = {}
        state_file = self.config.state_file or str(self.output_dir / ".scraper_state.json")
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                self._state = json.load(f)
            logger.info(f"Resumed from state: {state_file}")

    def _save_state(self):
        """Save scraper state for resume capability."""
        state_file = self.config.state_file or str(self.output_dir / ".scraper_state.json")
        with open(state_file, "w") as f:
            json.dump(self._state, f, indent=2)

    def get_stats(self) -> dict:
        """Get scraping statistics."""
        return {**self._stats, "seen_hashes": len(self._seen_hashes)}

    def print_stats(self):
        """Print scraping statistics."""
        stats = self.get_stats()
        logger.info("=" * 50)
        logger.info("Scraping Statistics:")
        for k, v in stats.items():
            logger.info(f"  {k}: {v}")
        logger.info("=" * 50)

    @abstractmethod
    def source_name(self) -> SourceName:
        """Return the source name enum."""
        ...

    @abstractmethod
    def scrape(self, **kwargs) -> Generator[ScrapedDocument, None, None]:
        """
        Main scraping method. Yields ScrapedDocument objects.
        Subclasses implement the actual scraping logic.
        """
        ...

    def run(self, **kwargs) -> dict:
        """Execute the full scraping pipeline."""
        self._stats["start_time"] = datetime.utcnow().isoformat()
        logger.info(f"Starting {self.source_name().value} scraper...")

        try:
            for doc in self.scrape(**kwargs):
                self.save_document(doc)
        except KeyboardInterrupt:
            logger.warning("Scraping interrupted by user")
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise
        finally:
            self._stats["end_time"] = datetime.utcnow().isoformat()
            self._save_seen_hashes()
            self._save_state()
            self.print_stats()

        return self.get_stats()
