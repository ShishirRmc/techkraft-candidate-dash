import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#1f1633',
          padding: '24px',
        }}>
          <div style={{
            backgroundColor: '#150f23',
            border: '1px solid #362d59',
            borderRadius: '12px',
            padding: '32px',
            maxWidth: '480px',
            textAlign: 'center',
          }}>
            <h1 style={{
              fontFamily: "'Space Grotesk', 'Rubik', sans-serif",
              fontSize: '24px',
              fontWeight: 500,
              color: '#ffffff',
              marginBottom: '12px',
            }}>
              Something went wrong
            </h1>
            <p style={{
              fontFamily: "'Rubik', sans-serif",
              fontSize: '14px',
              color: 'rgba(255,255,255,0.72)',
              lineHeight: 1.5,
              marginBottom: '24px',
            }}>
              An unexpected error occurred. Please refresh the page to try again.
            </p>
            <button
              onClick={() => window.location.reload()}
              style={{
                backgroundColor: '#ffffff',
                color: '#1f1633',
                fontFamily: "'Rubik', sans-serif",
                fontSize: '14px',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.2px',
                padding: '12px 16px',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                minHeight: '44px',
              }}
            >
              RELOAD PAGE
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
