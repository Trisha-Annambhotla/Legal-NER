"""
ner_pipeline.py
---------------
Custom spaCy NER pipeline for Indian High Court judgment text.

Priority:
  1. Load trained model from ./models/model-best
  2. Fallback to en_core_web_trf → en_core_web_sm

Optimized for:
  - Large legal documents
  - Faster batch processing
  - Clean + deduplicated output
"""

import re
from typing import Dict, List

try:
    import spacy
    _SPACY_AVAILABLE = True
except ImportError:
    _SPACY_AVAILABLE = False


# ── ENTITY LABELS (extend based on your training) ─────────────────────────────
RELEVANT_LABELS = {
    "PERSON", "ORG", "GPE", "DATE", "LAW",
    "NORP", "FAC", "LOC",
    # custom labels (if trained)
    "CASE_NUMBER", "COURT", "JUDGE", "ADVOCATE",
    "PETITIONER", "RESPONDENT", "ACT"
}


# ── GLOBAL MODEL ──────────────────────────────────────────────────────────────
_nlp = None


def _load_model():
    """
    Load spaCy model (priority: trained → pretrained fallback)
    """
    global _nlp
    if _nlp is not None:
        return _nlp

    if not _SPACY_AVAILABLE:
        raise ImportError("Run: pip install spacy")

    # 1️⃣ Try loading your trained model
    try:
        _nlp = spacy.load("models/model-best")
        print("[INFO] Loaded trained model: models/model-best")
        return _nlp
    except Exception:
        print("[WARNING] Trained model not found, falling back...")

    # 2️⃣ Fallback models
    for model_name in ("en_core_web_trf", "en_core_web_sm"):
        try:
            _nlp = spacy.load(model_name)
            print(f"[INFO] Loaded fallback model: {model_name}")
            return _nlp
        except OSError:
            continue

    raise OSError("No spaCy model found. Install one using spacy download.")


# ── CHUNKING ──────────────────────────────────────────────────────────────────

def _chunk_text(text: str, max_chars: int = 40000) -> List[str]:
    """
    Split large text into chunks safely.
    """
    if len(text) <= max_chars:
        return [text]

    chunks, current = [], []
    current_len = 0

    for para in text.split("\n\n"):
        para_len = len(para) + 2
        if current_len + para_len > max_chars and current:
            chunks.append("\n\n".join(current))
            current, current_len = [], 0
        current.append(para)
        current_len += para_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks


# ── CLEANING ──────────────────────────────────────────────────────────────────

def _clean_entity_text(text: str) -> str:
    """
    Clean entity text.
    """
    text = re.sub(r"^[\s,;.'\"-]+|[\s,;.'\"-]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _deduplicate(entities: List[str]) -> List[str]:
    """
    Case-insensitive deduplication.
    """
    seen = set()
    result = []

    for ent in entities:
        key = ent.lower()
        if key not in seen:
            seen.add(key)
            result.append(ent)

    return result


# ── CORE NER ──────────────────────────────────────────────────────────────────

def run_spacy_ner(text: str) -> Dict[str, List[str]]:
    """
    Run NER on full document.
    """
    nlp = _load_model()

    collected = {label: [] for label in RELEVANT_LABELS}

    chunks = _chunk_text(text)

    # 🚀 FAST processing
    docs = nlp.pipe(chunks, batch_size=8)

    for doc in docs:
        for ent in doc.ents:
            if ent.label_ in RELEVANT_LABELS:
                cleaned = _clean_entity_text(ent.text)

                # basic filtering
                if cleaned and len(cleaned) > 2:
                    collected[ent.label_].append(cleaned)

    return {k: _deduplicate(v) for k, v in collected.items()}


# ── PAGE LEVEL ────────────────────────────────────────────────────────────────

def run_spacy_ner_per_page(pages: List[Dict]) -> List[Dict]:
    """
    Page-wise NER.
    """
    results = []
    nlp = _load_model()

    texts = [p.get("cleaned_text", "") for p in pages]

    docs = nlp.pipe(texts, batch_size=8)

    for page, doc in zip(pages, docs):
        page_entities = {label: [] for label in RELEVANT_LABELS}

        for ent in doc.ents:
            if ent.label_ in RELEVANT_LABELS:
                cleaned = _clean_entity_text(ent.text)
                if cleaned:
                    page_entities[ent.label_].append(cleaned)

        results.append({
            "page_num": page["page_num"],
            "entities": {k: _deduplicate(v) for k, v in page_entities.items()}
        })

    return results


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    sample = """
    IN THE HIGH COURT OF MADRAS

    BEFORE THE HON'BLE JUSTICE A.K. SINGH

    Raman Kumar (Petitioner)
    vs
    State of Tamil Nadu (Respondent)

    Case No: W.P. 1234/2023

    Order dated 15 March 2023 under the Income Tax Act, 1961.
    """

    result = run_spacy_ner(sample)
    print(json.dumps(result, indent=2))