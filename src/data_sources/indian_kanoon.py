"""
Indian Kanoon Data Source (indiankanoon.org)

Indian Kanoon is the largest free repository of Indian court judgments.
It provides full-text searchable judgments from:
- Supreme Court of India
- All High Courts (including Gujarat HC)
- District Courts
- Tribunals

This scraper fetches Gujarat-relevant court rulings with full text.

USAGE:
    source = IndianKanoonDataSource(config)
    source.run(
        query="Gujarat murder Section 302",
        court_filter="Gujarat",
        max_results=500
    )

NOTE: Indian Kanoon has an API for institutional access.
Contact them at contact@indiankanoon.org for bulk data access.
For the POC, we use respectful web scraping with rate limits.
"""

import re
import logging
from typing import Generator, Optional
from urllib.parse import urljoin, quote_plus

from bs4 import BeautifulSoup

from src.data_sources.base import (
    BaseDataSource,
    DataSourceConfig,
    DocumentType,
    ScrapedDocument,
    SourceName,
)

logger = logging.getLogger(__name__)

# Gujarat-relevant search queries for building the corpus
DEFAULT_QUERIES = [
    # Criminal law queries
    "Gujarat murder Section 302 IPC",
    "Gujarat theft Section 379 IPC",
    "Gujarat robbery Section 392 IPC",
    "Gujarat cheating Section 420 IPC",
    "Gujarat assault Section 323 IPC",
    "Gujarat dowry death Section 304B IPC",
    "Gujarat kidnapping Section 363 IPC",
    "Gujarat NDPS Act Gujarat",
    "Gujarat criminal breach of trust Section 406",
    "Gujarat forgery Section 468 IPC",
    "Gujarat domestic violence Gujarat",
    "Gujarat road accident Section 304A IPC",
    "Gujarat criminal trespass Section 441",
    "Gujarat SC ST Atrocities Act Gujarat",
    "Gujarat POCSO Act Gujarat",
    "Gujarat Arms Act Gujarat",
    "Gujarat cybercrime Gujarat",
    "Gujarat extortion Section 384 IPC",
    "Gujarat rioting Section 147 IPC",
    "Gujarat attempt to murder Section 307 IPC",

    # BNS (New criminal code) queries
    "Bharatiya Nyaya Sanhita Gujarat",
    "BNS Section 103 murder Gujarat",
    "BNSS Gujarat High Court",
    "Bharatiya Sakshya Adhiniyam Gujarat",

    # Procedural queries
    "chargesheet deficiency Gujarat",
    "investigation procedure Gujarat",
    "FIR registration Gujarat",
    "bail conditions Gujarat",
    "anticipatory bail Gujarat High Court",
    "evidence collection procedure Gujarat",
    "panchnama procedure Gujarat",
    "Section 173 CrPC Gujarat",
    "witness protection Gujarat",
    "forensic evidence Gujarat",

    # Landmark Gujarat cases
    "Gujarat High Court landmark criminal",
    "Gujarat acquittal chargesheet deficiency",
    "Gujarat conviction rate analysis",
]

# Court filters for Indian Kanoon
COURT_FILTERS = {
    "supreme_court": "supremecourt",
    "gujarat_hc": "gujarathighcourt",
    "gujarat_district": "gujaratdistrict",
    "all_high_courts": "allahc",
}


