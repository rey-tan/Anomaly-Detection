import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import NotificationsDropdown from '../components/NotificationsDropdown'
import * as api from '../api'
import { vi } from 'vitest'

vi.mock('../api', () => ({ fetchNotifications: vi.fn(), markNotificationRead: vi.fn() }))

describe('NotificationsDropdown', () => {
  it('renders the notification dropdown and displays items', async () => {
    api.fetchNotifications.mockResolvedValue([{ id: 1, title: 'New alert', message: 'Check your analysis', type: 'analysis_complete', is_read: false, analysis_id: 42, created_at: '2026-06-07T12:00:00Z' }])

    render(
      <MemoryRouter>
        <NotificationsDropdown token="tok" onOpenAll={() => {}} onSelectAnalysis={() => {}} />
      </MemoryRouter>
    )

    fireEvent.click(await screen.findByRole('button', { name: /Alerts/i }))
    expect(await screen.findByText(/New alert/i)).toBeInTheDocument()
    expect(screen.getByText(/Recent alerts/i)).toBeInTheDocument()
  })
})
