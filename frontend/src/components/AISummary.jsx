import { useState } from 'react'
import { api } from '../api'

export default function AISummary({ candidateId }) {
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleGenerate = async () => {
    setLoading(true)
    setError('')
    setSummary('')
    try {
      const data = await api.generateSummary(candidateId)
      setSummary(data.summary)
    } catch (err) {
      setError(err.message || 'Failed to generate summary')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="summary-section">
      <button
        onClick={handleGenerate}
        className="btn-generate"
        disabled={loading}
      >
        {loading ? 'GENERATING...' : 'GENERATE SUMMARY'}
      </button>
      {loading && (
        <div className="summary-loading">
          <div className="spinner" aria-hidden="true"></div>
          <span>Analyzing candidate data...</span>
        </div>
      )}
      {error && <p className="summary-error" role="alert">{error}</p>}
      {summary && <p className="summary-text">{summary}</p>}
    </div>
  )
}
