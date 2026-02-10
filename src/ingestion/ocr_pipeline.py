"""
Gujarat Police SLM - OCR Pipeline
Multilingual OCR for Gujarati, Hindi, English documents.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    """Detect language from Unicode character ranges."""
    if not text.strip():
        return "en"
    gu_chars = sum(1 for c in text if '\u0A80' <= c <= '\u0AFF')
    hi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    total = len(text)
    if total == 0:
        return "en"
    if gu_chars / total > 0.1:
        return "gu"
    if hi_chars / total > 0.1:
        return "hi"
    return "en"


class OCRPipeline:
    """Multilingual OCR pipeline for Gujarat Police documents."""

    def __init__(self, languages="eng+hin+guj", confidence_threshold=0.80):
        self.languages = languages
        self.confidence_threshold = confidence_threshold
        self._tesseract_available = False
        self._paddle_available = False
        self._check_engines()

    def _check_engines(self):
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
            logger.info("Tesseract OCR available")
        except Exception:
            logger.warning("Tesseract not available - install tesseract-ocr")

        try:
            from paddleocr import PaddleOCR
            self._paddle_available = True
            logger.info("PaddleOCR available")
        except ImportError:
            logger.warning("PaddleOCR not available - handwritten fallback disabled")

    def preprocess_image(self, image):
        """Preprocess scanned image for better OCR."""
        try:
            import cv2
            import numpy as np
            if isinstance(image, str):
                img = cv2.imread(image)
            else:
                img = np.array(image)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            return binary
        except ImportError:
            logger.warning("OpenCV not available, skipping preprocessing")
            return image

    def ocr_page_tesseract(self, image) -> dict:
        """OCR a single page using Tesseract."""
        import pytesseract
        data = pytesseract.image_to_data(image, lang=self.languages, output_type=pytesseract.Output.DICT)
        text_parts = []
        confidences = []
        for i, txt in enumerate(data['text']):
            conf = int(data['conf'][i])
            if conf > 0 and txt.strip():
                text_parts.append(txt)
                confidences.append(conf)
        full_text = ' '.join(text_parts)
        avg_conf = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
        return {"text": full_text, "confidence": avg_conf}

    def ocr_page_paddle(self, image_path: str) -> dict:
        """OCR using PaddleOCR (fallback for handwritten content)."""
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        result = ocr.ocr(image_path, cls=True)
        texts, confidences = [], []
        if result and result[0]:
            for line in result[0]:
                texts.append(line[1][0])
                confidences.append(line[1][1])
        return {
            "text": '\n'.join(texts),
            "confidence": sum(confidences) / len(confidences) if confidences else 0.0,
        }

    def process_pdf(self, pdf_path: str) -> dict:
        """Process a PDF file through OCR."""
        doc_id = str(uuid.uuid4())
        pages = []

        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path, dpi=300)
        except ImportError:
            logger.error("pdf2image not installed. Run: pip install pdf2image")
            return {"document_id": doc_id, "error": "pdf2image not available", "pages": []}

        for i, image in enumerate(images):
            preprocessed = self.preprocess_image(image)

            if self._tesseract_available:
                result = self.ocr_page_tesseract(preprocessed)
            elif self._paddle_available:
                # Save temp image for PaddleOCR
                temp_path = f"/tmp/ocr_temp_{doc_id}_{i}.png"
                image.save(temp_path)
                result = self.ocr_page_paddle(temp_path)
                os.remove(temp_path)
            else:
                result = {"text": "", "confidence": 0.0}

            # Fallback to PaddleOCR if Tesseract confidence is low
            if result["confidence"] < self.confidence_threshold and self._paddle_available:
                temp_path = f"/tmp/ocr_temp_{doc_id}_{i}.png"
                image.save(temp_path)
                paddle_result = self.ocr_page_paddle(temp_path)
                os.remove(temp_path)
                if paddle_result["confidence"] > result["confidence"]:
                    result = paddle_result

            # Split into paragraphs and detect language
            paragraphs = []
            for para_text in result["text"].split('\n\n'):
                if para_text.strip():
                    paragraphs.append({
                        "text": para_text.strip(),
                        "language": detect_language(para_text),
                        "confidence": result["confidence"],
                    })

            lang_primary = detect_language(result["text"])
            pages.append({
                "page_number": i + 1,
                "confidence": result["confidence"],
                "language_primary": lang_primary,
                "paragraphs": paragraphs,
            })

        confidences = [p["confidence"] for p in pages]
        overall = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "document_id": doc_id,
            "source_file": str(pdf_path),
            "pages": pages,
            "overall_confidence": round(overall, 4),
            "needs_manual_review": overall < self.confidence_threshold,
            "processed_at": datetime.utcnow().isoformat(),
        }

    def process_image(self, image_path: str) -> dict:
        """Process a single image file."""
        doc_id = str(uuid.uuid4())
        preprocessed = self.preprocess_image(image_path)

        if self._tesseract_available:
            result = self.ocr_page_tesseract(preprocessed)
        else:
            result = {"text": "", "confidence": 0.0}

        paragraphs = []
        for para in result["text"].split('\n\n'):
            if para.strip():
                paragraphs.append({
                    "text": para.strip(),
                    "language": detect_language(para),
                    "confidence": result["confidence"],
                })

        return {
            "document_id": doc_id,
            "source_file": str(image_path),
            "pages": [{"page_number": 1, "confidence": result["confidence"],
                       "language_primary": detect_language(result["text"]),
                       "paragraphs": paragraphs}],
            "overall_confidence": result["confidence"],
            "needs_manual_review": result["confidence"] < self.confidence_threshold,
            "processed_at": datetime.utcnow().isoformat(),
        }

    def process_directory(self, input_dir: str, output_dir: str, resume: bool = True):
        """Batch process all documents in a directory."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp'}
        files = [f for f in input_path.rglob('*') if f.suffix.lower() in extensions]

        processed = 0
        errors = 0
        for f in files:
            out_file = output_path / f"{f.stem}.json"
            if resume and out_file.exists():
                continue

            try:
                if f.suffix.lower() == '.pdf':
                    result = self.process_pdf(str(f))
                else:
                    result = self.process_image(str(f))

                with open(out_file, 'w', encoding='utf-8') as fh:
                    json.dump(result, fh, ensure_ascii=False, indent=2)
                processed += 1
                logger.info(f"Processed: {f.name} (conf: {result['overall_confidence']:.2f})")
            except Exception as e:
                errors += 1
                logger.error(f"Failed: {f.name}: {e}")

        logger.info(f"OCR complete: {processed} processed, {errors} errors, {len(files)} total")
        return {"processed": processed, "errors": errors, "total": len(files)}
