import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createServer } from 'node:net';
import { spawn } from 'node:child_process';

const origin = process.env.ARCOENERGY_AUTH_TEST_ORIGIN || 'http://127.0.0.1:18081';
const chromeBin = process.env.CHROME_BIN || 'google-chrome';
const timeoutMs = 20_000;
const permissions = [
  'customers:read', 'customers:write', 'quotes:read', 'quotes:write',
  'installations:read', 'installations:write', 'inventory:read', 'inventory:write',
  'inventory:manage', 'inventory:issue', 'inventory:costs:read', 'expenses:read',
  'expenses:write', 'receivables:read', 'receivables:write', 'accounts:read',
  'accounts:write', 'accounts:manage', 'suppliers:read', 'suppliers:manage',
  'purchases:read', 'purchases:write', 'team:manage', 'sales:read',
  'sales:write', 'reports:read',
];

function fail(message) { throw new Error(message); }

async function freePort() {
  const server = createServer();
  await new Promise((resolve, reject) => server.once('error', reject).listen(0, '127.0.0.1', resolve));
  const { port } = server.address();
  await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
  return port;
}

async function waitForJson(url, child, deadline) {
  let lastError;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) fail(`Chrome exited with status ${child.exitCode}.`);
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(1000) });
      if (response.ok) return response.json();
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) { lastError = error; }
    await new Promise(resolve => setTimeout(resolve, 150));
  }
  throw new Error(`Chrome DevTools did not become ready: ${lastError}`);
}

