import { useState, useEffect, useRef } from 'react'
import { api } from '../api'

export default function AdminNotes({ candidateId, internalNotes, onNotesUpdated }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(internalNotes || '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const textareaRef = useRef(null)

  // Auto-dismiss success after 3 seconds
  useEffect(() => {
    if (!success) return
    const timer = setTimeout(() => setSuccess(''), 3000)
    return () => clearTimeout(timer)
  }, [success])

  // Focus textarea when entering edit mode
  useEffect(() => {
    if (editing && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [editing])

  const handleEdit = () => {
    setDraft(internalNotes || '')
    setError('')
    setEditing(true)
  }

  const handleCancel = () => {
    setEditing(false)
    setError('')
  }

  const handleSave = async () => {
    setSaving(true)
    setError('')
    try {
      await api.updateNotes(candidateId, draft || null)
      setSuccess('Notes saved')
      setEditing(false)
      onNotesUpdated()
    } catch (err) {
      setError(err.message || 'Failed to save notes')
    } finally {
      setSaving(false)
    }
  }

  if (editing) {
    return (
      <div className="admin-notes-edit">
        <textarea
          ref={textareaRef}
          className="admin-notes-textarea"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Add internal notes..."
          aria-label="Internal notes"
          disabled={saving}
        />
        <div className="admin-notes-actions">
          <button
            onClick={handleSave}
            className="btn-submit-score"
            disabled={saving}
          >
            {saving ? 'SAVING...' : 'SAVE'}
          </button>
          <button
            onClick={handleCancel}
            className="btn-ghost"
            disabled={saving}
          >
            CANCEL
          </button>
        </div>
        {error && <p className="score-error" role="alert">{error}</p>}
      </div>
    )
  }

  return (
    <div className="admin-notes-view">
      <div className="admin-notes">
        {internalNotes || 'No internal notes for this candidate.'}
      </div>
      <button onClick={handleEdit} className="btn-ghost admin-edit-btn">
        EDIT
      </button>
      {success && <p className="score-success" role="status">{success}</p>}
    </div>
  )
}
