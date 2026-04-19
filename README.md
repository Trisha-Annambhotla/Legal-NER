# Legal-NER — Indian High Court Judgment Pipeline

A modular, hybrid (rule-based + spaCy NER + human feedback) pipeline that extracts structured legal information from High Court judgment PDFs.

---

## Project Structure

```
Legal-NER/
├── main.py                        # Primary CLI entry point / orchestrator
├── pipeline.py                    # Legacy pipeline runner (see note below)
├── pdf_extractor.py               # Step 1 — Extract text from PDFs (pdfplumber)
├── text_cleaner.py                # Step 2 — Clean & normalise text
├── ner_pipeline.py                # Step 3 — spaCy NER (en_core_web_trf)
├── rule_engine.py                 # Step 4 — Regex/rule-based extraction
├── hybrid_merger.py               # Step 5 — Merge & deduplicate both outputs
├── feedback.py                    # Step 6 — Human-in-the-loop feedback store
├── extract.py                     # Utility: converts annotations → spaCy DocBin + RAG data
├── requirements.txt
├── feedback_store.json            # Auto-created on first run
├── merged_ner_training_data.json  # Generated training data (do not edit manually)
├── output.txt                     # Sample/debug output (generated artifact)
│
├── configs/
│   └── config.cfg                 # spaCy training configuration
│
├── data/
│   ├── train.spacy                # Training corpus (spaCy binary format)
│   └── dev.spacy                  # Validation corpus
│
├── extracted_text/                # Pre-extracted judgment text files (used by extract.py)
│   ├── 1. A.P. Industrial Infrastructure Corpn. Ltd. v. S.N. Raj Kumar.txt
│   └── ...
│
├── index/
│   ├── legal_index.faiss          # FAISS vector index for semantic search
│   └── legal_index.chunks.json    # Chunk metadata for the FAISS index
│
├── models/
│   ├── model-best/                # Best checkpoint from spaCy training
│   └── model-last/                # Final checkpoint from spaCy training
│
├── scripts/
│   ├── annotate.py                # Annotation helper
│   ├── evaluate.py                # Model evaluation
│   ├── merge_data.py              # Merge multiple annotation sources
│   └── train.py                  # spaCy training script
│
└── output/                        # Auto-created; one JSON per processed PDF
```

> **Note on `pipeline.py` vs `main.py`:** `main.py` is the canonical entry point documented here. `pipeline.py` is a legacy runner retained for reference — prefer `main.py` for all new usage.

> **Note on `extract.py` vs `pdf_extractor.py`:** `pdf_extractor.py` is the pipeline module that extracts text from PDFs during inference. `extract.py` is a standalone utility that converts `master_annotations.json` + `extracted_text/` into `train.spacy` and `rag_data.json` for model training.

---

## Installation

### 1. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Download a spaCy model

For best accuracy (transformer-based, requires GPU or fast CPU):
```bash
python -m spacy download en_core_web_trf
```

Lighter alternative (CPU-friendly):
```bash
python -m spacy download en_core_web_sm
```

> The pipeline auto-detects whichever model is installed and falls back gracefully from `trf` → `lg` → `sm`.

---

## Usage

### Process a single PDF

```bash
python main.py --pdf /path/to/judgment.pdf
```

### Process all PDFs in a folder

```bash
python main.py --dir /path/to/judgments/
```

### Non-interactive (batch) mode — no user prompts

```bash
python main.py --dir judgments/ --no-interactive
```

### Rule-based only (skip spaCy — much faster)

```bash
python main.py --pdf judgment.pdf --no-spacy
```

### Custom output folder & feedback store

```bash
python main.py --dir judgments/ --output results/ --feedback my_store.json
```

---

## Feedback Loop

When a required field (`case_number`, `judge`, `petitioner`, `respondent`) is **missing or uncertain**, the pipeline will pause and prompt you:

```
[FEEDBACK] File : writ_petition_2023.pdf
           Field: judge
           Current value: <not detected>
  → Enter correct value for 'judge' (or press Enter to skip): A.K. Singh
           Saved: judge = A.K. Singh
[FEEDBACK] Store updated → feedback_store.json
```

On the **next run** of the same file, the correction is applied automatically with no prompt.

