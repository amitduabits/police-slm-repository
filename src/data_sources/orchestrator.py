"""
Data Source Orchestrator

Manages all data sources and provides a unified interface for:
1. Running all scrapers with proper sequencing
2. Progress tracking across sources
3. Resume capability for interrupted runs
4. Unified statistics and reporting
5. Data validation after scraping

Usage:
    orchestrator = DataSourceOrchestrator(base_output_dir="data/sources")
    orchestrator.run_all()
    # or selectively:
    orchestrator.run_source("indian_kanoon", max_results_per_query=100)
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.data_sources.base import DataSourceConfig, SourceName
from src.data_sources.indian_kanoon import IndianKanoonDataSource, create_indian_kanoon_source
from src.data_sources.ecourts import ECourtsDataSource, create_ecourts_source
from src.data_sources.gujarat_hc import GujaratHCDataSource, create_gujarat_hc_source
from src.data_sources.supreme_court import SupremeCourtDataSource, create_supreme_court_source
from src.data_sources.india_code import IndiaCodeDataSource, create_india_code_source
from src.data_sources.ncrb import NCRBDataSource, create_ncrb_source

logger = logging.getLogger(__name__)


class DataSourceOrchestrator:
    """
    Orchestrates data collection from all verified sources.
    """

    def __init__(self, base_output_dir: str = "data/sources"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self._run_log_path = self.base_output_dir / "run_log.json"
        self._run_log = self._load_run_log()

    def _load_run_log(self) -> dict:
        if self._run_log_path.exists():
            with open(self._run_log_path) as f:
                return json.load(f)
        return {"runs": []}

    def _save_run_log(self):
        with open(self._run_log_path, "w") as f:
            json.dump(self._run_log, f, indent=2)

    def _create_source(self, source_name: str):
        """Factory method to create data source instances."""
        factories = {
            "indian_kanoon": lambda: create_indian_kanoon_source(
                str(self.base_output_dir / "indiankanoon")
            ),
            "ecourts": lambda: create_ecourts_source(
                str(self.base_output_dir / "ecourts")
            ),
            "gujarat_hc": lambda: create_gujarat_hc_source(
                str(self.base_output_dir / "gujhc")
            ),
            "supreme_court": lambda: create_supreme_court_source(
                str(self.base_output_dir / "scr")
            ),
            "india_code": lambda: create_india_code_source(
                str(self.base_output_dir / "indiacode")
            ),
            "ncrb": lambda: create_ncrb_source(
                str(self.base_output_dir / "ncrb")
            ),
        }
        factory = factories.get(source_name)
        if not factory:
            raise ValueError(f"Unknown source: {source_name}. Available: {list(factories.keys())}")
        return factory()

    def run_source(self, source_name: str, **kwargs) -> dict:
        """Run a specific data source scraper."""
        logger.info(f"=" * 60)
        logger.info(f"Starting data source: {source_name}")
        logger.info(f"=" * 60)

        source = self._create_source(source_name)
        start_time = datetime.utcnow().isoformat()

        try:
            stats = source.run(**kwargs)
            status = "completed"
        except Exception as e:
            logger.error(f"Source {source_name} failed: {e}")
            stats = source.get_stats()
            status = f"failed: {str(e)}"

        run_entry = {
            "source": source_name,
            "start_time": start_time,
            "end_time": datetime.utcnow().isoformat(),
            "status": status,
            "stats": stats,
            "kwargs": {k: str(v) for k, v in kwargs.items()},
        }
        self._run_log["runs"].append(run_entry)
        self._save_run_log()

        return stats

    def run_all(
        self,
        sources: list[str] = None,
        skip_completed: bool = True,
    ) -> dict:
        """
        Run all data source scrapers in recommended order.

        Recommended order:
        1. India Code (bare acts + section mappings) - fastest, foundational
        2. Indian Kanoon (court rulings) - largest corpus
        3. Gujarat HC (state-specific rulings)
        4. Supreme Court (precedent rulings)
        5. eCourts (district court data)
        6. NCRB (crime statistics)
        """
        if sources is None:
            sources = [
                "india_code",
                "indian_kanoon",
                "gujarat_hc",
                "supreme_court",
                "ecourts",
                "ncrb",
            ]

        all_stats = {}
        for source_name in sources:
            if skip_completed:
                # Check if source was completed in a previous run
                completed_runs = [
                    r for r in self._run_log.get("runs", [])
                    if r["source"] == source_name and r["status"] == "completed"
                ]
                if completed_runs:
                    logger.info(f"Skipping {source_name} (completed previously)")
                    all_stats[source_name] = {"status": "skipped (previously completed)"}
                    continue

            all_stats[source_name] = self.run_source(source_name)

        # Generate summary report
        self._generate_report(all_stats)
        return all_stats

    def _generate_report(self, all_stats: dict):
        """Generate a summary report of the data collection run."""
        report_path = self.base_output_dir / "collection_report.md"

        lines = [
            "# Data Collection Report",
            f"\nGenerated: {datetime.utcnow().isoformat()}",
            "\n## Source Summary\n",
        ]

        total_docs = 0
        for source_name, stats in all_stats.items():
            saved = stats.get("total_saved", 0) if isinstance(stats, dict) else 0
            total_docs += saved
            status = stats.get("status", "completed") if isinstance(stats, dict) else str(stats)
            lines.append(f"### {source_name}")
            lines.append(f"- Status: {status}")
            lines.append(f"- Documents saved: {saved}")
            if isinstance(stats, dict):
                lines.append(f"- Pages fetched: {stats.get('total_fetched', 0)}")
                lines.append(f"- Duplicates skipped: {stats.get('total_skipped_duplicate', 0)}")
                lines.append(f"- Errors: {stats.get('total_errors', 0)}")
            lines.append("")

        lines.append(f"\n## Total Documents Collected: {total_docs}")

        # Disk usage
        total_size = sum(
            f.stat().st_size
            for f in self.base_output_dir.rglob("*.json")
            if f.is_file()
        )
        lines.append(f"## Total Disk Usage: {total_size / (1024*1024):.1f} MB")

        with open(report_path, "w") as f:
            f.write("\n".join(lines))

        logger.info(f"Report saved to: {report_path}")

    def get_document_counts(self) -> dict:
        """Count documents per source and type."""
        counts = {}
        for source_dir in self.base_output_dir.iterdir():
            if source_dir.is_dir() and not source_dir.name.startswith("."):
                source_name = source_dir.name
                counts[source_name] = {}
                for type_dir in source_dir.iterdir():
                    if type_dir.is_dir():
                        doc_count = len(list(type_dir.rglob("*.json")))
                        counts[source_name][type_dir.name] = doc_count
        return counts

    def validate_data(self) -> dict:
        """Validate collected data for completeness and quality."""
        issues = []
        counts = self.get_document_counts()

        # Check minimum document counts
        minimums = {
            "indiankanoon": 100,
            "ecourts": 50,
            "gujhc": 30,
            "scr": 20,
            "indiacode": 5,
        }

        for source, min_count in minimums.items():
            total = sum(counts.get(source, {}).values())
            if total < min_count:
                issues.append(f"WARNING: {source} has only {total} docs (minimum: {min_count})")

        # Check for mapping files
        mapping_files = [
            "configs/ipc_to_bns_mapping.json",
            "configs/crpc_to_bnss_mapping.json",
            "configs/iea_to_bsa_mapping.json",
        ]
        for mf in mapping_files:
            if not os.path.exists(mf):
                issues.append(f"MISSING: {mf}")

        return {
            "counts": counts,
            "issues": issues,
            "valid": len(issues) == 0,
        }
