// Service worker v2 - clears cache on auth update
const CACHE_NAME = 'reading-alcove-v2';
self.addEventListener('install', e => { self.skipWaiting(); });
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.map(k => caches.delete(k))))
    .then(() => self.clients.claim())
  );
});
self.addEventListener('fetch', e => {
  // Pass all requests through to network - no caching
  e.respondWith(fetch(e.request));
});
