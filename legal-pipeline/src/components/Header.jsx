import React from 'react'
import { Link, useLocation } from 'react-router-dom'

const STEPS = [
  { path: '/',         label: 'Upload',     num: 1 },
  { path: '/ner',      label: 'Entities',   num: 2 },
  { path: '/annotate', label: 'Annotate',   num: 3 },
  { path: '/chat',     label: 'Chat',       num: 4 },
]

export default function Header() {
  const { pathname } = useLocation()
  const currentIdx = STEPS.findIndex(s => s.path === pathname)

  return (
    <header className="header">
      <div className="container">
        <div className="header__inner">
          <Link to="/" className="logo">Lex<span>Pipeline</span></Link>

          <nav className="stepper" aria-label="Progress">
            {STEPS.map((step, i) => {
              const done   = i < currentIdx
              const active = i === currentIdx
              return (
                <div
                  key={step.path}
                  className={`step ${active ? 'step--active' : ''} ${done ? 'step--done' : ''}`}
                  aria-current={active ? 'step' : undefined}
                >
                  <span className="step__num">
                    {done ? '✓' : step.num}
                  </span>
                  <span>{step.label}</span>
                </div>
              )
            })}
          </nav>
        </div>
      </div>
    </header>
  )
}
