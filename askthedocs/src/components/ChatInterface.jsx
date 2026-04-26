import { useState, useRef, useEffect } from 'react'
import './ChatInterface.css'

export default function ChatInterface({ messages, loading, onSend }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  // Scroll to the latest message whenever the list changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Re-focus the input once a response finishes loading
  useEffect(() => {
    if (!loading) inputRef.current?.focus()
  }, [loading])

  function handleSend() {
    const query = input.trim()
    if (!query || loading) return
    onSend(query)
    setInput('')
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
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
          onClick={handleSend}
          disabled={!input.trim() || loading}
        >
          Send
        </button>
      </div>
    </div>
  )
}
