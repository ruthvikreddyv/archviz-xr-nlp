import pytesseract
import cv2
import numpy as np
import fitz  # PyMuPDF
import os
import re
import shutil


def configure_tesseract():
    candidates = [
        os.getenv("TESSERACT_CMD"),
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            return candidate
    return None


# ── Text cleaning ─────────────────────────────────────────

GARBAGE_TOKENS = {
    "etn", "eg", "ce", "ge", "gy", "nx", "ata", "ada", "ae", "bene",
    "ene", "pee", "mir", "tos", "cicici", "nv", "lx", "yl", "le",
    "jl", "ven", "iv", "kq", "aa", "ee", "aaa", "yyy", "xxx",
}

STRIP_CHARS = "{}[]()_-~><'`\"\\/@#$%^&*+=|,."


def clean_text(raw: str) -> str:
    """
    Clean OCR output — two pass:
    1. Drop lines that are mostly symbols
    2. Drop garbage tokens within good lines
    """
    lines = raw.splitlines()
    good_tokens = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip lines mostly non-alphabetic
        alpha = sum(1 for c in line if c.isalpha())
        total = len(line.replace(" ", ""))
        if total > 0 and alpha / total < 0.4:
            continue

        for token in line.split():
            t = token.strip(STRIP_CHARS)
            if not t:
                continue
            tl = t.lower()

            # Drop known garbage
            if tl in GARBAGE_TOKENS:
                continue

            # Drop very short non-words
            if len(t) <= 2 and tl not in {
                "or", "of", "to", "at", "by", "is", "in", "an",
                "v", "k", "q", "x", "y"
            }:
                continue

            # Drop mostly non-alphabetic tokens
            a = sum(1 for c in t if c.isalpha())
            if len(t) > 0 and a / len(t) < 0.45:
                continue

            # Drop subscript patterns like x1, y2m
            if re.match(r"^[a-zA-Z]{1,2}[0-9]+[a-zA-Z]*$", t):
                continue

            good_tokens.append(t)

    # Join and final symbol cleanup
    result = " ".join(good_tokens)
    result = re.sub(r"[{}\[\]()~@#$%^&*]", " ", result)
    result = re.sub(r"\s{2,}", " ", result)
    return result.strip()


# ── Region-based OCR ──────────────────────────────────────

def ocr_region(region: np.ndarray, psm: int = 6) -> str:
    """OCR a single image region with 3x upscale."""
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    large = cv2.resize(gray, None, fx=3, fy=3,
                       interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(large, 0, 255,
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    config = f"--psm {psm} --oem 3"
    return pytesseract.image_to_string(thresh, config=config)


def extract_zones(img: np.ndarray) -> str:
    """
    Split image into 5 zones and OCR each independently.
    This is far more reliable than OCR-ing the whole image at once
    because each zone has different text density and background.

    Zones:
    - Title bar (top 10%)
    - Left column / encoder (10-82%, left 38%)
    - Center column / decoder (10-82%, 38-72%)
    - Right column / legend (10-82%, right 28%)
    - Description box (bottom 18%)
    """
    h, w = img.shape[:2]

    zones = [
        ("title",       img[:int(h*0.10), :]),
        ("left",        img[int(h*0.10):int(h*0.82), :int(w*0.38)]),
        ("center",      img[int(h*0.10):int(h*0.82), int(w*0.38):int(w*0.72)]),
        ("right",       img[int(h*0.10):int(h*0.82), int(w*0.72):]),
        ("description", img[int(h*0.82):, :]),
    ]

    all_text = []
    for name, zone in zones:
        if zone.size == 0:
            continue
        raw = ocr_region(zone, psm=6)
        clean = clean_text(raw)
        if clean:
            all_text.append(clean)

    # Merge and deduplicate adjacent repeated words
    combined = " ".join(all_text)
    words = combined.split()
    deduped = []
    for i, word in enumerate(words):
        if i > 0 and word.lower() == words[i - 1].lower():
            continue
        deduped.append(word)

    return " ".join(deduped)


# ── Main preprocessing ────────────────────────────────────

def preprocess_image(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {path}")

    h, w = img.shape[:2]
    # Upscale small images
    if w < 1000:
        img = cv2.resize(img, None, fx=2.0, fy=2.0,
                         interpolation=cv2.INTER_CUBIC)
    return img


def extract_from_image(path: str) -> str:
    if not configure_tesseract():
        raise ValueError(
            "Tesseract not found. Set TESSERACT_CMD or add "
            "tesseract.exe to your PATH."
        )

    img = preprocess_image(path)

    try:
        text = extract_zones(img)
    except pytesseract.TesseractNotFoundError:
        raise ValueError("Tesseract could not start. Check TESSERACT_CMD.")

    return text


def extract_from_pdf(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find PDF: {path}")
    doc = fitz.open(path)
    pages = [p.get_text().strip() for p in doc if p.get_text().strip()]
    doc.close()
    return " ".join(pages)


def extract(path: str) -> str:
    """
    Main entry point — route by file type, return clean text.
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        print("[OCR] Detected PDF - using PyMuPDF")
        text = extract_from_pdf(path)
    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
        print("[OCR] Detected image - using zone-based Tesseract")
        text = extract_from_image(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    if not text or len(text.split()) < 3:
        raise ValueError(
            "Too little text extracted. Use a clearer image "
            "(min 800px wide, good contrast)."
        )

    print(f"[OCR] Extracted {len(text.split())} words")
    return text


# ── Quick test ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pipeline/ocr.py <image_or_pdf>")
        sys.exit(1)

    configure_tesseract()
    path = sys.argv[1]
    print(f"\n[OCR] Processing: {path}\n")
    result = extract(path)
    print("── Extracted Text ──────────────────")
    print(result)
    print("────────────────────────────────────")
    print(f"Total words: {len(result.split())}")