To add corrections programmatically:
```python
from feedback import add_manual_correction
add_manual_correction("writ_petition_2023.pdf", "judge", "Justice A.K. Singh")
```

---

## Output Format

Each PDF produces a JSON file in `output/`:

```json
{
  "case_number": "W.P. No. 12345/2023",
  "judge": "A.K. SINGH",
  "date": "15.03.2023",
  "petitioner": "Raman Kumar",
  "respondent": "State of Tamil Nadu",

  "entities": {
    "PERSON":       ["A.K. Singh", "Priya Menon", "Raman Kumar"],
    "ORG":          ["High Court of Madras", "State of Tamil Nadu"],
    "DATE":         ["15.03.2023", "10.01.2023", "15 March 2023"],
    "CASE_NUMBERS": ["W.P. No. 12345/2023"],
    "LAW":          ["Indian Penal Code, 1860", "Income Tax Act, 1961"],
    "GPE":          ["Tamil Nadu", "India"],
    "NORP":         []
  },

  "all_judges":    ["A.K. SINGH", "PRIYA MENON"],
  "acts_sections": ["Indian Penal Code, 1860"],

  "_meta": {
    "filename":     "writ_petition_2023.pdf",
    "total_pages":  12,
    "processed_at": "2024-03-15T10:30:00.123456",
    "spacy_used":   true
  }
}
```

---

## Supported Case Number Formats

| Format | Example |
|---|---|
| Writ Petition | W.P. No. 1234/2023 |
| Writ Petition (Civil) | W.P.(C) 5678/2022 |
| Criminal Appeal | Crl.A. No. 99/2021 |
| Civil Appeal | C.A. No. 456/2020 |
| Original Suit | O.S. No. 789/2019 |
| Special Leave Petition | S.L.P. (Civil) No. 100/2023 |
| Regular Second Appeal | R.S.A. No. 22/2022 |

---

## Semantic Search Index

The `index/` folder contains a FAISS vector index built over the extracted judgment texts. This enables similarity-based retrieval across the judgment corpus:

- `legal_index.faiss` — the vector index
- `legal_index.chunks.json` — chunk metadata (file ID, text snippet, position)

The index is built separately from the main pipeline. To rebuild it after adding new judgments, run the indexing script (or refer to the relevant module that writes to `index/`).

---

## Training a Custom NER Model

The `scripts/` folder contains the full training workflow:

**1. Annotate new data**
```bash
python scripts/annotate.py
```

**2. Merge annotation sources**
```bash
python scripts/merge_data.py
```

**3. Convert annotations to spaCy format**
```bash
python extract.py
# Produces: train.spacy, rag_data.json
```
Move the generated `.spacy` files to `data/` before training.

**4. Train**
```bash
python scripts/train.py
# or: python -m spacy train configs/config.cfg --output models/
```

**5. Evaluate**
```bash
python scripts/evaluate.py
```

Trained models are saved to `models/model-best/` and `models/model-last/`. The pipeline will automatically use `model-best` if present.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No text extracted` | PDF may be scanned. Try OCR tools like `pytesseract` or `pdf2image` first |
| spaCy model not found | Run `python -m spacy download en_core_web_sm` |
| `pdfplumber` not installed | Run `pip install pdfplumber` |
| Judge not detected | Use the feedback prompt or `add_manual_correction()` |
| FAISS index missing | Rebuild the index using the indexing script before running retrieval |

---

## .gitignore Recommendations

The following should be excluded from version control:

```
venv*/
__pycache__/
*.pyc
output/
output.txt
merged_ner_training_data.json
rag_data.json
```

> The `venv310/` directory is platform-specific and should not be committed. Only `requirements.txt` is needed for reproducibility.

---

## Extending the Pipeline

- **Add new entity types** — edit `rule_engine.py`: add a new regex and extractor function, then expose it in `run_rule_extraction()`.
- **Custom judge patterns** — extend `_RE_JUDGE` in `rule_engine.py`.
- **New court types** — the case-number regex in `rule_engine.py` is straightforward to extend with additional HC-specific patterns.
- **Fine-tune spaCy** — use the `scripts/` workflow above to build a corpus from your feedback store and fine-tune `en_core_web_trf`.
- **Expand the FAISS index** — add new judgment texts to `extracted_text/` and rebuild the index to include them in semantic search.
