const CACHE_NAME = 'kefa-v2-dynamic';
const STATIC_CACHE_NAME = 'kefa-v2-static';

const STATIC_ASSETS = [
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/js/notifications.js',
  '/static/images/icon-192.png',
  '/static/images/icon-512.png',
  // Add a dedicated offline page if you have one, or fallback to home
  '/', 
];

// Install Event: Cache core static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching App Shell');
        return cache.addAll(STATIC_ASSETS);
      })
  );
  self.skipWaiting();
});

// Activate Event: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== STATIC_CACHE_NAME) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Fetch Event: The Core Logic
self.addEventListener('fetch', (event) => {
  // 1. Navigation Requests (HTML pages) -> Network First, Fallback to Cache
  // This ensures users always get the latest live scores/tables if online.
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Clone the response to store it in cache for offline use later
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
          return response;
        })
        .catch(() => {
          // If offline, try to return the cached version of this page
          return caches.match(event.request)
            .then((response) => {
              // If page not in cache, return the cached Home page or Offline page
              return response || caches.match('/');
            });
        })
    );
    return;
  }

  // 2. Static Assets (Images, CSS, JS) -> Cache First, Fallback to Network
  // These don't change often, so we serve them fast from cache.
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        return fetch(event.request).then((networkResponse) => {
           // Optional: Cache new static assets dynamically here if desired
           return networkResponse;
        });
      })
  );
});

// Notification Click Handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  let url = '/';
  if (event.notification.data && event.notification.data.url) {
    url = event.notification.data.url;
  }
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        for (let client of clientList) {
          if (client.url === url && 'focus' in client) {
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
  );
});

