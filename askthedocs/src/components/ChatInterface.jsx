import { useState, useRef, useEffect } from 'react'
import './ChatInterface.css'

const API_URL = 'http://localhost:8000'

export default function ChatInterface({ apiKey }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage() {
    const query = input.trim()
    if (!query || loading) return

    const id = Date.now()
    setMessages(prev => [...prev, { id, question: query, answer: null, source: null, error: null }])
    setInput('')
    setLoading(true)

    const headers = {
      'Content-Type': 'application/json',
      ...(apiKey ? { 'x-api-key': apiKey } : {}),
    }

    try {
      const res = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ query }),
      })
      const text = await res.text()
      const data = text ? JSON.parse(text) : {}
      if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`)
      setMessages(prev =>
        prev.map(m => m.id === id ? { ...m, answer: data.answer, source: data.source ?? null } : m)
      )
    } catch (err) {
      setMessages(prev =>
        prev.map(m => m.id === id ? { ...m, error: err.message } : m)
      )
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="chat-interface">
      <div className="message-list" role="log" aria-live="polite" aria-label="Chat messages">
        {messages.length === 0 && (
          <p className="chat-empty">Ask a question about your uploaded documents.</p>
        )}
        {messages.map(msg => (
          <div key={msg.id} className="message-exchange">
            <div className="message user-message">
              <span className="message-label">You</span>
              <p className="message-bubble">{msg.question}</p>
            </div>
            <div className="message assistant-message">
              <span className="message-label">Answer</span>
              {msg.error ? (
                <p className="message-bubble error-bubble">{msg.error}</p>
              ) : msg.answer === null ? (
                <div className="typing-indicator" aria-label="Loading answer">
                  <span /><span /><span />
                </div>
              ) : (
                <>
                  <p className="message-bubble">{msg.answer}</p>
                  {msg.source && (
                    <p className="message-source">Source: {msg.source}</p>
                  )}
                </>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question…"
          className="text-input chat-input"
          disabled={loading}
          aria-label="Question"
        />
        <button
          className="send-btn"
          onClick={sendMessage}
          disabled={!input.trim() || loading}
        >
          Send
        </button>
      </div>
    </div>
  )
}
