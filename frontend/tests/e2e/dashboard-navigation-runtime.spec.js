import { expect, test } from '@playwright/test';

const EMAIL = process.env.TEST_EMAIL || 'admin@isosmart.local';
const PASSWORD = process.env.TEST_PASSWORD || 'Admin@123456';
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8002';
const TLS_PROXY_HEADERS = { 'X-Forwarded-Proto': 'https' };

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

async function login(page, request) {
  const response = await request.post(`${BACKEND_URL}/api/auth/login/`, {
    data: {
      email: EMAIL,
      password: PASSWORD,
    },
    headers: TLS_PROXY_HEADERS,
  });
  expect(response.status(), 'login API should succeed').toBe(200);
  const loginData = await response.json();

  await page.context().setExtraHTTPHeaders({
    'X-ISO-LOCAL-AUTH-BYPASS': '1',
  });
  await page.context().addInitScript(({ access, refresh }) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }, { access: loginData.access, refresh: loginData.refresh });

  await page.goto('/login');
  await page.evaluate(({ access, refresh }) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }, { access: loginData.access, refresh: loginData.refresh });
}

async function gotoAuthenticatedRoute(page, request, path) {
  await page.goto(path);
  await page.waitForTimeout(750);
  if (page.url().endsWith('/login')) {
    await login(page, request);
    await page.goto(path);
    await page.waitForTimeout(750);
  }
}

test('main dashboards and routes load successfully', async ({ page, request }) => {
  test.setTimeout(420000);

  await page.route('**/settings/onboarding_status/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ onboarding_completed: true }),
    });
  });

  await login(page, request);

  for (const route of ROUTES) {
    await test.step(`visit ${route.name}`, async () => {
      await login(page, request);
      await gotoAuthenticatedRoute(page, request, route.path);
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
