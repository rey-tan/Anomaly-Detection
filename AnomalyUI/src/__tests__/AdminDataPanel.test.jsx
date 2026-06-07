import React from 'react'
import { render, screen } from '@testing-library/react'
import AdminDataPanel from '../components/AdminDataPanel'
import * as api from '../api'
import { vi } from 'vitest'

vi.mock('../api', () => ({
  fetchAdminSymbols: vi.fn(),
  fetchAdminPreview: vi.fn(),
  downloadAdminFile: vi.fn(),
  runAdminScrape: vi.fn(),
}))

describe('AdminDataPanel', () => {
  it('renders and loads the admin symbol list', async () => {
    api.fetchAdminSymbols.mockResolvedValue([{ name: 'API', first_date: '2024-01-01', last_date: '2024-12-31' }])

    render(<AdminDataPanel token="token-123" />)

    expect(await screen.findByText(/Dataset inventory and scraping/i)).toBeInTheDocument()
    expect(await screen.findByText('API')).toBeInTheDocument()
  })
})
