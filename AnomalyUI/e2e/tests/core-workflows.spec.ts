import { test, expect } from '@playwright/test'

const apiBase = 'http://localhost:8000'

const analysisData = {
  data: [
    {
      id: 1,
      date: '2024-01-01',
      close: 100,
      anomaly: true,
      cluster: -1,
      volume: 1000,
      change: 0,
    },
  ],
  models: {},
}

const aiExplanation = {
  source: 'AI',
  summary: 'AI generated summary',
  raw_summary: 'AI generated summary',
}

const notificationPayload = {
  id: 11,
  title: 'Analysis complete',
  message: 'Your analysis is ready. View the results now.',
  type: 'analysis_complete',
  is_read: false,
  analysis_id: 1,
  created_at: '2026-06-07T12:00:00Z',
}

async function stubLoginRoutes(page, token = 'test-token', username = 'e2euser', email = 'e2euser@example.com') {
  await page.route(`${apiBase}/login`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ access_token: token }),
  }))

  await page.route(`${apiBase}/me`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ id: 1, username, email, role: 'analyst' }),
  }))

  await page.route(`${apiBase}/me/analyses`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([]),
  }))
}

async function stubAnalysisRoutes(page) {
  await page.route(`${apiBase}/symbols`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(['API']),
  }))

  await page.route(`${apiBase}/analyze`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(analysisData),
  }))

  await page.route(`${apiBase}/analyze/explain`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(aiExplanation),
  }))
}

async function stubNotificationRoutes(page) {
  await page.route(`${apiBase}/me/notifications`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([notificationPayload]),
  }))

  await page.route(`${apiBase}/me/analyses/*/data`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(analysisData),
  }))
}

async function login(page, username, password) {
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: /Sign in to Anomaly Engine/i })).toBeVisible()
  await page.getByLabel('Username').fill(username)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: /sign in/i }).click()
  await expect(page).toHaveURL(/dashboard|analysis|results/)
}

test('Register -> OTP verification -> Login', async ({ page }) => {
  const username = `e2e-register-${Date.now()}`
  const email = `${username}@example.com`
  const password = 'Password123!'

  await page.route(`${apiBase}/register/request`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ message: 'OTP sent to your email. Verify within 10 minutes.', email, user_id: 1 }),
  }))

  await page.route(`${apiBase}/register/verify`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ id: 1, username, email, role: 'analyst', email_verified: true }),
  }))

  await page.goto('/register')
  await expect(page.getByRole('heading', { name: /Create an account/i })).toBeVisible()
  await page.getByLabel('Username').fill(username)
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByLabel('Confirm password', { exact: true }).fill(password)
  await page.getByRole('button', { name: /create account/i }).click()

  await expect(page.getByText(/OTP sent to your email/i)).toBeVisible()
  await page.getByLabel('OTP code').fill('123456')
  await page.getByRole('button', { name: /verify otp/i }).click()

  await expect(page.getByRole('heading', { name: /Sign in to Anomaly Engine/i })).toBeVisible()
})

test('Login -> Analysis -> Results', async ({ page }) => {
  const username = `e2e-login-${Date.now()}`
  const password = 'Password123!'

  await stubLoginRoutes(page, 'login-token', username, `${username}@example.com`)
  await stubAnalysisRoutes(page)

  await login(page, username, password)

  await page.goto('/analysis')
  await expect(page.getByRole('button', { name: /run analysis/i })).toBeVisible()
  await page.getByRole('button', { name: /run analysis/i }).click()

  await page.waitForURL('**/results', { timeout: 15000 })
  await expect(page.getByRole('heading', { name: /Inspect the latest analysis outputs/i })).toBeVisible()
})

test('Analysis -> Notifications received -> click View Analysis -> Results', async ({ page }) => {
  const username = `e2e-notify-${Date.now()}`
  const password = 'Password123!'

  await stubLoginRoutes(page, 'notify-token', username, `${username}@example.com`)
  await stubAnalysisRoutes(page)
  await stubNotificationRoutes(page)

  await login(page, username, password)

  const alerts = page.getByRole('button', { name: /alerts/i })
  await expect(alerts).toBeVisible()
  await alerts.click()

  await expect(page.getByRole('button', { name: /View Analysis/i })).toBeVisible()
  await page.getByRole('button', { name: /View Analysis/i }).click()

  await page.waitForURL('**/results', { timeout: 15000 })
  await expect(page.getByRole('heading', { name: /Inspect the latest analysis outputs/i })).toBeVisible()
})

test('Results -> Analyze with AI -> explanation displayed', async ({ page }) => {
  const username = `e2e-ai-${Date.now()}`
  const password = 'Password123!'

  await stubLoginRoutes(page, 'ai-token', username, `${username}@example.com`)
  await stubAnalysisRoutes(page)

  await login(page, username, password)

  await page.goto('/analysis')
  await expect(page.getByRole('button', { name: /run analysis/i })).toBeVisible()
  await page.getByRole('button', { name: /run analysis/i }).click()

  await page.waitForURL('**/results', { timeout: 15000 })
  await expect(page.getByRole('button', { name: /analyze with AI/i })).toBeVisible()
  await page.getByRole('button', { name: /analyze with AI/i }).click()
  await expect(page.getByText(/AI generated summary/i)).toBeVisible()
})

test('Sign out returns to login', async ({ page }) => {
  const username = `e2e-signout-${Date.now()}`
  const password = 'Password123!'

  await stubLoginRoutes(page, 'signout-token', username, `${username}@example.com`)
  await page.route(`${apiBase}/me/analyses`, route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) }))

  await login(page, username, password)

  await page.getByRole('button', { name: /sign out/i }).click()
  await expect(page.getByRole('heading', { name: /Sign in to Anomaly Engine/i })).toBeVisible()
})
