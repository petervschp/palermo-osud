const CACHE = "palermo-osud-brython-v1.3";
const ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.py",
  "./facts_chobotnica.json",
  "./manifest.json",
  "./assets/logo.svg",
  "./assets/icon-192.png",
  "./assets/icon-512.png"
];

// Brython CDN (cached as opaque responses on first load)
const CDN = [
  "https://cdn.jsdelivr.net/npm/brython@3.12.4/brython.min.js",
  "https://cdn.jsdelivr.net/npm/brython@3.12.4/brython_stdlib.min.js"
];

self.addEventListener("install", (evt) => {
  evt.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.addAll(ASSETS);
    // Cache CDN best-effort
    for (const url of CDN) {
      try { await cache.add(new Request(url, {mode:"no-cors"})); } catch(e) {}
    }
  })());
  self.skipWaiting();
});

self.addEventListener("activate", (evt) => {
  evt.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (evt) => {
  evt.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(evt.request, {ignoreVary:true});
    if (cached) return cached;

    try {
      const res = await fetch(evt.request);
      // Cache same-origin GETs
      if (evt.request.method === "GET" && new URL(evt.request.url).origin === self.location.origin) {
        cache.put(evt.request, res.clone());
      }
      return res;
    } catch (e) {
      // offline fallback to index for navigation
      const url = new URL(evt.request.url);
      if (evt.request.mode === "navigate" || url.pathname.endsWith("/")) {
        return cache.match("./index.html");
      }
      return cached || cache.match("./index.html");
    }
  })());
});
