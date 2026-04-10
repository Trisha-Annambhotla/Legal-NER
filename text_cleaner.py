"""
text_cleaner.py
---------------
Cleans and normalises raw text extracted from Indian High Court judgment PDFs.
Handles common artefacts: page numbers, running headers/footers, ligatures,
excess whitespace, and encoding noise.
"""

import re
from typing import List


# ── Regex patterns for common legal document artefacts ───────────────────────

# Standalone page numbers: "1", "- 2 -", "Page 3 of 45", etc.
_RE_PAGE_NUMBER = re.compile(
    r"^\s*[-–]?\s*\bPage\b\s*\d+\s*(?:of\s*\d+)?\s*[-–]?\s*$"
    r"|^\s*[-–]?\s*\d{1,4}\s*[-–]?\s*$",
    re.IGNORECASE | re.MULTILINE
)

# Common running headers/footers seen in HC judgments
_RE_HEADER_FOOTER = re.compile(
    r"(?m)^\s*(IN THE HIGH COURT OF|HIGH COURT OF JUDICATURE|"
    r"BEFORE THE HON['\u2019]?BLE|WWW\.LIVELAW\.IN|"
    r"Digitally signed by|For Private Circulation Only)\s*.*$",
    re.IGNORECASE
)

# Multiple blank lines → single blank line
_RE_MULTI_BLANK = re.compile(r"\n{3,}")

# Trailing / leading whitespace on each line
_RE_LINE_WHITESPACE = re.compile(r"[ \t]+$|^[ \t]+", re.MULTILINE)

# Non-breaking spaces and other invisible Unicode spaces
_RE_UNICODE_SPACES = re.compile(r"[\u00a0\u200b\u200c\u200d\u202f\u2060\ufeff]")

# Common PDF ligature artefacts
_LIGATURE_MAP = {
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl",
    "\ufb03": "ffi", "\ufb04": "ffl", "\ufb06": "st",
}


# ── Core cleaning functions ───────────────────────────────────────────────────

def _replace_ligatures(text: str) -> str:
    """Replace PDF ligature characters with their ASCII equivalents."""
    for ligature, replacement in _LIGATURE_MAP.items():
        text = text.replace(ligature, replacement)
    return text


def _remove_page_numbers(text: str) -> str:
    """Strip standalone page-number lines."""
    return _RE_PAGE_NUMBER.sub("", text)


def _remove_headers_footers(text: str) -> str:
    """Remove recurring header/footer lines typical of HC PDFs."""
    return _RE_HEADER_FOOTER.sub("", text)


def _normalise_whitespace(text: str) -> str:
    """Collapse excess whitespace while preserving paragraph breaks."""
    # Remove trailing/leading spaces per line
    text = _RE_LINE_WHITESPACE.sub("", text)
    # Collapse runs of 3+ blank lines into one blank line
    text = _RE_MULTI_BLANK.sub("\n\n", text)
    return text.strip()


def _fix_encoding(text: str) -> str:
    """Fix Unicode artefacts common in pdfplumber output."""
    text = _RE_UNICODE_SPACES.sub(" ", text)
    # Smart quotes → straight quotes
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    # Em/en dashes → hyphen (optional; remove if you need dash distinction)
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    return text


def clean_page_text(raw_text: str) -> str:
    """
    Apply the full cleaning pipeline to a single page's text.

    Steps applied (in order):
        1. Replace PDF ligatures
        2. Fix Unicode encoding artefacts
        3. Remove standalone page-number lines
        4. Remove known header/footer patterns
        5. Normalise whitespace

    Args:
        raw_text: Raw string from pdfplumber.

    Returns:
        Cleaned string ready for NLP processing.
    """
    text = _replace_ligatures(raw_text)
    text = _fix_encoding(text)
    text = _remove_page_numbers(text)
    text = _remove_headers_footers(text)
    text = _normalise_whitespace(text)
    return text


def clean_document(pages: List[dict]) -> dict:
    """
    Clean all pages extracted from a single PDF.

    Args:
        pages: List of page dicts from pdf_extractor (keys: 'page_num', 'text').

    Returns:
        Dict with:
            - 'cleaned_pages': list of dicts with 'page_num' and 'cleaned_text'
            - 'full_cleaned_text': all cleaned pages joined with newlines
    """
    cleaned_pages = []
    full_parts = []

    for page in pages:
        raw = page.get("text", "")
        cleaned = clean_page_text(raw) if raw else ""
        cleaned_pages.append({
            "page_num": page["page_num"],
            "cleaned_text": cleaned
        })
        if cleaned:
            full_parts.append(cleaned)

    return {
        "cleaned_pages": cleaned_pages,
        "full_cleaned_text": "\n\n".join(full_parts)
    }


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = """
                                    1
    IN THE HIGH COURT OF JUDICATURE AT MADRAS

    W.P. No. 12345/2023

    BEFORE THE HON'BLE MR. JUSTICE A.K. SINGH

    Petitioner  : Raman Kumar
    Respondent  : State of Tamil Nadu

    - 2 -

    JUDGMENT
    The petitioner has ﬁled this writ petition challenging the order dated
    15.03.2023 passed by the 1st respondent.
    """

    print(clean_page_text(sample))
