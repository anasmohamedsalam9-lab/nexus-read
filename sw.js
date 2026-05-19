// Service Worker for Nexus Scans PWA
const CACHE_NAME = 'nexus-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/styles.css',
  '/script.js',
  '/data.js',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  // Ignore API or external cross-origin requests for caching
  if (!event.request.url.startsWith(self.location.origin)) {
      return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response; // Return from cache
        }
        return fetch(event.request).catch(() => {
          // Fallback logic if needed
        });
      })
  );
});
