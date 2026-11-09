// Scope-specific caches also keep the origin's root service worker out of this app.
const prefix = "museum-" + new URL(self.registration.scope).pathname + "-";
const shellCache = prefix + "shell-bc324938118904d8";
const modelCache = prefix + "models-v1";
const roomCache = prefix + "room-v1";
const shellPaths = ["index.html", "museum.css", "favicon.svg", "manifest.webmanifest"];
const shellUrls = new Set(shellPaths.map(path => new URL(path, self.registration.scope).href));
const maxModels = 8;
const maxModelBytes = 4 * 1024 * 1024;

self.addEventListener("install", event => {
  event.waitUntil((async () => {
    // Only the small entrance page is prefetched. No Unity data or models here.
    try {
      const cache = await caches.open(shellCache);
      await cache.addAll(shellPaths.map(path => new Request(new URL(path, self.registration.scope), { cache: "reload" })));
    } catch (error) { console.warn("Entrance cache unavailable:", error); }
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) {
      if (key.startsWith(prefix + "shell-") && key !== shellCache) await caches.delete(key);
    }
    await self.clients.claim();
  })());
});

// Serialize writes/evictions: concurrent tabs must not grow an unbounded cache.
let modelWrites = Promise.resolve();
function storeModel(request, response, room = false) {
  modelWrites = modelWrites.catch(() => {}).then(async () => {
    const blob = await response.blob();
    if (blob.size > (room ? 12 * 1024 * 1024 : maxModelBytes)) return;
    const cache = await caches.open(room ? roomCache : modelCache);
    await cache.delete(request);
    const headers = new Headers(response.headers);headers.set("X-Museum-Bytes", String(blob.size));
    await cache.put(request, new Response(blob, { status: 200, headers }));
    const keys = await cache.keys();
    if (room) {
      const sizes = await Promise.all(keys.map(async key => Number((await cache.match(key)).headers.get("X-Museum-Bytes")) || 0));
      let total = sizes.reduce((a,b) => a+b,0), remaining=keys.length;
      for (let i=0;i<keys.length && (total>40*1024*1024 || remaining>32);i++) {
        await cache.delete(keys[i]);total-=sizes[i];remaining--;
      }
    } else for (const key of keys.slice(0, Math.max(0, keys.length - maxModels))) await cache.delete(key);
  }).catch(error => console.warn("Model cache unavailable:", error));
  return modelWrites;
}

self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  const scope = new URL(self.registration.scope);
  if (request.method !== "GET" || url.origin !== scope.origin || !url.pathname.startsWith(scope.pathname)) return;
  const relative = url.pathname.slice(scope.pathname.length);
  const room = /^Content\/room-[a-z0-9-]+-[a-f0-9]{32}\.bundle$/.test(relative);
  if (room || /^Content\/specimen-\d{2}-[a-f0-9]{32}\.bundle$/.test(relative)) {
    event.respondWith((async () => {
      try { const cached = await (await caches.open(room ? roomCache : modelCache)).match(request); if (cached) return cached; } catch (_) {}
      const response = await fetch(request);
      if (response.ok && response.status === 200) event.waitUntil(storeModel(request, response.clone(), room));
      return response;
    })());
    return;
  }
  if (shellUrls.has(url.href) || (request.mode === "navigate" && (relative === "" || relative === "index.html"))) {
    event.respondWith((async () => {
      const key = request.mode === "navigate" ? new URL("index.html", scope).href : request;
      try {
        const response = await fetch(request);
        if (response.ok) {
          event.waitUntil(caches.open(shellCache).then(cache => cache.put(key, response.clone())).catch(() => {}));
          return response;
        }
        const cached = await caches.match(key, { cacheName: shellCache });
        return cached || response;
      } catch (error) {
        const cached = await caches.match(key, { cacheName: shellCache });
        if (cached) return cached;
        throw error;
      }
    })());
  }
  // Unity's data cache owns startup data. Do not store a second copy here.
});
