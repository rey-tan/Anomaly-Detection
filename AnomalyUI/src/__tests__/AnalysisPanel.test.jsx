import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import AnalysisPanel from '../components/AnalysisPanel'
import * as api from '../api'
import { vi } from 'vitest'

vi.mock('../api', () => ({ fetchSymbols: vi.fn() }))

describe('AnalysisPanel', () => {
  it('renders the form and loads the symbol list', async () => {
    api.fetchSymbols.mockResolvedValue(['API'])
    render(<AnalysisPanel onSubmit={() => {}} loading={false} />)

    expect(await screen.findByRole('button', { name: /run analysis/i })).toBeInTheDocument()
    await waitFor(() => expect(api.fetchSymbols).toHaveBeenCalled())
  })
})
