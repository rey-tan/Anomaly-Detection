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


async function stubLoginRoutes(page: any, token = 'test-token', username = 'e2euser', email = 'e2euser@example.com') {
  await page.route(`${apiBase}/login`, (route: any) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ access_token: token }),
  }))

  await page.route(`${apiBase}/me`, (route: any) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ id: 1, username, email, role: 'analyst' }),
  }))

  await page.route(`${apiBase}/me/analyses`, (route: any) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([]),
  }))
}

async function stubAnalysisRoutes(page: any, analysisResponse: any = analysisData) {
  await page.route(`${apiBase}/symbols`, (route: any) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(['API']),
  }))

  await page.route(`${apiBase}/analyze`, (route: any) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(analysisResponse),
  }))

  await page.route(`${apiBase}/analyze/explain`, (route: any) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(aiExplanation),
  }))
}


async function login(page: any, username: string, password: string) {
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

test('Returning user journey: Login → view analysis history → run new analysis → compare results → sign out', async ({ page }) => {
  const username = `e2e-returning-${Date.now()}`
  const password = 'Password123!'

  const historyList = [
    {
      id: 1,
      stock: 'API',
      timeframe: '1D',
      start_date: '2025-01-01',
      end_date: '2025-06-01',
      status: 'success',
      executed_at: '2025-06-02T12:00:00Z',
      is_favorite: false,
      metrics: {},
      best_params: {},
    },
  ]

  const historyData = {
    data: [
      {
        date: '2025-01-02',
        close: 100,
        cluster: -1,
        cluster_dbscan: -1,
        anomaly: true,
        volume: 1000,
        change: 0,
      },
    ],
    models: {},
  }

  const newAnalysisResult = {
    data: [
      {
        id: 2,
        date: '2025-02-01',
        close: 110,
        cluster: -1,
        cluster_dbscan: -1,
        anomaly: true,
        volume: 1500,
        change: 1.0,
      },
      {
        id: 3,
        date: '2025-02-02',
        close: 112,
        cluster: 1,
        cluster_dbscan: 1,
        anomaly: false,
        volume: 900,
        change: 0.02,
      },
    ],
    models: {},
  }

  await stubLoginRoutes(page, 'returning-token', username, `${username}@example.com`)

  await page.route(`${apiBase}/me/analyses`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(historyList),
  }))

  await page.route(`${apiBase}/me/analyses/1/data`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(historyData),
  }))

  await stubAnalysisRoutes(page, newAnalysisResult)

  await login(page, username, password)

  await page.goto('/results')
  await expect(page.getByText(/Past analyses/i)).toBeVisible()
  await expect(page.getByRole('heading', { name: /Quickly revisit prior runs/i })).toBeVisible()
  const firstHistoryItem = page.locator('.analysis-list article').first()
  await expect(firstHistoryItem).toBeVisible()
  await firstHistoryItem.getByRole('button', { name: /View/i }).click()

  await expect(page.getByText('100')).toBeVisible()
  await expect(page.getByText(/Data points/i)).toBeVisible()

  await page.goto('/analysis')
  await expect(page.getByRole('button', { name: /run analysis/i })).toBeVisible()
  await page.getByLabel('Start date').fill('2025-02-01')
  await page.getByLabel('End date').fill('2025-02-28')
  await page.getByRole('button', { name: /run analysis/i }).click()

  await page.waitForURL('**/results', { timeout: 15000 })
  await expect(page.getByText('110')).toBeVisible()
  await expect(page.getByText(/Data points/i)).toBeVisible()
  // Request AI explanation for the new results and verify it's displayed
  await page.getByRole('button', { name: /analyze with AI/i }).click()
  await expect(page.getByText(/AI generated summary/i)).toBeVisible()

  await page.getByRole('button', { name: /sign out/i }).click()
  await expect(page.getByRole('heading', { name: /Sign in to Anomaly Engine/i })).toBeVisible()
})

test('Admin journey: Login → create user → delete user → view activity log → logout', async ({ page }) => {
  const username = `e2e-admin-${Date.now()}`
  const password = 'Password123!'
  const newUsername = `newuser-${Date.now()}`

  let users = [
    { id: 1, username, role: 'admin' },
  ]
  let nextUserId = 2

  await page.route(`${apiBase}/login`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ access_token: 'admin-token' }),
  }))

  await page.route(`${apiBase}/me`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ id: 1, username, email: `${username}@example.com`, role: 'admin' }),
  }))

  await page.route(`${apiBase}/me/analyses`, route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([]),
  }))

  await page.route(`${apiBase}/admin/users`, async (route) => {
    const request = route.request()
    if (request.method() === 'GET') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(users),
      })
    }
    if (request.method() === 'POST') {
      const payload = request.postDataJSON()
      const newUser = {
        id: nextUserId++,
        username: payload.username,
        role: payload.role || 'analyst',
      }
      users = [...users, newUser]
      return route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(newUser),
      })
    }
    return route.continue()
  })

  await page.route(new RegExp(`${apiBase}/admin/users/\\d+$`), async (route) => {
    const request = route.request()
    if (request.method() === 'DELETE') {
      const segments = new URL(request.url()).pathname.split('/')
      const userId = Number(segments.at(-1))
      users = users.filter((u) => u.id !== userId)
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'User deleted' }),
      })
    }
    return route.continue()
  })

  await page.route(new RegExp(`${apiBase}/admin/users/\\d+/activity`), async (route) => {
    const userId = Number(new URL(route.request().url()).pathname.split('/').slice(-2, -1)[0])
    const activity = [
      {
        id: 1,
        user_id: userId,
        username: userId === 1 ? username : newUsername,
        action: 'login',
        resource: 'user',
        details: { message: 'User logged in' },
        created_at: '2026-06-09T10:00:00Z',
      },
    ]
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(activity),
    })
  })

  await login(page, username, password)
  await page.goto('/users')

  await expect(page.getByRole('heading', { name: /User management/i })).toBeVisible()
  await page.getByPlaceholder('email').fill(`${newUsername}@example.com`)
  await page.getByPlaceholder('username').fill(newUsername)
  await page.getByPlaceholder('password').fill(password)
  const createUserRequest = page.waitForRequest((request) => request.url().endsWith('/admin/users') && request.method() === 'POST')
  await page.getByRole('button', { name: /create user/i }).click()
  await createUserRequest

  await expect(page.getByText(newUsername)).toBeVisible()

  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: /delete/i }).click()

  await expect(page.locator(`text=${newUsername}`)).not.toBeVisible()

  await page.getByRole('button', { name: /Activity/i }).click()
  await expect(page).toHaveURL(/\/activity$/)
  await expect(page.getByRole('heading', { name: /Audit log/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Show details/i })).toBeVisible()
  await page.getByRole('button', { name: /Show details/i }).click()
  await expect(page.getByText(/User logged in/i)).toBeVisible()

  await page.getByRole('button', { name: /sign out/i }).click()
  await expect(page.getByRole('heading', { name: /Sign in to Anomaly Engine/i })).toBeVisible()
})
