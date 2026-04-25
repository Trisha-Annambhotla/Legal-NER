/**
 * services/api.js
 * ---------------
 * All API calls to the Legal-NER FastAPI backend (api_server.py).
 *
 * Set USE_MOCKS = true to run the frontend without a backend.
 * Set USE_MOCKS = false (default) to hit the real endpoints.
 *
 * Vite proxies /upload /ner /annotate /chat → http://localhost:8000
 * (configured in vite.config.js)
 */

import axios from 'axios'

// ── Toggle ─────────────────────────────────────────────────────
const USE_MOCKS = false   // ← true = run without backend

const client = axios.create({ baseURL: '' })

// ── Mock helpers ───────────────────────────────────────────────
const delay = (ms = 1200) => new Promise(r => setTimeout(r, ms))

const MOCK_TEXT = `RETAINER AGREEMENT

This Retainer Agreement ("Agreement") is entered into as of January 15, 2024, between
Apex Legal Group LLP ("Firm"), located at 400 Park Avenue, New York, NY 10022, and
TechNova Solutions Inc. ("Client"), a corporation organized under the laws of Delaware.

PARTIES
Attorney: Sarah M. Whitfield, Esq. (Bar No. 2019-CA-7741)
Client:   TechNova Solutions Inc., represented by Marcus Chen, CEO

SCOPE OF SERVICES
The Firm agrees to represent Client in the matter of alleged patent infringement
(Case No. CV-2024-00187, Southern District of New York) involving US Patent 10,892,345
held by DataCore Technologies LLC.

FEES AND PAYMENT
Monthly retainer: $15,000 USD, due on the 1st of each month.
Hourly rate: $450/hr for senior counsel, $280/hr for associates.

TERM
This Agreement commences January 15, 2024 and continues until December 31, 2024.`

const MOCK_ENTITIES = [
  { id: 1,  text: 'Apex Legal Group LLP',    type: 'ORG'      },
  { id: 2,  text: 'January 15, 2024',        type: 'DATE'     },
  { id: 3,  text: 'TechNova Solutions Inc.',  type: 'ORG'      },
  { id: 4,  text: 'New York, NY 10022',       type: 'LOCATION' },
  { id: 5,  text: 'Sarah M. Whitfield',       type: 'PERSON'   },
  { id: 6,  text: 'Marcus Chen',              type: 'PERSON'   },
  { id: 7,  text: '$15,000 USD',              type: 'MONEY'    },
  { id: 8,  text: 'US Patent 10,892,345',     type: 'LAW'      },
  { id: 9,  text: 'December 31, 2024',        type: 'DATE'     },
  { id: 10, text: 'DataCore Technologies',    type: 'UNKNOWN'  },
  { id: 11, text: 'CV-2024-00187',            type: 'UNKNOWN'  },
]

// ── 1. Upload ──────────────────────────────────────────────────
export async function uploadDocument(file) {
  if (USE_MOCKS) {
    await delay(1500)
    return { filename: file.name, total_pages: 4, text: MOCK_TEXT }
  }
  const form = new FormData()
  form.append('file', file)
  const { data } = await client.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// ── 2. NER ─────────────────────────────────────────────────────
export async function runNER(text) {
  if (USE_MOCKS) {
    await delay(1000)
    return { entities: MOCK_ENTITIES }
  }
  const { data } = await client.post('/ner', { text })
  return data
}

// ── 3. Annotate ────────────────────────────────────────────────
export async function submitAnnotations(annotations, filename = 'uploaded_document.pdf') {
  if (USE_MOCKS) {
    await delay(900)
    return {
      entities: annotations,
      saved: annotations.filter(a => a.type && a.type !== 'UNKNOWN').length,
    }
  }
  const { data } = await client.post('/annotate', { annotations, filename })
  return data
}

// ── 4. Chat ────────────────────────────────────────────────────
export async function sendChatMessage(query, caseContext = '', history = []) {
  if (USE_MOCKS) {
    await delay(1400)
    const lower = query.toLowerCase()
    let response = ''
    if (lower.includes('retainer') || lower.includes('fee'))
      response = 'The monthly retainer is $15,000 USD. Senior counsel is billed at $450/hr and associates at $280/hr.'
    else if (lower.includes('party') || lower.includes('parties') || lower.includes('who'))
      response = 'The agreement is between Apex Legal Group LLP (the Firm) and TechNova Solutions Inc. (the Client).'
    else if (lower.includes('date') || lower.includes('term'))
      response = 'The agreement runs from January 15, 2024 through December 31, 2024.'
    else
      response = `Based on the document context, the query "${query}" relates to the legal representation in a patent infringement matter.`
    return { response, hits: 3 }
  }

  const { data } = await client.post('/chat', {
    query,
    context: caseContext,
    history: history.map(m => ({ role: m.role, content: m.content })),
    top_k: 5,
  })
  return data
}
