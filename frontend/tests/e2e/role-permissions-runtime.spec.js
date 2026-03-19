import { expect, test } from '@playwright/test';

const ADMIN_EMAIL = process.env.TEST_EMAIL || 'admin@isosmart.local';
const ADMIN_PASSWORD = process.env.TEST_PASSWORD || 'Admin@123456';
const BACKEND_URL = 'http://127.0.0.1:8002';

async function apiLogin(request, email, password) {
  const response = await request.post(`${BACKEND_URL}/api/auth/login/`, {
    data: { email, password },
  });
  expect(response.status(), `login should succeed for ${email}`).toBe(200);
  return response.json();
}

async function createUserWithRole(request, role, organizationId, adminAccessToken) {
  const unique = `${Date.now()}-${Math.floor(Math.random() * 100000)}`;
  const email = `role.${role}.${unique}@isosmart.local`;
  const password = 'RoleRuntime@123';

  const response = await request.post(`${BACKEND_URL}/api/auth/users/`, {
    data: {
      email,
      first_name: 'Role',
      last_name: role,
      phone: '0000000000',
      password,
      confirm_password: password,
      organization_id: organizationId,
      role,
    },
    headers: {
      Authorization: `Bearer ${adminAccessToken}`,
    },
  });

  expect(response.status(), `user creation should succeed for role ${role}`).toBe(201);
  return { email, password, role };
}

async function loginInUi(page, email, password) {
  await page.goto('/login');
  await page.locator('input#email, input[type="email"]').first().fill(email);
  await page.locator('input#password, input[type="password"]').first().fill(password);

  const loginResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/api/auth/login/') && response.request().method() === 'POST',
    { timeout: 45000 }
  );

  await page.locator('button[type="submit"]').first().click();
  const loginResponse = await loginResponsePromise;
  expect(loginResponse.status(), `UI login should succeed for ${email}`).toBe(200);

  await page.waitForURL((url) => !url.pathname.endsWith('/login'), {
    timeout: 45000,
  });
}

test('settings access is enforced by role (org_admin/iso_manager allowed)', async ({ page, request }) => {
  const adminSession = await apiLogin(request, ADMIN_EMAIL, ADMIN_PASSWORD);
  const organizationId = adminSession.profile.organization;

  const managerUser = await createUserWithRole(request, 'iso_manager', organizationId, adminSession.access);

  await loginInUi(page, managerUser.email, managerUser.password);
  await page.goto('/settings');

  await expect(page).toHaveURL(/\/settings/);
  await expect(page.getByRole('heading', { name: 'Configuración', exact: true })).toBeVisible();
});

test('settings access is denied for viewer/auditor/user roles', async ({ page, request }) => {
  const adminSession = await apiLogin(request, ADMIN_EMAIL, ADMIN_PASSWORD);
  const organizationId = adminSession.profile.organization;

  const restrictedRoles = ['viewer', 'auditor', 'user'];

  for (const role of restrictedRoles) {
    const roleUser = await createUserWithRole(request, role, organizationId, adminSession.access);

    await loginInUi(page, roleUser.email, roleUser.password);
    await page.goto('/settings');

    await expect(page.getByText('org_admin, iso_manager')).toBeVisible();
    await expect(page.getByRole('heading', { name: /Acceso Denegado|Access Denied/i })).toBeVisible();
  }
});
