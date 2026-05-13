import './SkeletonCard.css'

export function SkeletonCard() {
  return (
    <div className="skeleton-card" aria-hidden="true">
      <div className="skeleton-line skeleton-title" />
      <div className="skeleton-line skeleton-subtitle" />
      <div className="skeleton-tags">
        <div className="skeleton-line skeleton-tag" />
        <div className="skeleton-line skeleton-tag" />
        <div className="skeleton-line skeleton-tag" />
      </div>
      <div className="skeleton-line skeleton-date" />
    </div>
  )
}

export function SkeletonDetail() {
  return (
    <div className="skeleton-detail" aria-hidden="true">
      <div className="skeleton-line skeleton-heading" />
      <div className="skeleton-line skeleton-meta" />
      <div className="skeleton-tags">
        <div className="skeleton-line skeleton-tag" />
        <div className="skeleton-line skeleton-tag" />
      </div>
      <div className="skeleton-grid">
        <div className="skeleton-section">
          <div className="skeleton-line skeleton-section-title" />
          <div className="skeleton-line skeleton-row" />
          <div className="skeleton-line skeleton-row" />
          <div className="skeleton-line skeleton-row" />
        </div>
        <div className="skeleton-section">
          <div className="skeleton-line skeleton-section-title" />
          <div className="skeleton-line skeleton-row" />
          <div className="skeleton-line skeleton-row" />
        </div>
      </div>
    </div>
  )
}
