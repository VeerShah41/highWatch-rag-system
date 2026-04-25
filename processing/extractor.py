import re
from pypdf import PdfReader


def extract_text(file_path: str, mime_type: str) -> str:
    """
    Extract and clean text from a local file.
    Supports: PDF (via PyMuPDF), plain text, exported Google Docs (txt).
    """
    try:
        if mime_type == "application/pdf" or file_path.endswith(".pdf"):
            return _extract_pdf(file_path)
        else:
            return _extract_text_file(file_path)
    except Exception as e:
        print(f"[Extractor] Error extracting {file_path}: {e}")
        return ""


def _extract_pdf(file_path: str) -> str:
    """Extract text from a PDF using pypdf."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return _clean_text(text)


def _extract_text_file(file_path: str) -> str:
    """Read a plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return _clean_text(text)


def _clean_text(text: str) -> str:
    """Normalize and clean extracted text."""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Normalize multiple newlines to double newline (paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove excessive whitespace within lines
    text = re.sub(r"[ \t]+", " ", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text
