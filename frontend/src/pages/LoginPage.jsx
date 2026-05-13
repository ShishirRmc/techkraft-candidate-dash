import { useState } from 'react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './LoginPage.css'

export default function LoginPage() {
  const { login } = useAuth()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const justRegistered = location.state?.registered
  const sessionExpired = searchParams.get('expired') === 'true'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err.message || 'Login failed')
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
          <p className="text-eyebrow login-eyebrow">CANDIDATE DASHBOARD</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {justRegistered && (
            <div className="login-success">Account created. Sign in below.</div>
          )}
          {sessionExpired && (
            <div className="login-error">Your session has expired. Please sign in again.</div>
          )}
          {error && <div className="login-error">{error}</div>}

          <div className="form-field">
            <label htmlFor="email" className="text-caption">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@techkraft.com"
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
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? 'SIGNING IN...' : 'SIGN IN'}
          </button>
        </form>

        <p className="login-hint text-caption">
          Don't have an account? <Link to="/register" className="auth-link">Sign up</Link>
        </p>
        <p className="login-hint text-caption">
          Demo: reviewer1@techkraft.com / reviewer123
        </p>
      </div>
    </div>
  )
}
