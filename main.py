"""
main.py
-------
End-to-end orchestrator for the Legal NLP Pipeline.

Usage
-----
# Single PDF:
    python main.py --pdf path/to/judgment.pdf

# All PDFs in a folder:
    python main.py --dir path/to/judgments/

# Non-interactive (batch) mode — only auto-applies stored feedback:
    python main.py --dir judgments/ --no-interactive

# Skip spaCy (faster, rule-based only):
    python main.py --pdf judgment.pdf --no-spacy

# Custom output folder and feedback store:
    python main.py --dir judgments/ --output results/ --feedback my_store.json

Outputs
-------
One JSON file per PDF in the output directory, plus a combined
`all_results.json` when processing a directory.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# ── Pipeline modules ──────────────────────────────────────────────────────────
from pdf_extractor import extract_text_from_pdf, extract_from_directory
from text_cleaner  import clean_document
from rule_engine   import run_rule_extraction
from hybrid_merger import merge_results
from feedback      import apply_feedback_loop, DEFAULT_STORE_PATH


# ── Optional spaCy import (graceful degradation) ─────────────────────────────
try:
    from ner_pipeline import run_spacy_ner
    _SPACY_READY = True
except Exception as _spacy_err:
    _SPACY_READY = False
    print(f"[WARNING] spaCy NER unavailable: {_spacy_err}")
    print("          Running in rule-based-only mode.")


# ── Per-document pipeline ─────────────────────────────────────────────────────

def process_pdf(
    pdf_path:        str,
    output_dir:      str      = "output",
    feedback_store:  str      = DEFAULT_STORE_PATH,
    interactive:     bool     = True,
    use_spacy:       bool     = True,
    save_json:       bool     = True,
) -> Dict:
    """
    Run the full pipeline on a single PDF.

    Steps:
        1. Extract text page by page
        2. Clean each page
        3. Run spaCy NER on full cleaned text (if available)
        4. Run rule-based extraction
        5. Merge results (hybrid)
        6. Apply feedback loop (prompt user for missing fields)
        7. Save structured JSON

    Args:
        pdf_path:       Path to the source PDF.
        output_dir:     Folder where JSON outputs are written.
        feedback_store: Path to the feedback JSON store.
        interactive:    Whether to prompt user for missing fields.
        use_spacy:      Whether to run spaCy NER.
        save_json:      Whether to write the output JSON file.

    Returns:
        The final structured result dict.
    """
    filename = os.path.basename(pdf_path)
    print(f"\n{'='*60}")
    print(f"  Processing: {filename}")
    print(f"{'='*60}")

    # ── Step 1: PDF Extraction ────────────────────────────────────────────
    print("[1/5] Extracting text from PDF...")
    raw_data = extract_text_from_pdf(pdf_path)
    print(f"      Pages found: {raw_data['total_pages']}")

    # ── Step 2: Text Cleaning ─────────────────────────────────────────────
    print("[2/5] Cleaning text...")
    clean_data = clean_document(raw_data["pages"])
    full_text  = clean_data["full_cleaned_text"]

    if not full_text.strip():
        print("[WARNING] No extractable text found. Possibly a scanned/image PDF.")
        return {"filename": filename, "error": "No text extracted"}

    # ── Step 3: spaCy NER ─────────────────────────────────────────────────
    spacy_entities: Dict = {}
    if use_spacy and _SPACY_READY:
        print("[3/5] Running spaCy NER...")
        try:
            spacy_entities = run_spacy_ner(full_text)
            total_ents = sum(len(v) for v in spacy_entities.values())
            print(f"      Entities found: {total_ents}")
        except Exception as e:
            print(f"[WARNING] spaCy NER failed: {e}. Falling back to rules only.")
    else:
        print("[3/5] spaCy NER skipped.")

    # ── Step 4: Rule-Based Extraction ────────────────────────────────────
    print("[4/5] Running rule-based extraction...")
    rule_data = run_rule_extraction(full_text)
    print(f"      Case numbers: {rule_data['case_numbers']}")
    print(f"      Judges:       {rule_data['judges']}")
    print(f"      Dates:        {rule_data['dates'][:3]}{'...' if len(rule_data['dates'])>3 else ''}")

    # ── Step 5: Hybrid Merge ──────────────────────────────────────────────
    print("[5/5] Merging results (hybrid)...")
    merged = merge_results(rule_data, spacy_entities)

    # ── Feedback Loop ─────────────────────────────────────────────────────
    merged = apply_feedback_loop(
        merged, filename,
        store_path=feedback_store,
        interactive=interactive
    )

    # ── Add metadata ──────────────────────────────────────────────────────
    merged["_meta"] = {
        "filename":        filename,
        "total_pages":     raw_data["total_pages"],
        "processed_at":    datetime.now().isoformat(),
        "spacy_used":      use_spacy and _SPACY_READY,
    }

    # ── Save JSON ─────────────────────────────────────────────────────────
    if save_json:
        os.makedirs(output_dir, exist_ok=True)
        stem = os.path.splitext(filename)[0]
        out_path = os.path.join(output_dir, f"{stem}.json")
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(merged, fh, indent=2, ensure_ascii=False)
        print(f"\n[✓] Output saved → {out_path}")

    return merged


# ── Batch processing ──────────────────────────────────────────────────────────

def process_directory(
    pdf_dir:        str,
    output_dir:     str  = "output",
    feedback_store: str  = DEFAULT_STORE_PATH,
    interactive:    bool = True,
    use_spacy:      bool = True,
) -> List[Dict]:
    """
    Run the pipeline on every PDF in a directory.

    Returns:
        List of result dicts (one per PDF).
    """
    pdf_files = sorted(
        f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")
    )

    if not pdf_files:
        print(f"[ERROR] No PDF files found in: {pdf_dir}")
        return []

    print(f"[INFO] Found {len(pdf_files)} PDF(s) in {pdf_dir}")
    all_results = []

    for filename in pdf_files:
        pdf_path = os.path.join(pdf_dir, filename)
        try:
            result = process_pdf(
                pdf_path,
                output_dir=output_dir,
                feedback_store=feedback_store,
                interactive=interactive,
                use_spacy=use_spacy,
            )
            all_results.append(result)
        except Exception as e:
            print(f"[ERROR] Failed on {filename}: {e}")
            all_results.append({"filename": filename, "error": str(e)})

    # Save combined results
    combined_path = os.path.join(output_dir, "all_results.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(combined_path, "w", encoding="utf-8") as fh:
        json.dump(all_results, fh, indent=2, ensure_ascii=False)
    print(f"\n[✓] Combined results saved → {combined_path}")

    return all_results


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Legal NLP Pipeline for Indian High Court Judgment PDFs"
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pdf", metavar="FILE",
                        help="Path to a single PDF file")
    source.add_argument("--dir", metavar="DIR",
                        help="Directory containing PDF files")

    parser.add_argument("--output",    default="output",
                        help="Output directory for JSON files (default: output/)")
    parser.add_argument("--feedback",  default=DEFAULT_STORE_PATH,
                        help=f"Feedback store path (default: {DEFAULT_STORE_PATH})")
    parser.add_argument("--no-interactive", action="store_true",
                        help="Disable interactive prompts (batch mode)")
    parser.add_argument("--no-spacy",       action="store_true",
                        help="Skip spaCy NER (rule-based only, faster)")

    return parser.parse_args()


def main():
    args = _parse_args()
    interactive = not args.no_interactive
    use_spacy   = not args.no_spacy

    if args.pdf:
        result = process_pdf(
            args.pdf,
            output_dir=args.output,
            feedback_store=args.feedback,
            interactive=interactive,
            use_spacy=use_spacy,
        )
        print("\n── Extracted Structure ──────────────────────────────────")
        # Print without the verbose extraction_sources
        display = {k: v for k, v in result.items() if k != "extraction_sources"}
        print(json.dumps(display, indent=2))

    elif args.dir:
        results = process_directory(
            args.dir,
            output_dir=args.output,
            feedback_store=args.feedback,
            interactive=interactive,
            use_spacy=use_spacy,
        )
        print(f"\n── Processed {len(results)} file(s) ──────────────────────")


if __name__ == "__main__":
    main()
