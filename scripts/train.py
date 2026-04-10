# scripts/train.py
"""
Run with:
    python scripts/train.py

Or directly with spaCy CLI (preferred — more stable):
    python -m spacy train configs/config.cfg \
        --output models/ \
        --paths.train data/train.spacy \
        --paths.dev data/dev.spacy \
        --gpu-id 0
"""

import subprocess
import sys

cmd = [
    sys.executable, "-m", "spacy", "train",
    "configs/config.cfg",
    "--output", "models/",
    "--paths.train", "data/train.spacy",
    "--paths.dev",   "data/dev.spacy",
    "--gpu-id", "0",  # change to -1 for CPU
]

print("Starting fine-tuning of en_core_web_trf NER head...\n")
print("Watch for these columns in the output:")
print("  E    = epoch")
print("  #    = update step")
print("  LOSS NER  = training loss (should decrease)")
print("  ENTS_F    = F1 on dev set (should increase toward 1.0)")
print("  ENTS_P    = precision")
print("  ENTS_R    = recall")
print("  SCORE     = combined score used for model selection\n")
print("The BEST model is auto-saved to models/model-best/")
print("The LAST model is saved to models/model-last/\n")

subprocess.run(cmd)