// sw-arsip.js v1.0.2 - MILIK /arsip: bersihkan cache UI lama + arahkan "/" ke /arsip
// Riwayat: v1.0.2 cegah bentrok dengan fetch handler Maker Pro | v1.0.1 pindah ke folder arsip-sw/
// Dipanggil dari sw.js lewat: importScripts('/arsip-sw/sw-arsip.js');  (kode Maker Pro tidak diubah)

(function () {
  // Isi bila tahu nama cache lama milik UI arsip lama (awalan nama), contoh: ['arsip-lama-', 'dakwah-v']
  var AWALAN_CACHE_LAMA_ARSIP = [];

  // Halaman beranda lama yang harus dibuang dari SEMUA cache (Maker Pro memakai /maker.html, jadi aman)
  var HALAMAN_LAMA = ['/', '/index.html', '/index'];

  self.addEventListener('install', function () { self.skipWaiting(); });

  self.addEventListener('activate', function (event) {
    event.waitUntil((async function () {
      var keys = await caches.keys();
      for (var i = 0; i < keys.length; i++) {
        var k = keys[i];
        var cocok = AWALAN_CACHE_LAMA_ARSIP.some(function (a) { return k.indexOf(a) === 0; });
        if (cocok) { await caches.delete(k); continue; }
        var c = await caches.open(k);
        for (var j = 0; j < HALAMAN_LAMA.length; j++) {
          await c.delete(HALAMAN_LAMA[j], { ignoreSearch: true });
          await c.delete(new URL(HALAMAN_LAMA[j], self.location.origin).href, { ignoreSearch: true });
        }
      }
      await self.clients.claim();
      var wins = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      wins.forEach(function (w) {
        var p = new URL(w.url).pathname;
        if (p === '/' || p === '/index.html') w.navigate('/arsip');
      });
    })());
  });

  self.addEventListener('fetch', function (event) {
    var req = event.request;
    if (req.mode !== 'navigate') return;
    var p = new URL(req.url).pathname;
    if (p === '/' || p === '/index.html') {
      event.stopImmediatePropagation(); // handler Maker Pro tidak ikut jalan untuk "/"
      event.respondWith(Response.redirect('/arsip', 302));
    }
  });
})();
