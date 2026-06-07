import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
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

describe('ResultsPage AI actions', () => {
  it('shows the AI explanation button and calls the handler on click', () => {
    const handleExplain = vi.fn()

    render(
      <ResultsPage
        token="tok"
        results={mockResults}
        selectedAnalysis={{ id: 1, stock: 'API', timeframe: '1D', mode: 'Static' }}
        setResults={() => {}}
        setSelectedAnalysis={() => {}}
        aiExplanation={null}
        aiExplanationMarkdown=""
        aiError=""
        aiLoading={false}
        handleExplainWithAI={handleExplain}
        handleSelectAnalysis={() => {}}
        navigate={() => {}}
      />
    )

    const analyzeButton = screen.getByRole('button', { name: /Analyze with AI/i })
    expect(analyzeButton).toBeInTheDocument()

    fireEvent.click(analyzeButton)
    expect(handleExplain).toHaveBeenCalled()
  })
})
