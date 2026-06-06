import { useState } from 'react'
import { login } from '../api'

export default function LoginPage({ onSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await login(username, password)
      const token = response.access_token || response.token || response.accessToken
      if (!token) {
        throw new Error('Login response did not include an access token.')
      }
      onSuccess(token)
    } catch (err) {
      setError(err.message || 'Unable to login. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-background">
        <span />
        <span />
        <span />
      </div>
      <div className="auth-panel">
        <div className="brand-block">
          <p className="eyebrow">Secure access</p>
          <h1>Sign in to Anomaly Engine</h1>
          <p>
            Use your analyst account to run anomaly detection, review findings, and manage the workspace in dedicated pages.
          </p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              placeholder="Username or email"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          <button type="submit" className="primary-button" disabled={loading}>
            {loading ? "Authenticating…" : "Sign in"}
          </button>
          {error ? <div className="form-error">{error}</div> : null}
          <p className="auth-footer">
            Don't have an account? <a href="/register">Create one</a>
          </p>
        </form>
      </div>
    </main>
  )
}
