import { expect, test } from '@playwright/test';

const EMAIL = process.env.TEST_EMAIL || 'admin@isosmart.local';
const PASSWORD = process.env.TEST_PASSWORD || 'Admin@123456';

async function login(page) {
  await page.goto('/login');
  await page.locator('input#email, input[type="email"]').first().fill(EMAIL);
  await page.locator('input#password, input[type="password"]').first().fill(PASSWORD);

  const loginResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/api/auth/login/') && response.request().method() === 'POST',
    { timeout: 45000 }
  );

  await page.locator('button[type="submit"]').first().click();

  const loginResponse = await loginResponsePromise;
  expect(loginResponse.status(), 'login should succeed').toBe(200);

  await page.waitForURL((url) => !url.pathname.endsWith('/login'), {
    timeout: 45000,
  });
}

test('scope and processes dashboards load with tenant protections', async ({ page }) => {
  await login(page);

  const token = await page.evaluate(() => localStorage.getItem('access_token'));
  expect(token, 'access token should be present after login').toBeTruthy();

  await page.goto('/scope');
  const scopeLatest = await page.waitForResponse(
    (response) => response.url().includes('/api/scope/latest/') && response.request().method() === 'GET',
    { timeout: 45000 }
  );
  expect(scopeLatest.status(), 'scope latest should not fail').toBe(200);

  await page.goto('/processes');
  const processLatest = await page.waitForResponse(
    (response) => response.url().includes('/api/processes/maps/latest/') && response.request().method() === 'GET',
    { timeout: 45000 }
  );
  expect(processLatest.status(), 'process latest should not fail').toBe(200);

  const forbiddenScope = await page.request.get('/api/scope/latest/?organization_id=999999', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  expect(forbiddenScope.status(), 'scope endpoint should enforce tenant isolation').toBe(403);

  const forbiddenProcesses = await page.request.get('/api/processes/latest/?organization_id=999999', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  expect(forbiddenProcesses.status(), 'processes endpoint should enforce tenant isolation').toBe(403);
});
