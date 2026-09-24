# ==============================================================================
# SCRIPT OTOMATISASI EKSTRAKSI ZIP & PEMBUAT MANIFEST DAKWAH SUNNAH
# VERSI BERSIH NON-PETIK (BEBAS CACAT HURUF BESAR & AMAN KLIK GULIR)
# ==============================================================================

import os
import re
import json
import zipfile
import shutil
import sys

# Kamus pemetaan bulan Hijriah versi bersih NON-PETIK
HIJRIAH_NORMALIZE_MAP = {
    "muharram": "Muharram (1)",
    "muharram (1)": "Muharram (1)",
    "safar": "Safar (2)",
    "safar (2)": "Safar (2)",
    "rabi'ul awwal": "Rabiul Awwal (3)",
    "rabiul awwal": "Rabiul Awwal (3)",
    "rabi'ul awal": "Rabiul Awwal (3)",
    "rabiul awal": "Rabiul Awwal (3)",
    "rabi'ul awwal (3)": "Rabiul Awwal (3)",
    "rabiul awwal (3)": "Rabiul Awwal (3)",
    "rabi'ul akhir": "Rabiul Akhir (4)",
    "rabiul akhir": "Rabiul Akhir (4)",
    "rabi'ul akhir (4)": "Rabiul Akhir (4)",
    "rabiul akhir (4)": "Rabiul Akhir (4)",
    "jumadil awwal": "Jumadil Awwal (5)",
    "jumadil awal": "Jumadil Awwal (5)",
    "jumadil awwal (5)": "Jumadil Awwal (5)",
    "jumadil awal (5)": "Jumadil Awwal (5)",
    "jumadil akhir": "Jumadil Akhir (6)",
    "jumadil akhir (6)": "Jumadil Akhir (6)",
    "rajab": "Rajab (7)",
    "rajab (7)": "Rajab (7)",
    "sya'ban": "Syaban (8)",
    "syaban": "Syaban (8)",
    "sya'ban (8)": "Syaban (8)",
    "syaban (8)": "Syaban (8)",
    "ramadhan": "Ramadhan (9)",
    "ramadhan (9)": "Ramadhan (9)",
    "syawwal": "Syawwal (10)",
    "syawal": "Syawwal (10)",
    "syawwal (10)": "Syawwal (10)",
    "syawal (10)": "Syawwal (10)",
    "dzulqa'dah": "Dzulqadah (11)",
    "dzulqadah": "Dzulqadah (11)",
    "dzulqa'dah (11)": "Dzulqadah (11)",
    "dzulqadah (11)": "Dzulqadah (11)",
    "dzulhijjah": "Dzulhijjah (12)",
    "dzulhijjah (12)": "Dzulhijjah (12)"
}

# Kamus nama kategori resmi versi NON-PETIK (Doa, Bidah, Dzikir, dll.)
DISPLAY_KATEGORI_MAP = {
    "doa": "Doa",
    "do'a": "Doa",
    "bidah": "Bidah",
    "bid'ah": "Bidah",
    "dzikir": "Dzikir",
    "tauhid": "Tauhid",
    "kitab": "Kitab",
    "sholat": "Sholat",
    "adab": "Adab",
    "akidah": "Akidah",
    "muamalah": "Muamalah",
    "hadits shahih & hasan": "Hadits Shahih & Hasan",
    "hadits dhaif & maudhu": "Hadits Dhaif & Maudhu",
    "sunnah": "Sunnah",
    "tafsir": "Tafsir",
    "syirik": "Syirik",
    "rumah tangga": "Rumah Tangga",
    "reminder": "Reminder",
    "fikih": "Fikih",
    "puasa": "Puasa",
    "manhaj salaf": "Manhaj Salaf",
    "firqah-firqah": "Firqah-Firqah"
}

