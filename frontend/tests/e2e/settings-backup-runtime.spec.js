import { expect, test } from '@playwright/test';

const EMAIL = process.env.TEST_EMAIL || 'admin@isosmart.local';
const PASSWORD = process.env.TEST_PASSWORD || 'Admin@123456';

async function login(request) {
  const response = await request.post('/api/auth/login/', {
    data: {
      email: EMAIL,
      password: PASSWORD,
    },
  });

  expect(response.status(), 'login API should succeed').toBe(200);
  return response.json();
}

test('settings backup and export flows work with tenant protections', async ({ page, request }) => {
  await page.goto('/login');
  await expect(page.locator('input#email')).toBeVisible();

  const loginData = await login(request);
  const organizationId = loginData.profile.organization;
  const headers = {
    Authorization: `Bearer ${loginData.access}`,
  };

  const historyBefore = await request.get(`/api/settings/backups/?organization_id=${organizationId}`, {
    headers,
  });
  expect(historyBefore.status(), 'backup history should load').toBe(200);

  const backupResponse = await request.post('/api/settings/trigger_backup/', {
    data: { organization_id: organizationId },
    headers,
  });
  expect(backupResponse.status(), 'manual backup should succeed').toBe(200);

  const backupData = await backupResponse.json();
  expect(backupData.last_backup_at, 'manual backup should return a timestamp').toBeTruthy();
  expect(backupData.history_entry?.description, 'manual backup should create history').toContain('Backup');

  const historyAfter = await request.get(`/api/settings/backups/?organization_id=${organizationId}`, {
    headers,
  });
  expect(historyAfter.status(), 'backup history should still load after backup').toBe(200);

  const historyData = await historyAfter.json();
  expect(historyData.count, 'backup history should contain at least one entry').toBeGreaterThan(0);
  expect(historyData.results[0]?.description, 'latest history entry should describe the backup').toContain('Backup');

  const exportResponse = await request.get(`/api/export/?organization_id=${organizationId}&type=all`, {
    headers,
  });
  expect(exportResponse.status(), 'settings export should succeed').toBe(200);

  const exportData = await exportResponse.json();
  expect(exportData.organization_id, 'export should stay within the current organization').toBe(organizationId);
  expect(exportData.export_type, 'export should honor the requested type').toBe('all');

  const forbiddenHistory = await request.get('/api/settings/backups/?organization_id=999999', {
    headers,
  });
  expect(forbiddenHistory.status(), 'backup history should enforce tenant isolation').toBe(403);
});