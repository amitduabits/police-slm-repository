"""
NCRB Data Source (ncrb.gov.in)

National Crime Records Bureau publishes annual "Crime in India" reports
with comprehensive statistics. This module downloads and parses:
- State-wise crime statistics (Gujarat specific)
- District-wise crime data
- IPC/SLL crime heads
- Conviction rates
- Charge-sheeting rates
- Disposal of cases by courts

NCRB data is available as PDF reports and Excel tables at:
https://ncrb.gov.in/crime-in-india-table-addtional-table-and-chapter-contents
"""

import logging
import re
from typing import Generator, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.data_sources.base import (
    BaseDataSource, DataSourceConfig, DocumentType, ScrapedDocument, SourceName,
)

logger = logging.getLogger(__name__)

# NCRB report URLs for recent years
NCRB_REPORT_URLS = {
    "2022": "https://ncrb.gov.in/crime-in-india-year-2022",
    "2021": "https://ncrb.gov.in/crime-in-india-year-2021",
    "2020": "https://ncrb.gov.in/crime-in-india-year-2020",
    "2019": "https://ncrb.gov.in/crime-in-india-year-2019",
}

# Key tables relevant to Gujarat Police
RELEVANT_TABLES = [
    "Table 1A.1 - Cognizable Crimes Under IPC - State/UT-wise",
    "Table 1A.2 - Cognizable Crimes Under SLL - State/UT-wise",
    "Table 1.2 - Disposal of IPC Crime Cases by Police",
    "Table 1.3 - Disposal of IPC Crime Cases by Courts",
    "Table 1.9 - Incidence of Cognizable Crime (IPC) District-wise",
    "Table 3A - Murder",
    "Table 3B - Attempt to Murder",
    "Table 4 - Kidnapping and Abduction",
    "Table 5 - Robbery",
    "Table 6 - Burglary/House Breaking",
    "Table 7 - Theft",
    "Table 8 - Riots",
    "Table 10 - Dowry Deaths",
    "Table 15 - Cheating",
    "Table 16 - Forgery",
]


class NCRBDataSource(BaseDataSource):
    """
    Downloads and parses NCRB Crime in India statistics.
    Gujarat-specific data extraction.
    """

    BASE_URL = "https://ncrb.gov.in"

    def source_name(self) -> SourceName:
        return SourceName.NCRB

    def fetch_report_index(self, year: str) -> list[dict]:
        """Fetch the table of contents for a specific year's report."""
        url = NCRB_REPORT_URLS.get(year)
        if not url:
            logger.warning(f"No NCRB report URL for year {year}")
            return []

        response = self.fetch_page(url)
        if not response:
            return []

        soup = BeautifulSoup(response.text, "lxml")
        tables = []

        # Find links to tables/chapters
        for link in soup.select("a[href]"):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # Filter for relevant content
            if any(keyword in text.lower() for keyword in [
                "table", "chapter", "murder", "robbery", "theft",
                "kidnap", "dowry", "crime", "disposal", "chargesheet",
                "conviction", "gujarat",
            ]):
                tables.append({
                    "title": text,
                    "url": urljoin(self.BASE_URL, href),
                    "year": year,
                    "is_pdf": href.lower().endswith(".pdf"),
                    "is_excel": href.lower().endswith((".xlsx", ".xls", ".csv")),
                })

        return tables

    def fetch_table_data(self, table_info: dict) -> Optional[str]:
        """Fetch table data (PDF text extraction or HTML table)."""
        url = table_info["url"]

        if table_info.get("is_pdf"):
            # Download PDF - will be processed by OCR pipeline later
            response = self.fetch_page(url)
            if response:
                return f"[PDF_DATA:{url}]"
            return None

        if table_info.get("is_excel"):
            return f"[EXCEL_DATA:{url}]"

        # HTML page
        response = self.fetch_page(url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        # Find data tables
        tables = soup.select("table")
        if tables:
            # Extract Gujarat-specific rows
            gujarat_data = []
            for table in tables:
                for row in table.select("tr"):
                    row_text = row.get_text(strip=True).lower()
                    if "gujarat" in row_text or "total" in row_text:
                        cells = [td.get_text(strip=True) for td in row.select("td, th")]
                        gujarat_data.append(" | ".join(cells))

            if gujarat_data:
                return "\n".join(gujarat_data)

        # Fallback: get all text
        content = soup.select_one(".field--name-body") or soup.select_one("#content")
        if content:
            return content.get_text(separator="\n", strip=True)

        return None

    def scrape(
        self,
        years: list[str] = None,
        **kwargs,  # Accept additional kwargs for compatibility
    ) -> Generator[ScrapedDocument, None, None]:
        """Main scraping method for NCRB data."""
        if years is None:
            years = ["2022", "2021", "2020"]

        for year in years:
            state_key = f"ncrb:{year}"
            if self._state.get(state_key):
                continue

            logger.info(f"Fetching NCRB data for year {year}")
            tables = self.fetch_report_index(year)

            for table_info in tables:
                content = self.fetch_table_data(table_info)
                if not content:
                    continue

                doc = ScrapedDocument(
                    source=SourceName.NCRB,
                    source_url=table_info["url"],
                    document_type=DocumentType.CRIME_STATISTICS,
                    title=f"NCRB {year} - {table_info['title']}",
                    content=content,
                    language="en",
                    date_published=f"{year}-01-01",
                    metadata={
                        "year": year,
                        "table_title": table_info["title"],
                        "is_pdf": table_info.get("is_pdf", False),
                        "is_excel": table_info.get("is_excel", False),
                        "source": "ncrb",
                    },
                )
                yield doc

            self._state[state_key] = True
            self._save_state()


def create_ncrb_source(output_dir: str = "data/sources/ncrb") -> NCRBDataSource:
    config = DataSourceConfig(
        base_url="https://ncrb.gov.in",
        output_dir=output_dir,
        delay_seconds=2.0,
        max_concurrent=1,
        max_retries=3,
        timeout=60,
    )
    return NCRBDataSource(config)
