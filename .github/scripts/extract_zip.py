# ==============================================================================
# SCRIPT OTOMATISASI EKSTRAKSI ZIP & PEMBUAT MANIFEST DAKWAH SUNNAH
# ==============================================================================

import os
import re
import json
import zipfile
import shutil
import sys

# Kamus pemetaan bulan Hijriah agar format penulisan seragam dan baku
HIJRIAH_NORMALIZE_MAP = {
    "muharram": "Muharram (1)",
    "muharram (1)": "Muharram (1)",
    "safar": "Safar (2)",
    "safar (2)": "Safar (2)",
    "rabi'ul awwal": "Rabi'ul Awwal (3)",
    "rabiul awwal": "Rabi'ul Awwal (3)",
    "rabi'ul awal": "Rabi'ul Awwal (3)",
    "rabiul awal": "Rabi'ul Awwal (3)",
    "rabi'ul awwal (3)": "Rabi'ul Awwal (3)",
    "rabi'ul akhir": "Rabi'ul Akhir (4)",
    "rabiul akhir": "Rabi'ul Akhir (4)",
    "rabi'ul akhir (4)": "Rabi'ul Akhir (4)",
    "jumadil awwal": "Jumadil Awwal (5)",
    "jumadil awal": "Jumadil Awwal (5)",
    "jumadil awwal (5)": "Jumadil Awwal (5)",
    "jumadil akhir": "Jumadil Akhir (6)",
    "jumadil akhir (6)": "Jumadil Akhir (6)",
    "rajab": "Rajab (7)",
    "rajab (7)": "Rajab (7)",
    "sya'ban": "Sya'ban (8)",
    "syaban": "Sya'ban (8)",
    "sya'ban (8)": "Sya'ban (8)",
    "ramadhan": "Ramadhan (9)",
    "ramadhan (9)": "Ramadhan (9)",
    "syawwal": "Syawwal (10)",
    "syawal": "Syawwal (10)",
    "syawwal (10)": "Syawwal (10)",
    "dzulqa'dah": "Dzulqa'dah (11)",
    "dzulqadah": "Dzulqa'dah (11)",
    "dzulqa'dah (11)": "Dzulqa'dah (11)",
    "dzulhijjah": "Dzulhijjah (12)",
    "dzulhijjah (12)": "Dzulhijjah (12)"
}

# Kamus nama kategori resmi untuk mencegah Do'A atau Bid'Ah menjadi cacat
DISPLAY_KATEGORI_MAP = {
    "doa": "Do'a",
    "do'a": "Do'a",
    "bidah": "Bid'ah",
    "bid'ah": "Bid'ah",
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

# Kamus emoji resmi dakwah
KATEGORI_EMOJI_MAP = {
    "dzikir": "🙌",
    "tauhid": "☝️",
    "kitab": "📚",
    "doa": "🤲",
    "do'a": "🤲",
    "sholat": "🕌",
    "bidah": "🚫",
    "bid'ah": "🚫",
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
    "ramadhan": "🌙",
    "puasa": "🍽️",
    "manhaj salaf": "🔥",
    "firqah-firqah": "‼️"
}

def smart_capitalize(text):
    """
    Kapitalisasi kata yang cerdas:
    Hanya huruf pertama yang dikapitalisasi, huruf setelah petik tetap kecil (Do'a, bukan Do'A).
    """
    if not text:
        return ""
    words = text.strip().split()
    result = []
    for w in words:
        if len(w) > 0:
            result.append(w[0].upper() + w[1:].lower())
    return " ".join(result)

def get_canonical_kategori(kat_str):
    """
    Menghasilkan nama kategori resmi yang konsisten, bersih, dan bebas cacat huruf besar setelah petik.
    """
    if not kat_str:
        return "Umum"
    clean_str = kat_str.strip().lower().replace("’", "'").replace("‘", "'")
    if clean_str in HIJRIAH_NORMALIZE_MAP:
        return HIJRIAH_NORMALIZE_MAP[clean_str]
    if clean_str in DISPLAY_KATEGORI_MAP:
        return DISPLAY_KATEGORI_MAP[clean_str]
    return smart_capitalize(kat_str)

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
    Memindai folder posters dan menyusun ulang manifest.json dengan data kategori yang rapi.
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
            kategori_baku = get_canonical_kategori(raw_kategori)
            kategori_set.add(kategori_baku)

            # Temukan semua gambar slide (1.jpg, 2.jpg, dst.)
            images = [f for f in files if re.match(r"^\d+\.(jpg|jpeg|png|webp)$", f, re.IGNORECASE)]
            images.sort(key=lambda x: int(re.match(r"^(\d+)", x).group(1)))

            # Cek berkas PDF brosur jika ada
            has_pdf = "brosur.pdf" if "brosur.pdf" in files else None

            # Normalisasi emoji kategori
            kategori_clean_key = kategori_baku.strip().lower().replace("’", "'").replace("‘", "'")
            emoji = KATEGORI_EMOJI_MAP.get(kategori_clean_key, "📂")

            poster_item = {
                "judul": meta.get("judul", "Poster Dakwah"),
                "sub_judul": meta.get("sub_judul", ""),
                "kategori": kategori_baku,
                "kategori_emoji": emoji,
                "tags": meta.get("tags", ""),
                "images": ", ".join(images) if images else "1.jpg",
                "tidakpakepdf": "brosur.pdf",
                "pdf": has_pdf,
                "path": rel_path,
                "content": content
            }
            posters_list.append(poster_item)

    # Urutkan kategori agar bulan Hijriah di urutan awal, lalu alfabetis
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

    print(f"✅ Sukses membuat manifest.json dengan {len(posters_list)} poster dan {len(sorted_kategori)} kategori!")

if __name__ == "__main__":
    extract_all_zips()
    build_manifest()
