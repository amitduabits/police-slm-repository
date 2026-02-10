"""
Gujarat Police SLM - Command Line Interface

Usage:
    # Data Collection
    python -m src.cli collect --source indian_kanoon --max-results 500
    python -m src.cli collect --all
    python -m src.cli collect --validate

    # Ingestion Pipeline
    python -m src.cli ingest --input data/raw/ --output data/processed/
    python -m src.cli ingest --ocr --batch-size 100

    # Embedding
    python -m src.cli embed --input data/processed/ --collection all

    # Model
    python -m src.cli model --prepare-training-data
    python -m src.cli model --train
    python -m src.cli model --evaluate

    # API Server
    python -m src.cli serve --host 0.0.0.0 --port 8000

    # Utilities
    python -m src.cli convert-section 302 --from IPC --to BNS
    python -m src.cli stats
    python -m src.cli health
"""

import sys
import logging
import click
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/gujpol.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose):
    """Gujarat Police AI Investigation Support System"""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    Path("logs").mkdir(exist_ok=True)


@cli.group()
def collect():
    """Data collection from verified sources."""
    pass


@collect.command("run")
@click.option("--source", "-s", type=click.Choice([
    "indian_kanoon", "ecourts", "gujarat_hc", "supreme_court", "india_code", "ncrb", "all"
]), required=True, help="Data source to scrape")
@click.option("--max-results", "-n", default=50, help="Max results per query")
@click.option("--output-dir", "-o", default="data/sources", help="Output directory")
def collect_run(source, max_results, output_dir):
    """Run data collection from a specific source."""
    from src.data_sources.orchestrator import DataSourceOrchestrator

    orchestrator = DataSourceOrchestrator(base_output_dir=output_dir)

    if source == "all":
        stats = orchestrator.run_all()
    else:
        stats = orchestrator.run_source(source, max_results_per_query=max_results)

    click.echo(f"\nCollection complete. Stats: {stats}")


@collect.command("validate")
@click.option("--output-dir", "-o", default="data/sources")
def collect_validate(output_dir):
    """Validate collected data."""
    from src.data_sources.orchestrator import DataSourceOrchestrator

    orchestrator = DataSourceOrchestrator(base_output_dir=output_dir)
    result = orchestrator.validate_data()

    click.echo("\n=== Data Validation Report ===")
    click.echo(f"\nDocument Counts:")
    for source, counts in result["counts"].items():
        total = sum(counts.values())
        click.echo(f"  {source}: {total} documents")
        for dtype, count in counts.items():
            click.echo(f"    - {dtype}: {count}")

    if result["issues"]:
        click.echo(f"\nIssues Found ({len(result['issues'])}):")
        for issue in result["issues"]:
            click.echo(f"  ⚠ {issue}")
    else:
        click.echo("\n✅ All validations passed!")


@collect.command("save-mappings")
def collect_save_mappings():
    """Save IPC↔BNS, CrPC↔BNSS section mappings."""
    from src.data_sources.india_code import create_india_code_source
    source = create_india_code_source()
    source.save_mappings("configs")
    click.echo("✅ Section mappings saved to configs/")


@cli.command("convert-section")
@click.argument("section")
@click.option("--from", "from_code", default="IPC", help="Source code (IPC/BNS/CrPC/BNSS)")
@click.option("--to", "to_code", default="BNS", help="Target code (IPC/BNS/CrPC/BNSS)")
def convert_section(section, from_code, to_code):
    """Convert a section number between IPC/BNS/CrPC/BNSS."""
    from src.data_sources.india_code import create_india_code_source
    source = create_india_code_source()
    result = source.convert_section(section, from_code, to_code)
    if result:
        click.echo(f"{from_code} Section {section} → {to_code} Section {result}")
    else:
        click.echo(f"No mapping found for {from_code} Section {section} → {to_code}")


@cli.group()
def ingest():
    """Document ingestion pipeline."""
    pass


@ingest.command("ocr")
@click.option("--input-dir", "-i", default="data/raw", help="Input directory")
@click.option("--output-dir", "-o", default="data/processed/ocr", help="Output directory")
@click.option("--batch-size", "-b", default=50, help="Batch size")
@click.option("--languages", "-l", default="eng+hin+guj", help="Tesseract languages")
def ingest_ocr(input_dir, output_dir, batch_size, languages):
    """Run OCR on raw documents."""
    click.echo(f"Running OCR on {input_dir} → {output_dir}")
    click.echo(f"Languages: {languages}, Batch: {batch_size}")
    # Actual implementation will import from src.ingestion.ocr_pipeline
    click.echo("OCR pipeline will be initialized when run.")


@ingest.command("parse")
@click.option("--input-dir", "-i", default="data/processed/ocr")
@click.option("--output-dir", "-o", default="data/processed/structured")
def ingest_parse(input_dir, output_dir):
    """Parse OCR output into structured documents."""
    click.echo(f"Parsing {input_dir} → {output_dir}")


