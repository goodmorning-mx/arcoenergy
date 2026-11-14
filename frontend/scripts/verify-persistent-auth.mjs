import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createServer } from 'node:net';
import { spawn } from 'node:child_process';

const origin = process.env.ARCOENERGY_AUTH_TEST_ORIGIN || 'http://127.0.0.1:18081';
const chromeBin = process.env.CHROME_BIN || 'google-chrome';
const timeoutMs = 20_000;
const commandTimeoutMs = 15_000;
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
  let failRefreshesRemaining = 0;
  let currentAccessToken = '';
  let expireNextFieldAction = false;
  const invalidAccessTokens = new Set();
  const fieldActionAttempts = [];
  let agentChatRequests = 0;
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
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(new Error(`${method}: Chrome DevTools did not respond within ${commandTimeoutMs} ms.`));
      }, commandTimeoutMs);
      pending.set(id, {
        resolve(value) { clearTimeout(timer); resolve(value); },
        reject(error) { clearTimeout(timer); reject(error); },
        method,
      });
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
        try {
          await send('Fetch.fulfillRequest', {
            requestId, responseCode: status,
            responseHeaders: [{ name: 'Content-Type', value: 'application/json' }],
            body: payload === null ? '' : Buffer.from(JSON.stringify(payload)).toString('base64'),
          });
        } catch (error) {
          // Chrome can cancel an in-flight intercepted request during route changes.
          // Its interception ID is then stale; that is harmless to the browser test.
          if (!error.message.includes('Invalid InterceptionId')) throw error;
        }
      };
      if (pathname.endsWith('/auth/login')) {
        loginCount += 1;
        const tokens = tokenResponse(loginCount, route);
        currentAccessToken = tokens.access_token;
        void complete(200, tokens);
      } else if (pathname.endsWith('/auth/refresh')) {
        refreshCount += 1;
        if (failRefreshesRemaining > 0) {
          failRefreshesRemaining -= 1;
          void complete(503, { detail: 'Temporary test outage.' });
        }
        else {
          const tokens = tokenResponse(loginCount + refreshCount, route);
          currentAccessToken = tokens.access_token;
          void complete(200, tokens);
        }
      } else if (pathname.endsWith('/auth/logout')) {
        void complete(204, null);
      } else if (route === '/app' && pathname.endsWith('/v1/installations')) {
        void complete(200, [installationFixture]);
      } else if (route === '/app' && pathname.endsWith('/v1/inventory/movements')) {
        void complete(200, []);
      } else if (route === '/app' && pathname.endsWith('/v1/inventory')) {
        void complete(200, [inventoryFixture]);
      } else if (route === '/app' && pathname.endsWith('/v1/inventory/consume')) {
        const authorization = Object.entries(request.headers || {}).find(([name]) => name.toLowerCase() === 'authorization')?.[1] || '';
        fieldActionAttempts.push({ authorization, body: request.postData || '' });
        if (expireNextFieldAction) { invalidAccessTokens.add(currentAccessToken); expireNextFieldAction = false; }
        const token = authorization.replace(/^Bearer\s+/i, '');
        const invalid = invalidAccessTokens.has(token);
        void complete(invalid ? 401 : 201, invalid ? { detail: 'Expired access token.' } : { id: 'browser-check-movement' });
      } else if (route === '/crm' && pathname.endsWith('/v1/agent/chat')) {
        agentChatRequests += 1;
        void complete(200, {
          conversationId: 'browser-check-agent-conversation',
          confirmation: {
            tool: 'arcoenergy.schedule_followup', arguments: { customer_id: 'browser-check-customer' },
            summary: 'Programar seguimiento de prueba', details: ['Cliente: Rosa de prueba', 'Fecha: 2026-11-20'],
            confirmation_token: 'browser-check-secret-token', intent_id: 'browser-check-intent',
            idempotency_key: 'browser-check-idempotency-key',
          },
        });
      } else {
        void send('Fetch.continueRequest', { requestId }).catch(error => {
          if (!error.message.includes('Invalid InterceptionId')) throw error;
        });
      }
    });

    const evaluate = async expression => {
      let result;
      try { result = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }); }
      catch (error) { throw new Error(`Browser expression failed: ${expression.slice(0, 180)} (${error.message})`); }
      if (result.exceptionDetails) {
        const detail = result.exceptionDetails.exception?.description || result.exceptionDetails.text;
        fail(`${detail || `Page evaluation failed on ${route}.`} [${expression.slice(0, 240)}]`);
      }
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
    await send('Fetch.enable', { patterns: [{ urlPattern: '*://*/api/*', requestStage: 'Request' }] });
    await send('Page.navigate', { url: `${origin}${route}/login` });
    await waitFor(`(() => {
      if (document.readyState !== 'complete') return false;
      const set = (name, value) => {
        const input = document.querySelector('input[name="' + name + '"]');
        if (!input) return false;
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        setter.call(input, value);
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
      };
      if (!set('email', 'session-check@arcoenergy.example') || !set('password', 'test-only-session-password')) return false;
      document.querySelector('form')?.requestSubmit();
      return true;
    })()`, 'login form render and submit');
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
    let latestRefreshToken = await evaluate("JSON.parse(localStorage.getItem('arcoenergy-auth-tokens') || 'null')?.refresh_token || ''");
    if (latestRefreshToken === storedRefreshToken) fail(`Refresh token was not rotated after reloading ${route}.`);
    if (route === '/app') {
      await evaluate("Array.from(document.querySelectorAll('.rail-item')).find(button => button.textContent.includes('Inventario'))?.click()");
      await waitFor("Boolean(document.querySelector('.field-actions select[name=installation_id]')) && Boolean(document.querySelector('.field-actions select[name=item_id]'))", 'installer inventory action form');
      await evaluate(`(() => {
        const select = document.querySelector('.field-actions select[name="installation_id"]');
        const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
        setter.call(select, 'browser-check-order');
        select.dispatchEvent(new Event('input', { bubbles: true }));
        select.dispatchEvent(new Event('change', { bubbles: true }));
      })()`);
      await waitFor("Array.from(document.querySelector('.field-actions select[name=item_id]').options).some(option => option.value === 'browser-check-item')", 'assigned item available for the installation');
      expireNextFieldAction = true;
      await evaluate(`(() => {
        const item = document.querySelector('.field-actions select[name="item_id"]');
        const selectSetter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
        selectSetter.call(item, 'browser-check-item');
        item.dispatchEvent(new Event('input', { bubbles: true }));
        item.dispatchEvent(new Event('change', { bubbles: true }));
        const quantity = document.querySelector('.field-actions input[name="quantity"]');
        const inputSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        inputSetter.call(quantity, '1');
        quantity.dispatchEvent(new Event('input', { bubbles: true }));
        quantity.dispatchEvent(new Event('change', { bubbles: true }));
        item.closest('form').requestSubmit();
      })()`);
      try {
        await waitFor("document.body.innerText.includes('Consumo registrado en la orden de trabajo.')", 'field action retry after access token renewal');
      } catch (error) {
        const state = await evaluate("JSON.stringify({body:document.body?.innerText?.slice(-900), actionRequests:" + JSON.stringify(fieldActionAttempts) + ", refreshCalls:" + refreshCount + ", form:document.querySelector('.field-actions form')?.innerText})");
        fail(`${error.message}; browser state=${state}.`);
      }
      if (refreshCount < 2 || fieldActionAttempts.length !== 2) fail(`Expected a 401, forced refresh and one action retry; refresh calls=${refreshCount}, field action requests=${fieldActionAttempts.length}.`);
      const firstAction = JSON.parse(fieldActionAttempts[0].body);
      const secondAction = JSON.parse(fieldActionAttempts[1].body);
      const savedAccessToken = await evaluate("JSON.parse(localStorage.getItem('arcoenergy-auth-tokens') || 'null')?.access_token || ''");
      if (fieldActionAttempts[0].authorization === fieldActionAttempts[1].authorization || fieldActionAttempts[1].authorization !== `Bearer ${savedAccessToken}`) fail(`Field action did not retry with the rotated access token: ${JSON.stringify(fieldActionAttempts.map(attempt => attempt.authorization))}.`);
      if (!firstAction.operation_id || firstAction.operation_id !== secondAction.operation_id) fail('Field action retry did not preserve its idempotency identifier.');
      latestRefreshToken = await evaluate("JSON.parse(localStorage.getItem('arcoenergy-auth-tokens') || 'null')?.refresh_token || ''");
      if (latestRefreshToken === storedRefreshToken) fail('Field action renewal did not persist its rotated refresh token.');

      const queuedAttemptStart = fieldActionAttempts.length;
      const refreshCountBeforeQueue = refreshCount;
      failRefreshesRemaining = 2;
      expireNextFieldAction = true;
      await evaluate(`(() => {
        const item = document.querySelector('.field-actions select[name="item_id"]');
        const selectSetter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
        selectSetter.call(item, 'browser-check-item');
        item.dispatchEvent(new Event('input', { bubbles: true }));
        item.dispatchEvent(new Event('change', { bubbles: true }));
        const quantity = document.querySelector('.field-actions input[name="quantity"]');
        const inputSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        inputSetter.call(quantity, '1');
        quantity.dispatchEvent(new Event('input', { bubbles: true }));
        quantity.dispatchEvent(new Event('change', { bubbles: true }));
        item.closest('form').requestSubmit();
      })()`);
      const queuedActions = await waitFor(`new Promise(resolve => {
        const request = indexedDB.open('arcoenergy-field-cache');
        request.onsuccess = () => {
          const database = request.result;
          const transaction = database.transaction('actions-queue', 'readonly');
          const rows = transaction.objectStore('actions-queue').getAll();
          rows.onsuccess = () => { const own = rows.result.filter(row => row.owner === 'session-check@arcoenergy.example'); database.close(); resolve(own.map(row => ({ operation_id: row.operation_id, summary: row.summary }))); };
          rows.onerror = () => { database.close(); resolve([]); };
        };
        request.onerror = () => resolve([]);
      })`, 'field action retained after renewal failure', rows => Array.isArray(rows) && rows.length > 0);
      await waitForRequestCount(refreshCountBeforeQueue + 2, 'queued operation refresh retry after a temporary failure');
      const queuedId = queuedActions[0].operation_id;
      const queuedAttempts = fieldActionAttempts.slice(queuedAttemptStart);
      if (refreshCount < refreshCountBeforeQueue + 2 || queuedAttempts.length < 2) fail(`Expected failed refresh attempts and a queued field action; refresh calls=${refreshCount}, action retries=${queuedAttempts.length}.`);
      if (queuedAttempts.some(attempt => JSON.parse(attempt.body).operation_id !== queuedId)) fail('Failed-refresh retry changed or lost the queued action identifier.');
      if (queuedActions.length !== 1) fail(`Expected one pending field action after refresh failure, received ${queuedActions.length}.`);
    } else if (route === '/crm') {
      await evaluate("document.querySelector('button.agent-launcher')?.click()");
      await waitFor("Boolean(document.querySelector('section[aria-label=\"¿Qué necesitas resolver?\"] input[aria-label=Mensaje]'))", 'CRM agent chat panel');
      await evaluate(`(() => {
        const input = document.querySelector('section[aria-label="¿Qué necesitas resolver?"] input[aria-label="Mensaje"]');
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        setter.call(input, 'Programa seguimiento de prueba');
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.closest('form').requestSubmit();
      })()`);
      await waitFor("document.body.innerText.includes('Programar seguimiento de prueba')", 'agent confirmation preview');
      if (agentChatRequests !== 1) fail(`Expected one simulated agent request, received ${agentChatRequests}.`);
      const storageKey = await evaluate("Object.keys(sessionStorage).find(key => key.startsWith('arcoenergy-agent:')) || ''");
      const storedChat = await evaluate(`sessionStorage.getItem(${JSON.stringify(storageKey)}) || ''`);
      if (!storageKey || storedChat.includes('browser-check-secret-token') || storedChat.includes('browser-check-idempotency-key')) fail('The CRM chat did not persist under the user key or stored confirmation credentials.');
      await send('Page.reload');
      await waitFor("document.querySelector('button.agent-launcher') && document.querySelector('input[name=password]') === null", 'CRM after authenticated agent chat reload');
      await evaluate("document.querySelector('button.agent-launcher')?.click()");
      await waitFor("document.body.innerText.includes('Programar seguimiento de prueba') && document.body.innerText.includes('La confirmación anterior venció')", 'restored CRM chat with expired confirmation');
      const confirmButtons = await evaluate("Array.from(document.querySelectorAll('[aria-label=\"Confirmación de operación\"] button')).filter(button => button.textContent.includes('Confirmar y ejecutar')).length");
      if (confirmButtons !== 0) fail('A restored CRM confirmation remained executable after reload.');
      const savedChat = await evaluate(`sessionStorage.getItem(${JSON.stringify(storageKey)}) || ''`);
      if (agentChatRequests !== 1 || savedChat.includes('browser-check-secret-token')) fail('Reload lost the conversation or persisted a confirmation credential.');
    }
    const failedRefreshExpected = refreshCount + 1;
    failRefreshesRemaining = 5;
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
    if (retainedRefreshToken !== latestRefreshToken) fail(`A temporary refresh outage discarded the saved session on ${route}.`);
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

