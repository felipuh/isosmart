import { expect, test } from '@playwright/test';

const makeFakeJwt = (payload) => {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  return `${header}.${body}.signature`;
};

test('assistant hydrates state and persists conversation id across reload', async ({ page }) => {
  const now = Math.floor(Date.now() / 1000);
  const access = makeFakeJwt({ exp: now + 3600, sub: 10, organization_id: 1, role: 'org_admin' });
  const refresh = makeFakeJwt({ exp: now + 86400, sub: 10 });

  await page.addInitScript(({ accessToken, refreshToken }) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }, { accessToken: access, refreshToken: refresh });

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
        user: { id: 10, email: 'assistant@e2e.local', first_name: 'Assistant', last_name: 'E2E' },
        profile: { id: 11, role: 'org_admin', organization: 1 },
        organizations: [{ id: 1, name: 'Org E2E', is_current: true }],
      }),
    });
  });

  let stateCalls = 0;
  let streamCalls = 0;
  const stateUrls = [];

  await page.route('**/api/integration/assistant/state/**', async (route) => {
    stateCalls += 1;
    const url = route.request().url();
    stateUrls.push(url);

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        ok: true,
        conversation_id: 321,
        title: 'Conversacion QA',
        messages: [
          { role: 'assistant', content: 'Mensaje desde backend para hidratar panel' },
        ],
      }),
    });
  });

  await page.route('**/api/integration/assistant/stream/', async (route) => {
    streamCalls += 1;
    const payload = route.request().postDataJSON();

    expect(payload.conversationId, 'conversation id should come from hydrated state').toBe(321);

    const sseBody =
      'event: chunk\n' +
      'data: {"text":"Respuesta en streaming"}\n\n' +
      'event: done\n' +
      'data: {"ok":true,"provider":"remote","conversation_id":321}\n\n';

    await route.fulfill({
      status: 200,
      headers: {
        'content-type': 'text/event-stream',
        'cache-control': 'no-cache',
      },
      body: sseBody,
    });
  });

  await page.goto('/');

  const assistantToggle = page.locator('button.fixed.bottom-6.right-6').first();
  await assistantToggle.click();

  const panel = page.locator('div.fixed.bottom-20.right-6').first();
  await expect(panel).toBeVisible();
  await expect(panel.locator('text=Mensaje desde backend para hidratar panel')).toBeVisible();

  const input = panel.locator('input').first();
  await input.fill('Necesito ayuda de prueba');
  await panel.locator('button').last().click();

  await expect.poll(() => streamCalls, { timeout: 20000 }).toBe(1);

  await expect(panel.locator('text=Respuesta en streaming')).toBeVisible({ timeout: 20000 });

  await page.reload();
  await assistantToggle.click();
  await expect(panel).toBeVisible();
  await expect(panel.locator('text=Mensaje desde backend para hidratar panel')).toBeVisible();

  expect(stateCalls, 'state endpoint should be requested at least twice').toBeGreaterThanOrEqual(2);
  const persistedConversationId = await page.evaluate(() => localStorage.getItem('assistant_conversation_id'));
  expect(persistedConversationId).toBe('321');
});

test('assistant shows local fallback answer when stream endpoint fails', async ({ page }) => {
  const now = Math.floor(Date.now() / 1000);
  const access = makeFakeJwt({ exp: now + 3600, sub: 10, organization_id: 1, role: 'org_admin' });
  const refresh = makeFakeJwt({ exp: now + 86400, sub: 10 });

  await page.addInitScript(({ accessToken, refreshToken }) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }, { accessToken: access, refreshToken: refresh });

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
        user: { id: 10, email: 'assistant@e2e.local', first_name: 'Assistant', last_name: 'E2E' },
        profile: { id: 11, role: 'org_admin', organization: 1 },
        organizations: [{ id: 1, name: 'Org E2E', is_current: true }],
      }),
    });
  });

  await page.route('**/api/integration/assistant/state/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true, conversation_id: null, messages: [] }),
    });
  });

  let streamCalls = 0;
  await page.route('**/api/integration/assistant/stream/', async (route) => {
    streamCalls += 1;
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'simulated provider failure' }),
    });
  });

  await page.goto('/');

  const assistantToggle = page.locator('button.fixed.bottom-6.right-6').first();
  await assistantToggle.click();

  const panel = page.locator('div.fixed.bottom-20.right-6').first();
  await expect(panel).toBeVisible();

  const input = panel.locator('input').first();
  await input.fill('riesgo operativo de prueba');
  await panel.locator('button').last().click();

  await expect.poll(() => streamCalls, { timeout: 20000 }).toBe(1);

  const bubbles = panel.locator('div.p-4.h-72.overflow-y-auto.space-y-3 > div');
  await expect.poll(async () => await bubbles.count(), { timeout: 20000 }).toBeGreaterThanOrEqual(2);
  const assistantText = await bubbles.last().innerText();
  expect(assistantText.trim().length).toBeGreaterThan(0);
});