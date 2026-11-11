import { defineConfig, devices } from '@playwright/test'

// E2E runs against an ISOLATED stack: API :8041 on the throwaway `finpilot_e2e` database
// (dropped and re-created on start) and Vite :5191. Your real database is never touched.
export default defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/global-setup.js',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:5191',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: '../scripts/e2e-api.sh',
      url: 'http://127.0.0.1:8041/api/v1/health',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command: 'node node_modules/vite/bin/vite.js --port 5191',
      env: { FINPILOT_API_URL: 'http://127.0.0.1:8041' },
      url: 'http://localhost:5191',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
})
