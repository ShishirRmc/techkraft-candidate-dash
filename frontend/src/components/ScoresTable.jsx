function getScoreClass(score) {
  if (score >= 4) return 'score-high'
  if (score >= 3) return 'score-mid'
  return 'score-low'
}

function getScoreLabel(score) {
  if (score >= 4) return 'high'
  if (score >= 3) return 'medium'
  return 'low'
}

export default function ScoresTable({ scores, showReviewer, isAdmin, onDeleteScore }) {
  if (!scores || scores.length === 0) {
    return <p className="no-scores">No scores yet. Be the first to evaluate.</p>
  }

  return (
    <table className="scores-table">
      <thead>
        <tr>
          <th>Category</th>
          <th>Score</th>
          <th>Note</th>
          {showReviewer && <th>Reviewer</th>}
          {isAdmin && onDeleteScore && <th></th>}
        </tr>
      </thead>
      <tbody>
        {scores.map((s) => (
          <tr key={s.id}>
            <td>{s.category.replace('_', ' ')}</td>
            <td>
              <span
                className={`score-value ${getScoreClass(s.score)}`}
                aria-label={`Score ${s.score} - ${getScoreLabel(s.score)}`}
              >
                {s.score}
              </span>
            </td>
            <td>{s.note || '—'}</td>
            {showReviewer && <td>{s.reviewer_email || '—'}</td>}
            {isAdmin && onDeleteScore && (
              <td>
                <button
                  className="btn-delete-score"
                  onClick={() => onDeleteScore(s.id)}
                  aria-label={`Delete score ${s.id}`}
                  title="Delete score"
                >
                  ×
                </button>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
