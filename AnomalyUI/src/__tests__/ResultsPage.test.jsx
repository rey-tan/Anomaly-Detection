import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'

vi.mock('../api', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    explainAnalysis: vi.fn(() => Promise.resolve({ raw_summary: 'OK', summary: 'OK', entries: [], anomaly_count: 0, source: 'ai' })),
  }
})
import * as api from '../api'
import ResultsPage from '../pages/ResultsPage'

const mockResults = {
  data: [
    { date: '2026-06-01', close: 100, cluster: -1, RSI: 50, bb_width: 1.4 },
    { date: '2026-06-02', close: 101, cluster: 0, RSI: 55, bb_width: 1.1 },
  ],
  models: {
    DBSCAN: { metrics: { precision: 0.9 }, params: { eps: 0.5 } },
  },
}

describe('ResultsPage', () => {
  it('renders the empty state when no results are available', () => {
    render(
      <ResultsPage
        token="tok"
        results={null}
        selectedAnalysis={null}
        setResults={() => {}}
        setSelectedAnalysis={() => {}}
        handleSelectAnalysis={() => {}}
        navigate={() => {}}
      />
    )

    expect(screen.getByText(/No results yet/i)).toBeInTheDocument()
    expect(screen.getByText(/Chart preview/i)).toBeInTheDocument()
  })

  it('renders results summary and a working AI button', async () => {
    render(
      <ResultsPage
        token="tok"
        results={mockResults}
        selectedAnalysis={{ id: 1, stock: 'API', timeframe: '1D', mode: 'Static', start_date: '2026-06-01', end_date: '2026-06-02' }}
        setResults={() => {}}
        setSelectedAnalysis={() => {}}
        handleSelectAnalysis={() => {}}
        navigate={() => {}}
      />
    )

    expect(screen.getByText(/Data points/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Analyze with AI/i }))
    await waitFor(() => expect(api.explainAnalysis).toHaveBeenCalled())
  })
})
