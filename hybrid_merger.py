"""
hybrid_merger.py
----------------
Merges spaCy NER output with rule-based extraction results into a single
coherent, deduplicated structured record.

Merge strategy
--------------
* Rule-based values win for highly structured fields:
    case_number, judge, petitioner, respondent, dates
  because regex patterns are carefully crafted for HC judgment formats.
* spaCy values are used as fallbacks and to enrich the free-form
  entity buckets (PERSON, ORG, GPE, LAW, etc.).
* Duplicates are removed across both sources (case-insensitive).
"""

import re
from typing import Any, Dict, List, Optional


# ── Utility helpers ───────────────────────────────────────────────────────────

def _normalise(text: str) -> str:
    """Collapse whitespace and strip edges."""
    return re.sub(r"\s+", " ", text).strip()


def _dedup_list(items: List[str]) -> List[str]:
    """Remove case-insensitive duplicates, preserving first-seen order."""
    seen, out = set(), []
    for item in items:
        key = _normalise(item).lower()
        if key and key not in seen:
            seen.add(key)
            out.append(_normalise(item))
    return out


def _first_nonempty(*values: Optional[Any]) -> Optional[str]:
    """Return the first non-None, non-empty string from the provided values."""
    for v in values:
        if v and str(v).strip():
            return _normalise(str(v))
    return None


# ── Merge functions ───────────────────────────────────────────────────────────

def _merge_persons(rule_judges: List[str], spacy_persons: List[str]) -> List[str]:
    """
    Combine rule-based judge names with spaCy PERSON entities.
    Rule-based names come first (higher confidence).
    """
    combined = list(rule_judges) + [
        p for p in spacy_persons
        if p.lower() not in {j.lower() for j in rule_judges}
    ]
    return _dedup_list(combined)


def _merge_dates(rule_dates: List[str], spacy_dates: List[str]) -> List[str]:
    """Merge date lists, rule-based first."""
    return _dedup_list(rule_dates + spacy_dates)


def _merge_orgs(spacy_orgs: List[str]) -> List[str]:
    """Return deduplicated ORG list from spaCy."""
    return _dedup_list(spacy_orgs)


# ── Primary merge function ────────────────────────────────────────────────────

def merge_results(
    rule_data: Dict,
    spacy_data: Dict,
) -> Dict:
    """
    Merge rule-based and spaCy extraction results into a unified output dict.

    Args:
        rule_data:  Output from rule_engine.run_rule_extraction().
                    Keys: case_numbers, judges, dates, petitioner,
                          respondent, acts_sections.
        spacy_data: Output from ner_pipeline.run_spacy_ner().
                    Keys: PERSON, ORG, GPE, DATE, LAW, NORP, FAC, LOC.

    Returns:
        Merged structured dict ready for JSON output.
    """

    # ── Structured / primary fields (rule-based wins) ─────────────────────
    case_number = _first_nonempty(
        rule_data.get("case_numbers", [None])[0]
        if rule_data.get("case_numbers") else None
    )

    judge = _first_nonempty(
        rule_data.get("judges", [None])[0]
        if rule_data.get("judges") else None,
        spacy_data.get("PERSON", [None])[0]
        if spacy_data.get("PERSON") else None
    )

    petitioner = _first_nonempty(rule_data.get("petitioner"))
    respondent  = _first_nonempty(rule_data.get("respondent"))

    # Primary date = first rule-based date (most likely the judgment date)
    primary_date = _first_nonempty(
        rule_data.get("dates", [None])[0]
        if rule_data.get("dates") else None,
        spacy_data.get("DATE", [None])[0]
        if spacy_data.get("DATE") else None
    )

    # ── Enriched entity buckets ───────────────────────────────────────────
    all_persons = _merge_persons(
        rule_data.get("judges", []),
        spacy_data.get("PERSON", [])
    )

    all_dates = _merge_dates(
        rule_data.get("dates", []),
        spacy_data.get("DATE", [])
    )

    all_orgs = _merge_orgs(spacy_data.get("ORG", []))

    all_case_numbers = _dedup_list(rule_data.get("case_numbers", []))

    laws_from_spacy = _dedup_list(spacy_data.get("LAW", []))
    laws_from_rules = _dedup_list(rule_data.get("acts_sections", []))
    all_laws = _dedup_list(laws_from_rules + laws_from_spacy)

    # ── Assemble final output structure ───────────────────────────────────
    return {
        # Primary structured fields
        "case_number": case_number,
        "judge":       judge,
        "date":        primary_date,
        "petitioner":  petitioner,
        "respondent":  respondent,

        # Enriched entity buckets
        "entities": {
            "PERSON":       all_persons,
            "ORG":          all_orgs,
            "DATE":         all_dates,
            "CASE_NUMBERS": all_case_numbers,
            "LAW":          all_laws,
            "GPE":          _dedup_list(spacy_data.get("GPE", [])),
            "NORP":         _dedup_list(spacy_data.get("NORP", [])),
        },

        # Metadata
        "all_judges":        _dedup_list(rule_data.get("judges", [])),
        "acts_sections":     all_laws,
        "extraction_sources": {
            "rule_based": {
                "case_numbers": rule_data.get("case_numbers", []),
                "judges":       rule_data.get("judges", []),
                "dates":        rule_data.get("dates", []),
                "petitioner":   rule_data.get("petitioner"),
                "respondent":   rule_data.get("respondent"),
            },
            "spacy": spacy_data,
        },
    }


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    rule = {
        "case_numbers": ["W.P. No. 12345/2023"],
        "judges": ["A.K. SINGH", "PRIYA MENON"],
        "dates": ["15.03.2023", "10.01.2023"],
        "petitioner": "Raman Kumar",
        "respondent": "State of Tamil Nadu",
        "acts_sections": ["Indian Penal Code, 1860"],
    }

    spacy = {
        "PERSON": ["Raman Kumar", "A.K. Singh", "Advocate General"],
        "ORG":    ["High Court of Madras", "State of Tamil Nadu"],
        "DATE":   ["15 March 2023", "15.03.2023"],
        "LAW":    ["Income Tax Act, 1961"],
        "GPE":    ["Tamil Nadu", "India"],
        "NORP":   [],
        "FAC":    [],
        "LOC":    [],
    }

    merged = merge_results(rule, spacy)
    print(json.dumps(merged, indent=2))
