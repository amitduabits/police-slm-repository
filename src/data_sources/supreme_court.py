"""
Supreme Court of India Data Source (main.sci.gov.in)

The Supreme Court website provides:
- Judgments (searchable by case type, year, party name)
- Daily Orders
- Case Status

SCI judgments establish precedents that are binding on all Gujarat courts.
Criminal law precedents are essential for the SOP assistant.
"""

import re
import logging
from typing import Generator, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.data_sources.base import (
    BaseDataSource,
    DataSourceConfig,
    DocumentType,
    ScrapedDocument,
    SourceName,
)

logger = logging.getLogger(__name__)

# Key SCI criminal law search queries for Gujarat Police corpus
SCI_QUERIES = [
    # Core criminal procedure
    "investigation procedure CrPC police",
    "Section 173 CrPC chargesheet",
    "Section 161 CrPC statement",
    "Section 164 CrPC confession",
    "FIR registration mandatory",
    "zero FIR procedure",
    "arrest procedure rights accused",
    "bail principles criminal",
    "anticipatory bail guidelines",
    "Section 438 CrPC anticipatory bail",
    "remand custody judicial",

    # Evidence and investigation
    "evidence collection criminal trial",
    "electronic evidence Section 65B",
    "dying declaration admissibility",
    "circumstantial evidence conviction",
    "forensic evidence DNA",
    "CCTV footage evidence",
    "CDR call detail record evidence",
    "recovery panchnama procedure",
    "identification parade TIP",
    "scene of crime preservation",

    # Specific offences
    "murder Section 302 IPC ingredients",
    "dowry death Section 304B",
    "kidnapping Section 363 366",
    "robbery dacoity Section 392 395",
    "cheating Section 420 IPC",
    "NDPS Act drug offence",
    "POCSO child sexual abuse",
    "SC ST Atrocities Act",
    "domestic violence Protection Women",

    # Chargesheet and trial
    "chargesheet deficiency acquittal",
    "incomplete investigation acquittal",
    "prosecution evidence lacunae",
    "benefit of doubt acquittal",
    "conviction rate criminal justice",

    # BNS/BNSS (new criminal codes)
    "Bharatiya Nyaya Sanhita",
    "Bharatiya Nagarik Suraksha Sanhita",
    "Bharatiya Sakshya Adhiniyam",
]


class SupremeCourtDataSource(BaseDataSource):
    """
    Scraper for Supreme Court of India judgments.
    """

    BASE_URL = "https://main.sci.gov.in"
    JUDGMENT_URL = "https://main.sci.gov.in/judgments"

    def source_name(self) -> SourceName:
        return SourceName.SUPREME_COURT

    def search_judgments(
        self,
        keyword: str = "",
        case_type: str = "Criminal Appeal",
        year_from: int = 2020,
        year_to: int = 2025,
        page: int = 1,
    ) -> list[dict]:
        """Search SCI judgments."""
        search_url = f"{self.BASE_URL}/judgments"

        params = {
            "keyword": keyword,
            "case_type": case_type,
            "year_from": str(year_from),
            "year_to": str(year_to),
            "page": str(page),
        }

        response = self.fetch_page(search_url, params=params)
        if not response:
            return []

        soup = BeautifulSoup(response.text, "lxml")
        results = []

        # Parse judgment listing
        rows = soup.select("table tbody tr") or soup.select(".judgment-list .item")
        for row in rows:
            link = row.select_one("a[href]")
            if not link:
                continue

            href = link.get("href", "")
            title = link.get_text(strip=True)

            cols = row.select("td")
            date_text = cols[1].get_text(strip=True) if len(cols) > 1 else ""
            bench_text = cols[2].get_text(strip=True) if len(cols) > 2 else ""

            results.append({
                "title": title,
                "url": urljoin(self.BASE_URL, href),
                "date": date_text,
                "bench": bench_text,
            })

        return results

    def fetch_judgment(self, url: str) -> Optional[dict]:
        """Fetch full judgment text."""
        response = self.fetch_page(url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        content = soup.select_one("#judgment-text") or soup.select_one(".judgment-content")
        if not content:
            # SCI often serves PDFs
            pdf_link = soup.select_one("a[href$='.pdf']") or soup.select_one(
                "a[href*='judgment']"
            )
            if pdf_link:
                return {
                    "full_text": f"[PDF - {urljoin(url, pdf_link['href'])}]",
                    "pdf_url": urljoin(url, pdf_link["href"]),
                }
            return None

        return {
            "full_text": content.get_text(separator="\n", strip=True),
            "html_content": str(content),
        }

    def scrape(
        self,
        queries: list[str] = None,
        year_from: int = 2020,
        year_to: int = 2025,
        max_per_query: int = 30,
        max_results_per_query: int = None,  # Alias for max_per_query
        **kwargs,
    ) -> Generator[ScrapedDocument, None, None]:
        """Main scraping method for SCI judgments."""
        # Handle alias for max_results_per_query
        if max_results_per_query is not None:
            max_per_query = max_results_per_query
        if queries is None:
            queries = SCI_QUERIES

        for query in queries:
            state_key = f"sci:{query}"
            if self._state.get(state_key):
                continue

            logger.info(f"Searching SCI: {query}")
            page = 1
            count = 0

            while count < max_per_query:
                results = self.search_judgments(
                    keyword=query,
                    year_from=year_from,
                    year_to=year_to,
                    page=page,
                )
                if not results:
                    break

                for result in results:
                    if count >= max_per_query:
                        break

                    judgment = self.fetch_judgment(result["url"])
                    if not judgment:
                        continue

                    doc = ScrapedDocument(
                        source=SourceName.SUPREME_COURT,
                        source_url=result["url"],
                        document_type=DocumentType.COURT_RULING,
                        title=result["title"],
                        content=judgment.get("full_text", ""),
                        html_content=judgment.get("html_content", ""),
                        language="en",
                        date_published=result.get("date"),
                        court="Supreme Court of India",
                        metadata={
                            "query": query,
                            "bench": result.get("bench"),
                            "pdf_url": judgment.get("pdf_url"),
                        },
                    )
                    count += 1
                    yield doc

                page += 1

            self._state[state_key] = True
            self._save_state()


def create_supreme_court_source(output_dir: str = "data/sources/scr") -> SupremeCourtDataSource:
    config = DataSourceConfig(
        base_url="https://main.sci.gov.in",
        output_dir=output_dir,
        delay_seconds=3.0,
        max_concurrent=1,
        max_retries=3,
        timeout=30,
    )
    return SupremeCourtDataSource(config)
