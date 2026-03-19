import { expect, test } from '@playwright/test';

const EMAIL = process.env.TEST_EMAIL || 'admin@isosmart.local';
const PASSWORD = process.env.TEST_PASSWORD || 'Admin@123456';
const BACKEND_URL = 'http://127.0.0.1:8002';

async function login(request) {
  const response = await request.post(`${BACKEND_URL}/api/auth/login/`, {
    data: {
      email: EMAIL,
      password: PASSWORD,
    },
  });

  expect(response.status(), 'login API should succeed').toBe(200);
  return response.json();
}

test('business reports endpoint exports pdf/xlsx/csv with tenant protections', async ({ request }) => {
  const loginData = await login(request);
  const organizationId = loginData.profile.organization;
  const headers = {
    Authorization: `Bearer ${loginData.access}`,
  };

  const pdfResponse = await request.get(
    `${BACKEND_URL}/api/settings/business_report/?organization_id=${organizationId}&type=sgq_executive&file_format=pdf`,
    { headers }
  );
  expect(pdfResponse.status(), 'executive PDF should be generated').toBe(200);
  expect(pdfResponse.headers()['content-type']).toContain('application/pdf');
  expect(pdfResponse.headers()['content-disposition']).toContain('.pdf');
  const pdfBody = await pdfResponse.body();
  expect(pdfBody.slice(0, 4).toString(), 'PDF should start with %PDF magic bytes').toBe('%PDF');

  const xlsxResponse = await request.get(
    `${BACKEND_URL}/api/settings/business_report/?organization_id=${organizationId}&type=risks&file_format=xlsx`,
    { headers }
  );
  expect(xlsxResponse.status(), 'risks XLSX should be generated').toBe(200);
  expect(xlsxResponse.headers()['content-type']).toContain('spreadsheetml');
  expect(xlsxResponse.headers()['content-disposition']).toContain('.xlsx');
  const xlsxBody = await xlsxResponse.body();
  expect(xlsxBody.slice(0, 2).toString(), 'XLSX should use ZIP PK signature').toBe('PK');

  const csvResponse = await request.get(
    `${BACKEND_URL}/api/settings/business_report/?organization_id=${organizationId}&type=objectives&file_format=csv`,
    { headers }
  );
  expect(csvResponse.status(), 'objectives CSV should be generated').toBe(200);
  expect(csvResponse.headers()['content-type']).toContain('text/csv');
  expect(csvResponse.headers()['content-disposition']).toContain('.csv');
  const csvBody = await csvResponse.text();
  expect(csvBody.length, 'CSV should contain data rows or headers').toBeGreaterThan(20);

  const invalidFormat = await request.get(
    `${BACKEND_URL}/api/settings/business_report/?organization_id=${organizationId}&type=risks&file_format=docx`,
    { headers }
  );
  expect(invalidFormat.status(), 'invalid format should be rejected').toBe(400);

  const forbidden = await request.get(
    `${BACKEND_URL}/api/settings/business_report/?organization_id=999999&type=risks&file_format=pdf`,
    { headers }
  );
  expect(forbidden.status(), 'report endpoint should enforce tenant isolation').toBe(403);
});

test('reports page is reachable from authenticated session', async ({ page, request }) => {
  const loginData = await login(request);

  await page.goto('/login');
  await page.evaluate(({ access, refresh }) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }, { access: loginData.access, refresh: loginData.refresh });

  await page.goto('/reports');
  await expect(page.getByText('Reportes de Negocio')).toBeVisible();
  await expect(page.getByText('Descargar reporte')).toBeVisible();
});
