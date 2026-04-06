import { expect, test } from '@playwright/test';

const EMAIL = process.env.TEST_EMAIL || 'admin@isosmart.local';
const PASSWORD = process.env.TEST_PASSWORD || 'Admin@123456';

const ROUTES = [
  { path: '/', name: 'dashboard-home' },
  { path: '/stakeholders', name: 'stakeholders' },
  { path: '/context?tab=signals', name: 'context-signals', expectedText: 'Señales externas auditables' },
  { path: '/context?tab=alerts', name: 'context-alerts', expectedText: 'Alertas climáticas y ESG' },
  { path: '/context?tab=radar', name: 'context-radar', expectedText: 'Radar dinámico de contexto' },
  { path: '/scope', name: 'scope' },
  { path: '/processes', name: 'processes' },
  { path: '/documents', name: 'documents' },
  { path: '/risks', name: 'risks' },
  { path: '/objectives', name: 'objectives' },
  { path: '/leadership', name: 'leadership' },
  { path: '/resources', name: 'resources' },
  { path: '/planning', name: 'planning' },
  { path: '/operations', name: 'operations' },
  { path: '/performance', name: 'performance' },
  { path: '/improvement', name: 'improvement' },
  { path: '/reports', name: 'reports' },
  { path: '/settings', name: 'settings' },
];

async function login(page) {
  await page.context().setExtraHTTPHeaders({
    'X-ISO-LOCAL-AUTH-BYPASS': '1',
  });

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

test('main dashboards and routes load successfully', async ({ page }) => {
  test.setTimeout(420000);

  await page.route('**/settings/onboarding_status/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ onboarding_completed: true }),
    });
  });

  await login(page);

  for (const route of ROUTES) {
    await test.step(`visit ${route.name}`, async () => {
      await page.goto(route.path);
      await expect(page).not.toHaveURL(/\/login$/);

      const mainLocator = page.locator('main');
      const headingLocator = page.locator('h1, h2').first();
      if (await mainLocator.count()) {
        await expect(mainLocator).toBeVisible({ timeout: 15000 });
      }
      await expect(headingLocator).toBeVisible({ timeout: 15000 });

      await expect(page.getByRole('heading', { name: /Acceso Denegado|Access Denied/i })).toHaveCount(0);

      if (route.expectedText) {
        await expect(page.getByText(route.expectedText)).toBeVisible({ timeout: 45000 });
      }
    });
  }
});