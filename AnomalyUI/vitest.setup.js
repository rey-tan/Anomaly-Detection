import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock localStorage for jsdom environment
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}

global.localStorage = localStorageMock

// Reset mocks before each test
beforeEach(() => {
  vi.clearAllMocks()
})


