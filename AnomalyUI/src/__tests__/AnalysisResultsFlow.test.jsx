import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AppRoutes from '../routes/AppRoutes'

describe('App routing', () => {
  it('renders the login page when unauthenticated and visiting /login', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <AppRoutes
          user={null}
          token=""
          analyses={[]}
          setAnalyses={() => {}}
          results={null}
          selectedAnalysis={null}
          setResults={() => {}}
          setSelectedAnalysis={() => {}}
          aiExplanation={null}
          aiExplanationMarkdown=""
          aiError=""
          aiLoading={false}
          handleExplainWithAI={() => {}}
          activityUser={null}
          handleOpenLastRun={() => {}}
          handleAnalyze={() => {}}
          handleSelectAnalysis={() => {}}
          loading={false}
          error=""
          onLogout={() => {}}
          onOpenNotifications={() => {}}
          setActivityUser={() => {}}
          handleLogin={() => {}}
        />
      </MemoryRouter>
    )

    expect(screen.getByText(/Sign in to Anomaly Engine/i)).toBeInTheDocument()
  })
})
