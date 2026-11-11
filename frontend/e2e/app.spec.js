import { expect, test } from '@playwright/test'

// Test-only credentials for the throwaway finpilot_e2e database.
const USER = { name: 'E2E Tester', email: 'e2e@example.com', password: 'E2e-Test-Password-1' }

test.describe.configure({ mode: 'serial' })

async function login(page) {
  await page.goto('/')
  const setup = page.getByRole('heading', { name: 'Create your account' })
  const signIn = page.getByRole('heading', { name: 'Sign in' })
  await expect(setup.or(signIn)).toBeVisible()
  if (await setup.isVisible()) {
    await page.getByLabel('Name').fill(USER.name)
    await page.getByLabel('Email').fill(USER.email)
    await page.getByLabel('Password', { exact: true }).fill(USER.password)
    await page.getByLabel('Confirm password').fill(USER.password)
    await page.getByRole('button', { name: 'Create account' }).click()
  } else {
    await page.getByLabel('Email').fill(USER.email)
    await page.getByLabel('Password').fill(USER.password)
    await page.getByRole('button', { name: 'Sign in' }).click()
  }
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
}

test('empty account shows honest empty states', async ({ page }) => {
  await login(page)
  await expect(page.getByText('Your dashboard is empty')).toBeVisible()
  await expect(page.getByTestId('kpi-net-worth')).toContainText('₹0.00')
  await expect(page.getByTestId('kpi-savings-rate')).toContainText('No income recorded this month')
  await expect(page.getByText('No reports generated')).toBeVisible()
})

test('record income and expense, see savings rate', async ({ page }) => {
  await login(page)
  await page.getByRole('link', { name: 'Personal Finance' }).first().click()
  await expect(page.getByText(/No transactions in /)).toBeVisible()

  await page.getByRole('button', { name: 'Add income' }).click()
  await page.getByRole('dialog').getByLabel('Amount (₹)').fill('80000')
  await page.getByRole('dialog').getByLabel('Source').fill('Employer')
  await page.getByRole('dialog').getByLabel('Category').fill('Salary')
  await page.getByRole('button', { name: 'Save' }).click()

  await page.getByRole('button', { name: 'Add expense' }).click()
  await page.getByRole('dialog').getByLabel('Amount (₹)').fill('20000')
  await page.getByRole('dialog').getByLabel('Category').fill('Rent')
  await page.getByRole('button', { name: 'Save' }).click()

  await expect(page.getByTestId('tx-table')).toContainText('Rent')
  await expect(page.getByTestId('pf-savings')).toContainText('₹60,000.00')
  await expect(page.getByTestId('pf-savings-rate')).toContainText('75.0%')

  // validation: zero amount is rejected inline
  await page.getByRole('button', { name: 'Add expense' }).click()
  await page.getByRole('dialog').getByLabel('Amount (₹)').fill('0')
  await page.getByRole('dialog').getByLabel('Category').fill('Food')
  await page.getByRole('button', { name: 'Save' }).click()
  await expect(page.getByText('Please fix the highlighted fields.')).toBeVisible()
  await page.getByRole('button', { name: 'Cancel' }).click()

  // edit then delete the expense
  await page.getByTestId('tx-table').getByRole('row', { name: /Rent/ }).getByLabel('Edit').click()
  await page.getByRole('dialog').getByLabel('Amount (₹)').fill('25000')
  await page.getByRole('button', { name: 'Save' }).click()
  await expect(page.getByTestId('pf-savings-rate')).toContainText('68.8%')
  await page.getByTestId('tx-table').getByRole('row', { name: /Rent/ }).getByLabel('Delete').click()
  await page.getByRole('dialog').getByRole('button', { name: 'Delete' }).click()
  await expect(page.getByTestId('tx-table')).not.toContainText('Rent')
  await expect(page.getByTestId('pf-savings-rate')).toContainText('100.0%')
})

