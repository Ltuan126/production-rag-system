import { useEffect, useState } from 'react'

const backendUrl = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000'

export default function App() {
  const [question, setQuestion] = useState('How does the RAG system work?')
  const [result, setResult] = useState(null)
  const [documents, setDocuments] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

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
        body: JSON.stringify({ question, top_k: 4 }),
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

        {error ? <p className="error">{error}</p> : null}

        {result ? (
          <>
            <p className="answer">{result.answer}</p>
            <div className="sources">
              {result.sources.map((source) => (
                <article key={`${source.source}-${source.score}`} className="source-card">
                  <div className="source-meta">
                    <strong>{source.source}</strong>
                    <span>{source.score.toFixed(2)}</span>
                  </div>
                  <p>{source.content}</p>
                </article>
              ))}
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