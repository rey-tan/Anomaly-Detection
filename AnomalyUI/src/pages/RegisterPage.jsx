import React from 'react'
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { registerRequest, verifyOTP } from '../api'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [otp, setOtp] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const validateEmail = (value) => /[^@\s]+@[^@\s]+\.[^@\s]+/.test(value)

  const handleRegister = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (!username || !email || !password || !confirmPassword) {
      setError('All fields are required.')
      return
    }

    if (username.length < 3) {
      setError('Username must be at least 3 characters long.')
      return
    }

    if (!validateEmail(email)) {
      setError('Please enter a valid email address.')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await registerRequest(username, email, password)
      setSuccess('OTP sent to your email. Enter it below to complete registration.')
      setStep(2)
    } catch (err) {
      setError(err.message || 'Unable to send OTP. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (!otp) {
      setError('Please enter the OTP sent to your email.')
      return
    }

    setLoading(true)
    try {
      await verifyOTP(email, otp)
      setSuccess('Email verified! Redirecting to login...')
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      setError(err.message || 'Unable to verify OTP. Please try again.')
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
          <p className="eyebrow">Get started</p>
          <h1>Create an account</h1>
          <p>
            Register for an analyst account with email verification before signing in.
          </p>
        </div>
        <form className="auth-form" onSubmit={step === 1 ? handleRegister : handleVerify}>
          {step === 1 ? (
            <>
              <label>
                Username
                <input
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  autoComplete="username"
                  required
                />
              </label>
              <label>
                Email
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="email"
                  required
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="new-password"
                  required
                />
              </label>
              <label>
                Confirm password
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  autoComplete="new-password"
                  required
                />
              </label>
            </>
          ) : (
            <>
              <label>
                Email
                <input
                  type="email"
                  value={email}
                  readOnly
                />
              </label>
              <label>
                OTP code
                <input
                  value={otp}
                  onChange={(event) => setOtp(event.target.value)}
                  autoComplete="one-time-code"
                  placeholder="Enter OTP"
                  required
                />
              </label>
            </>
          )}
          <button type="submit" className="primary-button" disabled={loading}>
            {loading ? (step === 1 ? 'Sending OTP…' : 'Verifying OTP…') : (step === 1 ? 'Create account' : 'Verify OTP')}
          </button>
          {error ? <div className="form-error">{error}</div> : null}
          {success ? <div className="form-success">{success}</div> : null}
          <p className="auth-footer">
            Already have an account? <Link to="/login" className="highlighted-text">Sign in</Link>
          </p>
        </form>
      </div>
    </main>
  )
}
