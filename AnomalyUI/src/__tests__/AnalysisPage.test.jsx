import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AnalysisPage from '../pages/AnalysisPage'

describe('AnalysisPage', () => {
  it('renders the analysis page heading', () => {
    render(
      <MemoryRouter>
        <AnalysisPage token="tok" setResults={() => {}} setSelectedAnalysis={() => {}} />
      </MemoryRouter>
    )
    expect(screen.getByText(/Run a new anomaly detection job/i)).toBeInTheDocument()
  })

  it('renders an error when one is provided', () => {
    const message = 'Analysis failed due to network issues'
    render(
      <MemoryRouter>
        <AnalysisPage token="tok" setResults={() => {}} setSelectedAnalysis={() => {}} error={message} />
      </MemoryRouter>
    )
    expect(screen.getByText(message)).toBeInTheDocument()
  })
})
