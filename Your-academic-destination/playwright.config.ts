import { defineConfig, devices } from '@playwright/test';

/**
 * E2E configuration for the academic destination frontend.
 * Requires the backend running locally on :8000 against wijhatak_test
 * (SMS_MODE=queue so OTPs are fetchable via /internal/sms/dequeue).
 */
export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 1,
  workers: 1,
  reporter: [['html', { open: 'never' }], ['list']],
  timeout: 90000,
  expect: { timeout: 15000 },
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    locale: 'ar-SY',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
    timeout: 120000,
    env: {
      VITE_API_URL: 'http://localhost:8000',
    },
  },
});