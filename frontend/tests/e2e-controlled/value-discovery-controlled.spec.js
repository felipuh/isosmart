// CONTROLLED_AGENT_E2E: actual React, Django, and disposable PostgreSQL.
// Only auth bootstrap and inference are local fixtures; onboarding persistence
// and Value Discovery APIs are never mocked.
import { expect, test } from '@playwright/test';

const principals = JSON.parse(process.env.VALUE_DISCOVERY_E2E_PRINCIPALS);

const json = (body, status = 200) => ({
  status,
  contentType: 'application/json',
  body: JSON.stringify(body),
});

const openAs = async (page, principal) => {
  await page.addInitScript((email) => {
    localStorage.setItem('isosmart_language', 'es-LATAM');
    window.localStorage.setItem('controlled_e2e_email', email);
  }, principal.email);
  await page.route('**/api/auth/me/', (route) => route.fulfill(json({
    user: { id: principal.user_id, email: principal.email, first_name: 'Value', last_name: 'Discovery' },
    profile: { id: principal.user_id, role: 'quality_manager', organization: principal.organization_id },
    organizations: [{ id: principal.organization_id, name: 'Controlled E2E tenant', is_current: true }],
  })));
  await page.route('**/api/auth/refresh/', (route) => route.fulfill(json({})));
  await page.route('**/api/settings/onboarding_status/**', (route) => route.fulfill(json({
    organization_id: principal.organization_id,
    onboarding_completed: false,
  })));
  const controlledPrincipal = JSON.stringify({
    organization_id: principal.organization_id,
    user_id: principal.user_id,
    role: 'quality_manager',
  });
  await page.route(/\/api\/v1\/onboarding\//, (route) => route.continue({
    headers: { ...route.request().headers(), 'x-controlled-principal': controlledPrincipal },
  }));
};

test('Step 11 persists real Value Discovery effects and Step 12 naturally unlocks after reload', async ({ page }) => {
  await openAs(page, principals.positive);
  await page.goto('/onboarding');

  await expect(page.getByRole('heading', { name: 'Descubrimiento de valor' })).toBeVisible();
  await expect(page.getByText('LOCKED', { exact: true })).toBeVisible();
  await page.getByLabel('Propósito declarado de la organización').fill('Ofrecer servicios confiables a clientes locales.');
  await page.getByRole('button', { name: 'Iniciar descubrimiento de valor' }).click();

  await expect(page.getByText('Clarify process ownership:')).toBeVisible();
  await expect(page.getByText('process clarity')).toBeVisible();
  await expect(page.getByText('La evaluación financiera aún no está disponible: no existe una línea base financiera autorizada.')).toBeVisible();
  await expect(page.getByText('AVAILABLE', { exact: true })).toBeVisible();

  await page.reload();
  await expect(page.getByText('Clarify process ownership:')).toBeVisible();
  await expect(page.getByText('Referencias de documentos y datos')).toBeVisible();
  await expect(page.getByText('AVAILABLE', { exact: true })).toBeVisible();
});

test('malformed controlled provider output cannot complete Step 11 or unlock Step 12', async ({ page }) => {
  await openAs(page, principals.negative);
  await page.goto('/onboarding');

  await expect(page.getByText('LOCKED', { exact: true })).toBeVisible();
  await page.getByLabel('Propósito declarado de la organización').fill('E2E_FORCE_INVALID_MODEL_OUTPUT');
  await page.getByRole('button', { name: 'Iniciar descubrimiento de valor' }).click();

  await expect(page.getByText(/financial assessment/i)).toBeVisible();
  await expect(page.getByText('LOCKED', { exact: true })).toBeVisible();
  await expect(page.getByText('AVAILABLE', { exact: true })).toBeVisible();
});
