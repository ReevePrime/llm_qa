import { useState } from 'react'
import FileUpload from './components/FileUpload'
import './App.css'

export default function App() {
  const [apiKey, setApiKey] = useState('')

  return (
    <div className="app">
      <header className="app-header">
        <h1>AskTheDocs</h1>
        <p className="app-subtitle">Upload documents, then ask questions</p>
      </header>

      <main className="app-main">
        <div className="card">
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

        <div className="card">
          <h2 className="card-title">Upload Documents</h2>
          <FileUpload apiKey={apiKey} />
        </div>
      </main>
    </div>
  )
}
