// Route-scoped offline message. Keep authenticated pages and APIs network-only.
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (event.request.mode !== 'navigate' || url.origin !== self.location.origin || url.pathname !== '/pwa/') return;
  event.respondWith(fetch(event.request).catch(() => new Response(
    'Sin conexión. Vuelve a conectarte para consultar tu Portafolio Kairos.',
    {status: 503, headers: {'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store'}}
  )));
});
