import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createServer } from 'node:net';
import { spawn } from 'node:child_process';

const baseUrl = process.env.ARCOENERGY_PWA_URL || 'http://127.0.0.1:18081/app/';
const chromeBin = process.env.CHROME_BIN || 'google-chrome';
const timeoutMs = 30_000;

function fail(message) {
  throw new Error(message);
}

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
    } catch (error) {
      lastError = error;
    }
    await new Promise(resolve => setTimeout(resolve, 150));
  }
  throw new Error(`Chrome DevTools did not become ready: ${lastError}`);
}

async function main() {
  const port = await freePort();
  const profile = await mkdtemp(join(tmpdir(), 'arcoenergy-offline-chrome-'));
  const child = spawn(chromeBin, [
    '--headless=new', '--no-sandbox', '--disable-dev-shm-usage', '--disable-extensions',
    '--no-first-run', '--disable-background-networking', '--disable-sync',
    `--user-data-dir=${profile}`, '--remote-debugging-address=127.0.0.1',
    `--remote-debugging-port=${port}`, 'about:blank',
  ], { stdio: 'ignore' });
  let socket;
  try {
    const deadline = Date.now() + timeoutMs;
    await waitForJson(`http://127.0.0.1:${port}/json/version`, child, deadline);
    const targetResponse = await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' });
    if (!targetResponse.ok) fail(`Chrome could not create a DevTools page: HTTP ${targetResponse.status}.`);
    const target = await targetResponse.json();
    socket = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      socket.addEventListener('open', resolve, { once: true });
      socket.addEventListener('error', reject, { once: true });
    });

    let nextId = 0;
    const pending = new Map();
    socket.addEventListener('message', event => {
      const message = JSON.parse(event.data);
      if (!message.id) return;
      const request = pending.get(message.id);
      if (!request) return;
      pending.delete(message.id);
      if (message.error) request.reject(new Error(message.error.message));
      else request.resolve(message.result || {});
    });
    const send = (method, params = {}) => new Promise((resolve, reject) => {
      const id = ++nextId;
      pending.set(id, { resolve, reject });
      socket.send(JSON.stringify({ id, method, params }));
    });
    const evaluate = async expression => {
      const result = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
      if (result.exceptionDetails) fail(result.exceptionDetails.text || 'Page evaluation failed.');
      return result.result?.value;
    };
    const waitFor = async (expression, description, matches = Boolean) => {
      let lastValue;
      while (Date.now() < deadline) {
        lastValue = await evaluate(expression);
        if (matches(lastValue)) return lastValue;
        await new Promise(resolve => setTimeout(resolve, 200));
      }
      fail(`Timed out waiting for ${description}; last page state: ${JSON.stringify(lastValue)}.`);
    };

    await send('Page.enable');
    await send('Runtime.enable');
    await send('Network.enable');
    await send('Page.navigate', { url: baseUrl });
    await waitFor("document.readyState === 'complete' && document.body?.innerText.includes('Iniciar sesión')", 'online PWA login render');
    await waitFor("Boolean(navigator.serviceWorker?.controller)", 'active PWA service worker controller');
    await waitFor("caches.open('arcoenergy-shell-v1').then(async cache => (await cache.keys()).some(request => new URL(request.url).pathname.startsWith('/app/assets/') && request.url.endsWith('.js')))", 'PWA JavaScript asset in the offline cache');
    const probeUrl = new URL(process.env.ARCOENERGY_NETWORK_PROBE_PATH || '/api/health', baseUrl).href;
    const probeLiteral = JSON.stringify(probeUrl);
    const onlineProbe = await evaluate(`fetch(${probeLiteral}, { cache: 'no-store' }).then(response => ({ ok: response.ok, status: response.status })).catch(error => ({ error: String(error) }))`);
    if (!onlineProbe?.ok) fail(`Online network probe failed before offline emulation: ${JSON.stringify(onlineProbe)}.`);

    await send('Network.emulateNetworkConditions', {
      offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0,
    });
    await send('Page.navigate', { url: baseUrl });
    const offlineState = await waitFor("({url:location.href,ready:document.readyState,body:document.body?.innerText?.slice(0,180),online:navigator.onLine,controlled:Boolean(navigator.serviceWorker?.controller)})", 'offline PWA login render from cached shell and assets', state => state.ready === 'complete' && state.body?.includes('Iniciar sesión') && state.controlled);
    if (!offlineState) fail('PWA did not render after network loss.');
    const offlineProbe = await evaluate(`fetch(${probeLiteral}, { cache: 'no-store' }).then(() => false).catch(() => true)`);
    if (!offlineProbe) fail('The API probe remained available while the browser network was offline.');
    console.log('PWA offline shell verified: login UI rendered from cache and API requests remained network-only after network loss.');
  } finally {
    if (socket && socket.readyState < WebSocket.CLOSING) socket.close();
    child.kill('SIGTERM');
    await new Promise(resolve => {
      if (child.exitCode !== null) return resolve();
      child.once('exit', resolve);
      setTimeout(() => { child.kill('SIGKILL'); resolve(); }, 3000).unref();
    });
    await rm(profile, { recursive: true, force: true });
  }
}

main().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
