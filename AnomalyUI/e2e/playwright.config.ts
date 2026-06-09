import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e/tests',
  timeout: 120_000,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
  },
})
