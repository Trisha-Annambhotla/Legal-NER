# Integration Guide — Legal-NER Backend ↔ React Frontend

## Directory Layout After Integration

```
Legal-NER/                      ← your existing backend
├── api_server.py               ← NEW: FastAPI server (copy here)
├── requirements_api.txt        ← NEW: extra pip packages
├── main.py                     ← unchanged
├── pipeline.py                 ← unchanged
├── ner_pipeline.py             ← unchanged
├── pdf_extractor.py            ← unchanged
├── feedback.py                 ← unchanged
├── ...
└── legal-pipeline/             ← NEW: React frontend (copy here)
    ├── package.json
    ├── vite.config.js
    └── src/
        └── services/api.js     ← already wired to real endpoints
```

---

## Step 1 — Copy files into Legal-NER/

```bash
# Copy the FastAPI server into the backend root
cp api_server.py  Legal-NER/

# Copy the React app into the backend root (or anywhere convenient)
cp -r legal-pipeline/  Legal-NER/
```

---

## Step 2 — Install backend API dependencies

```bash
cd Legal-NER/
pip install -r requirements_api.txt
```

> Your existing requirements (pdfplumber, spacy, sentence-transformers,
> faiss-cpu) must already be installed. If not: `pip install -r requirements.txt`

---

## Step 3 — Start the FastAPI backend

```bash
cd Legal-NER/
uvicorn api_server:app --reload --port 8000
```

Verify it's running:
```
http://localhost:8000/health
```
Expected response:
```json
{ "status": "ok", "spacy_ready": true, "faiss_index": true }
```

If `spacy_ready` is false, your custom model at `models/model-best` failed to
load. The server still works — it falls back to rule-based extraction only.

If `faiss_index` is false, `index/legal_index.faiss` is missing. The `/chat`
route will still work using local document context only.

---

## Step 4 — Start the React frontend

```bash
cd Legal-NER/legal-pipeline/
npm install
npm run dev       # → http://localhost:3000
```

The Vite dev server proxies all API calls:

| Frontend call  | Proxied to                    |
|----------------|-------------------------------|
| POST /upload   | http://localhost:8000/upload  |
| POST /ner      | http://localhost:8000/ner     |
| POST /annotate | http://localhost:8000/annotate|
| POST /chat     | http://localhost:8000/chat    |

---

## API Contract (what the frontend sends / receives)

### POST /upload
```
Request : multipart/form-data  { file: <PDF> }
Response: { filename, total_pages, text }
```
Calls: `extract_text_from_pdf()` → `clean_document()`

### POST /ner
```
Request : { text: string }
Response: { entities: [{ id, text, type }, ...] }
```
Types: `PERSON | ORG | LOCATION | DATE | MONEY | LAW | UNKNOWN`  
Calls: `run_ner()` (spaCy) + `run_rule_extraction()` + `merge_results()`

### POST /annotate
```
Request : { annotations: [{ id, text, type }], filename?: string }
Response: { entities: [...], saved: number }
```
Calls: `add_manual_correction()` → writes to `feedback_store.json`  
Only entities where `type !== "UNKNOWN"` are persisted.

### POST /chat
```
Request : { query, context?, history?, top_k? }
Response: { response: string, hits: number }
```
Calls: `retrieve()` (FAISS, all-MiniLM-L6-v2)  
Falls back to keyword scan of the uploaded document `context` string.

---

## Switching Mocks On/Off

`legal-pipeline/src/services/api.js` — line 13:

```js
const USE_MOCKS = false   // false = real backend (default)
                          // true  = mock responses, no backend needed
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| CORS error in browser | Make sure `uvicorn` is on port 8000 and Vite on 3000 |
| `spacy_ready: false` | Run `python -m spacy download en_core_web_sm` |
| `/chat` returns no hits | Check `index/legal_index.faiss` exists; rebuild index if missing |
| Upload fails with 500 | Check uvicorn terminal — usually a pdfplumber or temp-file issue |
| `module not found` on import | Run from `Legal-NER/` root, not a subdirectory |
