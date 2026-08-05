from pathlib import Path

from pypdf import PdfReader


def extract_text(filepath: Path) -> str:
    reader = PdfReader(str(filepath))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages_text).strip()
