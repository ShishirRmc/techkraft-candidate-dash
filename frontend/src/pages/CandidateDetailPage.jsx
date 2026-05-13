import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'
import ScoresTable from '../components/ScoresTable'
import ScoreForm from '../components/ScoreForm'
import AISummary from '../components/AISummary'
import AdminNotes from '../components/AdminNotes'
import { SkeletonDetail } from '../components/SkeletonCard'
import './CandidateDetailPage.css'

export default function CandidateDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const [candidate, setCandidate] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    const fetchCandidate = async () => {
      setLoading(true)
      setError('')
      try {
        const data = await api.getCandidate(id, { signal: controller.signal })
        setCandidate(data)
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Failed to load candidate')
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    fetchCandidate()
    return () => controller.abort()
  }, [id])

  const refreshCandidate = async () => {
    try {
      const data = await api.getCandidate(id)
      setCandidate(data)
    } catch (err) {
      // Silent refresh failure — data is already displayed
    }
  }

  // Determine which categories the current user has already scored
  const scoredCategories = candidate?.scores
    ? candidate.scores.map((s) => s.category)
    : []

  const handleDeleteScore = async (scoreId) => {
    try {
      await api.deleteScore(id, scoreId)
      await refreshCandidate()
    } catch (err) {
      console.error('Failed to delete score:', err)
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="detail-content">
          <SkeletonDetail />
        </div>
      </Layout>
    )
  }

  if (error && !candidate) {
    return (
      <Layout>
        <div className="detail-content">
          <Link to="/" className="back-link">← BACK TO LIST</Link>
          <div className="empty-state" role="alert">{error}</div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="detail-content">
        <Link to="/" className="back-link">← BACK TO LIST</Link>

        {/* Profile Header */}
        <div className="profile-header">
          <div className="profile-info">
            <h1 className="text-heading-xl">{candidate.name}</h1>
            <div className="profile-meta">
              <span className="text-body-md profile-email">{candidate.email}</span>
              <span className="text-body-strong profile-role">{candidate.role_applied}</span>
              <span className={`status-pill status-${candidate.status}`}>
                {candidate.status}
              </span>
            </div>
            {candidate.skills && (
              <div className="profile-skills">
                {candidate.skills.split(',').map((skill) => (
                  <span key={skill} className="skill-tag">{skill.trim()}</span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Main Grid */}
        <div className="detail-grid">
          {/* Scores Table */}
          <div className="detail-section">
            <h2 className="section-title">
              <span className="text-eyebrow">SCORES</span>
            </h2>
            <ScoresTable
              scores={candidate.scores}
              showReviewer={user?.role === 'admin'}
              isAdmin={user?.role === 'admin'}
              onDeleteScore={user?.role === 'admin' ? handleDeleteScore : undefined}
            />
          </div>

          {/* Score Form */}
          <div className="detail-section">
            <h2 className="section-title">
              <span className="text-eyebrow">SUBMIT SCORE</span>
            </h2>
            <ScoreForm
              candidateId={id}
              scoredCategories={scoredCategories}
              onScoreSubmitted={refreshCandidate}
            />
          </div>

          {/* AI Summary */}
          <div className="detail-section">
            <h2 className="section-title">
              <span className="text-eyebrow">AI SUMMARY</span>
            </h2>
            <AISummary candidateId={id} />
          </div>

          {/* Admin Notes — only visible to admins */}
          {user?.role === 'admin' && (
            <div className="detail-section">
              <h2 className="section-title">
                <span className="text-eyebrow">INTERNAL NOTES</span>
                <span className="admin-badge">ADMIN</span>
              </h2>
              <AdminNotes
                candidateId={id}
                internalNotes={candidate.internal_notes}
                onNotesUpdated={refreshCandidate}
              />
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
