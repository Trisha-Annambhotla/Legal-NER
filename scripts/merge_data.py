# scripts/merge_data.py
"""
Run this every time you annotate a new document and add its examples
to master_annotations.py:

    python scripts/merge_data.py

It rebuilds train.spacy and dev.spacy from the full TRAIN_DATA.
Then re-run training — spaCy will resume from model-last if it exists.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.annotate import build_docbin
from training_data.master_annotations import TRAIN_DATA
import random

random.seed(42)
data = TRAIN_DATA.copy()
random.shuffle(data)

split    = int(len(data) * 0.8)
train    = data[:split]
dev      = data[split:]

os.makedirs("data", exist_ok=True)
build_docbin(train, "data/train.spacy", "train")
build_docbin(dev,   "data/dev.spacy",   "dev")

print(f"\nReady. Now run:")
print(f"  python -m spacy train configs/config.cfg --output models/ "
      f"--paths.train data/train.spacy --paths.dev data/dev.spacy --gpu-id 0")