# Kamus emoji resmi dakwah versi NON-PETIK
KATEGORI_EMOJI_MAP = {
    "doa": "🤲",
    "bidah": "🚫",
    "dzikir": "🙌",
    "tauhid": "☝️",
    "kitab": "📚",
    "sholat": "🕌",
    "adab": "✨",
    "akidah": "🛡️",
    "muamalah": "🤝",
    "hadits shahih & hasan": "✅",
    "sunnah": "👤",
    "tafsir": "📖",
    "syirik": "⚠️",
    "rumah tangga": "🏠",
    "reminder": "📌",
    "hadits dhaif & maudhu": "❌",
    "fikih": "🕋",
    "muharram (1)": "🌙",
    "safar (2)": "🌙",
    "rabiul awwal (3)": "🌙",
    "rabiul akhir (4)": "🌙",
    "jumadil awwal (5)": "🌙",
    "jumadil akhir (6)": "🌙",
    "rajab (7)": "🌙",
    "syaban (8)": "🌙",
    "ramadhan (9)": "🌙",
    "syawwal (10)": "🌙",
    "dzulqadah (11)": "🌙",
    "dzulhijjah (12)": "🌙",
    "puasa": "🍽️",
    "manhaj salaf": "🔥",
    "firqah-firqah": "‼️"
}

def clean_non_petik(text):
    """
    Menghapus semua tanda petik (' atau ’ atau ‘) dari nama kategori
    agar tidak ada lagi bug string HTML onclick.
    """
    if not text:
        return ""
    return text.replace("'", "").replace("’", "").replace("‘", "").strip()

def get_canonical_kategori(kat_str):
    """
    Menghasilkan nama kategori resmi yang 100% NON-PETIK dan rapi.
    Contoh: Do'A -> Doa, Bid'ah -> Bidah, Rabi'ul Akhir (4) -> Rabiul Akhir (4).
    """
    if not kat_str:
        return "Umum"
    
    # 1. Bersihkan string dari petik dan ubah ke huruf kecil untuk pencocokan kamus
    clean_lower = clean_non_petik(kat_str).lower()
    
    # 2. Cek apakah ada di kamus bulan Hijriah
    if clean_lower in HIJRIAH_NORMALIZE_MAP:
        return HIJRIAH_NORMALIZE_MAP[clean_lower]
        
    # 3. Cek apakah ada di kamus kategori utama (Doa, Bidah, dll.)
    if clean_lower in DISPLAY_KATEGORI_MAP:
        return DISPLAY_KATEGORI_MAP[clean_lower]
        
    # 4. Fallback: Huruf awal besar setiap kata tanpa tanda petik
    words = clean_lower.split()
    return " ".join([w.capitalize() for w in words]) if words else "Umum"

def parse_frontmatter(md_content):
    """
    Mengekstrak frontmatter YAML dari berkas poster.md secara akurat.
    """
    meta = {}
    content = md_content
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", md_content, re.DOTALL)
    if match:
        yaml_text = match.group(1)
        content = match.group(2).strip()
        for line in yaml_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip("'").strip('"')
                meta[key] = val
    return meta, content

def update_poster_md_kategori(md_path, kategori_baru):
    """
    MEROMBAK ULANG berkas poster.md di dalam folder poster agar tulisan
    kategori di dalamnya otomatis terupdate menjadi non-petik (misal: kategori: Doa).
    """
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        
        # Ganti baris 'kategori: ...' di dalam frontmatter YAML dengan kategori baru
        new_text = re.sub(
            r"^(kategori\s*:\s*).*$", 
            f"kategori: {kategori_baru}", 
            raw_text, 
            flags=re.MULTILINE
        )
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(new_text)
    except Exception as e:
        print(f"Peringatan: Gagal memperbarui file {md_path}: {e}")

