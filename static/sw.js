// Service Worker v4 — offline-capable
// Caches app shell + static assets; stores library in Cache API for offline browsing

const CACHE_VERSION = 'v4';
const SHELL_CACHE = 'alcove-shell-' + CACHE_VERSION;
const DATA_CACHE  = 'alcove-data-'  + CACHE_VERSION;

const SHELL_ASSETS = [
  '/offline',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/alcove_logo.png',
];

// App shell pages — cached at runtime on every successful online visit.
// "/" and "/home" are new here: iOS reloads the manifest's start_url ("/")
// on a cold launch of the installed PWA, so it must be handled the same
// way "/books" already was, or airplane-mode relaunches fail outright.
const APP_PAGES = ['/', '/home', '/books'];

// Install — cache shell assets
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(SHELL_CACHE).then(c => c.addAll(SHELL_ASSETS))
    .then(() => self.skipWaiting())
  );
});

// Activate — delete old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== SHELL_CACHE && k !== DATA_CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Fetch strategy
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Only handle same-origin GET requests
  if (e.request.method !== 'GET' || url.origin !== self.location.origin) return;

  // /books/data — network first, cache on success for offline fallback
  if (url.pathname === '/books/data') {
    e.respondWith(
      fetch(e.request).then(res => {
        if (res.ok) {
          const clone = res.clone();
          caches.open(DATA_CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      }).catch(() => caches.match(e.request))
    );
    return;
  }

  // App shell pages (/, /home, /books) — network first, fall back to their
  // own cached copy, then the cached /books page, then /offline.
  if (APP_PAGES.includes(url.pathname)) {
    e.respondWith(
      fetch(e.request).then(res => {
        if (res.ok) {
          const clone = res.clone();
          caches.open(SHELL_CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      }).catch(() =>
        caches.match(e.request).then(cached =>
          cached || caches.match('/books').then(booksCached =>
            booksCached || caches.match('/offline')
          )
        )
      )
    );
    return;
  }

  // Static assets — cache first, network fallback
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(
      caches.match(e.request).then(cached =>
        cached || fetch(e.request).then(res => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(SHELL_CACHE).then(c => c.put(e.request, clone));
          }
          return res;
        })
      )
    );
    return;
  }

  // Everything else — network only (auth pages, API calls, etc.)
  // Do NOT cache: /login, /signup, /settings, POST requests
});
