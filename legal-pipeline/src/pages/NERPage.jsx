import React, { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePipeline } from '../context/PipelineContext.jsx'
import EntityTag from '../components/EntityTag.jsx'

// Group entities by type for the summary panel
function groupBy(arr, key) {
  return arr.reduce((acc, item) => {
    const k = item[key] || 'UNKNOWN'
    ;(acc[k] = acc[k] || []).push(item)
    return acc
  }, {})
}

// Simple text highlighter — marks entity spans inline
function HighlightedText({ text, entities }) {
  if (!text) return null

  // Build a flat list of [start, end, type] sorted by start
  // Using string matching (no char offsets from mock) — match by text value
  const segments = []
  let remaining  = text

  // Build matches via String.indexOf for each entity text
  const matches = []
  entities.forEach(ent => {
    let idx = 0
    while (true) {
      const pos = remaining.indexOf(ent.text, idx)
      if (pos === -1) break
      matches.push({ start: pos, end: pos + ent.text.length, type: ent.type, label: ent.text })
      idx = pos + 1
    }
  })

  // Sort by start, resolve overlaps (keep longest)
  matches.sort((a, b) => a.start - b.start || b.end - a.end)
  const resolved = []
  let cursor = 0
  for (const m of matches) {
    if (m.start < cursor) continue
    resolved.push(m)
    cursor = m.end
  }

  // Build React nodes
  cursor = 0
  const nodes = []
  resolved.forEach((m, i) => {
    if (m.start > cursor) nodes.push(text.slice(cursor, m.start))
    nodes.push(
      <mark key={i} className={`highlight highlight--${m.type}`} title={m.type}>
        {m.label}
      </mark>
    )
    cursor = m.end
  })
  if (cursor < text.length) nodes.push(text.slice(cursor))

  return <>{nodes}</>
}

export default function NERPage() {
  const navigate = useNavigate()
  const { extractedText, entities, fileName } = usePipeline()

  const grouped    = useMemo(() => groupBy(entities, 'type'), [entities])
  const unknowns   = useMemo(() => entities.filter(e => e.type === 'UNKNOWN'), [entities])
  const TYPE_ORDER = ['PERSON', 'ORG', 'DATE', 'MONEY', 'LAW', 'LOCATION', 'UNKNOWN']

  if (!extractedText) {
    return (
      <div className="container">
        <div className="error-banner">No document loaded. <button className="btn btn--ghost btn--sm" onClick={() => navigate('/')}>Go back</button></div>
      </div>
    )
  }

  return (
    <div className="container container--wide">
      <div className="flex flex--between flex--center mb-2">
        <div>
          <h1 className="page-title">Named Entity Recognition</h1>
          <p className="page-sub">
            {entities.length} entities detected in <span className="text-mono">{fileName}</span>
          </p>
        </div>
        <div className="flex gap-1">
          <button className="btn btn--outline" onClick={() => navigate('/')}>← Back</button>
          <button className="btn btn--primary" onClick={() => navigate('/annotate')}>
            Refine Annotations →
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.25rem', alignItems: 'start' }}>
        {/* Extracted text with highlights */}
        <div className="card">
          <div className="card__title">Extracted Text</div>
          <div className="extracted-text">
            <HighlightedText text={extractedText} entities={entities} />
          </div>
        </div>

        {/* Entity summary */}
        <div>
          <div className="card">
            <div className="card__title">Detected Entities</div>
            {TYPE_ORDER.filter(t => grouped[t]).map(type => (
              <div key={type} style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.4rem' }}>
                  <EntityTag type={type} />
                  <span className="text-faint" style={{ fontSize: '0.75rem' }}>
                    {grouped[type].length}
                  </span>
                </div>
                <div className="entity-list">
                  {grouped[type].map(e => (
                    <div key={e.id} className="entity-item">
                      <span className="entity-item__text">{e.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {unknowns.length > 0 && (
            <div className="card mt-2" style={{ borderColor: '#e8c5b8' }}>
              <div className="card__title">Needs Annotation</div>
              <p className="text-faint" style={{ fontSize: '0.8rem', marginBottom: '0.75rem' }}>
                {unknowns.length} {unknowns.length === 1 ? 'entity' : 'entities'} could not be classified automatically.
              </p>
              <button className="btn btn--primary" style={{ width: '100%' }} onClick={() => navigate('/annotate')}>
                Label Unknown Entities
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