@ingest.command("clean")
@click.option("--input-dir", "-i", default="data/processed/structured")
@click.option("--output-dir", "-o", default="data/processed/cleaned")
def ingest_clean(input_dir, output_dir):
    """Clean and normalize parsed documents."""
    click.echo(f"Cleaning {input_dir} → {output_dir}")


@ingest.command("process-sources")
@click.option("--input-dir", "-i", default="data/sources", help="Input directory with scraped data")
@click.option("--output-dir", "-o", default="data/processed/cleaned", help="Output directory")
def ingest_process_sources(input_dir, output_dir):
    """Process scraped source documents into embedding-ready format."""
    from src.ingestion.processor import create_processor

    click.echo(f"Processing documents from {input_dir} to {output_dir}")

    processor = create_processor()
    stats = processor.process_source_dir(input_dir, output_dir)

    click.echo(f"\nProcessed {stats.total_processed} documents")
    click.echo(f"  Failed: {stats.total_failed}")
    click.echo(f"  By source: {stats.by_source}")
    click.echo(f"  By type: {stats.by_type}")


@cli.group()
def embed():
    """Embedding and vector store operations."""
    pass


@embed.command("create")
@click.option("--input-dir", "-i", default="data/processed/cleaned")
@click.option("--collection", "-c", default="all_documents", help="ChromaDB collection name")
@click.option("--batch-size", "-b", default=32, help="Embedding batch size")
def embed_create(input_dir, collection, batch_size):
    """Create embeddings and store in ChromaDB."""
    from src.retrieval.embeddings import create_embedding_pipeline

    click.echo(f"Creating embeddings from {input_dir} (batch: {batch_size})")

    pipeline = create_embedding_pipeline()
    stats = pipeline.embed_directory(input_dir, batch_size)

    click.echo(f"\nEmbedded {stats['total_docs']} documents into {stats['total_chunks']} chunks")
    click.echo(f"Average chunks per document: {stats['total_chunks'] / stats['total_docs'] if stats['total_docs'] > 0 else 0:.1f}")


@embed.command("search")
@click.argument("query")
@click.option("--top-k", "-k", default=5, help="Number of results")
@click.option("--collection", "-c", default="all_documents")
def embed_search(query, top_k, collection):
    """Test search against the vector store."""
    from src.retrieval.embeddings import create_embedding_pipeline

    click.echo(f"Searching for: {query} (top-{top_k} in {collection})")

    pipeline = create_embedding_pipeline()
    results = pipeline.search(query, collection=collection, top_k=top_k)

    click.echo(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        click.echo(f"\n{i}. Score: {result.score:.3f}")
        click.echo(f"   Title: {result.title[:100]}")
        click.echo(f"   Source: {result.source} | Court: {result.court or 'N/A'}")
        if result.sections:
            click.echo(f"   Sections: {', '.join(result.sections[:5])}")
        click.echo(f"   Text: {result.chunk_text[:200]}...")


@cli.group()
def model():
    """Model training and inference."""
    pass


@model.command("prepare-data")
def model_prepare_data():
    """Prepare training data for fine-tuning."""
    click.echo("Preparing training data...")


@model.command("train")
@click.option("--base-model", default="mistralai/Mistral-7B-Instruct-v0.3")
@click.option("--epochs", default=3)
@click.option("--batch-size", default=4)
def model_train(base_model, epochs, batch_size):
    """Fine-tune the SLM with QLoRA."""
    click.echo(f"Training: {base_model}, epochs={epochs}, batch={batch_size}")


@model.command("evaluate")
def model_evaluate():
    """Evaluate the fine-tuned model."""
    click.echo("Running evaluation...")


@cli.command("serve")
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000)
@click.option("--reload", is_flag=True, help="Enable hot reload for development")
def serve(host, port, reload):
    """Start the FastAPI server."""
    import uvicorn
    click.echo(f"Starting server at {host}:{port}")
    uvicorn.run("src.api.main:app", host=host, port=port, reload=reload)


@cli.command("stats")
def stats():
    """Show system statistics."""
    from src.data_sources.orchestrator import DataSourceOrchestrator

    orchestrator = DataSourceOrchestrator()
    counts = orchestrator.get_document_counts()
    total = 0
    click.echo("\n=== System Statistics ===\n")
    for source, type_counts in counts.items():
        source_total = sum(type_counts.values())
        total += source_total
        click.echo(f"{source}: {source_total} documents")
    click.echo(f"\nTotal: {total} documents")


@cli.command("health")
def health():
    """Check system health."""
    click.echo("\n=== System Health Check ===\n")

    checks = {
        "Python": True,
        "Data directory": Path("data").exists(),
        "Config files": Path("configs").exists(),
        "Logs directory": Path("logs").exists(),
    }

    # Check optional services
    try:
        import chromadb
        checks["ChromaDB library"] = True
    except ImportError:
        checks["ChromaDB library"] = False

    try:
        import torch
        checks["PyTorch"] = True
        checks["CUDA available"] = torch.cuda.is_available()
    except ImportError:
        checks["PyTorch"] = False

    for check, status in checks.items():
        icon = "✅" if status else "❌"
        click.echo(f"  {icon} {check}")


def main():
    cli()


if __name__ == "__main__":
    main()
