Build the complete multilingual OCR pipeline for Gujarat Police documents.

Documents are in Gujarati, Hindi, and English (often mixed in the same document).

Create/update `src/ingestion/ocr_pipeline.py` with:

1. **Pre-processing module**:
   - Deskew scanned pages using OpenCV
   - Denoise using Non-Local Means denoising
   - Binarize using adaptive thresholding
   - Remove stamps/watermarks (detect and mask colored regions)
   - Ensure minimum 300 DPI (upscale if needed)

2. **OCR Engine wrapper**:
   - Primary: Tesseract with `eng+hin+guj` language pack
   - Fallback: PaddleOCR for handwritten content (panchnamas)
   - Confidence scoring per page
   - Flag pages below 80% confidence for manual review

3. **Language detection**:
   - Detect language PER PARAGRAPH (not per document)
   - Use Unicode range detection: Gujarati (U+0A80-U+0AFF), Hindi/Devanagari (U+0900-U+097F), English (ASCII)
   - Tag each paragraph with detected language

4. **Post-processing**:
   - Legal terminology spell correction dictionary (create a JSON dict with common legal terms in all 3 languages)
   - Fix common OCR errors in Devanagari/Gujarati scripts
   - Normalize whitespace and line breaks

5. **Output format**: Structured JSON per document:
   ```json
   {
     "document_id": "uuid",
     "source_file": "path",
     "pages": [
       {
         "page_number": 1,
         "confidence": 0.92,
         "language_primary": "en",
         "paragraphs": [
           {"text": "...", "language": "en", "confidence": 0.95, "bbox": [x,y,w,h]}
         ]
       }
     ],
     "overall_confidence": 0.89,
     "needs_manual_review": false,
     "processed_at": "ISO timestamp"
   }
   ```

6. **Batch processing**:
   - Process files from data/raw/ to data/processed/ocr/
   - Progress bar with ETA
   - Resume capability (skip already processed files)
   - Error logging with document ID to logs/ocr_errors.log

7. **CLI integration**: Wire up `python -m src.cli ingest ocr` command

Also create `src/ingestion/legal_dictionary.json` with 200+ common legal terms in English, Hindi, and Gujarati (IPC section names, court terminology, police terminology).

Test with a sample: create a simple test image with mixed English/Hindi text and run OCR on it.
