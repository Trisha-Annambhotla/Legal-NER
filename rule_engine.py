"""
rule_engine.py
--------------
Rule-based (regex) extraction of structured legal entities from
Indian High Court judgment text.

Entities extracted:
  - Case numbers  (W.P., Crl.A., C.A., O.S., etc.)
  - Judge names   (JUSTICE / HON'BLE patterns)
  - Dates         (DD.MM.YYYY, DD/MM/YYYY, Month DD YYYY, etc.)
  - Petitioner    (first party listed under "Petitioner" heading)
  - Respondent    (first party listed under "Respondent" heading)
  - Acts/Sections (Section X of <Act>)
"""

import re
from typing import Dict, List, Optional


# ── Compiled regex patterns ───────────────────────────────────────────────────

# Case numbers: W.P. No. 1234/2020, Crl.A. No. 56/2019, W.P.(C) 789/2021, etc.
_RE_CASE_NUMBER = re.compile(
    r"\b("
    r"W\.P\.(?:\(C\)|\(MD\)|\(PIL\))?\s*No\.?\s*\d+\s*/\s*\d{4}"
    r"|Crl\.(?:A|M\.P|R\.C|O\.P)\.?\s*(?:No\.?)?\s*\d+\s*/\s*\d{4}"
    r"|C\.A\.?\s*No\.?\s*\d+\s*/\s*\d{4}"
    r"|O\.S\.?\s*No\.?\s*\d+\s*/\s*\d{4}"
    r"|A\.S\.?\s*No\.?\s*\d+\s*/\s*\d{4}"
    r"|S\.L\.P\.?\s*\(?(?:Civil|Crl)\)?\.?\s*No\.?\s*\d+\s*/\s*\d{4}"
    r"|R\.S\.A\.?\s*No\.?\s*\d+\s*/\s*\d{4}"
    r")",
    re.IGNORECASE
)

# Judge names: JUSTICE A.K. Singh / HON'BLE MR. JUSTICE FIRSTNAME LASTNAME
_RE_JUDGE = re.compile(
    r"(?:HON[''']?BLE\s+(?:MR\.|MRS\.|MS\.|DR\.)?\s*)?"
    r"(?:JUSTICE|J\.)\s+"
    r"([A-Z][A-Z.\s]{2,50}?)(?=\n|,|\band\b|&|\Z)",
    re.IGNORECASE
)

# Dates in various formats found in legal docs
_RE_DATE = re.compile(
    r"\b(?:"
    # DD.MM.YYYY or DD-MM-YYYY
    r"\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4}"
    r"|"
    # DD Month YYYY  /  Month DD, YYYY
    r"\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{4}"
    r"|"
    r"(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2},?\s+\d{4}"
    r")\b",
    re.IGNORECASE
)

# Petitioner block: "Petitioner : Name" or "Petitioner\nName"
_RE_PETITIONER = re.compile(
    r"Petitioner\s*[:\-–]\s*([^\n\r]+)"
    r"|Petitioner\s*\n\s*([A-Z][^\n\r]+)",
    re.IGNORECASE
)

# Respondent block
_RE_RESPONDENT = re.compile(
    r"Respondent\s*[:\-–]\s*([^\n\r]+)"
    r"|Respondent\s*\n\s*([A-Z][^\n\r]+)",
    re.IGNORECASE
)

# Acts and Sections: "Section 34 of the Indian Penal Code"
_RE_ACT_SECTION = re.compile(
    r"(?:Section|Sec\.|S\.)\s*\d+[A-Z]?\s+(?:of\s+the\s+)?"
    r"([A-Z][A-Za-z\s,()]+?(?:Act|Code|Rules|Regulations|Ordinance)(?:\s*,?\s*\d{4})?)",
    re.IGNORECASE
)


# ── Extraction helpers ────────────────────────────────────────────────────────

def extract_case_numbers(text: str) -> List[str]:
    """Return all unique case numbers found in the text."""
    matches = _RE_CASE_NUMBER.findall(text)
    # Normalise whitespace inside each match
    return list(dict.fromkeys(re.sub(r"\s+", " ", m).strip() for m in matches))


def extract_judges(text: str) -> List[str]:
    """Return all judge names found in the text."""
    raw_matches = _RE_JUDGE.findall(text)
    judges = []
    for m in raw_matches:
        name = re.sub(r"\s+", " ", m).strip().rstrip(".,;")
        if name and len(name) > 2:
            judges.append(name)
    return list(dict.fromkeys(judges))


def extract_dates(text: str) -> List[str]:
    """Return all date strings found in the text."""
    matches = _RE_DATE.findall(text)
    return list(dict.fromkeys(m.strip() for m in matches))


def _first_group(match: Optional[re.Match]) -> Optional[str]:
    """Return the first non-empty group from a match object."""
    if not match:
        return None
    for grp in match.groups():
        if grp and grp.strip():
            return grp.strip()
    return None


def extract_petitioner(text: str) -> Optional[str]:
    """Return the primary petitioner name."""
    m = _RE_PETITIONER.search(text)
    return _first_group(m)


def extract_respondent(text: str) -> Optional[str]:
    """Return the primary respondent name."""
    m = _RE_RESPONDENT.search(text)
    return _first_group(m)


def extract_acts_sections(text: str) -> List[str]:
    """Return all unique Act/Section references found in the text."""
    matches = _RE_ACT_SECTION.findall(text)
    return list(dict.fromkeys(re.sub(r"\s+", " ", m).strip() for m in matches))


# ── Main entry point ──────────────────────────────────────────────────────────

def run_rule_extraction(text: str) -> Dict:
    """
    Run all rule-based extractors on the given text.

    Args:
        text: Cleaned full text of a judgment.

    Returns:
        Dict with keys: case_numbers, judges, dates,
                        petitioner, respondent, acts_sections.
    """
    return {
        "case_numbers": extract_case_numbers(text),
        "judges":       extract_judges(text),
        "dates":        extract_dates(text),
        "petitioner":   extract_petitioner(text),
        "respondent":   extract_respondent(text),
        "acts_sections": extract_acts_sections(text),
    }


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = """
    IN THE HIGH COURT OF JUDICATURE AT MADRAS

    W.P. No. 12345/2023

    BEFORE THE HON'BLE MR. JUSTICE A.K. SINGH AND
    THE HON'BLE MRS. JUSTICE PRIYA MENON

    Petitioner  : Raman Kumar
    Respondent  : State of Tamil Nadu

    ORDER dated 15.03.2023

    This writ petition was filed under Section 226 of the Constitution of India
    read with Section 34 of the Indian Penal Code, 1860.
    """

    import json
    result = run_rule_extraction(sample)
    print(json.dumps(result, indent=2))
