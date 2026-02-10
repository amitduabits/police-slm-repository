Build document parsers for each Gujarat Police document type.

Create `src/ingestion/parsers.py` with these parser classes:

## FIR Parser (class FIRParser)
Extract from raw OCR text:
- FIR number, date, time
- Police station, district
- Complainant details (name, address, relation)
- Accused details (if known)
- IPC/BNS sections cited (normalize both old and new codes using configs/ipc_to_bns_mapping.json)
- Incident description (narrative text)
- Location of incident
- Evidence mentioned

## Chargesheet Parser (class ChargesheetParser)
Extract:
- Case number, FIR reference
- Accused list with details
- Witnesses list
- Evidence inventory
- Sections charged under (normalize IPC↔BNS)
- Investigation officer details
- Chronology of investigation
- Forensic/expert reports referenced

## Court Ruling Parser (class CourtRulingParser)
Extract:
- Case citation
- Judge name, court
- Charges considered
- Verdict (convicted/acquitted per section)
- Key reasoning paragraphs
- Sentences imposed
- Precedents cited

## Panchnama Parser (class PanchnamaParser)
Extract:
- Panchnama number, date, time
- Location
- Panch witness names
- Items found/seized
- Description of scene
- IO name

## For each parser:
1. Use regex + heuristic rules first (these documents follow government templates)
2. Handle all three languages (English, Hindi, Gujarati)
3. Normalize section references using the IPC↔BNS mapping from configs/
4. Store as structured JSON with original text preserved
5. Include confidence score for each extracted field
6. Log extraction failures for manual review

## Also create:
- `src/ingestion/section_normalizer.py` - Loads configs/ipc_to_bns_mapping.json and provides:
  - `normalize_section("302", "IPC")` → returns both IPC and BNS equivalents
  - `parse_section_reference("sec. 302 IPC")` → structured output
  - Handle ALL common formats: "sec. 302", "Section 302", "s.302", "IPC 302", "BNS 103", "u/s 302"

- `src/ingestion/entity_normalizer.py` - Standardize:
  - Police station names (handle Gujarati/Hindi/English variants)
  - District names (all 33 Gujarat districts)
  - Court names
  - Date formats (DD/MM/YYYY, DD-MM-YY, Gujarati dates, Hindi dates → ISO 8601)

## Wire up CLI:
- `python -m src.cli ingest parse --input-dir data/processed/ocr --output-dir data/processed/structured`

## Test:
Create sample fixture files in tests/fixtures/ for each document type and test parsing.
