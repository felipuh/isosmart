const { defineConfig } = require('@playwright/test');

const baseURL = process.env.BASE_URL || 'http://127.0.0.1:3011';

// CONTROLLED_INTEGRATION_E2E: real ISO Smart backend + PostgreSQL, controlled principal.
module.exports = defineConfig({
  testDir: './tests/e2e-controlled',
  testMatch: ['**/*.spec.js'],
  timeout: 120000,
  expect: { timeout: 15000 },
  workers: 1,
  reporter: [['list']],
  use: { baseURL, headless: true, trace: 'retain-on-failure' },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 3011 --strictPort',
    url: baseURL,
    reuseExistingServer: false,
    timeout: 120000,
    env: { VITE_BACKEND_PROXY_TARGET: process.env.VITE_BACKEND_PROXY_TARGET || '' },
  },
});
