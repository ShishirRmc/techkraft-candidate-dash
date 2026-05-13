import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import Layout from '../components/Layout'
import './CandidateListPage.css'

const STATUS_OPTIONS = ['', 'new', 'reviewing', 'interviewed', 'offered', 'rejected', 'archived']
const ROLE_OPTIONS = ['', 'Frontend Engineer', 'Backend Engineer', 'Full Stack Developer', 'DevOps Engineer', 'Data Engineer']
const PAGE_SIZE_OPTIONS = [5, 10, 20, 50]

const SORTABLE_COLUMNS = [
  { key: 'name', label: 'Name' },
  { key: 'role_applied', label: 'Role Applied' },
  { key: 'status', label: 'Status' },
  { key: 'skills', label: 'Skills' },
  { key: 'created_at', label: 'Applied' },
  { key: 'scores', label: 'Scores' },
]

export default function CandidateListPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const [candidates, setCandidates] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)

  // Initialize state from URL search params
  const [page, setPage] = useState(() => parseInt(searchParams.get('page')) || 1)
  const [pageSize, setPageSize] = useState(() => parseInt(searchParams.get('page_size')) || 10)
  const [sortBy, setSortBy] = useState(() => searchParams.get('sort_by') || 'created_at')
  const [sortOrder, setSortOrder] = useState(() => searchParams.get('sort_order') || 'desc')
  const [filters, setFilters] = useState(() => ({
    status: searchParams.get('status') || '',
    role: searchParams.get('role') || '',
    skill: searchParams.get('skill') || '',
    keyword: searchParams.get('keyword') || '',
  }))

  const debouncedSkill = useDebouncedValue(filters.skill, 300)
  const debouncedKeyword = useDebouncedValue(filters.keyword, 300)

  // Fetch stats on mount
  useEffect(() => {
    const controller = new AbortController()
    api.getStats({ signal: controller.signal })
      .then(setStats)
      .catch(() => {})
    return () => controller.abort()
  }, [])

  // Sync state to URL search params
  useEffect(() => {
    const params = {}
    if (filters.status) params.status = filters.status
    if (filters.role) params.role = filters.role
    if (debouncedSkill) params.skill = debouncedSkill
    if (debouncedKeyword) params.keyword = debouncedKeyword
    if (page > 1) params.page = String(page)
    if (pageSize !== 10) params.page_size = String(pageSize)
    if (sortBy && sortBy !== 'created_at') params.sort_by = sortBy
    if (sortOrder !== 'desc') params.sort_order = sortOrder
    setSearchParams(params, { replace: true })
  }, [filters.status, filters.role, debouncedSkill, debouncedKeyword, page, pageSize, sortBy, sortOrder])

  // Fetch candidates
  useEffect(() => {
    const controller = new AbortController()

    const fetchCandidates = async () => {
      setLoading(true)
      try {
        const data = await api.listCandidates({
          status: filters.status,
          role: filters.role,
          skill: debouncedSkill,
          keyword: debouncedKeyword,
          page,
          page_size: pageSize,
          sort_by: sortBy,
          sort_order: sortOrder,
        }, { signal: controller.signal })
        setCandidates(data.items)
        setTotal(data.total)
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Failed to fetch candidates:', err)
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    fetchCandidates()
    return () => controller.abort()
  }, [page, pageSize, filters.status, filters.role, debouncedSkill, debouncedKeyword, sortBy, sortOrder])

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    setPage(1)
  }

  const handleStatsClick = (status) => {
    setFilters((prev) => ({ ...prev, status: prev.status === status ? '' : status }))
    setPage(1)
  }

  const handleSort = (column) => {
    // Only sort by supported backend columns
    if (!['name', 'created_at', 'status', 'role_applied'].includes(column)) return
    if (sortBy === column) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortBy(column)
      setSortOrder('asc')
    }
    setPage(1)
  }

  const handlePageSizeChange = (newSize) => {
    setPageSize(newSize)
    setPage(1)
  }

  const totalPages = Math.ceil(total / pageSize)
  const startItem = total === 0 ? 0 : (page - 1) * pageSize + 1
  const endItem = Math.min(page * pageSize, total)

  const getSortIndicator = (column) => {
    if (sortBy !== column) return null
    return <span className="sort-indicator">{sortOrder === 'asc' ? '▲' : '▼'}</span>
  }

  return (
    <Layout>
      <div className="list-content">
        {/* Stats Row */}
        {stats && (
          <div className="stats-row">
            <button
              className={`stat-card stat-total ${filters.status === '' ? 'stat-active' : ''}`}
              onClick={() => handleStatsClick('')}
            >
              <span className="stat-value">{stats.total}</span>
              <span className="stat-label">Total</span>
            </button>
            <button
              className={`stat-card stat-new ${filters.status === 'new' ? 'stat-active' : ''}`}
              onClick={() => handleStatsClick('new')}
            >
              <span className="stat-value">{stats.new}</span>
              <span className="stat-label">New</span>
            </button>
            <button
              className={`stat-card stat-reviewing ${filters.status === 'reviewing' ? 'stat-active' : ''}`}
              onClick={() => handleStatsClick('reviewing')}
            >
              <span className="stat-value">{stats.reviewing}</span>
              <span className="stat-label">Reviewing</span>
            </button>
            <button
              className={`stat-card stat-interviewed ${filters.status === 'interviewed' ? 'stat-active' : ''}`}
              onClick={() => handleStatsClick('interviewed')}
            >
              <span className="stat-value">{stats.interviewed}</span>
              <span className="stat-label">Interviewed</span>
            </button>
            <button
              className={`stat-card stat-offered ${filters.status === 'offered' ? 'stat-active' : ''}`}
              onClick={() => handleStatsClick('offered')}
            >
              <span className="stat-value">{stats.offered}</span>
              <span className="stat-label">Offered</span>
            </button>
            <button
              className={`stat-card stat-rejected ${filters.status === 'rejected' ? 'stat-active' : ''}`}
              onClick={() => handleStatsClick('rejected')}
            >
              <span className="stat-value">{stats.rejected}</span>
              <span className="stat-label">Rejected</span>
            </button>
          </div>
        )}

        {/* Filters */}
        <div className="filters-bar">
          <div className="filter-group">
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              aria-label="Filter by status"
            >
              <option value="">All Statuses</option>
              {STATUS_OPTIONS.filter(Boolean).map((s) => (
                <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
              ))}
            </select>

            <select
              value={filters.role}
              onChange={(e) => handleFilterChange('role', e.target.value)}
              aria-label="Filter by role"
            >
              <option value="">All Roles</option>
              {ROLE_OPTIONS.filter(Boolean).map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>

            <input
              type="text"
              placeholder="Filter by skill..."
              value={filters.skill}
              onChange={(e) => handleFilterChange('skill', e.target.value)}
              aria-label="Filter by skill"
            />
          </div>

          <div className="search-box">
            <input
              type="text"
              placeholder="Search candidates..."
              value={filters.keyword}
              onChange={(e) => handleFilterChange('keyword', e.target.value)}
              aria-label="Search candidates"
            />
          </div>
        </div>

        {/* Table */}
        <div className="table-container">
          <table className="candidates-table">
            <thead>
              <tr>
                {SORTABLE_COLUMNS.map((col) => {
                  const isSortable = ['name', 'created_at', 'status', 'role_applied'].includes(col.key)
                  return (
                    <th
                      key={col.key}
                      className={isSortable ? 'sortable' : ''}
                      onClick={() => isSortable && handleSort(col.key)}
                    >
                      {col.label}{getSortIndicator(col.key)}
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="table-loading">Loading...</td></tr>
              ) : candidates.length === 0 ? (
                <tr><td colSpan={6} className="table-empty">No candidates match your filters.</td></tr>
              ) : (
                candidates.map((c) => (
                  <tr
                    key={c.id}
                    className="candidate-row"
                    onClick={() => navigate(`/candidates/${c.id}`)}
                  >
                    <td className="cell-name">{c.name}</td>
                    <td>{c.role_applied}</td>
                    <td>
                      <span className={`status-pill status-${c.status}`}>{c.status}</span>
                    </td>
                    <td className="cell-skills">
                      {c.skills ? (() => {
                        const allSkills = c.skills.split(',')
                        const shown = allSkills.slice(0, 3)
                        const remaining = allSkills.length - 3
                        return (
                          <>
                            {shown.map((skill) => (
                              <span key={skill} className="skill-tag">{skill.trim()}</span>
                            ))}
                            {remaining > 0 && <span className="skills-more">+{remaining} more</span>}
                          </>
                        )
                      })() : <span className="cell-no-scores">—</span>}
                    </td>
                    <td>{new Date(c.created_at).toLocaleDateString()}</td>
                    <td>
                      {c.score_count > 0 ? (
                        <span className="score-badge">
                          <span className="score-badge-count">{c.score_count} score{c.score_count !== 1 ? 's' : ''}</span>
                          <span className="score-badge-sep">●</span>
                          <span className={`score-badge-avg ${
                            c.avg_score >= 4 ? 'avg-high' : c.avg_score >= 3 ? 'avg-mid' : 'avg-low'
                          }`}>{c.avg_score}</span>
                        </span>
                      ) : (
                        <span className="cell-no-scores">No scores</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="pagination-footer">
          <div className="page-size-selector">
            <label>Rows per page:</label>
            <select
              value={pageSize}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              aria-label="Rows per page"
            >
              {PAGE_SIZE_OPTIONS.map((size) => (
                <option key={size} value={size}>{size}</option>
              ))}
            </select>
          </div>

          <span className="page-info">
            Showing {startItem}-{endItem} of {total}
          </span>

          <div className="page-nav">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-ghost"
            >
              PREV
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages || totalPages === 0}
              className="btn-ghost"
            >
              NEXT
            </button>
          </div>
        </div>
      </div>
    </Layout>
  )
}
