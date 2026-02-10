"""
Gujarat High Court Data Source (gujarathighcourt.nic.in)

Official website of the Gujarat High Court.
Provides access to:
- Judgments and Orders (searchable by date, bench, case type)
- Cause Lists
- Case Status

The Gujarat HC website has a judgment search interface that
allows searching by date range, bench, and case type.
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

# Gujarat HC Bench Types
BENCHES = {
    "ahmedabad": "Ahmedabad Bench",
    "surat": "Surat Bench",
    "rajkot": "Rajkot Bench",
}

# Criminal case types in Gujarat HC
CRIMINAL_CASE_TYPES_HC = [
    "Criminal Appeal",
    "Criminal Misc. Application",
    "Special Criminal Application",
    "Criminal Revision Application",
    "Bail Application",
    "R/Criminal Misc. Application",
    "R/Special Criminal Application",
]


class GujaratHCDataSource(BaseDataSource):
    """
    Scraper for Gujarat High Court judgments.
    """

    BASE_URL = "https://gujarathighcourt.nic.in"
    JUDGMENT_SEARCH_URL = "https://gujarathighcourt.nic.in/judgment-search"

    def source_name(self) -> SourceName:
        return SourceName.GUJARAT_HC

    def search_judgments(
        self,
        date_from: str = "2020-01-01",
        date_to: str = "2025-12-31",
        bench: str = "ahmedabad",
        case_type: str = "Criminal Appeal",
        page: int = 1,
    ) -> list[dict]:
        """
        Search Gujarat HC judgments.

        The Gujarat HC website uses a form-based search.
        We simulate the form submission.
        """
        search_url = f"{self.BASE_URL}/judgment"

        params = {
            "from_date": date_from,
            "to_date": date_to,
            "bench": bench,
            "case_type": case_type,
            "page": str(page),
        }

        response = self.fetch_page(search_url, params=params)
        if not response:
            return []

        soup = BeautifulSoup(response.text, "lxml")
        results = []

        # Parse judgment listing
        judgment_items = soup.select(".judgment-item") or soup.select("tr.judgment-row")
        if not judgment_items:
            # Try alternative structure
            judgment_items = soup.select(".views-row") or soup.select("table tbody tr")

        for item in judgment_items:
            # Extract case number, date, judges, parties, link
            link_elem = item.select_one("a[href]")
            if not link_elem:
                continue

            href = link_elem.get("href", "")
            title = link_elem.get_text(strip=True)

            date_elem = item.select_one(".date") or item.select_one("td:nth-child(2)")
            date_text = date_elem.get_text(strip=True) if date_elem else ""

            judge_elem = item.select_one(".judge") or item.select_one("td:nth-child(3)")
            judge_text = judge_elem.get_text(strip=True) if judge_elem else ""

            results.append({
                "title": title,
                "url": urljoin(self.BASE_URL, href),
                "date": date_text,
                "judge": judge_text,
                "bench": bench,
                "case_type": case_type,
            })

        return results

    def fetch_judgment_text(self, url: str) -> Optional[dict]:
        """Fetch the full text of a judgment from its URL."""
        response = self.fetch_page(url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        # Try multiple selectors for judgment content
        content_selectors = [
            "#judgment-text",
            ".judgment-content",
            ".field--name-body",
            "#block-gujarathighcourt-content",
            "article .content",
            ".node__content",
        ]

        content_div = None
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                break

        if not content_div:
            # Try to find a PDF link
            pdf_link = soup.select_one("a[href$='.pdf']")
            if pdf_link:
                return {
                    "full_text": f"[PDF judgment - download from: {urljoin(url, pdf_link['href'])}]",
                    "pdf_url": urljoin(url, pdf_link["href"]),
                    "html_content": "",
                }
            logger.warning(f"Could not extract judgment content from {url}")
            return None

        full_text = content_div.get_text(separator="\n", strip=True)
        html_content = str(content_div)

        # Extract metadata from the judgment text
        judges = self._extract_judges(full_text[:2000])
        case_number = self._extract_case_number(full_text[:1000])
        sections = self._extract_sections(full_text)
        date = self._extract_date(full_text[:2000])

        return {
            "full_text": full_text,
            "html_content": html_content,
            "judges": judges,
            "case_number": case_number,
            "sections": sections,
            "date": date,
        }

    def _extract_judges(self, text: str) -> list[str]:
        """Extract judge names from judgment header."""
        patterns = [
            r"(?:HON'?BLE|HONOURABLE|Hon\.)\s+(?:MR\.?\s+|MS\.?\s+|SMT\.?\s+)?JUSTICE\s+([A-Z][A-Z\s.]+)",
            r"(?:CORAM|Before)[\s:]+(.+?)(?:\n|$)",
        ]
        judges = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            judges.extend([m.strip() for m in matches if m.strip()])
        return judges[:5]

    def _extract_case_number(self, text: str) -> Optional[str]:
        """Extract case number from judgment."""
        patterns = [
            r"(R/Criminal\s+\w+\s+Application\s+No\.\s*\d+\s+of\s+\d{4})",
            r"(Criminal\s+Appeal\s+No\.\s*\d+\s+of\s+\d{4})",
            r"(Special\s+Criminal\s+Application\s+No\.\s*\d+\s+of\s+\d{4})",
            r"(Bail\s+Application\s+No\.\s*\d+\s+of\s+\d{4})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_sections(self, text: str) -> list[str]:
        """Extract legal sections cited."""
        sections = set()
        patterns = [
            r"[Ss]ection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?(?:I\.?P\.?C\.?|Indian\s+Penal\s+Code)",
            r"[Ss]ection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?(?:Cr\.?P\.?C\.?|Code\s+of\s+Criminal)",
            r"[Ss]ection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?(?:B\.?N\.?S\.?|Bharatiya\s+Nyaya)",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                sections.add(match.group(0).strip())
        return sorted(list(sections))[:30]

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract judgment date."""
        patterns = [
            r"[Dd]ated?\s*:?\s*(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})",
            r"(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*(\d{4})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                try:
                    if len(groups) == 3 and groups[1].isdigit():
                        return f"{groups[2]}-{int(groups[1]):02d}-{int(groups[0]):02d}"
                    elif len(groups) == 3:
                        from datetime import datetime
                        dt = datetime.strptime(f"{groups[0]} {groups[1]} {groups[2]}", "%d %B %Y")
                        return dt.strftime("%Y-%m-%d")
                except (ValueError, IndexError):
                    continue
        return None

    def scrape(
        self,
        benches: list[str] = None,
        case_types: list[str] = None,
        date_from: str = "2020-01-01",
        date_to: str = "2025-12-31",
        max_per_combo: int = 50,
        max_results_per_query: int = None,  # Alias for max_per_combo
        **kwargs,
    ) -> Generator[ScrapedDocument, None, None]:
        """
        Main scraping method for Gujarat HC judgments.
        """
        # Handle alias for max_results_per_query
        if max_results_per_query is not None:
            max_per_combo = max_results_per_query
        if benches is None:
            benches = list(BENCHES.keys())
        if case_types is None:
            case_types = CRIMINAL_CASE_TYPES_HC

        for bench in benches:
            for case_type in case_types:
                state_key = f"gujhc:{bench}:{case_type}"
                if self._state.get(state_key):
                    logger.info(f"Skipping completed: {bench} - {case_type}")
                    continue

                logger.info(f"Searching: Gujarat HC {BENCHES.get(bench, bench)} - {case_type}")

                page = 1
                count = 0
                while count < max_per_combo:
                    results = self.search_judgments(
                        date_from=date_from,
                        date_to=date_to,
                        bench=bench,
                        case_type=case_type,
                        page=page,
                    )
                    if not results:
                        break

                    for result in results:
                        if count >= max_per_combo:
                            break

                        judgment = self.fetch_judgment_text(result["url"])
                        if not judgment or not judgment["full_text"]:
                            continue

                        doc = ScrapedDocument(
                            source=SourceName.GUJARAT_HC,
                            source_url=result["url"],
                            document_type=DocumentType.COURT_RULING,
                            title=result["title"],
                            content=judgment["full_text"],
                            html_content=judgment.get("html_content", ""),
                            language="en",
                            date_published=judgment.get("date") or result.get("date"),
                            case_number=judgment.get("case_number"),
                            court=f"Gujarat High Court - {BENCHES.get(bench, bench)}",
                            sections_cited=judgment.get("sections", []),
                            judges=judgment.get("judges", [result.get("judge", "")]),
                            metadata={
                                "bench": bench,
                                "case_type": case_type,
                                "pdf_url": judgment.get("pdf_url"),
                            },
                        )

                        count += 1
                        yield doc

                    page += 1

                self._state[state_key] = True
                self._save_state()


def create_gujarat_hc_source(output_dir: str = "data/sources/gujhc") -> GujaratHCDataSource:
    """Factory function to create Gujarat HC data source."""
    config = DataSourceConfig(
        base_url="https://gujarathighcourt.nic.in",
        output_dir=output_dir,
        delay_seconds=3.0,
        max_concurrent=1,
        max_retries=3,
        timeout=30,
    )
    return GujaratHCDataSource(config)
