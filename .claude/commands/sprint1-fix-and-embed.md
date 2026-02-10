Execute Sprint 1: Fix Indian Kanoon parser + Build embedding pipeline.

We have 10 India Code documents collected. Indian Kanoon scraper ran 37 queries but saved 0 documents due to HTML parsing mismatch. Fix this first, then build the embedding pipeline.

## TASK 1: Fix Indian Kanoon Parser (30 min)

The issue is in `src/data_sources/indian_kanoon.py` - the `_parse_search_results()` and `_parse_judgment_page()` methods use CSS selectors that don't match Indian Kanoon's actual HTML structure.

1. First, manually fetch one page to see the real HTML:
```python
import requests
r = requests.get("https://indiankanoon.org/search/?formInput=Gujarat+murder+Section+302", 
                  headers={"User-Agent": "Mozilla/5.0"})
print(r.text[:5000])  # See actual HTML structure
```

2. Then fetch one judgment page:
```python
r = requests.get("https://indiankanoon.org/doc/1560742/",
                  headers={"User-Agent": "Mozilla/5.0"})
print(r.text[:5000])
```

3. Update the CSS selectors in `_parse_search_results()` and `_parse_judgment_page()` to match the ACTUAL HTML structure you see.

Common issues:
- Indian Kanoon may use different class names than `.result`, `.result_title`, `#judgment`
- They may serve different HTML to scrapers vs browsers
- The judgment text div might be `.judgments` or `.expanded` or something else

4. After fixing, re-run: `python -m src.cli collect run --source indian_kanoon --max-results 30`
5. Verify at least 20+ documents saved in `data/sources/indiankanoon/`

## TASK 2: Process Collected Documents (20 min)

Take all documents from `data/sources/` and prepare them for embedding:

Create `src/ingestion/processor.py`:

```python
class DocumentProcessor:
    """Process scraped documents into embedding-ready format."""
    
    def process_source_dir(self, source_dir="data/sources", output_dir="data/processed/cleaned"):
        """Read all JSON docs from source scrapers, normalize, output cleaned JSONs."""
        # 1. Walk data/sources/ recursively, find all .json files
        # 2. For each JSON file, load it as ScrapedDocument
        # 3. Normalize section references using SectionNormalizer
        # 4. Detect language per paragraph
        # 5. Save cleaned version to data/processed/cleaned/
        # 6. Return stats: total processed, per source, per type
```

Wire up to CLI: `python -m src.cli ingest process-sources`

Run it on the 10 India Code docs + any Indian Kanoon docs we now have.

## TASK 3: Build Embedding Pipeline (45 min)

Create `src/retrieval/embeddings.py`:

1. Load embedding model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
   - This model supports Hindi, Gujarati, English
   - Runs locally, ~500MB download first time
   - Use device="cpu" for now (change to "cuda" when GPU available)

2. Use the DocumentChunker from `src/retrieval/chunker.py` to chunk documents

3. Create ChromaDB collections:
   - Start ChromaDB: `docker run -d -p 8100:8000 chromadb/chroma:latest` (or use docker-compose)
   - If Docker not available on Windows, use ChromaDB in-process mode (persistent local directory)
   - Create collections: "court_rulings", "bare_acts", "all_documents"

4. Embed and store all chunks with metadata

Create the pipeline:
```python
class EmbeddingPipeline:
    def __init__(self, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                 chroma_persist_dir="data/embeddings/chroma"):
        self.model = SentenceTransformer(model_name)
        self.client = chromadb.PersistentClient(path=chroma_persist_dir)
        self.chunker = DocumentChunker()
    
    def embed_directory(self, input_dir="data/processed/cleaned"):
        """Chunk and embed all documents in directory."""
        # For each JSON doc in input_dir:
        #   1. Chunk it using DocumentChunker
        #   2. Embed chunks using sentence-transformer
        #   3. Store in ChromaDB with metadata
        
    def search(self, query, collection="all_documents", top_k=5):
        """Search embedded documents."""
        # Embed query, search ChromaDB, return results with scores
```

Wire up to CLI:
- `python -m src.cli embed create --input-dir data/processed/cleaned`
- `python -m src.cli embed search "murder bail conditions Gujarat" --top-k 5`

## TASK 4: Verify It Works (10 min)

Run these test searches and show results:
1. `python -m src.cli embed search "Section 302 IPC murder punishment"`
2. `python -m src.cli embed search "theft investigation procedure"`
3. `python -m src.cli embed search "bail conditions NDPS Act"`
4. `python -m src.cli embed search "dowry death Section 304B"`
5. `python -m src.cli embed search "chargesheet filing procedure Section 173"`

Each should return relevant chunks with scores > 0.5.

Print: total documents processed, total chunks embedded, average chunks per document.

## DONE CRITERIA:
- Indian Kanoon parser fixed, 20+ court rulings collected
- All collected docs processed and cleaned
- ChromaDB running with embedded chunks
- Search returning relevant results for test queries
- Print "SPRINT 1 COMPLETE" with stats
