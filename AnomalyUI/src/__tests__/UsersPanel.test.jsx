import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import UsersPanel from '../components/UsersPanel'
import * as api from '../api'
import { vi } from 'vitest'

vi.mock('../api', () => ({ getUsers: vi.fn(), createUser: vi.fn(), updateUserRole: vi.fn(), deleteUser: vi.fn() }))

describe('UsersPanel', () => {
  it('renders the user list after loading users', async () => {
    api.getUsers.mockResolvedValue([{ id: 1, username: 'admin', role: 'admin' }])

    render(<UsersPanel token="abc" currentUser={{ id: 1, username: 'admin', role: 'admin' }} />)

    expect(await screen.findByText(/admin/i)).toBeInTheDocument()
    expect(api.getUsers).toHaveBeenCalledWith('abc')
  })

  it('creates a user when the form is submitted', async () => {
    api.getUsers.mockResolvedValueOnce([]).mockResolvedValueOnce([{ id: 2, username: 'newuser', role: 'analyst' }])
    api.createUser.mockResolvedValue({ id: 2, username: 'newuser', role: 'analyst' })

    render(<UsersPanel token="abc" currentUser={{ id: 1, username: 'admin', role: 'admin' }} />)

    fireEvent.change(screen.getByPlaceholderText(/email/i), { target: { value: 'newuser@example.com' } })
    fireEvent.change(screen.getByPlaceholderText(/username/i), { target: { value: 'newuser' } })
    fireEvent.change(screen.getByPlaceholderText(/password/i), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /Create user/i }))

    await waitFor(() => expect(api.createUser).toHaveBeenCalledWith('abc', 'newuser@example.com', 'newuser', 'password123', 'analyst'))
  })
})
