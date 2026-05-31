import { useEffect, useState } from 'react'

const backendUrl = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000'

export default function App() {
  const [question, setQuestion] = useState('How does the RAG system work?')
  const [topK, setTopK] = useState(4)
  const [result, setResult] = useState(null)
  const [documents, setDocuments] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [expanded, setExpanded] = useState(() => new Set())

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/documents`)
        if (!response.ok) {
          return
        }

        setDocuments(await response.json())
      } catch {
        setDocuments(null)
      }
    }

    loadDocuments()
  }, [])

  const handleReindex = async () => {
    setLoading(true)
    try {
      const r = await fetch(`${backendUrl}/api/ingest`, { method: 'POST' })
      if (!r.ok) throw new Error('Failed to schedule reindex')
      // poll for new index briefly
      setTimeout(async () => {
        try {
          const resp = await fetch(`${backendUrl}/api/documents`)
          if (resp.ok) setDocuments(await resp.json())
        } catch {}
        setLoading(false)
      }, 1100)
    } catch (err) {
      setLoading(false)
      setError(err.message)
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch(`${backendUrl}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question, top_k: topK }),
      })

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }

      setResult(await response.json())
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  const copyAnswer = async () => {
    if (!result?.answer) return
    try {
      await navigator.clipboard.writeText(result.answer)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // ignore
    }
  }

  const toggleExpand = (key) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Production RAG System</p>
        <h1>Ask questions over your documents with a focused retrieval pipeline.</h1>
        <p className="lede">
          A practical full-stack starting point for ingestion, retrieval, caching, and response
          delivery.
        </p>
        {documents ? (
          <div className="stats-row">
            <div className="stat-card">
              <strong>{documents.total_documents}</strong>
              <span>documents</span>
            </div>
            <div className="stat-card">
              <strong>{documents.total_paragraphs}</strong>
              <span>paragraphs</span>
            </div>
            <div className="stat-card">
              <strong>{documents.total_characters}</strong>
              <span>characters</span>
            </div>
          </div>
        ) : null}
      </section>

      <section className="panel query-panel">
        <form onSubmit={handleSubmit} className="query-form">
          <label htmlFor="question">Your question</label>
          <textarea
            id="question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={5}
            placeholder="Ask about architecture, onboarding, or any document you've added."
          />
          <div className="query-controls">
            <label htmlFor="top-k">Top K sources</label>
            <input
              id="top-k"
              type="range"
              min={1}
              max={10}
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
            />
            <span>{topK}</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="submit" disabled={loading}>
              {loading ? 'Searching...' : 'Run retrieval'}
            </button>
            <button type="button" onClick={handleReindex} disabled={loading}>
              Re-index documents
            </button>
          </div>
        </form>
      </section>

      <section className="panel answer-panel">
        <div className="panel-header">
          <h2>Answer</h2>
          <span>{result ? `${result.sources.length} sources` : 'No query yet'}</span>
        </div>

        {result ? (
          <div className="result-meta">
            <span className="meta-pill">top_k: {result.top_k}</span>
            <span className="meta-pill">{result.took_ms} ms</span>
            <span className={`meta-pill ${result.cached ? 'cache-hit' : 'cache-miss'}`}>
              {result.cached ? 'cache hit' : 'cache miss'}
            </span>
            <button className="copy-btn" onClick={copyAnswer} aria-label="Copy answer">
              {copied ? 'Copied' : 'Copy answer'}
            </button>
          </div>
        ) : null}

        {error ? <p className="error">{error}</p> : null}

        {result ? (
          <>
            <p className="answer">{result.answer}</p>
            <div className="sources">
              {result.sources.map((source, idx) => {
                const key = `${source.source}-${idx}`
                const isExpanded = expanded.has(key)
                const preview = source.content.length > 260 ? source.content.slice(0, 260) + '…' : source.content
                return (
                  <article key={key} className={`source-card ${isExpanded ? 'expanded' : 'collapsed'}`}>
                    <div className="source-meta">
                      <strong>{source.source}</strong>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span>{source.score.toFixed(2)}</span>
                        <button className="small-btn" onClick={() => toggleExpand(key)}>
                          {isExpanded ? 'Show less' : 'Show more'}
                        </button>
                        <button
                          className="small-btn"
                          onClick={async () => {
                            try {
                              await navigator.clipboard.writeText(source.content)
                            } catch {}
                          }}
                        >
                          Copy
                        </button>
                      </div>
                    </div>
                    <p>{isExpanded ? source.content : preview}</p>
                  </article>
                )
              })}
            </div>
          </>
        ) : (
          <>
            <p className="placeholder">Submit a question to see retrieved context and the answer.</p>
            {documents?.documents?.length ? (
              <div className="document-list">
                <h3>Loaded documents</h3>
                {documents.documents.map((document) => (
                  <div key={document.path} className="document-item">
                    <strong>{document.path}</strong>
                    <span>
                      {document.paragraphs} paragraphs · {document.characters} chars
                    </span>
                  </div>
                ))}
              </div>
            ) : null}
          </>
        )}
      </section>
    </main>
  )
}