const installationFixture = {
  id: 'browser-check-order', folio: 'AE-CHECK-1', scheduled_at: null,
  lead_installer: 'session-check@arcoenergy.example', assigned_installers: ['session-check@arcoenergy.example'],
  confirmed_installers: [], status: 'assigned', notes: '',
  customer: { id: 'browser-check-customer', name: 'Cliente de verificación', city: 'Tampico', address: 'Tampico' },
  checklist: [], materials: [{ item_id: 'browser-check-item', item_name: 'Panel de verificación', requested_quantity: 1, preissued_quantity: 0, consumed_quantity: 0, remaining_quantity: 1, remaining_to_issue: 0, available_for_order: 2, shortage_quantity: 0 }],
};
const inventoryFixture = { id: 'browser-check-item', name: 'Panel de verificación', category: 'Paneles', unit: 'pieza', quantity: 2, reserved_quantity: 0, available_quantity: 2, minimum_quantity: 0, unit_cost: 1, barcode: null };

function tokenResponse(sequence, route) {
  const installerPermissions = ['installations:read', 'inventory:read', 'inventory:write', 'expenses:write'];
  return {
    access_token: `browser-check-access-${sequence}`,
    refresh_token: `browser-check-refresh-${sequence}`,
    token_type: 'bearer', expires_in: 900,
    identity: {
      user_id: 'browser-check-user', organization_id: 'arcoenergy',
      roles: route === '/app' ? ['instalador'] : ['administrador'], permissions: route === '/app' ? installerPermissions : permissions,
      email: 'session-check@arcoenergy.example', name: 'Browser Session Check',
    },
  };
}

for (const route of ['/app', '/crm']) {
  await verifySurface(route);
  console.log(route === '/app'
    ? '/app login, saved-session and expired-access field-action checks passed.'
    : '/crm login and saved-session browser checks passed.');
}
