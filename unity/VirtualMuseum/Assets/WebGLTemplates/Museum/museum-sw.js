// Give the museum its own controller on origins shared with another site.
// Requests use the browser's normal network and cache behavior.
self.addEventListener("install", (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});
