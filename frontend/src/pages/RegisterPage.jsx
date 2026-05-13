import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import './LoginPage.css'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [touched, setTouched] = useState(false)

  const passwordTooShort = touched && password.length > 0 && password.length < 6

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (password.length < 6) {
      setTouched(true)
      return
    }
    setError('')
    setLoading(true)
    try {
      await api.register(email, password)
      navigate('/login', { state: { registered: true } })
    } catch (err) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h1 className="text-heading-xl">
            Tech<span className="lime-chip">Kraft</span>
          </h1>
          <p className="text-eyebrow login-eyebrow">CREATE ACCOUNT</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && <div className="login-error">{error}</div>}

          <div className="form-field">
            <label htmlFor="email" className="text-caption">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div className="form-field">
            <label htmlFor="password" className="text-caption">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setTouched(true) }}
              onBlur={() => setTouched(true)}
              placeholder="••••••••"
              required
              autoComplete="new-password"
              minLength={6}
              aria-describedby="password-hint"
            />
            {passwordTooShort && (
              <span id="password-hint" className="field-error" role="alert">
                Password must be at least 6 characters
              </span>
            )}
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading || passwordTooShort}
          >
            {loading ? 'CREATING ACCOUNT...' : 'SIGN UP'}
          </button>
        </form>

        <p className="login-hint text-caption">
          Already have an account? <Link to="/login" className="auth-link">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
