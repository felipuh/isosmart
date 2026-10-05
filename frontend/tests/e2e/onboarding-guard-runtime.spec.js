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

test('Foundation Gate submits only the server-published questions and reflects the server result', async ({ page }) => {
  await mockAuthenticatedSession(page);
  await page.route('**/api/settings/onboarding_status/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ organization_id: 1, onboarding_completed: false }),
    });
  });

  const pathId = '11111111-1111-4111-8111-111111111111';
  const questionId = '22222222-2222-4222-8222-222222222222';
  let gatePassed = false;
  await page.route('**/api/v1/onboarding/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        foundation_gate: {
          status: gatePassed ? 'passed' : 'not_started',
          paths: [{
            id: pathId,
            standard_code: 'ISO 9000',
            edition: '2026',
            required_score: '80.00',
            questions: gatePassed ? [] : [{
              id: questionId,
              scenario: 'Which published option applies?',
              options: [{ id: 'yes', label: 'Yes' }, { id: 'no', label: 'No' }],
            }],
          }],
        },
        steps: [],
        step_count: 17,
      }),
    });
  });
  await page.route('**/api/v1/learning/iso9000/attempts', async (route) => {
    const payload = route.request().postDataJSON();
    expect(payload).toEqual({
      learning_path_id: pathId,
      answers: [{ question_id: questionId, selected_option_ids: ['yes'] }],
    });
    gatePassed = true;
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ score: '100.00', passed: true, feedback: [] }),
    });
  });

  await page.goto('/onboarding');
  await expect(page.getByText('Puerta de Foundation ISO 9000:2026')).toBeVisible();
  await page.getByLabel('Yes').check();
  await page.getByRole('button', { name: 'Enviar evaluación' }).click();
  await expect(page.getByText('Aprobada')).toBeVisible();
  await expect(page.getByText('Resultado: 100.00%')).toBeVisible();
});

test('controlled integration saves the source-defined organizational profile through the canonical tenant API', async ({ page }) => {
  await mockAuthenticatedSession(page);
  let legacyOnboardingComplete = false;
  let profileComplete = false;
  const canonicalOrganizationId = '33333333-3333-4333-8333-333333333333';

  await page.route('**/api/settings/onboarding_status/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        organization_id: 1,
        onboarding_completed: legacyOnboardingComplete,
        commercially_available_standards: ['ISO9001_2015'],
      }),
    });
  });
  await page.route('**/api/v1/onboarding/organizations', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ organizations: [{ id: canonicalOrganizationId, display_name: 'Canonical QMS Org' }] }),
    });
  });
  await page.route('**/api/v1/onboarding/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        foundation_gate: { status: 'passed', paths: [] },
        steps: [{
          number: 10,
          key: 'organizational_profile',
          title: 'Organizational Profile',
          status: profileComplete ? 'COMPLETE' : 'AVAILABLE',
          prerequisites: ['foundation_gate'],
        }],
        step_count: 17,
      }),
    });
  });
  await page.route('**/api/v1/onboarding/organizational-profile', async (route) => {
    const payload = route.request().postDataJSON();
    expect(payload.organization_id).toBe(canonicalOrganizationId);
    expect(payload.event_id).toMatch(/^[0-9a-f-]{36}$/);
    expect(payload).toMatchObject({
      role: 'quality_manager',
      expertise_level: 'intermediate',
      size_range: '10-50',
      employees_count: 45,
      sites_count: 2,
      countries: ['Costa Rica', 'Panamá'],
      sector: 'Manufactura',
      certification_status: 'first_time',
    });
    profileComplete = true;
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        workflow_id: '44444444-4444-4444-8444-444444444444',
        step: 'organizational_profile',
        status: 'complete',
        replay: false,
      }),
    });
  });
  await page.route('**/api/iso-clauses/initialize_standards/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });
  await page.route('**/api/settings/complete_onboarding/**', async (route) => {
    legacyOnboardingComplete = true;
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });
  await page.route('**/api/settings/run_onboarding_orchestration/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });

  await page.goto('/onboarding');
  await page.getByRole('button', { name: 'Continuar' }).click();
  await expect(page.getByLabel('Organización canónica')).toHaveValue(canonicalOrganizationId);
  await page.getByLabel('Sector principal').fill('Manufactura');
  await page.getByRole('button', { name: 'Continuar' }).click();
  await page.getByLabel('Número aproximado de colaboradores').fill('45');
  await page.getByLabel('Número de sedes / plantas').fill('2');
  await page.getByLabel('Países (separados por coma)').fill('Costa Rica, Panamá');
  await page.getByRole('button', { name: 'Continuar' }).click();
  await page.getByRole('button', { name: 'Crear mi sistema' }).click();

  await expect.poll(() => profileComplete).toBe(true);
  await expect(page).toHaveURL(/\/$/);
});
