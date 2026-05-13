import { useAuth } from '../context/AuthContext'
import './Layout.css'
import './shared.css'

export default function Layout({ children }) {
  const { user, logout } = useAuth()

  return (
    <div className="app-layout">
      {/* Skip to content link — WCAG 2.1 */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <header role="banner">
        <nav className="nav-bar" aria-label="Primary navigation">
          <div className="nav-brand text-heading-sm">
            Tech<span className="lime-chip-sm">Kraft</span>
          </div>
          <div className="nav-right">
            {user && (
              <>
                <span className="nav-user text-caption">
                  {user.email}
                  <span className="role-pill">{user.role}</span>
                </span>
                <button onClick={logout} className="btn-ghost">LOGOUT</button>
              </>
            )}
          </div>
        </nav>
      </header>

      <main id="main-content">
        {children}
      </main>
    </div>
  )
}
