"""
api_server.py
-------------
FastAPI server that exposes the Legal-NER pipeline as REST endpoints
consumed by the React frontend.

Place this file in the root of your Legal-NER/ directory (same level as
main.py, pipeline.py, etc.) and run:

    uvicorn api_server:app --reload --port 8000

Routes
------
POST /upload    — PDF upload → extracted + cleaned text
POST /ner       — text → hybrid NER entity list
POST /annotate  — user annotations → persisted to feedback_store.json
POST /chat      — RAG query → retrieved context answer
"""

import os
import json
import tempfile
import traceback
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Pipeline imports ──────────────────────────────────────────────────────────
from pdf_extractor import extract_text_from_pdf
from text_cleaner  import clean_document
from rule_engine   import run_rule_extraction
from hybrid_merger import merge_results
from feedback      import (
    load_feedback_store,
    save_feedback_store,
    add_manual_correction,
    DEFAULT_STORE_PATH,
)
# FAISS RAG retriever — optional, fails gracefully if index is incompatible
try:
    from pipeline import retrieve as _faiss_retrieve
    _FAISS_READY = True
except Exception as e:
    _FAISS_READY = False
    print(f"[WARNING] FAISS pipeline unavailable: {e}")

# Optional spaCy NER
try:
    from ner_pipeline import run_ner as run_spacy_ner
    _SPACY_READY = True
except Exception as e:
    _SPACY_READY = False
    print(f"[WARNING] spaCy NER unavailable: {e}. Rule-based only.")


# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Legal-NER API", version="1.0.0")

# Allow the React dev server (port 3000) to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class NERRequest(BaseModel):
    text: str

class AnnotationItem(BaseModel):
    id: int
    text: str
    type: str           # e.g. "PERSON", "ORG", "DATE", "LAW", "UNKNOWN"

class AnnotateRequest(BaseModel):
    annotations: List[AnnotationItem]
    filename: Optional[str] = "uploaded_document.pdf"

class ChatMessage(BaseModel):
    role: str           # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    query: str
    context: Optional[str] = ""   # full extracted text (for local context)
    history: Optional[List[ChatMessage]] = []
    top_k: Optional[int] = 5


# ── Helpers ───────────────────────────────────────────────────────────────────

def _entities_to_list(spacy_ents: Dict[str, List[str]], rule_merged: Dict) -> List[Dict]:
    """
    Convert the hybrid merged dict into a flat entity list the frontend expects.

    Frontend entity shape:
        { id, text, type }

    We normalise spaCy label names → frontend type names where needed.
    """
    LABEL_MAP = {
        # spaCy / custom model labels → frontend labels
        "PERSON":   "PERSON",
        "PER":      "PERSON",
        "ORG":      "ORG",
        "GPE":      "LOCATION",
        "LOC":      "LOCATION",
        "DATE":     "DATE",
        "MONEY":    "MONEY",
        "LAW":      "LAW",
        "CARDINAL": "OTHER",
        "ORDINAL":  "OTHER",
        "NORP":     "ORG",
    }

    seen  = set()
    items = []
    eid   = 1

    # 1. Entities from spaCy NER
    for label, texts in spacy_ents.items():
        mapped = LABEL_MAP.get(label, "UNKNOWN")
        for text in texts:
            key = (text.strip().lower(), mapped)
            if key not in seen and text.strip():
                seen.add(key)
                items.append({"id": eid, "text": text.strip(), "type": mapped})
                eid += 1

    # 2. Rule-engine fields not already present
    rule_fields = {
        "case_numbers": "LAW",
        "judges":       "PERSON",
        "petitioners":  "PERSON",
        "respondents":  "PERSON",
        "dates":        "DATE",
        "acts":         "LAW",
        "citations":    "LAW",
    }

    for field, ftype in rule_fields.items():
        for text in rule_merged.get(field, []):
            key = (text.strip().lower(), ftype)
            if key not in seen and text.strip():
                seen.add(key)
                items.append({"id": eid, "text": text.strip(), "type": ftype})
                eid += 1

    # 3. Plain scalar fields (judge, petitioner, respondent, case_number)
    scalar_fields = {
        "judge":       "PERSON",
        "petitioner":  "PERSON",
        "respondent":  "PERSON",
        "case_number": "LAW",
    }
    for field, ftype in scalar_fields.items():
        val = rule_merged.get(field)
        if val and isinstance(val, str):
            key = (val.strip().lower(), ftype)
            if key not in seen:
                seen.add(key)
                items.append({"id": eid, "text": val.strip(), "type": ftype})
                eid += 1

    return items


