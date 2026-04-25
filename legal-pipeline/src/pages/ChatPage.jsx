import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePipeline } from '../context/PipelineContext.jsx'
import { sendChatMessage } from '../services/api.js'
import Loader from '../components/Loader.jsx'
import EntityTag from '../components/EntityTag.jsx'

const SUGGESTIONS = [
  'Who are the parties in this agreement?',
  'What are the fee arrangements?',
  'What is the term of this agreement?',
  'What legal matter does this cover?',
]

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function ChatPage() {
  const navigate = useNavigate()
  const { extractedText, entities, fileName, chatHistory, setChatHistory } = usePipeline()
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')
  const messagesEndRef           = useRef(null)
  const inputRef                 = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory, loading])

  if (!extractedText) {
    return (
      <div className="container">
        <div className="error-banner">No document loaded. <button className="btn btn--ghost btn--sm" onClick={() => navigate('/')}>Go back</button></div>
      </div>
    )
  }

  const sendMessage = async (text) => {
    const query = (text || input).trim()
    if (!query) return

    const userMsg = { role: 'user', content: query, time: new Date() }
    const nextHistory = [...chatHistory, userMsg]
    setChatHistory(nextHistory)
    setInput('')
    setError('')
    setLoading(true)

    try {
      const { response } = await sendChatMessage(
        query,
        extractedText,
        nextHistory.map(m => ({ role: m.role, content: m.content }))
      )
      setChatHistory(prev => [...prev, {
        role: 'assistant',
        content: response,
        time: new Date()
      }])
    } catch (err) {
      console.error(err)
      setError(err?.response?.data?.detail || 'Failed to get a response. Is the backend running?')
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const knownEntities = entities.filter(e => e.type !== 'UNKNOWN').slice(0, 8)

  return (
    <div className="container container--wide">
      <div className="flex flex--between flex--center mb-2">
        <div>
          <h1 className="page-title">Document Chat</h1>
          <p className="page-sub">
            Ask questions about <span style={{ fontFamily: 'var(--mono)' }}>{fileName}</span> — answers are grounded in the document.
          </p>
        </div>
        <button className="btn btn--outline" onClick={() => navigate('/annotate')}>← Annotate</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: '1.25rem', alignItems: 'start' }}>
        {/* Chat panel */}
        <div>
          <div className="chat-layout">
            {/* Messages */}
            <div className="chat-messages">
              {chatHistory.length === 0 && (
                <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--ink-faint)' }}>
                  <div style={{ fontSize: '1.8rem', marginBottom: '0.5rem' }}>💬</div>
                  <div style={{ fontSize: '0.85rem' }}>Ask anything about your document.</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center', marginTop: '1rem' }}>
                    {SUGGESTIONS.map(s => (
                      <button key={s} className="btn btn--outline btn--sm" onClick={() => sendMessage(s)}>{s}</button>
                    ))}
                  </div>
                </div>
              )}

              {chatHistory.map((msg, i) => (
                <div key={i} className={`message message--${msg.role}`}>
                  <div className="message__bubble">{msg.content}</div>
                  <div className="message__meta">
                    {msg.role === 'user' ? 'You' : 'LexPipeline'} · {formatTime(msg.time || new Date())}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message message--assistant">
                  <div className="message__bubble" style={{ color: 'var(--ink-light)' }}>
                    <Loader text="Thinking…" />
                  </div>
                </div>
              )}

              {error && (
                <div className="error-banner">
                  <span>⚠</span> {error}
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input row */}
            <div className="chat-input-row">
              <textarea
                ref={inputRef}
                className="input"
                placeholder="Ask about parties, fees, dates, legal references…"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={2}
                disabled={loading}
              />
              <button
                className="btn btn--primary"
                onClick={() => sendMessage()}
                disabled={loading || !input.trim()}
                style={{ height: '44px', alignSelf: 'flex-end' }}
              >
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Context sidebar */}
        <div>
          <div className="card">
            <div className="card__title">Case Context</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--ink-light)', marginBottom: '0.75rem' }}>
              Entities grounding this chat session:
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {knownEntities.map(e => (
                <div key={e.id} className="entity-item" style={{ padding: '0.3rem 0.6rem' }}>
                  <EntityTag type={e.type} />
                  <span className="entity-item__text" style={{ fontSize: '0.75rem' }}>{e.text}</span>
                </div>
              ))}
              {entities.length > 8 && (
                <div className="text-faint" style={{ fontSize: '0.75rem' }}>
                  + {entities.length - 8} more entities
                </div>
              )}
            </div>
          </div>

          <div className="card mt-2">
            <div className="card__title">Suggestions</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  className="btn btn--ghost btn--sm"
                  style={{ justifyContent: 'flex-start', textAlign: 'left', fontWeight: 400 }}
                  onClick={() => sendMessage(s)}
                  disabled={loading}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="card mt-2">
            <div className="card__title">Session</div>
            <div className="text-faint" style={{ fontSize: '0.78rem' }}>
              {chatHistory.filter(m => m.role === 'user').length} messages sent
            </div>
            <button
              className="btn btn--ghost btn--sm mt-2"
              style={{ color: 'var(--accent)' }}
              onClick={() => setChatHistory([])}
            >
              Clear history
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
