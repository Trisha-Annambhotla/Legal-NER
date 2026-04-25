import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePipeline } from '../context/PipelineContext.jsx'
import { uploadDocument, runNER } from '../services/api.js'
import Loader from '../components/Loader.jsx'

export default function UploadPage() {
  const navigate   = useNavigate()
  const { setExtractedText, setFileName, setEntities, reset } = usePipeline()
  const fileRef    = useRef(null)
  const [file, setFile]       = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [dragging, setDragging] = useState(false)

  const handleFile = (f) => {
    if (!f) return
    if (f.type !== 'application/pdf') {
      setError('Please upload a PDF file.')
      return
    }
    setError('')
    setFile(f)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleProcess = async () => {
    if (!file) { setError('Please select a PDF first.'); return }
    setLoading(true)
    setError('')
    reset()
    try {
      const { text }     = await uploadDocument(file)
      const { entities } = await runNER(text)
      setExtractedText(text)
      setFileName(file.name)
      setEntities(entities)
      navigate('/ner')
    } catch (err) {
      console.error(err)
      setError(err?.response?.data?.detail || 'Upload failed. Check that the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1 className="page-title">Upload Legal Document</h1>
      <p className="page-sub">Upload a PDF to begin entity extraction and case analysis.</p>

      {/* Drop zone */}
      <div
        className={`upload-zone ${dragging ? 'upload-zone--active' : ''}`}
        onClick={() => fileRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onKeyDown={e => e.key === 'Enter' && fileRef.current?.click()}
        aria-label="Upload PDF"
      >
        <div className="upload-zone__icon">📄</div>
        <div className="upload-zone__label">
          <strong>Click to browse</strong> or drag &amp; drop a PDF
        </div>
        <div className="text-faint mt-1" style={{ fontSize: '0.78rem' }}>PDF files only · Max 50 MB</div>
        {file && (
          <div className="upload-zone__file">
            {file.name} &nbsp;·&nbsp; {(file.size / 1024).toFixed(0)} KB
          </div>
        )}
        <input
          ref={fileRef}
          type="file"
          accept="application/pdf"
          className="sr-only"
          onChange={e => handleFile(e.target.files[0])}
        />
      </div>

      {error && (
        <div className="error-banner mt-2">
          <span>⚠</span> {error}
        </div>
      )}

      <div className="mt-3" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <button
          className="btn btn--primary"
          onClick={handleProcess}
          disabled={loading || !file}
        >
          {loading ? <Loader text="Extracting &amp; running NER…" /> : 'Process Document →'}
        </button>

        {!file && (
          <span className="text-faint">No file selected</span>
        )}
      </div>

      {/* Info */}
      <div className="divider" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
        {[
          ['01', 'Extract',  'Text is pulled from your PDF using OCR / digital extraction.'],
          ['02', 'Identify', 'Named Entity Recognition detects parties, dates, amounts &amp; more.'],
          ['03', 'Analyse',  'Chat with a RAG model grounded in your document context.'],
        ].map(([n, title, desc]) => (
          <div key={n} className="card" style={{ padding: '1.1rem' }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '0.7rem', color: 'var(--ink-faint)', marginBottom: '0.4rem' }}>{n}</div>
            <div style={{ fontWeight: 500, marginBottom: '0.3rem' }}>{title}</div>
            <div className="text-faint" style={{ fontSize: '0.8rem' }} dangerouslySetInnerHTML={{ __html: desc }} />
          </div>
        ))}
      </div>
    </div>
  )
}
