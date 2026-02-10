Execute Phase 1 (Data Pipeline) of the Gujarat Police SLM project completely.

This is weeks 1-4 of the 6-month POC. Do everything in order:

## Step 1: Verify Environment
- Run `python -m src.cli health`
- Verify Docker services are running (postgres, chroma, redis)
- Verify Tesseract OCR is installed with eng+hin+guj language packs

## Step 2: Save Section Mappings
- Run `python -m src.cli collect save-mappings`
- Verify configs/ipc_to_bns_mapping.json exists and has 100+ entries
- Verify configs/crpc_to_bnss_mapping.json exists
- Test: convert Section 302 IPC → should return BNS 103

## Step 3: Collect Data from Verified Sources
Run all data source scrapers. Start with India Code (fastest, foundational), then Indian Kanoon (largest):
- `python -m src.cli collect run --source india_code`
- `python -m src.cli collect run --source indian_kanoon --max-results 50`
- `python -m src.cli collect run --source gujarat_hc --max-results 30`
- `python -m src.cli collect run --source supreme_court --max-results 20`
- `python -m src.cli collect run --source ncrb`

After each, report how many documents were saved.

## Step 4: Process Local Documents
If there are any documents in data/raw/:
- Run OCR pipeline: `python -m src.cli ingest ocr`
- Parse into structured format: `python -m src.cli ingest parse`
- Clean and normalize: `python -m src.cli ingest clean`

## Step 5: Create Embeddings
- Run: `python -m src.cli embed create`
- Verify ChromaDB collections were created
- Test search: `python -m src.cli embed search "murder bail conditions Gujarat"`

## Step 6: Validation
- Run: `python -m src.cli collect validate`
- Run: `python -m src.cli stats`
- Report: total documents per source, total embeddings, storage usage

## Step 7: Phase 1 Report
Generate a Phase 1 completion report (data/phase1_report.md) with:
- Documents collected per source
- OCR accuracy stats
- Search test results (3 test queries with top results)
- Issues found and recommendations
- Ready/not-ready assessment for Phase 2

Print "PHASE 1 COMPLETE" when done.
