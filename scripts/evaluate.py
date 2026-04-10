# scripts/evaluate.py
"""
Run after training:
    python scripts/evaluate.py

This shows you EXACTLY which entity labels are working and which need more data.
"""

import spacy
from spacy.tokens import DocBin
from spacy.scorer import Scorer
from collections import defaultdict

def evaluate(model_path="models/model-best", dev_path="data/dev.spacy"):
    print(f"\nLoading model: {model_path}")
    nlp = spacy.load(model_path)
    
    print(f"Loading dev set: {dev_path}")
    db = DocBin().from_disk(dev_path)
    
    # Reconstruct docs with gold annotations
    gold_docs = list(db.get_docs(nlp.vocab))
    
    # Run model predictions
    pred_docs = []
    for gold_doc in gold_docs:
        pred_doc = nlp(gold_doc.text)
        pred_docs.append(pred_doc)
    
    # Score per entity
    scorer = Scorer()
    examples = []
    from spacy.training import Example
    for gold, pred in zip(gold_docs, pred_docs):
        examples.append(Example(pred, gold))
    
    scores = scorer.score(examples)
    
    ents_per_type = scores.get("ents_per_type", {})
    
    print(f"\n{'─'*65}")
    print(f"  {'LABEL':<28} {'P':>6} {'R':>6} {'F1':>6}  {'STATUS'}")
    print(f"{'─'*65}")
    
    results = []
    for label, metrics in sorted(ents_per_type.items()):
        p  = metrics.get("p", 0) * 100
        r  = metrics.get("r", 0) * 100
        f1 = metrics.get("f", 0) * 100
        
        if f1 >= 80:
            status = "GOOD"
        elif f1 >= 60:
            status = "NEEDS DATA"
        else:
            status = "FIX NEEDED"
        
        print(f"  {label:<28} {p:>5.1f}% {r:>5.1f}% {f1:>5.1f}%  {status}")
        results.append((label, f1))
    
    print(f"{'─'*65}")
    
    overall_f1 = scores.get("ents_f", 0) * 100
    overall_p  = scores.get("ents_p", 0) * 100
    overall_r  = scores.get("ents_r", 0) * 100
    print(f"  {'OVERALL':<28} {overall_p:>5.1f}% {overall_r:>5.1f}% {overall_f1:>5.1f}%")
    print(f"{'─'*65}\n")
    
    # Show which labels need more training data
    needs_work = [(l, f) for l, f in results if f < 80]
    if needs_work:
        print("Labels needing more annotated examples:")
        for label, f1 in sorted(needs_work, key=lambda x: x[1]):
            needed = max(0, int((80 - f1) * 0.5))
            print(f"  {label}: F1={f1:.1f}% — add ~{needed}+ more examples")
    else:
        print("All labels above 80% F1. Model is ready for production.")
    
    return scores

if __name__ == "__main__":
    evaluate()