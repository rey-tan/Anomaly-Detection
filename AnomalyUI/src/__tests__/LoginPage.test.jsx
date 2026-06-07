import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import LoginPage from '../pages/LoginPage'
import * as api from '../api'
import { vi } from 'vitest'

vi.mock('../api', () => ({ login: vi.fn() }))

describe('LoginPage', () => {
  it('renders the login form and calls login with credentials', async () => {
    api.login.mockResolvedValue({ access_token: 'token-123' })
    const onSuccess = vi.fn()

    render(
      <BrowserRouter>
        <LoginPage onSuccess={onSuccess} />
      </BrowserRouter>
    )

    fireEvent.change(screen.getByLabelText(/Username/i), { target: { value: 'testuser' } })
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'password' } })
    fireEvent.click(screen.getByRole('button', { name: /Sign in/i }))

    await waitFor(() => expect(api.login).toHaveBeenCalledWith('testuser', 'password'))
    expect(onSuccess).toHaveBeenCalledWith('token-123')
  })
})
