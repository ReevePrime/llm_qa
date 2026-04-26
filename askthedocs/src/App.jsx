import { useState } from 'react'
import FileUpload from './components/FileUpload'
import ChatInterface from './components/ChatInterface'
import './App.css'

const API_URL = 'http://localhost:8000'

export default function App() {
  const [apiKey, setApiKey] = useState('')

  // Uploaded documents
  const [uploadedDocs, setUploadedDocs] = useState([])
  const [uploadStatus, setUploadStatus] = useState('idle') // 'idle'|'loading'|'success'|'error'
  const [uploadError, setUploadError] = useState(null)

  // Chat
  const [messages, setMessages] = useState([])
  const [queryLoading, setQueryLoading] = useState(false)

  async function handleUpload(files) {
    setUploadStatus('loading')
    setUploadError(null)
    const formData = new FormData()
    for (const file of files) formData.append('files', file)
    try {
      const res = await fetch(`${API_URL}/ingest`, {
        method: 'POST',
        headers: apiKey ? { 'x-api-key': apiKey } : {},
        body: formData,
      })
      const text = await res.text()
      const data = text ? JSON.parse(text) : {}
      if (!res.ok) throw new Error(detailMessage(data.detail, res.status))
      setUploadedDocs(prev => [...prev, ...files.map(f => f.name)])
      setUploadStatus('success')
    } catch (err) {
      setUploadError(err.message)
      setUploadStatus('error')
    }
  }

  async function handleQuery(query) {
    const id = Date.now()
    setMessages(prev => [...prev, { id, question: query, answer: null, source: null, error: null }])
    setQueryLoading(true)
    try {
      const res = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey ? { 'x-api-key': apiKey } : {}),
        },
        body: JSON.stringify({ query }),
      })
      const text = await res.text()
      const data = text ? JSON.parse(text) : {}
      if (!res.ok) throw new Error(detailMessage(data.detail, res.status))
      setMessages(prev =>
        prev.map(m => m.id === id ? { ...m, answer: data.answer, source: data.source ?? null } : m)
      )
    } catch (err) {
      setMessages(prev =>
        prev.map(m => m.id === id ? { ...m, error: err.message } : m)
      )
    } finally {
      setQueryLoading(false)
    }
  }

  function resetUpload() {
    setUploadStatus('idle')
    setUploadError(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>AskTheDocs</h1>
        <p className="app-subtitle">Upload documents, then ask questions</p>
      </header>

      <main className="app-main">
        <div className="card api-key-card">
          <label className="field-label" htmlFor="api-key">API Key</label>
          <input
            id="api-key"
            type="password"
            value={apiKey}
            onChange={e => setApiKey(e.target.value)}
            placeholder="Enter your API key"
            className="text-input"
            autoComplete="current-password"
          />
        </div>

        <div className="card chat-card">
          <h2 className="card-title">Ask a Question</h2>
          <ChatInterface
            messages={messages}
            loading={queryLoading}
            onSend={handleQuery}
          />
        </div>

        <div className="card upload-card">
          <h2 className="card-title">Upload Documents</h2>
          <FileUpload
            uploadedDocs={uploadedDocs}
            status={uploadStatus}
            error={uploadError}
            onUpload={handleUpload}
            onReset={resetUpload}
          />
        </div>
      </main>
    </div>
  )
}

function detailMessage(detail, status) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(e => e.msg ?? JSON.stringify(e)).join(', ')
  return `HTTP ${status}`
}
