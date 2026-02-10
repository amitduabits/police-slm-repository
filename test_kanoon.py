"""Quick test of Indian Kanoon scraper."""
import sys
sys.path.insert(0, '.')
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

from src.data_sources.indian_kanoon import IndianKanoonDataSource
from src.data_sources.base import DataSourceConfig

# Create config with longer delay to avoid rate limiting
config = DataSourceConfig(
    base_url="https://indiankanoon.org",
    output_dir="data/sources/indiankanoon",
    delay_seconds=5.0,  # Increased from 2 to 5 seconds
    max_retries=2,
)

# Create scraper
scraper = IndianKanoonDataSource(config)

print("Testing Indian Kanoon scraper...")
print("=" * 60)

# Test with just one query and only 2 documents to avoid rate limiting
result = scraper.run(
    queries=["Gujarat murder Section 302 IPC"],
    max_results_per_query=2,  # Reduced to 2 for testing
)

print("\n" + "=" * 60)
print("RESULTS:")
print(f"Total fetched: {result.get('total_fetched', 0)}")
print(f"Total saved: {result.get('total_saved', 0)}")
print(f"Total errors: {result.get('total_errors', 0)}")

# Check saved files
import os
saved_files = [f for f in os.listdir("data/sources/indiankanoon")
               if f.endswith('.json') and not f.startswith('.')]
print(f"\nSaved files: {len(saved_files)}")
if saved_files:
    print("First few files:")
    for f in saved_files[:5]:
        print(f"  - {f}")
