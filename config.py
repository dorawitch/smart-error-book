import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Default to local SQLite so the project can run out of the box.
DB_URI = os.getenv("DB_URI", f"sqlite:///{BASE_DIR / 'error_book.db'}")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))

# OCR configuration. If Tesseract is not installed, OCR service will degrade gracefully.
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")
OCR_LANG = os.getenv("OCR_LANG", "chi_sim+eng")
