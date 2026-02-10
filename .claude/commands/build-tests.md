Build a comprehensive test suite for the Gujarat Police SLM system.

## Test Structure

### tests/unit/test_data_sources.py
- Test IndianKanoonDataSource._parse_search_results() with sample HTML
- Test IndianKanoonDataSource._extract_sections() with various formats
- Test IndianKanoonDataSource._extract_date() with multiple date formats
- Test ECourtsDataSource district code lookup
- Test IndiaCodeDataSource.convert_section() - IPC→BNS and BNS→IPC
- Test section mapping completeness (302→103, 420→318(4), etc.)
- Test ScrapedDocument serialization/deserialization
- Test deduplication via content hash

### tests/unit/test_parsers.py
- Test FIRParser with sample FIR text (English, Hindi, Gujarati)
- Test ChargesheetParser with sample chargesheet
- Test CourtRulingParser with sample judgment
- Test section normalization: "sec. 302" = "Section 302" = "IPC 302" = "s.302"
- Test date normalization across all formats
- Test entity normalization (Gujarat district names in all 3 languages)

### tests/unit/test_security.py
- Test AES-256 encryption/decryption roundtrip
- Test PII detection (Aadhaar: 12 digits, phone: 10 digits, etc.)
- Test JWT token generation and verification
- Test token expiry
- Test RBAC permission matrix
- Test audit log hash chain integrity
- Test prompt injection prevention patterns

### tests/unit/test_rag.py
- Test chunking respects paragraph boundaries
- Test chunking metadata attachment
- Test query expansion (murder → [Section 302, BNS 103, hatya, etc.])
- Test context assembly (max token limit, source formatting)
- Test prompt template rendering

### tests/integration/test_api.py
- Test /health returns 200
- Test /auth/login with valid/invalid credentials
- Test /auth/login brute force lockout
- Test RBAC: officer cannot access /admin/* endpoints
- Test /search/query returns results with citations
- Test /utils/convert-section/302?from_code=IPC&to_code=BNS
- Test /documents/upload file processing
- Test audit log captures all API calls

### tests/integration/test_pipeline.py
- Test end-to-end: upload document → OCR → parse → embed → search
- Test: FIR input → SOP suggestions with sources
- Test: chargesheet input → review with score

### tests/fixtures/
Create realistic test fixtures:
- sample_fir_english.txt - Sample FIR in English
- sample_fir_hindi.txt - Sample FIR in Hindi
- sample_chargesheet.txt - Sample chargesheet
- sample_judgment.txt - Sample court judgment
- sample_panchnama.txt - Sample panchnama

## Configuration
- pytest.ini or in pyproject.toml [tool.pytest.ini_options]
- conftest.py with database fixtures, test client, sample data
- Use httpx.AsyncClient for API tests
- Use factory_boy for test data generation

## Run
Wire up: `make test`, `make test-unit`, `make test-integration`
Target: >80% coverage on src/
