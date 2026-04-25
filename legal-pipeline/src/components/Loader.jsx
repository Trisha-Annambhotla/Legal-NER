import React from 'react'

export default function Loader({ text = 'Processing…' }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', color: 'var(--ink-light)', fontSize: '0.85rem' }}>
      <span className="loader">
        <span className="loader__dot" />
        <span className="loader__dot" />
        <span className="loader__dot" />
      </span>
      {text}
    </span>
  )
}
