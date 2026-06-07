import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import AnalysisHistory from '../components/AnalysisHistory'
import * as api from '../api'
import { vi } from 'vitest'

vi.mock('../api', () => ({
  fetchAnalyses: vi.fn(),
  fetchAnalysisData: vi.fn(),
  toggleFavorite: vi.fn(),
}))

describe('AnalysisHistory', () => {
  it('renders recent analyses and allows selecting one', async () => {
    api.fetchAnalyses.mockResolvedValue([{ id: 1, stock: 'API', executed_at: new Date().toISOString(), mode: 'Static', timeframe: '1D', status: 'success', is_favorite: false }])
    api.fetchAnalysisData.mockResolvedValue({ data: [] })

    const onSelectAnalysis = vi.fn()
    render(<AnalysisHistory token="tok" onSelectAnalysis={onSelectAnalysis} />)

    expect(await screen.findByText(/API/i)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /View/i }))
    await waitFor(() => expect(onSelectAnalysis).toHaveBeenCalledWith(1))
  })
})
