/* Service Worker - Maker Pro v1.2.5
   v1.2.5: demo.zip ikut disimpan untuk mode offline (demo.json lama tetap dicoba sebagai cadangan).
   v1.2.4: halaman /maker jaringan dulu, berkas pendamping cache dulu.

   Struktur situs: halaman aplikasi di /maker, berkas pendamping di akar situs (/).
   Strategi:
   - Halaman /maker (navigasi): JARINGAN DULU, jika offline pakai salinan tersimpan
     (tidak lagi cache-first, jadi versi baru langsung terpakai saat online).
   - Berkas satu asal (demo.zip, demo.json, ikon, dll) + font Google: tampilkan cache dulu, perbarui di latar belakang.
   - Permintaan lain (mis. cek lisensi api.github.com) TIDAK disentuh sama sekali. */
const APP_VERSION = 'v1.2.5';
const CACHE_NAME = 'maker-pro-' + APP_VERSION;
const APP_PAGE = '/maker';
const CORE_FILES = [
  APP_PAGE,
  '/postermaker.manifest.json',
  '/demo.zip',
  '/demo.json',
  '/icon.png',
  '/pwa-icon-192.png',
  '/pwa-icon-512.png',
  '/pwa-icon-maskable-512.png',
  '/apple-touch-icon.png'
];
const FONT_HOSTS = ['fonts.googleapis.com', 'fonts.gstatic.com'];

/* Respons hasil redirect tidak boleh dipakai untuk navigasi: bersihkan dulu */
async function cleanResponse(res) {
  if (!res || !res.redirected) return res;
  const body = await res.clone().blob();
  return new Response(body, { status: 200, statusText: 'OK', headers: res.headers });
}

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    // Satu berkas gagal (mis. demo.zip belum ada) tidak boleh menggagalkan seluruh instalasi
    await Promise.all(CORE_FILES.map(async (url) => {
      try {
        const res = await fetch(new Request(url, { cache: 'reload' }));
        if (res && res.ok) await cache.put(url, await cleanResponse(res));
      } catch (e) { /* abaikan */ }
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k.startsWith('maker-pro-') && k !== CACHE_NAME).map((k) => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return;
  if (req.headers.has('range')) return;

  const sameOrigin = url.origin === self.location.origin;
  const isFont = FONT_HOSTS.includes(url.hostname);
  if (!sameOrigin && !isFont) return;

  if (req.mode === 'navigate') {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      try {
        const fresh = await fetch(req);
        if (fresh && fresh.ok) {
          const copy = await cleanResponse(fresh.clone());
          cache.put(req, copy).catch(() => {});
        }
        return fresh;
      } catch (e) {
        const cached = (await cache.match(req, { ignoreSearch: true })) || (await cache.match(APP_PAGE));
        if (cached) return cached;
        return new Response('<h1>Offline</h1><p>Buka aplikasi sekali saat online agar bisa dipakai offline.</p>',
          { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
      }
    })());
    return;
  }

  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(req);
    const network = fetch(req).then((res) => {
      if (res && (res.ok || res.type === 'opaque')) cache.put(req, res.clone()).catch(() => {});
      return res;
    }).catch(() => null);
    if (cached) { event.waitUntil(network); return cached; }
    const res = await network;
    return res || new Response('', { status: 504 });
  })());
});
