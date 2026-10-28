// CONTROLLED_INTEGRATION_E2E: real ISO Smart backend + PostgreSQL behind a controlled
// principal header. Shell/auth bootstrap endpoints are stubbed; QMS persistence is NOT mocked.
// This is not a current authentic AdminApps E2E.
import { expect, test } from '@playwright/test';

const ids = JSON.parse(process.env.QMS_E2E_PRINCIPAL);

const makeFakeJwt = (payload) => {
  const enc = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
  return `${enc({ alg: 'HS256', typ: 'JWT' })}.${enc(payload)}.signature`;
};

const openAs = async (page, role) => {
  const now = Math.floor(Date.now() / 1000);
  const access = makeFakeJwt({ exp: now + 3600, sub: 10, organization_id: 1, role });
  const refresh = makeFakeJwt({ exp: now + 86400, sub: 10 });
  await page.addInitScript(({ a, r }) => {
    localStorage.setItem('access_token', a);
    localStorage.setItem('refresh_token', r);
  }, { a: access, r: refresh });
  const json = (body, status = 200) => ({ status, contentType: 'application/json', body: JSON.stringify(body) });
  await page.route('**/api/**', (route) => route.fulfill(json({ results: [] })));
  await page.route('**/api/auth/refresh/', (route) => route.fulfill(json({ access, refresh })));
  await page.route('**/api/auth/me/', (route) => route.fulfill(json({
    user: { id: 10, email: 'manager@e2e.local', first_name: 'QMS', last_name: 'E2E' },
    profile: { id: 11, role: 'org_admin', organization: 1 },
    organizations: [{ id: 1, name: 'Org E2E', is_current: true }],
  })));
  await page.route('**/api/settings/onboarding_status/**', (route) => route.fulfill(json({
    organization_id: 1, onboarding_completed: true,
  })));
  const principal = JSON.stringify({
    organization_id: ids.organization_id, user_id: ids.manager_id, role,
  });
  await page.route(/\/api\/v1\/(qms|evidence)/, (route) => route.continue({
    headers: { ...route.request().headers(), 'x-controlled-principal': principal },
  }));
};

test('authorized role completes Evidence → Audit → Finding → NC → CAPA and reads it back after reload', async ({ page }) => {
  await openAs(page, 'quality_manager');
  await page.goto('/qms/capa');
  await expect(page.getByTestId('qms-capa-page')).toBeVisible();
  await expect(page.getByTestId('qms-readonly')).toHaveCount(0);

  await page.getByTestId('evidence-form').getByLabel(/SHA-256/).fill('ab'.repeat(32));
  await page.getByTestId('evidence-form').getByLabel('Source URI').fill('https://e2e.local/record-1');
  await page.getByTestId('evidence-form').getByRole('button').click();
  await expect(page.getByTestId('qms-evidence')).toContainText('https://e2e.local/record-1');

  const audit = page.getByTestId('audit-form');
  await audit.getByLabel('Scope').fill('E2E production scope');
  await audit.getByLabel('Criteria').fill('ISO 9001 program');
  await audit.getByLabel('Status').fill('planned');
  await audit.getByLabel('Lead auditor').fill('E2E Lead');
  await audit.getByRole('button').click();
  await expect(page.getByTestId('qms-audits')).toContainText('E2E production scope');

  const finding = page.getByTestId('finding-form');
  await finding.getByLabel('Type').fill('nonconformity');
  await finding.getByLabel('Statement').fill('E2E observed gap');
  await finding.getByRole('button').click();
  await expect(page.getByTestId('qms-findings')).toContainText('E2E observed gap');

  const nc = page.locator('[data-testid^="nc-form-"]');
  await nc.getByLabel('Description').fill('E2E nonconformity text');
  await nc.getByLabel('Severity').fill('major');
  await nc.getByLabel('Status').fill('detected');
  await nc.getByRole('button').click();
  await expect(page.getByTestId('qms-findings')).toContainText('E2E nonconformity text');
  await expect(page.locator('[data-testid^="nc-form-"]')).toHaveCount(0);

  const capa = page.getByTestId('capa-form');
  await capa.getByLabel(/cause reference/i).fill('7b1f1a52-2d2a-4a43-9a52-0a9d5d5b5e11');
  await capa.getByLabel('Action', { exact: true }).fill('E2E corrective action');
  await capa.getByLabel('Owner').selectOption({ label: 'colleague@e2e.local' });
  await capa.getByRole('button').click();
  await expect(page.getByTestId('qms-capa')).toContainText('E2E corrective action');

  await page.reload();
  await expect(page.getByTestId('qms-audits')).toContainText('E2E production scope');
  await expect(page.getByTestId('qms-findings')).toContainText('E2E nonconformity text');
  await expect(page.getByTestId('qms-capa')).toContainText('E2E corrective action');
  await expect(page.getByTestId('qms-evidence')).toContainText('https://e2e.local/record-1');
});

test('unauthorized role sees persisted data read-only and cannot write via the API', async ({ page }) => {
  await openAs(page, 'viewer');
  await page.goto('/qms/capa');
  await expect(page.getByTestId('qms-readonly')).toBeVisible();
  await expect(page.getByTestId('audit-form')).toHaveCount(0);
  await expect(page.getByTestId('qms-audits')).toContainText('E2E production scope');
  const denied = await page.evaluate(async (principal) => {
    const res = await fetch('/api/v1/qms/audits', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Controlled-Principal': principal },
      body: JSON.stringify({ scope: 's', criteria: 'c', status: 'x', lead_auditor: 'l' }),
    });
    return { status: res.status, body: await res.json() };
  }, JSON.stringify({ organization_id: ids.organization_id, user_id: ids.manager_id, role: 'viewer' }));
  expect(denied.status).toBe(403);
  expect(denied.body.code).toBe('QMS_WRITE_ROLE_REQUIRED');
});
