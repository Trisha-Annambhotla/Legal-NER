# scripts/annotate.py
import spacy
from spacy.tokens import DocBin
from collections import Counter
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from training_data.master_annotations import TRAIN_DATA

def build_docbin(data, output_path, split_name="train"):
    nlp = spacy.blank("en")
    db = DocBin()
    
    label_counter = Counter()
    skipped = 0
    total_spans = 0

    for i, (text, annotations) in enumerate(data):
        doc = nlp.make_doc(text)
        ents = []
        
        for start, end, label in annotations.get("entities", []):
            span = doc.char_span(start, end, label=label)
            if span is None:
                # Alignment failed — show exactly what went wrong
                snippet = text[max(0, start-5):end+5]
                print(f"  [ALIGN FAIL #{i}] '{text[start:end]}' ({label})")
                print(f"    Context: '...{snippet}...'")
                skipped += 1
                continue
            ents.append(span)
            label_counter[label] += 1
            total_spans += 1

        # SpaCy will reject overlapping ents — filter them out with a warning
        try:
            doc.ents = ents
        except Exception as e:
            # Use spacy's utility to remove overlaps (keeps longest span)
            from spacy.util import filter_spans
            doc.ents = filter_spans(ents)
            print(f"  [OVERLAP #{i}] Resolved overlap in: '{text[:60]}...'")

        db.add(doc)

    db.to_disk(output_path)
    
    print(f"\n{'='*50}")
    print(f"  {split_name.upper()} SET BUILT")
    print(f"  Documents : {len(data)}")
    print(f"  Spans     : {total_spans}")
    print(f"  Skipped   : {skipped} (alignment failures)")
    print(f"  Output    : {output_path}")
    print(f"\n  Per-label counts:")
    for label, count in sorted(label_counter.items()):
        bar = "█" * min(count, 30)
        print(f"    {label:<25} {bar} {count}")
    print(f"{'='*50}\n")
    
    return label_counter

if __name__ == "__main__":
    import random
    random.seed(42)
    random.shuffle(TRAIN_DATA)
    
    split = int(len(TRAIN_DATA) * 0.8)
    train_data = TRAIN_DATA[:split]
    dev_data   = TRAIN_DATA[split:]
    
    os.makedirs("data", exist_ok=True)
    build_docbin(train_data, "data/train.spacy", "train")
    build_docbin(dev_data,   "data/dev.spacy",   "dev")
    
    print(f"Train: {len(train_data)} | Dev: {len(dev_data)}")