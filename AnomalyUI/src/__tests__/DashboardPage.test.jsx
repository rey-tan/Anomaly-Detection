import React from 'react'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import DashboardPage from '../pages/Dashboard'

describe('DashboardPage', () => {
  it('renders the dashboard and shows the user role', () => {
    const user = { id: 1, username: 'analyst', role: 'analyst' }
    render(
      <BrowserRouter>
        <DashboardPage user={user} selectedAnalysis={null} results={null} onOpenLastRun={() => {}} />
      </BrowserRouter>
    )

    expect(screen.getByText(/Overview of the current anomaly workspace/i)).toBeInTheDocument()
    expect(screen.getByText(/Role: analyst/i)).toBeInTheDocument()
  })
})
