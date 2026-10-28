const { defineConfig } = require('@playwright/test');

const baseURL = process.env.BASE_URL || 'http://127.0.0.1:3012';

module.exports = defineConfig({
  testDir: './tests/e2e-controlled',
  testMatch: ['**/value-discovery-controlled.spec.js'],
  timeout: 120000,
  expect: { timeout: 15000 },
  workers: 1,
  reporter: [['list']],
  use: { baseURL, headless: true, trace: 'retain-on-failure' },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 3012 --strictPort',
    url: baseURL,
    reuseExistingServer: false,
    timeout: 120000,
    env: { VITE_BACKEND_PROXY_TARGET: process.env.VITE_BACKEND_PROXY_TARGET || '' },
  },
});
