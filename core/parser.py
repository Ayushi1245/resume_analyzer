import pdfplumber
from docx import Document
from pathlib import Path
import re


# PDF extraction artifacts that pdfplumber produces for undecodable glyphs
# (cid:XXX) = character ID references for emojis, icons, custom fonts
_CID_PATTERN = re.compile(r'\(cid:\d+\)')
# Brackets/parens left empty after CID removal
_EMPTY_BRACKETS = re.compile(r'\[\s*\]|\(\s*\)')


def _clean_pdf_artifacts(text: str) -> str:
    """Remove PDF extraction artifacts that aren't part of the actual resume."""
    # Remove (cid:XXX) character ID references
    text = _CID_PATTERN.sub('', text)
    # Remove empty brackets/parens left behind
    text = _EMPTY_BRACKETS.sub('', text)
    # Collapse multiple spaces into one
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def extract_text(file_path: str) -> str:
    """Extract plain text from PDF or DOCX."""
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        return _parse_pdf(file_path)
    elif path.suffix.lower() in (".docx", ".doc"):
        return _parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")


def _table_row_to_sentence(row: list) -> str:
    """Convert a single table row (list of cell values) into a readable sentence.

    pdfplumber returns each row as a list of strings (or None for empty cells).
    We filter out None/empty cells and join meaningful values with commas.

    Strategy: the first non-empty cell is treated as the subject, subsequent
    cells are appended with context-aware separators.

    Example input : ["MCA", "Graphic Era Hill University", "9.0", "Expected 2027"]
    Example output: "MCA at Graphic Era Hill University, CGPA 9.0, Expected 2027"
    """
    # Normalise: strip whitespace, drop None / blank cells
    cells = [str(c).strip() for c in row if c is not None and str(c).strip()]
    if not cells:
        return ""

    # Single cell → just return it
    if len(cells) == 1:
        return cells[0]

    # Two cells → "A at B" reads naturally for degree/institute pairs
    if len(cells) == 2:
        return f"{cells[0]} at {cells[1]}"

    # Three or more: first two joined with "at", rest appended with commas.
    # The third cell is prefixed with "CGPA" when it looks like a numeric grade.
    parts = [f"{cells[0]} at {cells[1]}"]
    for cell in cells[2:]:
        # Heuristic: if the cell is a number (e.g. "9.0", "8.5"), label it CGPA
        try:
            float(cell)
            parts.append(f"CGPA {cell}")
        except ValueError:
            parts.append(cell)

    return ", ".join(parts)


def _extract_table_text(page) -> str:
    """Extract all tables on a page and convert them to clean readable sentences.

    Returns an empty string when the page has no tables.
    """
    tables = page.extract_tables()
    if not tables:
        return ""

    table_lines = []
    for table in tables:
        for row in table:
            sentence = _table_row_to_sentence(row)
            if sentence:
                table_lines.append(sentence)

    return "\n".join(table_lines)


def _parse_pdf(path: str) -> str:
    """Extract text from a PDF resume, handling table sections gracefully.

    For each page the function:
      1. Calls extract_tables() to pull out any tabular data (Education grids,
         skills matrices, etc.) and converts each row into a human-readable
         sentence via _table_row_to_sentence().
      2. Calls extract_text() for the remainder of the page (bullet points,
         headings, paragraphs) — pdfplumber's default behaviour.
      3. Merges table sentences above the regular text so the structured data
         appears in reading order rather than being scattered / duplicated.
      4. Applies the existing _clean_pdf_artifacts() step on the combined
         output to strip (cid:XXX) codes, empty brackets, and extra spaces.

    Falls back to plain extract_text() when a page contains no tables at all,
    preserving the original behaviour for simple single-column resumes.
    """
    text_parts = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_segments = []

            # ── Step 1: Table-aware extraction ───────────────────────────────
            table_text = _extract_table_text(page)
            if table_text:
                page_segments.append(table_text)

            # ── Step 2: Regular (non-table) text extraction ──────────────────
            raw_text = page.extract_text()
            if raw_text:
                page_segments.append(raw_text)

            if not page_segments:
                continue

            # ── Step 3: Combine and clean ─────────────────────────────────────
            combined = "\n".join(page_segments)
            combined = _clean_pdf_artifacts(combined)

            # Collapse blank lines / stray whitespace per-line
            cleaned = "\n".join(
                line.strip() for line in combined.split("\n") if line.strip()
            )
            text_parts.append(cleaned)

    return "\n".join(text_parts)


def _parse_docx(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())


# --- Deterministic artifact scanner (no LLM needed) ---

# Patterns that indicate stray template remnants or typos
_ARTIFACT_PATTERNS = [
    (re.compile(r'\[\s*\]'),            'Empty brackets []'),
    (re.compile(r'\(\s*\)'),            'Empty parentheses ()'),
    (re.compile(r'\{\s*\}'),            'Empty curly braces {}'),
    (re.compile(r'\[.*?(cid:\d+).*?\]'), 'PDF character ID artifact'),
    (re.compile(r'\[insert\b.*?\]', re.IGNORECASE), 'Placeholder text [Insert...]'),
    (re.compile(r'\[your\b.*?\]', re.IGNORECASE),   'Placeholder text [Your...]'),
    (re.compile(r'\[TODO\b.*?\]', re.IGNORECASE),   'TODO marker'),
    (re.compile(r'\bTODO\b'),           'TODO marker'),
    (re.compile(r'\bXXX\b'),            'XXX placeholder'),
    (re.compile(r'\bFIXME\b'),          'FIXME marker'),
    (re.compile(r'<\s*>'),              'Empty angle brackets <>'),
    (re.compile(r'\*{3,}'),             'Excessive asterisks'),
    (re.compile(r'_{3,}'),              'Excessive underscores (possible template line)'),
]


def scan_stray_artifacts(text: str) -> list[dict]:
    """Deterministically scan resume text for stray artifacts.
    
    Returns a list of dicts with exact location info:
      - line_number: 1-indexed line where the artifact was found
      - line_text: the full line containing the artifact
      - matched_text: the exact artifact matched
      - issue: human-readable description of the problem
    """
    findings = []
    lines = text.split("\n")
    
    for line_num, line in enumerate(lines, start=1):
        for pattern, description in _ARTIFACT_PATTERNS:
            for match in pattern.finditer(line):
                findings.append({
                    "line_number": line_num,
                    "line_text": line.strip(),
                    "matched_text": match.group(),
                    "issue": description,
                })
    
    return findings

