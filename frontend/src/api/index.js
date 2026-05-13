const API_BASE = ''

function getToken() {
  return localStorage.getItem('token')
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  }

  const fetchOptions = { ...options, headers }
  // Pass signal through for AbortController support
  if (options.signal) {
    fetchOptions.signal = options.signal
  }

  const res = await fetch(`${API_BASE}${path}`, fetchOptions)

  if (!res.ok) {
    // Handle expired/invalid token — redirect to login
    if (res.status === 401 && token && !path.startsWith('/auth/')) {
      localStorage.removeItem('token')
      window.location.href = '/login?expired=true'
      return
    }

    const body = await res.json().catch(() => ({}))
    const error = new Error(body.detail || `Request failed: ${res.status}`)
    error.status = res.status
    throw error
  }

  if (res.status === 204) return null

  return res.json()
}

export const api = {
  // Auth
  login: (email, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),

  register: (email, password) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) }),

  me: () => request('/auth/me'),

  // Candidates
  listCandidates: (params = {}, options = {}) => {
    const query = new URLSearchParams()
    if (params.status) query.set('status', params.status)
    if (params.role) query.set('role', params.role)
    if (params.skill) query.set('skill', params.skill)
    if (params.keyword) query.set('keyword', params.keyword)
    if (params.page) query.set('page', params.page)
    if (params.page_size) query.set('page_size', params.page_size)
    if (params.sort_by) query.set('sort_by', params.sort_by)
    if (params.sort_order) query.set('sort_order', params.sort_order)
    return request(`/candidates?${query.toString()}`, options)
  },

  getStats: () => request('/candidates/stats'),

  getCandidate: (id, options = {}) => request(`/candidates/${id}`, options),

  submitScore: (candidateId, data) =>
    request(`/candidates/${candidateId}/scores`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  deleteScore: (candidateId, scoreId) =>
    request(`/candidates/${candidateId}/scores/${scoreId}`, { method: 'DELETE' }),

  generateSummary: (candidateId) =>
    request(`/candidates/${candidateId}/summary`, { method: 'POST' }),

  updateNotes: (candidateId, internalNotes) =>
    request(`/candidates/${candidateId}/notes`, {
      method: 'PATCH',
      body: JSON.stringify({ internal_notes: internalNotes }),
    }),
}
