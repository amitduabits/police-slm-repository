"""
Gujarat Police SLM - Verified Data Sources

This module contains scrapers/downloaders for verified, official legal data sources.
All data is sourced from government and recognized legal databases.

IMPORTANT: These scrapers respect rate limits and robots.txt.
For official deployment, obtain API access or data sharing agreements where available.

Sources:
1. eCourts India (ecourts.gov.in) - Court orders, case status
2. Indian Kanoon (indiankanoon.org) - Court judgments full text
3. Gujarat High Court (gujarathighcourt.nic.in) - HC judgments
4. Supreme Court of India (sci.gov.in) - SC judgments
5. India Code (indiacode.nic.in) - Bare acts (IPC, BNS, CrPC, BNSS)
6. NCRB (ncrb.gov.in) - Crime statistics
7. NJDG (njdg.ecourts.gov.in) - National Judicial Data Grid
"""

from src.data_sources.base import BaseDataSource, DataSourceConfig, ScrapedDocument
from src.data_sources.ecourts import ECourtsDataSource
from src.data_sources.indian_kanoon import IndianKanoonDataSource
from src.data_sources.gujarat_hc import GujaratHCDataSource
from src.data_sources.supreme_court import SupremeCourtDataSource
from src.data_sources.india_code import IndiaCodeDataSource
from src.data_sources.ncrb import NCRBDataSource
from src.data_sources.orchestrator import DataSourceOrchestrator

__all__ = [
    "BaseDataSource",
    "DataSourceConfig",
    "ScrapedDocument",
    "ECourtsDataSource",
    "IndianKanoonDataSource",
    "GujaratHCDataSource",
    "SupremeCourtDataSource",
    "IndiaCodeDataSource",
    "NCRBDataSource",
    "DataSourceOrchestrator",
]
