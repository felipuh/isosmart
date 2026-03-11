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

test('settings backup history and export work end-to-end', async ({ page }) => {
  await login(page);

  const token = await page.evaluate(() => localStorage.getItem('access_token'));
  expect(token, 'access token should be present after login').toBeTruthy();

  const authHeaders = {
    Authorization: `Bearer ${token}`,
  };

  const settingsResponse = await page.request.get('/api/settings/current/', {
    headers: authHeaders,
  });
  expect(settingsResponse.status(), 'settings current should load').toBe(200);

  const settingsData = await settingsResponse.json();
  const organizationId = settingsData.organization;
  expect(organizationId, 'organization id should be present in settings').toBeTruthy();

  const backupResponse = await page.request.post('/api/settings/trigger_backup/', {
    headers: authHeaders,
    data: { organization_id: organizationId },
  });
  expect(backupResponse.status(), 'backup trigger should succeed').toBe(200);

  const backupData = await backupResponse.json();
  expect(backupData.last_backup_at, 'backup response should include timestamp').toBeTruthy();
  expect(backupData.backup_id, 'backup response should include audit id').toBeTruthy();

  const historyResponse = await page.request.get(
    `/api/settings/backup_history/?organization_id=${organizationId}&limit=5`,
    {
      headers: authHeaders,
    }
  );
  expect(historyResponse.status(), 'backup history should succeed').toBe(200);

  const historyData = await historyResponse.json();
  expect(Array.isArray(historyData.results), 'history should contain results list').toBeTruthy();
  expect(historyData.count, 'history should contain at least one item').toBeGreaterThan(0);
  expect(historyData.results[0].organization_id).toBe(organizationId);
  expect(historyData.results[0].action).toBe('backup');

  const exportResponse = await page.request.get(
    `/api/export/?type=all&organization_id=${organizationId}`,
    {
      headers: authHeaders,
    }
  );
  expect(exportResponse.status(), 'export endpoint should succeed').toBe(200);

  const exportData = await exportResponse.json();
  expect(exportData.organization_id).toBe(organizationId);
  expect(exportData.export_type).toBe('all');
  expect(exportData.data).toBeTruthy();

  const forbiddenHistoryResponse = await page.request.get('/api/settings/backup_history/?organization_id=999999', {
    headers: authHeaders,
  });
  expect([403, 404], 'foreign organization should be denied').toContain(forbiddenHistoryResponse.status());
});
