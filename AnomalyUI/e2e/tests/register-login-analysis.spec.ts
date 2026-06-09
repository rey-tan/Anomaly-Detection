import { test, expect } from '@playwright/test'



test('System test: Register -> Login -> Analysis -> Results -> AI explanation -> Sign out', async ({ page, request }) => {
  const uiBase = 'http://localhost:5173'
  const apiBase = 'http://localhost:8000'
  const username = `e2eui_${Date.now()}`
  const email = `${username}@example.com`
  const password = 'Password123!'

  await page.route(`${apiBase}/register/request`, async (route) => {
    const payload = route.request().postDataJSON()
    const response = await request.post(`${apiBase}/test/register/request`, { data: payload })
    if (!response.ok()) {
      return route.fulfill({ status: response.status(), body: await response.text() })
    }
    const body = await response.text()
    return route.fulfill({ status: 200, contentType: 'application/json', body })
  })

  await page.route(`${apiBase}/register/verify`, async (route) => {
    const payload = route.request().postDataJSON()
    const response = await request.post(`${apiBase}/test/register/verify`, { data: payload })
    if (!response.ok()) {
      return route.fulfill({ status: response.status(), body: await response.text() })
    }
    const body = await response.text()
    return route.fulfill({ status: 200, contentType: 'application/json', body })
  })

  await page.goto(`${uiBase}/register`)
  await expect(page.getByRole('heading', { name: /Create an account/i })).toBeVisible()
  await page.getByLabel('Username').fill(username)
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByLabel('Confirm password', { exact: true }).fill(password)
  await page.getByRole('button', { name: /create account/i }).click()

  await expect(page.getByText(/OTP sent to your email/i)).toBeVisible()
  await expect(page.getByLabel('OTP code')).toBeVisible()

  await page.getByLabel('OTP code').fill('123456')
  await page.getByRole('button', { name: /verify otp/i }).click()

  await expect(page.getByRole('heading', { name: /Sign in to Anomaly Engine/i })).toBeVisible({ timeout: 10000 })

  // Login through the UI
  await page.getByLabel('Username').fill(username)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: /sign in/i }).click()

  await expect(page).toHaveURL(/dashboard|analysis|results/)
  // confirm we're authenticated (sign-out button present) before navigating
  await expect(page.getByRole('button', { name: /sign out/i })).toBeVisible({ timeout: 10000 })

  await page.goto(`${uiBase}/analysis`)
  // give the analysis panel a bit more time to render in CI/slow environments
  await expect(page.getByRole('button', { name: /run analysis/i })).toBeVisible({ timeout: 15000 })
  await page.getByLabel('Start date').fill('2025-05-01')
  await page.getByLabel('End date').fill('2026-01-01')
  await page.getByRole('button', { name: /run analysis/i }).click()

  await page.waitForURL('**/results', { timeout: 60000 })
  await expect(page.getByRole('button', { name: /analyze with AI/i })).toBeVisible()
  await Promise.all([
    page.waitForResponse((resp) => resp.url().includes('/analyze/explain') && resp.status() === 200, { timeout: 60000 }),
    page.getByRole('button', { name: /analyze with AI/i }).click(),
  ])

  await expect(page.getByText(/Why these points were flagged/i)).toBeVisible({ timeout: 60000 })
  await expect(page.getByText(/Source:/i)).toBeVisible({ timeout: 60000 })

  await page.getByRole('button', { name: /sign out/i }).click()
  await expect(page.getByRole('heading', { name: /Sign in to Anomaly Engine/i })).toBeVisible()
})
