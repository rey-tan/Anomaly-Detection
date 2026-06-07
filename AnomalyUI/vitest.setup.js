import React from 'react'
import '@testing-library/jest-dom'
import { vi } from 'vitest'

vi.mock('react-chartjs-2', () => ({
  __esModule: true,
  Line: (props) => React.createElement('div', { 'data-testid': 'mock-line-chart', ...props }),
  Scatter: (props) => React.createElement('div', { 'data-testid': 'mock-scatter-chart', ...props }),
}))

// Mock localStorage for jsdom environment
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}

global.localStorage = localStorageMock

if (typeof window !== 'undefined' && window.HTMLCanvasElement) {
  window.HTMLCanvasElement.prototype.getContext = () => ({
    fillRect: () => {},
    clearRect: () => {},
    getImageData: () => ({ data: [] }),
    putImageData: () => {},
    createImageData: () => ({ width: 0, height: 0 }),
    setTransform: () => {},
    drawImage: () => {},
    save: () => {},
    restore: () => {},
    beginPath: () => {},
    moveTo: () => {},
    lineTo: () => {},
    closePath: () => {},
    stroke: () => {},
    fillText: () => {},
    measureText: () => ({ width: 0 }),
    transform: () => {},
    translate: () => {},
    scale: () => {},
    arc: () => {},
    fill: () => {},
    strokeRect: () => {},
    clip: () => {},
    setLineDash: () => {},
    getContextAttributes: () => ({}),
  })
}

// Reset mocks before each test
beforeEach(() => {
  vi.clearAllMocks()
})


