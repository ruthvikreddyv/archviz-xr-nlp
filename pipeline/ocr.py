import pytesseract
import cv2
from PIL import Image
import fitz  # PyMuPDF
import os

# Tell pytesseract where Tesseract is installed on Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def preprocess_image(path: str):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not load image at: {path}")

    # Resize to at least 2x — dramatically improves OCR on small images
    height, width = img.shape[:2]
    if width < 1000:
        scale = 2.0
        img = cv2.resize(img, None, fx=scale, fy=scale,
                         interpolation=cv2.INTER_CUBIC)

    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=10)

    # Sharpen contrast
    _, thresh = cv2.threshold(gray, 0, 255,
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def extract_from_image(path: str) -> str:
    """
    Extract all text from a diagram image (JPG, PNG).
    Returns a clean string of all text found.
    """
    processed = preprocess_image(path)
    raw_text = pytesseract.image_to_string(processed)

    # Clean up: remove empty lines and strip whitespace
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    clean_text = " ".join(lines)

    return clean_text


def extract_from_pdf(path: str) -> str:
    """
    Extract all text from a PDF research paper.
    PyMuPDF reads the text layer directly — much better than OCR for PDFs.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find PDF at: {path}")

    doc = fitz.open(path)
    pages_text = []

    for page in doc:
        text = page.get_text()
        if text.strip():
            pages_text.append(text.strip())

    doc.close()
    return " ".join(pages_text)


def extract(path: str) -> str:
    """
    Smart router — detects file type and calls the right extractor.
    This is the function the rest of the pipeline will call.
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        print(f"[OCR] Detected PDF — using PyMuPDF")
        text = extract_from_pdf(path)
    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
        print(f"[OCR] Detected image — using Tesseract")
        text = extract_from_image(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    if not text:
        raise ValueError("No text could be extracted from the file. Check image quality.")

    print(f"[OCR] Extracted {len(text.split())} words")
    return text


# ── Quick test ──────────────────────────────────────────────
# Run this file directly to test: python pipeline/ocr.py
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pipeline/ocr.py <path_to_image_or_pdf>")
        print("Example: python pipeline/ocr.py test.png")
        sys.exit(1)

    path = sys.argv[1]
    print(f"\n[OCR] Processing: {path}")
    result = extract(path)
    print(f"\n── Extracted Text ──────────────────")
    print(result)
    print(f"────────────────────────────────────")
    print(f"Total words: {len(result.split())}")