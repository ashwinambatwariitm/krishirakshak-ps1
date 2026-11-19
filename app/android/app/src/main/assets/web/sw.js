/**
 * KrishiRakshak Offline Service Worker
 * Pre-caches UI assets so the app loads instantly offline on the Pi Wi-Fi hotspot.
 */

// Version of the offline copy: changing it makes browsers drop older copies (activate handler below)
const CACHE_NAME = "krishirakshak-v3";
const STATIC_ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./css/style.css",
  "./js/config.js",
  "./js/i18n_regional.js",
  "./js/i18n.js",
  "./js/api.js",
  "./js/canvas.js",
  "./js/state.js",
  "./js/app.js",
  "./assets/icon.svg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Network-first for API requests
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Network-first for the app files: when the Pi is reachable the phone always gets the current app (a cache-first
  // worker kept showing an old copy after updates); the cached copy is used only when the Pi cannot be reached
  event.respondWith(
    fetch(event.request).then((networkResponse) => {
      if (networkResponse && networkResponse.status === 200 && networkResponse.type === "basic") {
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
      }
      return networkResponse;
    }).catch(() => caches.match(event.request))
  );
});