# ── Route 1: Upload ───────────────────────────────────────────────────────────

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Accepts a PDF, extracts + cleans text, returns it to the frontend.
    Does NOT run NER here — that is a separate /ner call.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Save upload to a temp file so pdfplumber can open it
    try:
        suffix = f"_{file.filename}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        raw   = extract_text_from_pdf(tmp_path)
        clean = clean_document(raw["pages"])

        return {
            "filename":    file.filename,
            "total_pages": raw["total_pages"],
            "text":        clean["full_cleaned_text"],
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── Route 2: NER ──────────────────────────────────────────────────────────────

@app.post("/ner")
async def run_ner_endpoint(req: NERRequest):
    """
    Runs hybrid NER (spaCy + rule engine) on the provided text.
    Returns a flat entity list for the frontend.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty.")

    try:
        # spaCy NER (returns dict: label → [texts])
        spacy_ents: Dict = {}
        if _SPACY_READY:
            spacy_ents = run_spacy_ner(req.text)

        # Rule-based extraction
        rule_data = run_rule_extraction(req.text)

        # Hybrid merge
        merged = merge_results(rule_data, spacy_ents)

        entities = _entities_to_list(spacy_ents, merged)

        return {"entities": entities}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Route 3: Annotate ─────────────────────────────────────────────────────────

@app.post("/annotate")
async def annotate_entities(req: AnnotateRequest):
    """
    Persists user-supplied labels to feedback_store.json via
    add_manual_correction(), then returns the updated entity list.
    Only annotations with a non-UNKNOWN type are stored.
    """
    try:
        for ann in req.annotations:
            if ann.type and ann.type not in ("UNKNOWN", ""):
                add_manual_correction(
                    filename=req.filename,
                    field=ann.text,          # use entity text as the field key
                    value=ann.type,
                    store_path=DEFAULT_STORE_PATH,
                )

        # Return the submitted list with types applied (frontend merges these)
        updated = [
            {"id": ann.id, "text": ann.text, "type": ann.type or "UNKNOWN"}
            for ann in req.annotations
        ]
        return {"entities": updated, "saved": len(updated)}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Route 4: Chat (RAG) ───────────────────────────────────────────────────────

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """
    RAG-based Q&A using the FAISS index built from the extracted_text/ corpus.

    Strategy:
      1. Retrieve top_k relevant chunks from the FAISS index.
      2. Also do a local keyword search in the uploaded document context
         (req.context) as a fallback when no indexed chunks match.
      3. Return a structured answer with source metadata.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty.")

    try:
        context_parts = []

        # ── 1. FAISS retrieval (optional) ─────────────────────────────────
        hits = 0
        if _FAISS_READY:
            try:
                faiss_hits = _faiss_retrieve(req.query, top_k=req.top_k)
                hits = len(faiss_hits)
                for hit in faiss_hits:
                    meta = hit.get("meta", {})
                    case = meta.get("case_name", "Unknown case")
                    excerpt = hit.get("text", "")[:400].strip()
                    context_parts.append(f"[Case: {case}]\n{excerpt}")
            except Exception as faiss_err:
                print(f"[WARNING] FAISS search failed: {faiss_err}. Using local context only.")

        # ── 2. Local document context (always runs) ───────────────────────
        if req.context:
            # Simple keyword scan: pull 300-char windows around query terms
            query_words = [w for w in req.query.lower().split() if len(w) > 3]
            text_lower  = req.context.lower()
            for word in query_words[:3]:
                idx = text_lower.find(word)
                if idx != -1:
                    start   = max(0, idx - 100)
                    end     = min(len(req.context), idx + 300)
                    snippet = req.context[start:end].strip()
                    context_parts.append(f"[Uploaded document]\n{snippet}")
                    break   # one local snippet is enough

        # ── 3. Build answer ───────────────────────────────────────────────
        if context_parts:
            context_block = "\n\n---\n\n".join(context_parts[:4])
            response = (
                f"Based on the legal corpus, here is what I found for "
                f'"{req.query}":\n\n{context_block}'
            )
        else:
            response = (
                f'No directly relevant passages found in the index for "{req.query}". '
                "Try rephrasing with specific legal terms, party names, or case numbers."
            )

        return {"response": response, "hits": hits}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status":      "ok",
        "spacy_ready": _SPACY_READY,
        "faiss_index": os.path.exists("index/legal_index.faiss"),
    }