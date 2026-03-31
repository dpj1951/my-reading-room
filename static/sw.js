const CACHE_NAME = 'reading-alcove-v1';
const PRECACHE_URLS = ['/', '/books', '/authors'];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  // Only handle GET requests for same-origin navigation
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== location.origin) return;

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Cache successful responses for navigations and static assets
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request).then(cached => {
        if (cached) return cached;
        // Return offline fallback page
        return new Response(
          `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Offline — My Reading Alcove</title>
  <style>
    body { font-family: 'DM Sans', sans-serif; background: #0e0e12; color: #f0ede8; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; flex-direction: column; gap: 16px; text-align: center; padding: 24px; }
    h1 { font-size: 1.5rem; }
    p { color: #8a8795; font-size: 0.95rem; line-height: 1.6; max-width: 320px; }
    a { color: #3b9eff; text-decoration: none; font-size: 0.9rem; }
  </style>
</head>
<body>
  <h1>You're offline</h1>
  <p>Your library hasn't been cached yet. Visit your library while online first, and it'll be available here when you're offline.</p>
  <a href="/books">Try again</a>
</body>
</html>`,
          { headers: { 'Content-Type': 'text/html' } }
        );
      }))
  );
});