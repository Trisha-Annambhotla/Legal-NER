/**
 * context/PipelineContext.jsx
 * Holds all shared state across the 4-step pipeline.
 */

import React, { createContext, useContext, useState } from 'react'

const PipelineContext = createContext(null)

export function PipelineProvider({ children }) {
  const [extractedText, setExtractedText] = useState('')
  const [fileName, setFileName]           = useState('')
  const [entities, setEntities]           = useState([])
  const [chatHistory, setChatHistory]     = useState([])

  const reset = () => {
    setExtractedText('')
    setFileName('')
    setEntities([])
    setChatHistory([])
  }

  return (
    <PipelineContext.Provider value={{
      extractedText, setExtractedText,
      fileName,      setFileName,
      entities,      setEntities,
      chatHistory,   setChatHistory,
      reset
    }}>
      {children}
    </PipelineContext.Provider>
  )
}

export function usePipeline() {
  const ctx = useContext(PipelineContext)
  if (!ctx) throw new Error('usePipeline must be used within PipelineProvider')
  return ctx
}