class IndianKanoonDataSource(BaseDataSource):
    """
    Scraper for Indian Kanoon (indiankanoon.org).
    Fetches full-text court judgments relevant to Gujarat Police work.
    """

    BASE_URL = "https://indiankanoon.org"

    def source_name(self) -> SourceName:
        return SourceName.INDIAN_KANOON

    def _build_search_url(
        self,
        query: str,
        page: int = 0,
        court_filter: str = None,
    ) -> str:
        """Build the search URL for Indian Kanoon."""
        encoded_query = quote_plus(query)
        url = f"{self.BASE_URL}/search/?formInput={encoded_query}"

        if court_filter and court_filter in COURT_FILTERS:
            url += f"&pagenum={page}&{COURT_FILTERS[court_filter]}=true"
        elif page > 0:
            url += f"&pagenum={page}"

        return url

    def _parse_search_results(self, html: str) -> list[dict]:
        """Parse search results page to extract case links."""
        soup = BeautifulSoup(html, "lxml")
        results = []

        for result_div in soup.select(".result"):
            title_elem = result_div.select_one(".result_title a")
            if not title_elem:
                continue

            link = title_elem.get("href", "")
            # Accept both /doc/ and /docfragment/ URLs
            if not (link.startswith("/doc/") or link.startswith("/docfragment/")):
                continue

            title = title_elem.get_text(strip=True)

            # Extract snippet - updated to use 'headline' class
            snippet_elem = result_div.select_one(".headline")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            # Extract metadata (court, date)
            meta_elem = result_div.select_one(".docsource")
            meta_text = meta_elem.get_text(strip=True) if meta_elem else ""

            # Extract doc_id from either /doc/ or /docfragment/
            if "/doc/" in link:
                doc_id = link.split("/doc/")[1].split("/")[0].split("?")[0]
            else:
                doc_id = link.split("/docfragment/")[1].split("/")[0].split("?")[0]

            # Convert docfragment URLs to doc URLs for consistency
            if link.startswith("/docfragment/"):
                doc_url = f"/doc/{doc_id}/"
            else:
                doc_url = link

            results.append({
                "doc_id": doc_id,
                "url": urljoin(self.BASE_URL, doc_url),
                "title": title,
                "snippet": snippet,
                "meta": meta_text,
            })

        return results

    def _parse_judgment_page(self, html: str, url: str) -> Optional[dict]:
        """Parse a full judgment page to extract structured data."""
        soup = BeautifulSoup(html, "lxml")

        # Main judgment text - in article.middle_column > div.akoma-ntoso
        article = soup.select_one("article.middle_column")
        if not article:
            logger.warning(f"Could not find article.middle_column on {url}")
            return None
        
        judgment_div = article.select_one("div.akoma-ntoso")
        logger.debug(f"Found div.akoma-ntoso: {judgment_div is not None}")

        if not judgment_div:
            # Try alternative: any div with substantial text
            logger.debug(f"Trying to find any div in article")
            judgment_div = article.select_one("div")
            logger.debug(f"Found alternative div: {judgment_div is not None}")

        if not judgment_div:
            logger.warning(f"Could not find judgment text container on {url}")
            return None

        # Debug: print the actual HTML structure
        logger.debug(f"judgment_div tag: {judgment_div.name if judgment_div else 'None'}, classes: {judgment_div.get('class') if judgment_div else 'None'}")
        logger.debug(f"judgment_div HTML (first 500 chars): {str(judgment_div)[:500]}")

        # Get full text
        full_text = judgment_div.get_text(separator="\n", strip=True)
        html_content = str(judgment_div)

        logger.debug(f"Extracted text length: {len(full_text)}, first 200 chars: {full_text[:200]}")

        # Extract title
        title_elem = soup.select_one("h2.doc_title") or soup.select_one("title")
        title = title_elem.get_text(strip=True) if title_elem else "Unknown"

        # Extract court and date from doc source
        source_elem = soup.select_one(".docsource_main")
        source_text = source_elem.get_text(strip=True) if source_elem else ""

        # Extract judge names
        author_elem = soup.select_one(".doc_author")
        judges = []
        if author_elem:
            judges = [a.get_text(strip=True) for a in author_elem.select("a")]

        # Extract date
        date_published = self._extract_date(source_text + " " + full_text[:500])

        # Extract court name
        court = self._extract_court(source_text)

        # Extract case number
        case_number = self._extract_case_number(title + " " + full_text[:500])

        # Extract IPC/BNS sections cited
        sections = self._extract_sections(full_text)

        # Extract party names
        parties = self._extract_parties(title)

        return {
            "title": title,
            "full_text": full_text,
            "html_content": html_content,
            "court": court,
            "date_published": date_published,
            "case_number": case_number,
            "judges": judges,
            "sections": sections,
            "parties": parties,
            "source_text": source_text,
        }

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from judgment text."""
        patterns = [
            r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*(\d{4})",
            r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
            r"dated\s+(\d{1,2})[./-](\d{1,2})[./-](\d{4})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3 and not groups[1].isdigit():
                        # Month name format
                        from datetime import datetime
                        date_str = f"{groups[0]} {groups[1]} {groups[2]}"
                        dt = datetime.strptime(date_str, "%d %B %Y")
                        return dt.strftime("%Y-%m-%d")
                    elif len(groups) == 3:
                        return f"{groups[2]}-{groups[1]:>02}-{groups[0]:>02}"
                except (ValueError, IndexError):
                    continue
        return None

    def _extract_court(self, text: str) -> str:
        """Extract court name from source text."""
        court_patterns = {
            "Supreme Court of India": r"Supreme\s+Court",
            "Gujarat High Court": r"Gujarat\s+High\s+Court|High\s+Court\s+of\s+Gujarat",
            "Ahmedabad District Court": r"Ahmedabad.*District|District.*Ahmedabad",
            "Surat District Court": r"Surat.*District|District.*Surat",
            "Vadodara District Court": r"Vadodara.*District|District.*Vadodara|Baroda.*District",
            "Rajkot District Court": r"Rajkot.*District|District.*Rajkot",
        }
        for court_name, pattern in court_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return court_name
        return text[:100] if text else "Unknown"

    def _extract_case_number(self, text: str) -> Optional[str]:
        """Extract case number/citation."""
        patterns = [
            r"(Criminal\s+Appeal\s+No\.\s*\d+\s*/\s*\d{4})",
            r"(Criminal\s+Misc\.\s*Application\s+No\.\s*\d+\s*/\s*\d{4})",
            r"(Special\s+Criminal\s+Application\s+No\.\s*\d+\s*/\s*\d{4})",
            r"(Bail\s+Application\s+No\.\s*\d+\s*/\s*\d{4})",
            r"(CR\.?MA?\s*No\.\s*\d+\s*/\s*\d{4})",
            r"(Sessions\s+Case\s+No\.\s*\d+\s*/\s*\d{4})",
            r"(FIR\s+No\.\s*[A-Z0-9/-]+)",
            r"(\d{4}\s*\(\d+\)\s*SCC\s*\d+)",
            r"(\d{4}\s*\(\d+\)\s*GLR\s*\d+)",
            r"(AIR\s+\d{4}\s+\w+\s+\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_sections(self, text: str) -> list[str]:
        """Extract IPC/BNS/CrPC/BNSS sections cited in judgment."""
        sections = set()
        patterns = [
            # IPC sections
            r"[Ss]ection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?(?:Indian\s+Penal\s+Code|I\.?P\.?C\.?)",
            r"(?:IPC|I\.P\.C\.?)\s*[Ss](?:ection|ec\.?)\s*(\d+[A-Z]?)",
            r"[Ss]\.?\s*(\d+[A-Z]?)\s+IPC",
            # BNS sections
            r"[Ss]ection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?(?:Bharatiya\s+Nyaya\s+Sanhita|B\.?N\.?S\.?)",
            r"(?:BNS|B\.N\.S\.?)\s*[Ss](?:ection|ec\.?)\s*(\d+[A-Z]?)",
            # CrPC sections
            r"[Ss]ection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?(?:Code\s+of\s+Criminal\s+Procedure|Cr\.?P\.?C\.?|CrPC)",
            # BNSS
            r"[Ss]ection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?(?:Bharatiya\s+Nagarik\s+Suraksha\s+Sanhita|B\.?N\.?S\.?S\.?|BNSS)",
            # NDPS
            r"[Ss]ection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?(?:NDPS\s+Act|Narcotic)",
            # POCSO
            r"[Ss]ection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?POCSO",
            # Arms Act
            r"[Ss]ection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?Arms\s+Act",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                section_num = match.group(1)
                # Reconstruct with context
                full_match = match.group(0)
                sections.add(full_match.strip())

        return sorted(list(sections))[:50]  # Cap at 50 sections

    def _extract_parties(self, title: str) -> list[str]:
        """Extract party names from case title."""
        # Common pattern: "X vs Y" or "X v. Y" or "X versus Y"
        vs_pattern = r"(.+?)\s+(?:vs?\.?|versus)\s+(.+?)(?:\s+on\s+|\s*$)"
        match = re.search(vs_pattern, title, re.IGNORECASE)
        if match:
            return [match.group(1).strip(), match.group(2).strip()]
        return []

    def _detect_language(self, text: str) -> str:
        """Simple language detection for Indian legal text."""
        # Check for Gujarati Unicode range (U+0A80 - U+0AFF)
        gujarati_chars = len(re.findall(r'[\u0A80-\u0AFF]', text))
        # Check for Hindi/Devanagari Unicode range (U+0900 - U+097F)
        hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
        total_chars = len(text)

        if total_chars == 0:
            return "en"

        if gujarati_chars / total_chars > 0.1:
            return "gu"
        elif hindi_chars / total_chars > 0.1:
            return "hi"
        return "en"

    def scrape_search(
        self,
        query: str,
        court_filter: str = None,
        max_results: int = 100,
    ) -> Generator[ScrapedDocument, None, None]:
        """Scrape search results for a given query."""
        page = 0
        results_fetched = 0
        max_pages = max_results // 10 + 1

        while results_fetched < max_results and page < max_pages:
            url = self._build_search_url(query, page, court_filter)
            response = self.fetch_page(url)
            if not response:
                break

            results = self._parse_search_results(response.text)
            if not results:
                logger.info(f"No more results for query: {query}, page: {page}")
                break

            for result in results:
                if results_fetched >= max_results:
                    break

                # Fetch full judgment
                judgment_response = self.fetch_page(result["url"])
                if not judgment_response:
                    continue

                parsed = self._parse_judgment_page(judgment_response.text, result["url"])
                if not parsed:
                    logger.warning(f"Failed to parse judgment page: {result['url']}")
                    continue
                if not parsed["full_text"]:
                    logger.warning(f"Empty full_text in parsed judgment: {result['url']}, full_text length: {len(parsed['full_text']) if parsed['full_text'] else 0}, title: {parsed['title'][:100]}")
                    continue

                language = self._detect_language(parsed["full_text"])

                doc = ScrapedDocument(
                    source=SourceName.INDIAN_KANOON,
                    source_url=result["url"],
                    document_type=DocumentType.COURT_RULING,
                    title=parsed["title"],
                    content=parsed["full_text"],
                    html_content=parsed["html_content"],
                    language=language,
                    date_published=parsed["date_published"],
                    case_number=parsed["case_number"],
                    court=parsed["court"],
                    sections_cited=parsed["sections"],
                    judges=parsed["judges"],
                    parties=parsed["parties"],
                    metadata={
                        "query": query,
                        "court_filter": court_filter,
                        "doc_id": result["doc_id"],
                        "snippet": result["snippet"],
                        "source_meta": parsed["source_text"],
                    },
                )

                results_fetched += 1
                yield doc

            page += 1
            # Save state for resume
            self._state[f"query:{query}:page"] = page
            self._save_state()

    def scrape(
        self,
        queries: list[str] = None,
        court_filter: str = None,
        max_results_per_query: int = 50,
    ) -> Generator[ScrapedDocument, None, None]:
        """
        Main scraping method. Iterates through queries and yields documents.

        Args:
            queries: List of search queries. Defaults to DEFAULT_QUERIES.
            court_filter: Filter by court (e.g., "gujarat_hc", "supreme_court")
            max_results_per_query: Max results per query (default 50)
        """
        if queries is None:
            queries = DEFAULT_QUERIES

        for i, query in enumerate(queries):
            logger.info(f"Processing query {i+1}/{len(queries)}: {query}")

            # Check if we already completed this query (resume support)
            state_key = f"query:{query}:completed"
            if self._state.get(state_key):
                logger.info(f"Skipping completed query: {query}")
                continue

            yield from self.scrape_search(
                query=query,
                court_filter=court_filter,
                max_results=max_results_per_query,
            )

            self._state[state_key] = True
            self._save_state()


def create_indian_kanoon_source(output_dir: str = "data/sources/indiankanoon") -> IndianKanoonDataSource:
    """Factory function to create an Indian Kanoon data source with default config."""
    config = DataSourceConfig(
        base_url="https://indiankanoon.org",
        output_dir=output_dir,
        delay_seconds=3.0,  # Be respectful to Indian Kanoon servers
        max_concurrent=1,
        max_retries=3,
        timeout=30,
    )
    return IndianKanoonDataSource(config)
