const params = new URLSearchParams(window.location.search);
const id = params.get("id");

async function loadPoster() {
    try {
        const res = await fetch("/data/posters.json");
        if (!res.ok) throw new Error("Gagal mengambil posters.json");
        const posters = await res.json();
        if (!id) {
            location.href = "/index.html";
            return;
        }
        const poster = posters.find(item => item.id === id);
        if (!poster) {
            document.body.innerHTML = `<div style="color:white;text-align:center;padding:80px 20px;font-family:Arial;"><h1>❌ Poster tidak ditemukan</h1><p>ID Poster : ${id}</p><br><a href="/index.html" style="color:#FFD700;font-size:20px;text-decoration:none;">⬅ Kembali ke Beranda</a></div>`;
            return;
        }
        document.title = poster.title + " | Arsip Dakwah";
        document.getElementById("judul").textContent = poster.title;
        document.getElementById("judul2").textContent = poster.title;
        document.getElementById("kategori").textContent = "📂 " + poster.category;
        document.getElementById("gambar").src = poster.image;
        document.getElementById("gambar").alt = poster.title;
        document.getElementById("caption").textContent = poster.caption;
        document.getElementById("isi").textContent = poster.content;

        document.getElementById("copy").onclick = function() {
            navigator.clipboard.writeText(poster.content);
            alert("✅ Caption berhasil disalin");
        };

        const shareBtn = document.getElementById("share");
        if (shareBtn) {
            shareBtn.onclick = async function() {
                if (navigator.share) {
                    try {
                        await navigator.share({ title: poster.title, text: poster.caption, url: window.location.href });
                    } catch (e) {}
                } else {
                    navigator.clipboard.writeText(window.location.href);
                    alert("🔗 Link berhasil disalin");
                }
            };
        }

        const downloadBtn = document.getElementById("download");
        if (downloadBtn) {
            downloadBtn.innerHTML = "🖼️ Lihat Poster HD";
            downloadBtn.title = "Buka poster resolusi asli";
            downloadBtn.onclick = function() {
                const win = window.open(poster.image, "_blank");
                if (!win) alert("Browser memblokir tab baru. Izinkan pop-up lalu coba lagi.");
            };
        }
    } catch (err) {
        console.error(err);
        document.body.innerHTML = `<div style="color:white;text-align:center;padding:80px 20px;font-family:Arial;"><h1>❌ Gagal memuat poster</h1><p>Periksa data/posters.json atau koneksi.</p><br><a href="/index.html" style="color:#FFD700;font-size:20px;text-decoration:none;">⬅ Kembali ke Beranda</a></div>`;
    }
}
loadPoster();
