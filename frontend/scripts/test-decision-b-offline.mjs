import assert from 'node:assert/strict';
import fs from 'node:fs';
const source = fs.readFileSync('src/context/AuthContext.jsx', 'utf8');
const start = source.indexOf('  const refreshToken =');
const end = source.indexOf('  // Cambiar organización', start);
const body = source.slice(start, end);
const med = process.cwd().includes('ISO_Smart_MedSupplier');
let tests = 0;
for (const scenario of ['denied', 'unavailable', 'complete', ...(med ? ['missing-rotation'] : [])]) {
  const storage = new Map([['refresh_token', 'old-refresh'], ['access_token', 'old-access']]);
  let cleared = false;
  const api = { defaults: { headers: { common: {} } }, post: async () => {
    if (scenario === 'denied' || scenario === 'unavailable') throw new Error('synthetic denial');
    return { data: scenario === 'complete' ? { access: 'new-access', refresh: 'new-refresh' } : { access: 'new-access' } };
  }};
  const localStorage = { getItem: k => storage.get(k), setItem: (k, v) => storage.set(k, v) };
  const clearAuth = () => { cleared = true; storage.clear(); };
  const refresh = new Function('api', 'clearAuth', 'loadCurrentUser', 'localStorage', 'isTokenExpired', body + '\nreturn refreshToken;')(
    api, clearAuth, async () => {}, localStorage, () => false);
  const result = await refresh({ reloadUser: false });
  if (scenario === 'complete') {
    assert.equal(result, true); assert.equal(cleared, false);
    if (med) assert.equal(storage.get('refresh_token'), 'new-refresh');
  } else {
    assert.equal(result, false); assert.equal(cleared, true); assert.equal(storage.size, 0);
  }
  tests++;
}
console.log(JSON.stringify({ tests, passed: tests, scope: 'offline refresh closure; NOT browser E2E' }));
