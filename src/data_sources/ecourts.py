"""
eCourts India Data Source (ecourts.gov.in / services.ecourts.gov.in)

eCourts is the official Government of India platform for:
- Case status tracking
- Court orders and judgments
- Cause lists
- Case number search across all district courts

This module interfaces with the eCourts services API.
Gujarat-specific court data is available for all 33 districts.

FOR OFFICIAL DEPLOYMENT:
Gujarat Police should request direct database/API access from
the eCourts project (ecommittee@nic.in) under the Digital India initiative.
This will provide bulk data access without scraping.

DURING POC:
We use the public search interface with rate limiting.
"""

import re
import json
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

# Gujarat District Court Codes (eCourts internal codes)
GUJARAT_DISTRICTS = {
    "ahmedabad": {"code": "1", "name": "Ahmedabad"},
    "ahmedabad_rural": {"code": "36", "name": "Ahmedabad Rural"},
    "amreli": {"code": "2", "name": "Amreli"},
    "anand": {"code": "3", "name": "Anand"},
    "aravalli": {"code": "37", "name": "Aravalli"},
    "banaskantha": {"code": "4", "name": "Banaskantha"},
    "bharuch": {"code": "5", "name": "Bharuch"},
    "bhavnagar": {"code": "6", "name": "Bhavnagar"},
    "botad": {"code": "38", "name": "Botad"},
    "chhota_udepur": {"code": "39", "name": "Chhota Udepur"},
    "dahod": {"code": "7", "name": "Dahod"},
    "dang": {"code": "8", "name": "Dang"},
    "devbhumi_dwarka": {"code": "40", "name": "Devbhumi Dwarka"},
    "gandhinagar": {"code": "9", "name": "Gandhinagar"},
    "gir_somnath": {"code": "41", "name": "Gir Somnath"},
    "jamnagar": {"code": "10", "name": "Jamnagar"},
    "junagadh": {"code": "11", "name": "Junagadh"},
    "kheda": {"code": "12", "name": "Kheda"},
    "kutch": {"code": "13", "name": "Kutch"},
    "mahisagar": {"code": "42", "name": "Mahisagar"},
    "mehsana": {"code": "14", "name": "Mehsana"},
    "morbi": {"code": "43", "name": "Morbi"},
    "narmada": {"code": "15", "name": "Narmada"},
    "navsari": {"code": "16", "name": "Navsari"},
    "panchmahal": {"code": "17", "name": "Panchmahal"},
    "patan": {"code": "18", "name": "Patan"},
    "porbandar": {"code": "19", "name": "Porbandar"},
    "rajkot": {"code": "20", "name": "Rajkot"},
    "sabarkantha": {"code": "21", "name": "Sabarkantha"},
    "surat": {"code": "22", "name": "Surat"},
    "surendranagar": {"code": "23", "name": "Surendranagar"},
    "tapi": {"code": "24", "name": "Tapi"},
    "vadodara": {"code": "25", "name": "Vadodara"},
    "valsad": {"code": "26", "name": "Valsad"},
}

# Gujarat State Code in eCourts
GUJARAT_STATE_CODE = "9"

# Case types relevant to criminal investigations
CRIMINAL_CASE_TYPES = [
    {"code": "1", "name": "Sessions Case"},
    {"code": "2", "name": "Criminal Case"},
    {"code": "3", "name": "Criminal Misc. Application"},
    {"code": "4", "name": "Criminal Appeal"},
    {"code": "5", "name": "Criminal Revision"},
    {"code": "6", "name": "Bail Application"},
    {"code": "7", "name": "Anticipatory Bail"},
    {"code": "8", "name": "NDPS Case"},
    {"code": "9", "name": "POCSO Case"},
]


