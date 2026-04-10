"""
feedback.py
-----------
Human-in-the-loop feedback system for the Legal NLP pipeline.

Workflow:
  1. If an important field (judge, petitioner, respondent, case_number) is
     missing or uncertain, prompt the user to supply the correct value.
  2. Store all corrections in a JSON feedback store (feedback_store.json).
  3. On subsequent runs, auto-apply stored corrections before prompting.

The feedback store maps a (filename, field) key → corrected value so that
identical documents never prompt twice for the same field.
"""

import json
import os
import re
from typing import Any, Dict, Optional

# ── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_STORE_PATH = "feedback_store.json"

# Fields the pipeline will ask about if empty/uncertain
REQUIRED_FIELDS = ["case_number", "judge", "petitioner", "respondent"]


# ── Store I/O ─────────────────────────────────────────────────────────────────

def load_feedback_store(store_path: str = DEFAULT_STORE_PATH) -> Dict:
    """Load the persisted feedback store from disk."""
    if os.path.exists(store_path):
        with open(store_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_feedback_store(store: Dict, store_path: str = DEFAULT_STORE_PATH) -> None:
    """Persist the feedback store to disk."""
    with open(store_path, "w", encoding="utf-8") as fh:
        json.dump(store, fh, indent=2, ensure_ascii=False)


def _make_key(filename: str, field: str) -> str:
    """Create a stable dict key from filename + field."""
    # Normalise filename (strip path, lowercase)
    base = os.path.basename(filename).lower()
    return f"{base}::{field}"


# ── Value quality check ───────────────────────────────────────────────────────

def _is_missing(value: Any) -> bool:
    """Return True if a value is absent or looks like a placeholder."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def _is_uncertain(value: Any, field: str) -> bool:
    """
    Heuristic: flag value as uncertain if it looks implausible.
    E.g. a 'judge' that contains only digits, or a case_number
    without the expected slash-year pattern.
    """
    if _is_missing(value):
        return True

    val_str = str(value).strip() if not isinstance(value, list) else value[0] if value else ""

    if field == "case_number":
        # Must contain a year-slash pattern
        return not re.search(r"\d+\s*/\s*\d{4}", val_str)

    if field == "judge":
        # Should contain at least two alphabetic words
        words = re.findall(r"[A-Za-z]{2,}", val_str)
        return len(words) < 2

    return False


# ── Interactive prompt ────────────────────────────────────────────────────────

def _prompt_user(field: str, current_value: Any, filename: str) -> Optional[str]:
    """
    Ask the user to supply or correct a field value.
    Returns the user's input, or None if they skip.
    """
    display_val = current_value if not _is_missing(current_value) else "<not detected>"
    print(f"\n[FEEDBACK] File : {filename}")
    print(f"           Field: {field}")
    print(f"           Current value: {display_val}")
    user_input = input(
        f"  → Enter correct value for '{field}' (or press Enter to skip): "
    ).strip()
    return user_input if user_input else None


# ── Main feedback loop ────────────────────────────────────────────────────────

def apply_feedback_loop(
    result: Dict,
    filename: str,
    store_path: str = DEFAULT_STORE_PATH,
    interactive: bool = True,
) -> Dict:
    """
    Check required fields; prompt user for corrections; persist feedback.

    Args:
        result:      The structured extraction dict (will be mutated in-place).
        filename:    Source PDF filename (used as part of the store key).
        store_path:  Path to the JSON feedback store.
        interactive: If False, only apply stored feedback (no prompting).
                     Useful for batch/automated runs.

    Returns:
        Updated result dict with corrections applied.
    """
    store = load_feedback_store(store_path)
    store_changed = False

    for field in REQUIRED_FIELDS:
        key = _make_key(filename, field)
        current = result.get(field)

        # 1. Apply stored correction if available
        if key in store:
            stored_val = store[key]
            print(f"[FEEDBACK] Auto-applying stored correction for '{field}': {stored_val}")
            result[field] = stored_val
            continue

        # 2. If value is missing or uncertain, optionally prompt
        if _is_missing(current) or _is_uncertain(current, field):
            if not interactive:
                print(f"[FEEDBACK] '{field}' is missing/uncertain but interactive mode is off.")
                continue

            correction = _prompt_user(field, current, filename)
            if correction:
                result[field] = correction
                store[key] = correction
                store_changed = True
                print(f"           Saved: {field} = {correction}")

    if store_changed:
        save_feedback_store(store, store_path)
        print(f"[FEEDBACK] Store updated → {store_path}")

    return result


def add_manual_correction(
    filename: str,
    field: str,
    value: str,
    store_path: str = DEFAULT_STORE_PATH,
) -> None:
    """
    Programmatically add a correction without an interactive prompt.
    Useful for bulk corrections or testing.

    Args:
        filename: PDF filename.
        field:    Field name (e.g. 'judge').
        value:    Correct value to store.
        store_path: Path to the feedback store.
    """
    store = load_feedback_store(store_path)
    key = _make_key(filename, field)
    store[key] = value
    save_feedback_store(store, store_path)
    print(f"[FEEDBACK] Manual correction saved: {filename} | {field} = {value}")


def view_feedback_store(store_path: str = DEFAULT_STORE_PATH) -> None:
    """Pretty-print the current feedback store."""
    store = load_feedback_store(store_path)
    if not store:
        print("[FEEDBACK] Store is empty.")
        return
    print(f"\n[FEEDBACK] Store ({store_path}):")
    for key, val in store.items():
        print(f"  {key:60s} → {val}")


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Simulate a result with a missing judge
    test_result = {
        "case_number": "W.P. No. 123/2023",
        "judge": None,
        "petitioner": "Raman Kumar",
        "respondent": "State of Tamil Nadu",
    }

    updated = apply_feedback_loop(test_result, "sample_judgment.pdf", interactive=True)
    print("\nFinal result:", json.dumps(updated, indent=2))