def extract_all_zips():
    """
    Mengekstrak berkas ZIP yang diupload admin dan memindahkannya ke struktur folder posters.
    """
    repo_root = os.getcwd()
    uploads_dir = os.path.join(repo_root, "uploads")
    posters_dir = os.path.join(repo_root, "posters")

    if not os.path.exists(uploads_dir):
        print("Direktori uploads tidak ditemukan, melewati proses ekstraksi ZIP.")
        return

    os.makedirs(posters_dir, exist_ok=True)
    zip_files = [f for f in os.listdir(uploads_dir) if f.lower().endswith(".zip")]

    for zf in zip_files:
        zip_path = os.path.join(uploads_dir, zf)
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(posters_dir)
            print(f"Berhasil mengekstrak: {zf}")
            os.remove(zip_path)
        except Exception as e:
            print(f"Gagal mengekstrak {zf}: {e}")

def build_manifest():
    """
    Memindai folder posters, merombak isi poster.md jadi non-petik,
    dan menyusun ulang manifest.json bersih dari tanda petik.
    """
    repo_root = os.getcwd()
    posters_dir = os.path.join(repo_root, "posters")
    manifest_path = os.path.join(repo_root, "manifest.json")

    if not os.path.exists(posters_dir):
        print("Direktori posters tidak ditemukan.")
        return

    posters_list = []
    kategori_set = set()

    for root, dirs, files in os.walk(posters_dir):
        if "poster.md" in files:
            md_path = os.path.join(root, "poster.md")
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    meta, content = parse_frontmatter(f.read())
            except Exception as e:
                print(f"Gagal membaca {md_path}: {e}")
                continue

            rel_path = os.path.relpath(root, posters_dir).replace("\\", "/")
            raw_kategori = meta.get("kategori", "Umum")
            
            # STANDARISASI KE NON-PETIK (Do'A -> Doa, Bid'ah -> Bidah, dll.)
            kategori_baku = get_canonical_kategori(raw_kategori)
            kategori_set.add(kategori_baku)

            # Perbarui file poster.md fisik agar selamanya bersih dari petik
            if raw_kategori != kategori_baku:
                update_poster_md_kategori(md_path, kategori_baku)

            # Temukan semua gambar slide (1.jpg, 2.jpg, dst.)
            images = [f for f in files if re.match(r"^\d+\.(jpg|jpeg|png|webp)$", f, re.IGNORECASE)]
            images.sort(key=lambda x: int(re.match(r"^(\d+)", x).group(1)))

            # Cek berkas PDF brosur jika ada
            has_pdf = "brosur.pdf" if "brosur.pdf" in files else None

            # Ambil emoji resmi
            emoji_key = kategori_baku.lower().strip()
            emoji = KATEGORI_EMOJI_MAP.get(emoji_key, "📂")

            poster_item = {
                "judul": meta.get("judul", "Poster Dakwah"),
                "sub_judul": meta.get("sub_judul", ""),
                "kategori": kategori_baku,
                "kategori_emoji": emoji,
                "tags": clean_non_petik(meta.get("tags", "")),
                "images": ", ".join(images) if images else "1.jpg",
                "tidakpakepdf": "brosur.pdf",
                "pdf": has_pdf,
                "path": rel_path,
                "content": content
            }
            posters_list.append(poster_item)

    # Urutkan kategori agar bulan Hijriah di urutan awal, lalu kategori lainnya secara alfabetis
    def sort_key_kategori(k):
        match = re.search(r"\((\d+)\)", k)
        if match:
            return (0, int(match.group(1)), k)
        return (1, 0, k)

    sorted_kategori = sorted(list(kategori_set), key=sort_key_kategori)

    manifest_data = {
        "kategori_list": sorted_kategori,
        "kategori_emoji": KATEGORI_EMOJI_MAP,
        "total_poster": len(posters_list),
        "posters": posters_list
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Sukses merombak poster.md & membuat manifest.json!")
    print(f"Total: {len(posters_list)} poster, {len(sorted_kategori)} kategori bersih tanpa tanda petik.")

if __name__ == "__main__":
    extract_all_zips()
    build_manifest()
