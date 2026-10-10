const CACHE_NAME = 'maker-pro-offline-v3';
const ASSETS_TO_CACHE = [
    '/maker',
    '/postermaker.manifest.json',
    '/demo.json',
    '/icon.png'
];

self.addEventListener('install', (event) => {
    self.skipWaiting(); // Memaksa SW baru langsung aktif
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

self.addEventListener('activate', (event) => {
    // Menghapus cache versi lama
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request).then((fetchRes) => {
                return caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request.url, fetchRes.clone());
                    return fetchRes;
                });
            });
        }).catch(() => {
            // Abaikan jika offline agar tidak muncul layar error Dinosaurus
        })
    );
});
