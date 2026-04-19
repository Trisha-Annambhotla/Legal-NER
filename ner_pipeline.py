# ner_pipeline.py
import spacy
from pathlib import Path

MODEL_PATHS = [
    "models/model-best",
    "models/model-last",
]
SPACY_FALLBACK = ["en_core_web_trf", "en_core_web_lg", "en_core_web_sm"]

_nlp = None


def load_model():
    global _nlp
    if _nlp is not None:
        return _nlp

    for path in MODEL_PATHS:
        if Path(path).exists():
            try:
                _nlp = spacy.load(path)
                print(f"[NER] Loaded custom model: {path}")
                return _nlp
            except Exception as e:
                print(f"[NER] Failed to load {path}: {e}")

    for model_name in SPACY_FALLBACK:
        try:
            _nlp = spacy.load(model_name)
            print(f"[NER] Loaded spaCy model: {model_name}")
            return _nlp
        except OSError:
            continue

    raise RuntimeError(
        "No spaCy model found. Run: python -m spacy download en_core_web_sm"
    )


def run_ner(text: str) -> dict:
    nlp = load_model()
    doc = nlp(text)
    entities = {}
    for ent in doc.ents:
        entities.setdefault(ent.label_, [])
        if ent.text not in entities[ent.label_]:
            entities[ent.label_].append(ent.text)
    return entities