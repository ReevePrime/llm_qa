import { useState, useRef } from 'react'
import './FileUpload.css'

// The address of the FastAPI backend
const API_URL = 'http://localhost:8000'

// Possible values for the `status` state
// 'idle' | 'uploading' | 'success' | 'error'

export default function FileUpload({ apiKey }) {
  const [files, setFiles] = useState([])
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('')
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef(null)

  function openFilePicker() {
    fileInputRef.current.click()
  }

  function handleDragOver(e) {
    e.preventDefault()
    setIsDragOver(true)
  }

  // Only clear the highlight when the cursor leaves the drop zone itself,
  // not when it moves over a child element inside it.
  function handleDragLeave(e) {
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setIsDragOver(false)
    }
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragOver(false)
    const dropped = Array.from(e.dataTransfer.files)
    if (dropped.length) setFiles(dropped)
  }

  function handleFileInput(e) {
    setFiles(Array.from(e.target.files))
  }

  function removeFile(index) {
    setFiles(files.filter((_, i) => i !== index))
  }

  async function upload() {
    setStatus('uploading')
    setMessage('')

    const formData = new FormData()
    for (const file of files) formData.append('files', file)

    const headers = apiKey ? { 'x-api-key': apiKey } : {}

    try {
      const res = await fetch(`${API_URL}/ingest`, { method: 'POST', headers, body: formData })
      const text = await res.text()
      const data = text ? JSON.parse(text) : {}
      if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`)
      setStatus('success')
      setMessage(data.message ?? 'Upload successful')
      setFiles([])
    } catch (err) {
      setStatus('error')
      setMessage(err.message)
    }
  }

  function reset() {
    setStatus('idle')
    setMessage('')
    setFiles([])
    fileInputRef.current.value = ''
  }

  // Build the drop zone CSS class list
  const dropZoneClasses = ['drop-zone']
  if (isDragOver) dropZoneClasses.push('drag-over')
  if (status === 'uploading') dropZoneClasses.push('disabled')

  // Compute the upload button label up here to keep JSX clean
  let buttonLabel = 'Upload'
  if (status === 'uploading') {
    buttonLabel = 'Uploading…'
  } else if (files.length > 0) {
    buttonLabel = `Upload ${files.length} file${files.length > 1 ? 's' : ''}`
  }

  return (
    <div className="file-upload">
      <div
        className={dropZoneClasses.join(' ')}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => status !== 'uploading' && openFilePicker()}
        onKeyDown={e => e.key === 'Enter' && status !== 'uploading' && openFilePicker()}
        role="button"
        tabIndex={0}
        aria-label="Upload files — drag and drop or click to browse"
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileInput}
          className="file-input-hidden"
          tabIndex={-1}
          aria-hidden="true"
        />
        <UploadIcon />
        <p className="drop-zone-text">
          {isDragOver ? 'Drop files here' : 'Drag & drop files here'}
        </p>
        <p className="drop-zone-subtext">
          or <span className="browse-link">browse</span>
        </p>
      </div>

      {files.length > 0 && (
        <ul className="file-list" aria-label="Selected files">
          {files.map((file, i) => (
            <li key={i} className="file-item">
              <span className="file-name">{file.name}</span>
              <span className="file-size">{formatSize(file.size)}</span>
              {status !== 'uploading' && (
                <button
                  className="remove-btn"
                  onClick={() => removeFile(i)}
                  aria-label={`Remove ${file.name}`}
                >
                  ×
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      {status === 'uploading' && (
        <div className="progress-track" role="progressbar" aria-label="Uploading">
          <div className="progress-bar" />
        </div>
      )}

      {status === 'success' && (
        <div className="status-banner success" role="status">
          <span className="status-icon">✓</span>
          <span>{message}</span>
          <button className="inline-btn" onClick={reset}>Upload more</button>
        </div>
      )}

      {status === 'error' && (
        <div className="status-banner error" role="alert">
          <span className="status-icon">✕</span>
          <span>{message}</span>
          <button className="inline-btn" onClick={reset}>Try again</button>
        </div>
      )}

      {(status === 'idle' || status === 'uploading') && (
        <button
          className="upload-btn"
          onClick={upload}
          disabled={files.length === 0 || status === 'uploading'}
        >
          {buttonLabel}
        </button>
      )}
    </div>
  )
}

function UploadIcon() {
  return (
    <svg className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 16V4m0 0L8 8m4-4 4 4" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-1" />
    </svg>
  )
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