test('create an FD with live calculation preview', async ({ page }) => {
  await login(page)
  await page.getByRole('link', { name: 'FD & RD' }).first().click()
  await page.getByRole('button', { name: 'Add FD' }).first().click()
  await page.getByRole('dialog').getByLabel(/^Bank/).fill('My Bank')
  await page.getByRole('dialog').getByLabel('Principal (₹)').fill('100000')
  await page.getByRole('dialog').getByLabel('Interest rate (% p.a.)').fill('7')
  await page.getByRole('dialog').getByLabel('Start date').fill('2026-01-01')
  await page.getByRole('dialog').getByLabel('Maturity date').fill('2027-01-01')
  await expect(page.getByTestId('calc-preview')).toContainText('₹1,07,185.90')
  await page.getByRole('button', { name: 'Save' }).click()
  const row = page.getByTestId('fd-table').getByRole('row', { name: /My Bank/ })
  await expect(row).toContainText('Unverified')
  await expect(row).toContainText('₹1,07,185.90')
})

test('savings goal shows deterministic projection', async ({ page }) => {
  await login(page)
  await page.getByRole('link', { name: 'Financial Goals' }).first().click()
  await page.getByRole('button', { name: 'Savings goal' }).click()
  await page.getByRole('dialog').getByLabel('Goal name').fill('Emergency fund')
  await page.getByRole('dialog').getByLabel('Target amount (₹)').fill('100000')
  await page.getByRole('dialog').getByLabel('Saved so far (₹)').fill('25000')
  await page.getByRole('dialog').getByLabel('Monthly contribution (₹)').fill('5000')
  await page.getByRole('button', { name: 'Save' }).click()
  const card = page.getByTestId('goal-card').filter({ hasText: 'Emergency fund' })
  await expect(card).toContainText('25.0%')
  await expect(card).toContainText('15 mo')
  await expect(card).toContainText('Assumes no interest or return')
})

test('dashboard aggregates entered data', async ({ page }) => {
  await login(page)
  await expect(page.getByText('Your dashboard is empty')).toHaveCount(0)
  await expect(page.getByTestId('kpi-income')).toContainText('₹80,000.00')
  await expect(page.getByText('Emergency fund')).toBeVisible()
})

test('DEMO data is labelled, bannered and removable', async ({ page }) => {
  await login(page)
  await page.getByRole('link', { name: 'Settings' }).first().click()
  await page.getByRole('button', { name: 'Load DEMO data' }).click()
  await expect(page.getByTestId('demo-banner')).toBeVisible()
  await page.getByRole('link', { name: 'Personal Finance' }).first().click()
  await page.getByRole('button', { name: 'All months' }).click()
  await expect(page.getByTestId('tx-table').locator('table').getByText('DEMO', { exact: true }).first()).toBeVisible()
  await page.getByRole('link', { name: 'Settings' }).first().click()
  await page.getByRole('button', { name: 'Remove DEMO data' }).click()
  await expect(page.getByTestId('demo-banner')).toHaveCount(0)
})

test('mobile layout has no horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 })
  await login(page)
  for (const path of ['/', '/personal-finance', '/deposits', '/goals', '/portfolio', '/settings', '/stocks']) {
    await page.goto(path)
    await page.waitForLoadState('networkidle')
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
    expect(overflow, `horizontal overflow on ${path}`).toBeLessThanOrEqual(0)
  }
  await page.getByRole('button', { name: 'Open menu' }).click()
  await expect(page.getByRole('navigation', { name: 'Main' })).toBeVisible()
})

test('sign out and sign back in', async ({ page }) => {
  await login(page)
  await page.getByRole('button', { name: 'Sign out' }).first().click()
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
  await page.getByLabel('Email').fill(USER.email)
  await page.getByLabel('Password').fill('Wrong-password-99')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByRole('alert')).toContainText('Invalid email or password')
  await login(page)
})
