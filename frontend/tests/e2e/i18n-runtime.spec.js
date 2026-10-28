import { expect, test } from '@playwright/test';

const EMAIL = process.env.TEST_EMAIL || 'admin@isosmart.local';
const PASSWORD = process.env.TEST_PASSWORD || 'Admin@123456';

const LANGS = [
  {
    code: 'es-LATAM',
    loginSubtitle: 'Sistema de Gestión de Calidad',
    loginButton: 'Iniciar Sesión',
    dashboardTitle: 'Sistema Inteligente de Gestión de Calidad',
    onboardingTitle: 'Configuración Inicial',
    companySizeLabel: 'Rango de tamaño de empresa',
    companySizeFirstOption: '10 a 50',
    onboardingNext: 'Continuar',
    onboardingCreate: 'Crear mi sistema',
  },
  {
    code: 'en',
    loginSubtitle: 'Quality Management System',
    loginButton: 'Sign In',
    dashboardTitle: 'Intelligent Quality Management System',
    onboardingTitle: 'Initial Setup',
    companySizeLabel: 'Company size range',
    companySizeFirstOption: '10 to 50',
    onboardingNext: 'Continue',
    onboardingCreate: 'Create my system',
  },
  {
    code: 'pt',
    loginSubtitle: 'Sistema de Gestão da Qualidade',
    loginButton: 'Entrar',
    dashboardTitle: 'Sistema Inteligente de Gestão da Qualidade',
    onboardingTitle: 'Configuração Inicial',
    companySizeLabel: 'Faixa de tamanho da empresa',
    companySizeFirstOption: '10 a 50',
    onboardingNext: 'Continuar',
    onboardingCreate: 'Criar meu sistema',
  },
];

async function login(page) {
  await page.context().setExtraHTTPHeaders({
    'X-ISO-LOCAL-AUTH-BYPASS': '1',
  });

  await page.locator('input#email, input[type="email"]').first().fill(EMAIL);
  await page.locator('input#password, input[type="password"]').first().fill(PASSWORD);

  const loginResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/api/auth/login/') && response.request().method() === 'POST',
    { timeout: 45000 }
  );

  await page.locator('button[type="submit"]').first().click();

  const loginResponse = await loginResponsePromise;

  if (loginResponse.status() >= 400) {
    let body = '';
    try {
      body = await loginResponse.text();
    } catch {
      body = '';
    }
    throw new Error(`Login failed with status ${loginResponse.status()} ${body}`.trim());
  }

  await page.waitForURL((url) => !url.pathname.endsWith('/login'), {
    timeout: 45000,
  });
}

async function getLanguageSelect(page) {
  const headerLanguageSelect = page.locator('header select').first();
  if (await headerLanguageSelect.count()) {
    return headerLanguageSelect;
  }

  const onboardingLanguageSelect = page.locator('select').filter({
    has: page.locator('option[value="es-LATAM"]'),
  }).first();
  if (await onboardingLanguageSelect.count()) {
    return onboardingLanguageSelect;
  }

  return null;
}

async function applyLanguage(page, languageCode) {
  const languageSelect = await getLanguageSelect(page);
  if (languageSelect) {
    await expect(languageSelect).toBeVisible({ timeout: 45000 });
    await languageSelect.selectOption(languageCode);
    await expect(languageSelect).toHaveValue(languageCode);
  }

  await expect.poll(async () => page.evaluate(() => document.documentElement.lang), {
    timeout: 45000,
  }).toBe(languageCode);
  await page.waitForTimeout(400);
}

for (const lang of LANGS) {
  test(`i18n runtime ${lang.code} login + dashboard`, async ({ page }) => {
    await page.addInitScript((selectedLang) => {
      localStorage.setItem('isosmart_language', selectedLang);
    }, lang.code);

    await page.goto('/login');

    await expect(page.getByText(lang.loginSubtitle)).toBeVisible();
    await expect(page.getByRole('button', { name: lang.loginButton })).toBeVisible();

    await login(page);
    await applyLanguage(page, lang.code);

    if (page.url().includes('/onboarding')) {
      await expect(page.getByText(lang.onboardingTitle)).toBeVisible();
    } else {
      await expect(page).not.toHaveURL(/\/onboarding$/);
      await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 45000 });
    }
  });

  test(`i18n runtime ${lang.code} forced onboarding`, async ({ browser }) => {
    const context = await browser.newContext({
      extraHTTPHeaders: {
        'X-ISO-LOCAL-AUTH-BYPASS': '1',
      },
    });
    const page = await context.newPage();

    await context.route('**/settings/onboarding_status/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ onboarding_completed: false }),
      });
    });

    await page.addInitScript((selectedLang) => {
      localStorage.setItem('isosmart_language', selectedLang);
    }, lang.code);

    await page.goto('/login');
    await login(page);
    await applyLanguage(page, lang.code);

    await expect(page).toHaveURL(/\/onboarding$/);
    await expect(page.getByText(lang.onboardingTitle)).toBeVisible();

    await page.getByRole('button', { name: lang.onboardingNext }).click();
    await expect(page.getByText(lang.companySizeLabel)).toBeVisible();

    const firstOption = page
      .locator(`label:has-text("${lang.companySizeLabel}") select option`)
      .first();
    await expect(firstOption).toContainText(lang.companySizeFirstOption);

    await page.getByRole('button', { name: lang.onboardingNext }).click();
    await page.getByRole('button', { name: lang.onboardingNext }).click();
    await expect(page.getByRole('button', { name: lang.onboardingCreate })).toBeVisible();

    await context.close();
  });
}