async function verifySurface(route) {
  const port = await freePort();
  const profile = await mkdtemp(join(tmpdir(), 'arcoenergy-auth-chrome-'));
  const child = spawn(chromeBin, [
    '--headless=new', '--no-sandbox', '--disable-dev-shm-usage', '--disable-extensions',
    '--no-first-run', '--disable-background-networking', '--disable-sync',
    `--user-data-dir=${profile}`, '--remote-debugging-address=127.0.0.1',
    `--remote-debugging-port=${port}`, 'about:blank',
  ], { stdio: 'ignore' });
  let socket;
  let loginCount = 0;
  let refreshCount = 0;
  let failNextRefresh = false;
  try {
    const deadline = Date.now() + timeoutMs;
    await waitForJson(`http://127.0.0.1:${port}/json/version`, child, deadline);
    const targetResponse = await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' });
    if (!targetResponse.ok) fail(`Chrome could not create a page for ${route}: HTTP ${targetResponse.status}.`);
    const target = await targetResponse.json();
    socket = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      socket.addEventListener('open', resolve, { once: true });
      socket.addEventListener('error', reject, { once: true });
    });

    let nextId = 0;
    const pending = new Map();
    const send = (method, params = {}) => new Promise((resolve, reject) => {
      const id = ++nextId;
      pending.set(id, { resolve, reject, method });
      socket.send(JSON.stringify({ id, method, params }));
    });
    socket.addEventListener('message', event => {
      const message = JSON.parse(event.data);
      if (message.id) {
        const request = pending.get(message.id);
        if (!request) return;
        pending.delete(message.id);
        if (message.error) request.reject(new Error(`${request.method}: ${message.error.message}`));
        else request.resolve(message.result || {});
        return;
      }
      if (message.method !== 'Fetch.requestPaused') return;
      const { requestId, request } = message.params;
      const pathname = new URL(request.url).pathname;
      const complete = async (status, payload) => {
        await send('Fetch.fulfillRequest', {
          requestId, responseCode: status,
          responseHeaders: [{ name: 'Content-Type', value: 'application/json' }],
          body: payload === null ? '' : Buffer.from(JSON.stringify(payload)).toString('base64'),
        });
      };
      if (pathname.endsWith('/auth/login')) {
        loginCount += 1;
        void complete(200, tokenResponse(loginCount));
      } else if (pathname.endsWith('/auth/refresh')) {
        refreshCount += 1;
        if (failNextRefresh) { failNextRefresh = false; void complete(503, { detail: 'Temporary test outage.' }); }
        else void complete(200, tokenResponse(loginCount + refreshCount));
      } else if (pathname.endsWith('/auth/logout')) {
        void complete(204, null);
      } else {
        void send('Fetch.continueRequest', { requestId });
      }
    });

    const evaluate = async expression => {
      let result;
      try { result = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }); }
      catch (error) { throw new Error(`Browser expression failed: ${expression.slice(0, 180)} (${error.message})`); }
      if (result.exceptionDetails) fail(result.exceptionDetails.text || `Page evaluation failed on ${route}.`);
      return result.result?.value;
    };
    const waitFor = async (expression, description, matches = Boolean) => {
      let lastValue;
      while (Date.now() < deadline) {
        lastValue = await evaluate(expression);
        if (matches(lastValue)) return lastValue;
        await new Promise(resolve => setTimeout(resolve, 200));
      }
      fail(`Timed out waiting for ${description} on ${route}; last state: ${JSON.stringify(lastValue)}.`);
    };
    const waitForRequestCount = async (count, description) => {
      while (Date.now() < deadline && refreshCount < count) await new Promise(resolve => setTimeout(resolve, 50));
      if (refreshCount < count) fail(`Timed out waiting for ${description} on ${route}; refresh count=${refreshCount}.`);
    };

    await send('Page.enable');
    await send('Runtime.enable');
    await send('Fetch.enable', { patterns: [{ urlPattern: '*://*/api/auth/*', requestStage: 'Request' }] });
    await send('Page.navigate', { url: `${origin}${route}/login` });
    await waitFor("document.readyState === 'complete' && Boolean(document.querySelector('input[name=email]')) && Boolean(document.querySelector('input[name=password]'))", 'login form render');
    await evaluate(`(() => {
      const set = (name, value) => {
        const input = document.querySelector('input[name="' + name + '"]');
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        setter.call(input, value);
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
      };
      set('email', 'session-check@arcoenergy.example');
      set('password', 'test-only-session-password');
      document.querySelector('form').requestSubmit();
      return true;
    })()`);
    await waitFor(`location.pathname === '${route}/' && !document.querySelector('input[name=password]')`, 'authenticated landing view after login');
    const storedRefreshToken = await waitFor("(() => { try { return JSON.parse(localStorage.getItem('arcoenergy-auth-tokens') || 'null')?.refresh_token || '' } catch { return '' } })()", 'persistent token storage', value => Boolean(value));
    if (loginCount !== 1) fail(`Expected one intercepted login on ${route}, received ${loginCount}.`);

    await send('Page.navigate', { url: `${origin}${route}/login` });
    try {
      await waitFor(`location.pathname === '${route}/' && !document.querySelector('input[name=password]') && (() => { try { return (JSON.parse(localStorage.getItem('arcoenergy-auth-tokens') || 'null')?.refresh_token || '').startsWith('browser-check-refresh-') } catch { return false } })()`, 'session renewal and authenticated route restoration after reload');
    } catch (error) {
      const state = await evaluate("JSON.stringify({ path: location.pathname, loginVisible: Boolean(document.querySelector('input[name=password]')), tokens: localStorage.getItem('arcoenergy-auth-tokens')?.slice(0, 160), body: document.body?.innerText?.slice(0, 300) })");
      fail(`${error.message}; login calls=${loginCount}, refresh calls=${refreshCount}, browser state=${state}.`);
    }
    if (refreshCount < 1) fail(`Expected at least one intercepted refresh after reload on ${route}, received ${refreshCount}.`);
    const rotatedRefreshToken = await evaluate("JSON.parse(localStorage.getItem('arcoenergy-auth-tokens') || 'null')?.refresh_token || ''");
    if (rotatedRefreshToken === storedRefreshToken) fail(`Refresh token was not rotated after reloading ${route}.`);
    const failedRefreshExpected = refreshCount + 1;
    failNextRefresh = true;
    await evaluate(`(() => {
      const saved = JSON.parse(localStorage.getItem('arcoenergy-auth-tokens') || 'null');
      saved.expires_at = Date.now() + 30_000;
      const value = JSON.stringify(saved);
      localStorage.setItem('arcoenergy-auth-tokens', value);
      window.dispatchEvent(new StorageEvent('storage', { key: 'arcoenergy-auth-tokens', newValue: value }));
      window.dispatchEvent(new Event('online'));
      document.dispatchEvent(new Event('visibilitychange'));
    })()`);
    await waitForRequestCount(failedRefreshExpected, 'temporary refresh retry request');
    const retainedRefreshToken = await evaluate("JSON.parse(localStorage.getItem('arcoenergy-auth-tokens') || 'null')?.refresh_token || ''");
    if (retainedRefreshToken !== rotatedRefreshToken) fail(`A temporary refresh outage discarded the saved session on ${route}.`);
    await waitFor(`!document.querySelector('input[name=password]') && Boolean(localStorage.getItem('arcoenergy-auth-tokens'))`, 'session retention through temporary refresh outage');
    await evaluate("document.querySelector('button[title=\"Cerrar sesión\"]')?.click()");
    await waitFor(`location.pathname.endsWith('/login') && Boolean(document.querySelector('input[name=password]')) && !localStorage.getItem('arcoenergy-auth-tokens')`, 'explicit logout clearing the saved session');
  } finally {
    if (socket && socket.readyState < WebSocket.CLOSING) socket.close();
    child.kill('SIGTERM');
    await new Promise(resolve => {
      if (child.exitCode !== null) return resolve();
      child.once('exit', resolve);
      setTimeout(() => { child.kill('SIGKILL'); resolve(); }, 3000).unref();
    });
    await rm(profile, { recursive: true, force: true, maxRetries: 8, retryDelay: 100 });
  }
}

function tokenResponse(sequence) {
  return {
    access_token: `browser-check-access-${sequence}`,
    refresh_token: `browser-check-refresh-${sequence}`,
    token_type: 'bearer', expires_in: 900,
    identity: {
      user_id: 'browser-check-user', organization_id: 'arcoenergy',
      roles: ['administrador'], permissions,
      email: 'session-check@arcoenergy.example', name: 'Browser Session Check',
    },
  };
}

for (const route of ['/app', '/crm']) {
  await verifySurface(route);
  console.log(`${route} login and saved-session browser checks passed.`);
}
