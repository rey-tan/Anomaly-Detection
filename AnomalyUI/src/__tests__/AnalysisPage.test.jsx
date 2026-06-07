import React from 'react'
import { render, screen } from '@testing-library/react'
import AnalysisPage from '../pages/AnalysisPage'

describe('AnalysisPage', () => {
  it('renders the analysis page heading', () => {
    render(<AnalysisPage onSubmit={() => {}} loading={false} error="" />)
    expect(screen.getByText(/Run a new anomaly detection job/i)).toBeInTheDocument()
  })

  it('renders an error when one is provided', () => {
    const message = 'Analysis failed due to network issues'
    render(<AnalysisPage onSubmit={() => {}} loading={false} error={message} />)
    expect(screen.getByText(message)).toBeInTheDocument()
  })
})
