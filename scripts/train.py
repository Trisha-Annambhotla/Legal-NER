# scripts/train.py
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG = ROOT / "configs" / "config.cfg"
OUTPUT = ROOT / "models"
DATA_DIR = ROOT / "data"


def train():
    if not CONFIG.exists():
        print(f"Config not found: {CONFIG}")
        sys.exit(1)
    if not (DATA_DIR / "train.spacy").exists():
        print("Training data not found. Run scripts/merge_data.py first.")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "spacy", "train",
        str(CONFIG),
        "--output", str(OUTPUT),
        "--paths.train", str(DATA_DIR / "train.spacy"),
        "--paths.dev", str(DATA_DIR / "dev.spacy"),
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    train()