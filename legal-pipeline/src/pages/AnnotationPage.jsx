import React, { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePipeline } from '../context/PipelineContext.jsx'
import { submitAnnotations } from '../services/api.js'
import EntityTag from '../components/EntityTag.jsx'
import Loader from '../components/Loader.jsx'

const ENTITY_TYPES = ['PERSON', 'ORG', 'DATE', 'MONEY', 'LAW', 'LOCATION', 'OTHER']

export default function AnnotationPage() {
  const navigate = useNavigate()
  const { entities, setEntities, extractedText } = usePipeline()

  // Track user-provided labels for unknown entities
  const unknowns      = useMemo(() => entities.filter(e => e.type === 'UNKNOWN'), [entities])
  const [labels, setLabels]   = useState(() =>
    Object.fromEntries(unknowns.map(e => [e.id, '']))
  )
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [saved, setSaved]     = useState(false)

  if (!extractedText) {
    return (
      <div className="container">
        <div className="error-banner">No document loaded. <button className="btn btn--ghost btn--sm" onClick={() => navigate('/')}>Go back</button></div>
      </div>
    )
  }

  const handleLabelChange = (id, value) => {
    setLabels(prev => ({ ...prev, [id]: value }))
    setSaved(false)
  }

  const handleSubmit = async () => {
    const annotations = unknowns.map(e => ({
      id:   e.id,
      text: e.text,
      type: labels[e.id] || 'UNKNOWN'
    }))
    setLoading(true)
    setError('')
    try {
      const { entities: updated } = await submitAnnotations(annotations)
      setEntities(updated)
      setSaved(true)
    } catch (err) {
      console.error(err)
      setError(err?.response?.data?.detail || 'Failed to submit annotations.')
    } finally {
      setLoading(false)
    }
  }

  const knownEntities = entities.filter(e => e.type !== 'UNKNOWN')

  return (
    <div className="container">
      <div className="flex flex--between flex--center mb-2">
        <div>
          <h1 className="page-title">Refine Annotations</h1>
          <p className="page-sub">
            Label unclassified entities. Known entities are shown below for reference.
          </p>
        </div>
        <div className="flex gap-1">
          <button className="btn btn--outline" onClick={() => navigate('/ner')}>← NER</button>
          {saved && (
            <button className="btn btn--primary" onClick={() => navigate('/chat')}>
              Proceed to Chat →
            </button>
          )}
        </div>
      </div>

      {/* Unknown entities to annotate */}
      {unknowns.length === 0 ? (
        <div className="success-banner mb-2">
          ✓ All entities were classified automatically — no annotation needed.
        </div>
      ) : (
        <div className="card mb-2">
          <div className="card__title">Unknown Entities — {unknowns.length} to label</div>

          {unknowns.map(ent => (
            <div key={ent.id} className="annotation-row">
              <div className="annotation-row__text">
                <div style={{ fontWeight: 500 }}>{ent.text}</div>
                {/* Show surrounding context */}
                <div className="annotation-row__context">
                  {extractedText.includes(ent.text)
                    ? '…' + extractedText.slice(
                        Math.max(0, extractedText.indexOf(ent.text) - 40),
                        extractedText.indexOf(ent.text) + ent.text.length + 40
                      ).trim() + '…'
                    : ''}
                </div>
              </div>
              <select
                className="select annotation-row__select"
                value={labels[ent.id] || ''}
                onChange={e => handleLabelChange(ent.id, e.target.value)}
              >
                <option value="">— select type —</option>
                {ENTITY_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          ))}

          {error && <div className="error-banner mt-2"><span>⚠</span> {error}</div>}
          {saved && <div className="success-banner mt-2">✓ Annotations saved successfully.</div>}

          <div className="mt-3 flex gap-1" style={{ alignItems: 'center' }}>
            <button
              className="btn btn--primary"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? <Loader text="Saving…" /> : 'Save Annotations'}
            </button>
            {saved && (
              <button className="btn btn--outline" onClick={() => navigate('/chat')}>
                Proceed to Chat →
              </button>
            )}
          </div>
        </div>
      )}

      {/* Known entity reference */}
      <div className="card">
        <div className="card__title">Confirmed Entities ({knownEntities.length})</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {knownEntities.map(e => (
            <div key={e.id} className="entity-item">
              <EntityTag type={e.type} />
              <span className="entity-item__text">{e.text}</span>
            </div>
          ))}
        </div>

        {unknowns.length === 0 && (
          <div className="mt-3">
            <button className="btn btn--primary" onClick={() => navigate('/chat')}>
              Proceed to Chat →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
