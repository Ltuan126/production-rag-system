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

  const maxScore = result?.sources?.length ? Math.max(...result.sources.map((s) => s.score), 0.0001) : 1

  return (
    <main className="shell">
      <div className="title-strip">
        <span><span className="dot">●</span> RAG / QUERY CONSOLE</span>
        <span>{documents ? `${documents.total_documents} DOCS INDEXED` : '— DOCS INDEXED'}</span>
      </div>

      <section className="hero">
        <p className="eyebrow">Ask &amp; Retrieve</p>
        <h1>Ask a question. Trace the retrieval.</h1>
        <p className="lede">
          Submit a question and see exactly which document chunks were retrieved to answer it,
          ranked by relevance score.
        </p>
        {documents ? (
          <p className="corpus-note">
            Indexed corpus: <strong>{documents.total_documents}</strong> documents ·{' '}
            <strong>{documents.total_paragraphs}</strong> chunks
          </p>
        ) : null}
      </section>

      <section className="panel corner-frame query-panel">
        <span className="panel-tag">Input</span>
        <form onSubmit={handleSubmit} className="query-form">
          <label htmlFor="question">Your question</label>
          <div className="prompt-field">
            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={5}
              placeholder="Ask about architecture, onboarding, or any document you've added."
            />
          </div>
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
          <div className="button-row">
            <button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner" /> Searching
                </>
              ) : (
                'Run retrieval'
              )}
            </button>
            <button type="button" onClick={handleReindex} disabled={loading}>
              Re-index documents
            </button>
          </div>
        </form>
      </section>

      <section className="panel corner-frame answer-panel">
        <span className="panel-tag">Output</span>
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

        {error ? <p className="error">! {error}</p> : null}

        {result ? (
          <>
            <p className="answer">{result.answer}</p>
            <div className="sources">
              {result.sources.map((source, idx) => {
                const key = `${source.source}-${idx}`
                const isExpanded = expanded.has(key)
                const preview = source.content.length > 260 ? source.content.slice(0, 260) + '…' : source.content
                const fillPct = Math.max(6, Math.round((source.score / maxScore) * 100))
                return (
                  <article key={key} className={`source-card corner-frame ${isExpanded ? 'expanded' : 'collapsed'}`}>
                    <span className="source-tag">Specimen {String(idx + 1).padStart(2, '0')}</span>
                    <div className="source-meta">
                      <strong>{source.source}</strong>
                      <div className="source-actions">
                        <div className="score-gauge">
                          <div className="score-track">
                            <div className="score-fill" style={{ width: `${fillPct}%` }} />
                          </div>
                          <span className="score-value">{source.score.toFixed(2)}</span>
                        </div>
                        <button className="small-btn" onClick={() => toggleExpand(key)}>
                          {isExpanded ? 'Less' : 'More'}
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
          <p className="placeholder">// submit a question above to see the retrieved chunks and generated answer</p>
        )}
      </section>
    </main>
  )
}
