import pdfplumber
from docx import Document
from pathlib import Path


def extract_text(file_path: str) -> str:
    """Extract plain text from PDF or DOCX."""
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        return _parse_pdf(file_path)
    elif path.suffix.lower() in (".docx", ".doc"):
        return _parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")


def _parse_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # Strip stray whitespace aggressively — resume PDFs
                # often have extra newlines/spaces that inflate token counts
                cleaned = "\n".join(
                    line.strip() for line in text.split("\n") if line.strip()
                )
                text_parts.append(cleaned)
    return "\n".join(text_parts)


def _parse_docx(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
