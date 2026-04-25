import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { PipelineProvider } from './context/PipelineContext.jsx'
import Header from './components/Header.jsx'
import UploadPage     from './pages/UploadPage.jsx'
import NERPage        from './pages/NERPage.jsx'
import AnnotationPage from './pages/AnnotationPage.jsx'
import ChatPage       from './pages/ChatPage.jsx'

export default function App() {
  return (
    <PipelineProvider>
      <div className="page">
        <Header />
        <main className="main">
          <Routes>
            <Route path="/"          element={<UploadPage />} />
            <Route path="/ner"       element={<NERPage />} />
            <Route path="/annotate"  element={<AnnotationPage />} />
            <Route path="/chat"      element={<ChatPage />} />
            <Route path="*"          element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </PipelineProvider>
  )
}
