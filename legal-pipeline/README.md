# LexPipeline — AI Legal Document Frontend

A minimal, clean React frontend for the AI-powered legal document analysis pipeline.

## Stack

- **React 18** + **Vite 5**
- **React Router v6** — client-side routing
- **Axios** — API calls
- **Pure CSS** — no UI library; custom design tokens

## Project Structure

```
legal-pipeline/
├── index.html
├── vite.config.js
├── package.json
└── src/
    ├── main.jsx                  # Entry point
    ├── App.jsx                   # Router setup
    ├── index.css                 # Global styles + design tokens
    ├── context/
    │   └── PipelineContext.jsx   # Global state (text, entities, chat)
    ├── services/
    │   └── api.js                # All API calls (+ mock fallbacks)
    ├── components/
    │   ├── Header.jsx            # Nav + step indicator
    │   ├── Loader.jsx            # Animated loading dots
    │   └── EntityTag.jsx         # Coloured entity type badge
    └── pages/
        ├── UploadPage.jsx        # Step 1 — PDF upload
        ├── NERPage.jsx           # Step 2 — Entity results + highlights
        ├── AnnotationPage.jsx    # Step 3 — Label unknown entities
        └── ChatPage.jsx          # Step 4 — RAG chat
```

## Setup

```bash
npm install
npm run dev       # → http://localhost:3000
```

## Mock vs Real Backend

The app ships with **mock API responses** enabled so you can run it immediately without a backend.

To switch to real API calls, open `src/services/api.js` and set:

```js
const USE_MOCKS = false
```

The Vite dev server proxies these routes to `http://localhost:8000`:

| Route      | Method | Purpose                          |
|------------|--------|----------------------------------|
| `/upload`  | POST   | PDF → extracted text             |
| `/ner`     | POST   | text → entity list               |
| `/annotate`| POST   | annotations → updated entity list|
| `/chat`    | POST   | query + context → AI response    |

If your backend runs on a different port, update `vite.config.js`.

## Application Flow

```
Upload PDF → NER Results → Annotate Unknowns → RAG Chat
    /              /ner         /annotate          /chat
```

State is held in `PipelineContext` and shared across all pages.
