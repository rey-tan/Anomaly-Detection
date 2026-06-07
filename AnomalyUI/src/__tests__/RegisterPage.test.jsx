import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import RegisterPage from '../pages/RegisterPage'
import * as api from '../api'
import { vi } from 'vitest'

vi.mock('../api', () => ({ registerRequest: vi.fn(), verifyOTP: vi.fn() }))

describe('RegisterPage', () => {
  it('shows an error for a short password', async () => {
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    )

    fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'newuser' } })
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'newuser@example.com' } })
    fireEvent.change(screen.getByLabelText(/^Password/i), { target: { value: 'short' } })
    fireEvent.change(screen.getByLabelText(/Confirm password/i), { target: { value: 'short' } })
    fireEvent.click(screen.getByRole('button', { name: /Create account/i }))

    expect(await screen.findByText(/Password must be at least 8 characters long/i)).toBeInTheDocument()
  })

  it('shows an error when the email is already registered', async () => {
    api.registerRequest.mockRejectedValueOnce(new Error('Email already registered'))

    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    )

    fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'newuser' } })
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'taken@example.com' } })
    fireEvent.change(screen.getByLabelText(/^Password/i), { target: { value: 'password123' } })
    fireEvent.change(screen.getByLabelText(/Confirm password/i), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /Create account/i }))

    expect(await screen.findByText(/Email already registered/i)).toBeInTheDocument()
  })
})
