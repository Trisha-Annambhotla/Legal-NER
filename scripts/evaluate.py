# scripts/evaluate.py
import spacy
from pathlib import Path

ROOT = Path(__file__).parent.parent
MODEL_PATH = ROOT / "models" / "model-best"
DEV_DATA = ROOT / "data" / "dev.spacy"


def evaluate():
    if not MODEL_PATH.exists():
        print(f"Model not found: {MODEL_PATH}. Train first.")
        return
    if not DEV_DATA.exists():
        print(f"Dev data not found: {DEV_DATA}")
        return

    nlp = spacy.load(str(MODEL_PATH))
    from spacy.tokens import DocBin
    import spacy.training

    db = DocBin().from_disk(str(DEV_DATA))
    examples = [
        spacy.training.Example(nlp(doc.text), doc)
        for doc in db.get_docs(nlp.vocab)
    ]
    scorer = nlp.evaluate(examples)
    print("=== Evaluation Results ===")
    for key, val in scorer.items():
        if isinstance(val, float):
            print(f"  {key}: {val:.4f}")


if __name__ == "__main__":
    evaluate()