class ECourtsDataSource(BaseDataSource):
    """
    Scraper for eCourts India (ecourts.gov.in).
    Fetches court orders and case data from Gujarat district courts.
    """

    # eCourts services endpoint
    SERVICES_URL = "https://services.ecourts.gov.in/ecourtindia_v6"
    API_URL = "https://services.ecourts.gov.in/ecourtindia_v6"

    def source_name(self) -> SourceName:
        return SourceName.ECOURTS

    def _get_csrf_token(self) -> Optional[str]:
        """Get CSRF token from eCourts homepage."""
        response = self.fetch_page(f"{self.SERVICES_URL}/")
        if response:
            soup = BeautifulSoup(response.text, "lxml")
            token_elem = soup.select_one('input[name="csrf_token"]') or soup.select_one(
                'meta[name="csrf-token"]'
            )
            if token_elem:
                return token_elem.get("value") or token_elem.get("content")
        return None

    def search_by_act(
        self,
        state_code: str = GUJARAT_STATE_CODE,
        district_code: str = "1",  # Ahmedabad default
        act_type: str = "IPC",
        section: str = "302",
        year_from: int = 2020,
        year_to: int = 2025,
    ) -> Generator[dict, None, None]:
        """
        Search cases by Act and Section on eCourts.

        This uses the eCourts "Act/Section" search facility.
        """
        search_url = f"{self.SERVICES_URL}/index_act.php"

        params = {
            "state_code": state_code,
            "dist_code": district_code,
            "act_type": act_type,
            "under_sec": section,
            "from_year": str(year_from),
            "to_year": str(year_to),
            "search": "Search",
        }

        response = self.fetch_page(search_url, params=params)
        if not response:
            return

        soup = BeautifulSoup(response.text, "lxml")

        # Parse results table
        results_table = soup.select_one("table.table") or soup.select_one("#dispTable")
        if not results_table:
            logger.info(f"No results for {act_type} Section {section} in district {district_code}")
            return

        rows = results_table.select("tr")[1:]  # Skip header
        for row in rows:
            cols = row.select("td")
            if len(cols) < 4:
                continue

            case_data = {
                "sr_no": cols[0].get_text(strip=True),
                "case_number": cols[1].get_text(strip=True),
                "parties": cols[2].get_text(strip=True) if len(cols) > 2 else "",
                "filing_date": cols[3].get_text(strip=True) if len(cols) > 3 else "",
                "status": cols[4].get_text(strip=True) if len(cols) > 4 else "",
                "district_code": district_code,
                "act_type": act_type,
                "section": section,
            }

            # Check for order/judgment link
            order_link = row.select_one("a[href*='order']") or row.select_one(
                "a[onclick*='order']"
            )
            if order_link:
                case_data["order_link"] = order_link.get("href", "")

            yield case_data

    def fetch_case_orders(self, case_data: dict) -> Optional[str]:
        """Fetch court orders for a specific case."""
        if "order_link" not in case_data:
            return None

        order_url = case_data["order_link"]
        if not order_url.startswith("http"):
            order_url = urljoin(self.SERVICES_URL, order_url)

        response = self.fetch_page(order_url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        # Extract order text
        order_div = soup.select_one("#order_content") or soup.select_one(".order-text")
        if order_div:
            return order_div.get_text(separator="\n", strip=True)

        # Try PDF link
        pdf_link = soup.select_one("a[href*='.pdf']")
        if pdf_link:
            return f"PDF_LINK:{urljoin(order_url, pdf_link['href'])}"

        return None

    def search_by_fir(
        self,
        state_code: str = GUJARAT_STATE_CODE,
        district_code: str = "1",
        police_station: str = "",
        fir_number: str = "",
        year: int = 2024,
    ) -> Generator[dict, None, None]:
        """
        Search cases by FIR number on eCourts.
        """
        search_url = f"{self.SERVICES_URL}/index_fir.php"

        params = {
            "state_code": state_code,
            "dist_code": district_code,
            "police_station": police_station,
            "fir_no": fir_number,
            "fir_year": str(year),
            "search": "Search",
        }

        response = self.fetch_page(search_url, params=params)
        if not response:
            return

        soup = BeautifulSoup(response.text, "lxml")
        results_table = soup.select_one("table.table") or soup.select_one("#dispTable")
        if not results_table:
            return

        rows = results_table.select("tr")[1:]
        for row in rows:
            cols = row.select("td")
            if len(cols) < 3:
                continue

            yield {
                "case_number": cols[0].get_text(strip=True) if len(cols) > 0 else "",
                "parties": cols[1].get_text(strip=True) if len(cols) > 1 else "",
                "status": cols[2].get_text(strip=True) if len(cols) > 2 else "",
                "fir_number": fir_number,
                "year": year,
                "district_code": district_code,
            }

    def scrape(
        self,
        districts: list[str] = None,
        sections: list[str] = None,
        year_from: int = 2020,
        year_to: int = 2025,
        max_per_combo: int = 50,
        max_results_per_query: int = None,  # Alias for max_per_combo
        **kwargs,
    ) -> Generator[ScrapedDocument, None, None]:
        """
        Main scraping method for eCourts.

        Iterates through districts and IPC sections to build corpus.
        """
        # Handle alias for max_results_per_query
        if max_results_per_query is not None:
            max_per_combo = max_results_per_query
        if districts is None:
            # Start with major districts for POC
            districts = ["ahmedabad", "surat", "vadodara", "rajkot", "gandhinagar"]

        if sections is None:
            # Major criminal sections
            sections = [
                "302", "304", "304B", "307", "323", "326", "354", "363", "376",
                "379", "392", "395", "406", "420", "468", "498A", "506",
            ]

        for district_key in districts:
            district = GUJARAT_DISTRICTS.get(district_key)
            if not district:
                logger.warning(f"Unknown district: {district_key}")
                continue

            for section in sections:
                state_key = f"ecourts:{district_key}:{section}"
                if self._state.get(state_key):
                    logger.info(f"Skipping completed: {district['name']} IPC {section}")
                    continue

                logger.info(f"Searching: {district['name']} - IPC Section {section}")

                count = 0
                for case_data in self.search_by_act(
                    state_code=GUJARAT_STATE_CODE,
                    district_code=district["code"],
                    act_type="IPC",
                    section=section,
                    year_from=year_from,
                    year_to=year_to,
                ):
                    if count >= max_per_combo:
                        break

                    # Try to fetch the order
                    order_text = self.fetch_case_orders(case_data)
                    content = order_text or json.dumps(case_data, ensure_ascii=False)

                    doc = ScrapedDocument(
                        source=SourceName.ECOURTS,
                        source_url=f"{self.SERVICES_URL}",
                        document_type=DocumentType.COURT_RULING,
                        title=f"{case_data.get('case_number', 'Unknown')} - IPC {section}",
                        content=content,
                        language="en",
                        date_published=case_data.get("filing_date"),
                        case_number=case_data.get("case_number"),
                        court=f"{district['name']} District Court",
                        sections_cited=[f"IPC Section {section}"],
                        parties=case_data.get("parties", "").split(" vs "),
                        metadata={
                            "district": district["name"],
                            "district_code": district["code"],
                            "case_status": case_data.get("status"),
                            "source": "ecourts",
                            "has_order_text": order_text is not None,
                        },
                    )

                    count += 1
                    yield doc

                self._state[state_key] = True
                self._save_state()


def create_ecourts_source(output_dir: str = "data/sources/ecourts") -> ECourtsDataSource:
    """Factory function to create an eCourts data source."""
    config = DataSourceConfig(
        base_url="https://services.ecourts.gov.in",
        output_dir=output_dir,
        delay_seconds=3.0,
        max_concurrent=1,
        max_retries=3,
        timeout=30,
    )
    return ECourtsDataSource(config)
