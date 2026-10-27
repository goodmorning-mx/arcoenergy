const CACHE_NAME = 'arcoenergy-shell-v1';
const APP_SHELL = ['/app/'];

self.addEventListener('install', (event) => event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting())));
self.addEventListener('activate', (event) => event.waitUntil(Promise.all([self.clients.claim(), caches.keys().then((keys) => Promise.all(keys.filter((key) => key.startsWith('arcoenergy-shell-') && key !== CACHE_NAME).map((key) => caches.delete(key))))])));

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  const isApiOrAuth = url.pathname === '/api' || url.pathname.startsWith('/api/') || url.pathname === '/auth' || url.pathname.startsWith('/auth/');
  if (request.method !== 'GET' || isApiOrAuth || request.headers.has('authorization')) return;
  if (url.origin !== self.location.origin || !url.pathname.startsWith('/app/')) return;

  event.respondWith(
    fetch(request).then((response) => {
      if (response.ok) void caches.open(CACHE_NAME).then((cache) => cache.put(request, response.clone()));
      return response;
    }).catch(() => caches.match(request).then((cached) => cached || caches.match('/app/'))),
  );
});
