import { useState, useRef, useEffect } from 'react'
import './FileUpload.css'

export default function FileUpload({ uploadedDocs, status, error, onUpload, onReset }) {
  const [files, setFiles] = useState([])
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef(null)

  // Clear pending selection once the upload succeeds
  useEffect(() => {
    if (status === 'success') {
      setFiles([])
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }, [status])

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

  const loading = status === 'loading'

  const dropZoneClasses = ['drop-zone']
  if (isDragOver) dropZoneClasses.push('drag-over')
  if (loading) dropZoneClasses.push('disabled')

  let buttonLabel = 'Upload'
  if (loading) {
    buttonLabel = 'Uploading…'
  } else if (files.length > 0) {
    buttonLabel = `Upload ${files.length} file${files.length > 1 ? 's' : ''}`
  }

  return (
    <div className="file-upload">
      {uploadedDocs.length > 0 && (
        <ul className="ingested-list" aria-label="Ingested documents">
          {uploadedDocs.map((name, i) => (
            <li key={i} className="ingested-item">
              <DocIcon />
              <span className="file-name">{name}</span>
            </li>
          ))}
        </ul>
      )}

      <div
        className={dropZoneClasses.join(' ')}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !loading && openFilePicker()}
        onKeyDown={e => e.key === 'Enter' && !loading && openFilePicker()}
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
              {!loading && (
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

      {loading && (
        <div className="progress-track" role="progressbar" aria-label="Uploading">
          <div className="progress-bar" />
        </div>
      )}

      {status === 'success' && (
        <div className="status-banner success" role="status">
          <span className="status-icon">✓</span>
          <span>Documents ingested successfully</span>
          <button className="inline-btn" onClick={onReset}>Upload more</button>
        </div>
      )}

      {status === 'error' && (
        <div className="status-banner error" role="alert">
          <span className="status-icon">✕</span>
          <span>{error}</span>
          <button className="inline-btn" onClick={onReset}>Try again</button>
        </div>
      )}

      {(status === 'idle' || loading) && (
        <button
          className="upload-btn"
          onClick={() => onUpload(files)}
          disabled={files.length === 0 || loading}
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

function DocIcon() {
  return (
    <svg className="doc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  )
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
