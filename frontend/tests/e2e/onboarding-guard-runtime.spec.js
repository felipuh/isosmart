import { expect, test } from '@playwright/test';

const makeFakeJwt = (payload) => {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  return `${header}.${body}.signature`;
};

const mockAuthenticatedSession = async (page, { forgeOnboardingSession = false } = {}) => {
  const now = Math.floor(Date.now() / 1000);
  const access = makeFakeJwt({ exp: now + 3600, sub: 10, organization_id: 1, role: 'org_admin' });
  const refresh = makeFakeJwt({ exp: now + 86400, sub: 10 });

  await page.addInitScript(({ accessToken, refreshToken, forgeSession }) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    if (forgeSession) {
      sessionStorage.setItem('isosmart_onboarding_seen_1', '1');
    }
  }, { accessToken: access, refreshToken: refresh, forgeSession: forgeOnboardingSession });

  await page.route('**/api/auth/refresh/', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ access, refresh }),
    });
  });
  await page.route('**/api/auth/me/', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        user: { id: 10, email: 'onboarding@e2e.local', first_name: 'Onboarding', last_name: 'E2E' },
        profile: { id: 11, role: 'org_admin', organization: 1 },
        organizations: [{ id: 1, name: 'Org E2E', is_current: true }],
      }),
    });
  });
};

test('onboarding status error remains fail-closed even with forged sessionStorage', async ({ page }) => {
  await mockAuthenticatedSession(page, { forgeOnboardingSession: true });
  await page.route('**/api/settings/onboarding_status/**', async (route) => {
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'simulated authority outage' }),
    });
  });

  await page.goto('/');

  await expect(page.getByRole('alert')).toContainText('No se pudo validar el acceso');
  await expect(page.getByText('La ruta permanece bloqueada')).toBeVisible();
  await expect(page.locator('button.fixed.bottom-6.right-6')).toHaveCount(0);
  await expect(page).toHaveURL(/\/$/);
});

test('retry queries backend authority again before granting access', async ({ page }) => {
  await mockAuthenticatedSession(page);
  let statusCalls = 0;
  let backendAvailable = false;
  await page.route('**/api/settings/onboarding_status/**', async (route) => {
    statusCalls += 1;
    if (!backendAvailable) {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'temporary outage' }),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ organization_id: 1, onboarding_completed: true }),
    });
  });

  await page.goto('/');
  await expect(page.getByRole('alert')).toBeVisible();
  const callsBeforeRetry = statusCalls;
  backendAvailable = true;
  await page.getByRole('button', { name: 'Reintentar' }).click();

  await expect.poll(() => statusCalls).toBeGreaterThan(callsBeforeRetry);
  await expect(page.locator('button.fixed.bottom-6.right-6')).toBeVisible();
});

test('loading and invalid status never render protected content', async ({ page }) => {
  await mockAuthenticatedSession(page);
  let releaseStatus;
  const pendingStatus = new Promise((resolve) => {
    releaseStatus = resolve;
  });
  await page.route('**/api/settings/onboarding_status/**', async (route) => {
    await pendingStatus;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ organization_id: 1, onboarding_completed: 'yes' }),
    });
  });

  await page.goto('/');
  await expect(page.getByRole('status')).toContainText('Validando el estado de onboarding');
  await expect(page.locator('button.fixed.bottom-6.right-6')).toHaveCount(0);

  releaseStatus();
  await expect(page.getByRole('alert')).toContainText('No se pudo validar el acceso');
  await expect(page.locator('button.fixed.bottom-6.right-6')).toHaveCount(0);
});
