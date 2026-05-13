import { useState, useEffect, useRef } from 'react'
import { api } from '../api'

const CATEGORIES = ['technical', 'communication', 'problem_solving', 'culture_fit', 'leadership']

export default function ScoreForm({ candidateId, scoredCategories, onScoreSubmitted }) {
  const [category, setCategory] = useState('')
  const [scoreValue, setScoreValue] = useState(3)
  const [note, setNote] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  const successRef = useRef(null)
  const errorRef = useRef(null)

  // Pick first available category as default
  useEffect(() => {
    const available = CATEGORIES.find((c) => !scoredCategories.includes(c))
    setCategory(available || CATEGORIES[0])
  }, [scoredCategories])

  // Auto-dismiss success after 3 seconds
  useEffect(() => {
    if (!success) return
    const timer = setTimeout(() => setSuccess(''), 3000)
    return () => clearTimeout(timer)
  }, [success])

  // Focus management after submission
  useEffect(() => {
    if (success && successRef.current) successRef.current.focus()
  }, [success])

  useEffect(() => {
    if (error && errorRef.current) errorRef.current.focus()
  }, [error])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setSuccess('')
    setError('')
    try {
      await api.submitScore(candidateId, {
        category,
        score: parseInt(scoreValue),
        note: note || null,
      })
      setSuccess('Score submitted successfully')
      setNote('')
      setScoreValue(3)
      onScoreSubmitted()
    } catch (err) {
      setError(err.message || 'Failed to submit score')
    } finally {
      setSubmitting(false)
    }
  }

  const allScored = CATEGORIES.every((c) => scoredCategories.includes(c))

  return (
    <form onSubmit={handleSubmit} className="score-form">
      <div className="score-form-row">
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          aria-label="Score category"
          disabled={allScored}
        >
          {CATEGORIES.map((cat) => {
            const alreadyScored = scoredCategories.includes(cat)
            return (
              <option key={cat} value={cat} disabled={alreadyScored}>
                {cat.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                {alreadyScored ? ' (Already scored)' : ''}
              </option>
            )
          })}
        </select>
        <select
          value={scoreValue}
          onChange={(e) => setScoreValue(e.target.value)}
          aria-label="Score value"
          disabled={allScored}
        >
          {[1, 2, 3, 4, 5].map((v) => (
            <option key={v} value={v}>{v}/5</option>
          ))}
        </select>
      </div>
      <textarea
        placeholder="Optional note..."
        value={note}
        onChange={(e) => setNote(e.target.value)}
        aria-label="Score note"
        disabled={allScored}
      />
      <button
        type="submit"
        className="btn-submit-score"
        disabled={submitting || allScored}
      >
        {allScored ? 'ALL CATEGORIES SCORED' : submitting ? 'SUBMITTING...' : 'SUBMIT SCORE'}
      </button>
      {success && (
        <p className="score-success" role="status" ref={successRef} tabIndex={-1}>
          {success}
        </p>
      )}
      {error && (
        <p className="score-error" role="alert" ref={errorRef} tabIndex={-1}>
          {error}
        </p>
      )}
    </form>
  )
}
