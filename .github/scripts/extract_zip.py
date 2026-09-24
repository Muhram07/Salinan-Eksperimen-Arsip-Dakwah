# ==============================================================================
# SCRIPT OTOMATISASI EKSTRAKSI ZIP & PEMBUAT MANIFEST DAKWAH SUNNAH
# SINKRONISASI FOLDER _uploads & SUBFOLDER KATEGORI (DZIKIR, DOA, DLL.)
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

# Kamus nama kategori resmi versi NON-PETIK
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
    if not text:
        return ""
    return text.replace("'", "").replace("’", "").replace("‘", "").strip()

def get_canonical_kategori(kat_str):
    if not kat_str:
        return "Umum"
    clean_lower = clean_non_petik(kat_str).lower()
    if clean_lower in HIJRIAH_NORMALIZE_MAP:
        return HIJRIAH_NORMALIZE_MAP[clean_lower]
    if clean_lower in DISPLAY_KATEGORI_MAP:
        return DISPLAY_KATEGORI_MAP[clean_lower]
    words = clean_lower.split()
    return " ".join([w.capitalize() for w in words]) if words else "Umum"

def parse_frontmatter(md_content):
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
    Mengekstrak file ZIP dari folder '_uploads' atau 'uploads'.
    Membaca poster.md di dalam ZIP untuk mengetahui kategorinya,
    lalu memindahkannya ke subfolder yang benar: posters/<kategori>/<slug>/
    """
    repo_root = os.getcwd()
    posters_root = os.path.join(repo_root, "posters")
    os.makedirs(posters_root, exist_ok=True)

    # Deteksi folder upload (baik _uploads maupun uploads)
    possible_upload_dirs = [
        os.path.join(repo_root, "_uploads"),
        os.path.join(repo_root, "uploads")
    ]

    for uploads_dir in possible_upload_dirs:
        if not os.path.exists(uploads_dir):
            continue

        zip_files = [f for f in os.listdir(uploads_dir) if f.lower().endswith(".zip")]
        for zf in zip_files:
            zip_path = os.path.join(uploads_dir, zf)
            slug_name = os.path.splitext(zf)[0]
            temp_extract = os.path.join(repo_root, "_temp_extract")

            try:
                # 1. Ekstrak sementara ke folder temp
                if os.path.exists(temp_extract):
                    shutil.rmtree(temp_extract)
                os.makedirs(temp_extract, exist_ok=True)

                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(temp_extract)

                # 2. Cari file poster.md di dalam hasil ekstrak
                kat_folder = "umum"
                for r, d, f in os.walk(temp_extract):
                    if "poster.md" in f:
                        with open(os.path.join(r, "poster.md"), "r", encoding="utf-8") as md_f:
                            m, _ = parse_frontmatter(md_f.read())
                            kat_raw = m.get("kategori", "Umum")
                            kat_baku = get_canonical_kategori(kat_raw)
                            # Buat slug folder kategori (misal: "dzikir", "doa", dll.)
                            kat_folder = clean_non_petik(kat_baku).lower().replace(" ", "-")
                        break

                # 3. Pindahkan ke tujuan akhir: posters/<kategori>/<slug>/
                target_dir = os.path.join(posters_root, kat_folder, slug_name)
                os.makedirs(target_dir, exist_ok=True)

                # Salin semua isi file dari temp ke folder target
                for r, d, f in os.walk(temp_extract):
                    for file_name in f:
                        src_file = os.path.join(r, file_name)
                        dst_file = os.path.join(target_dir, file_name)
                        shutil.copy2(src_file, dst_file)

                # Bersihkan temp dan file zip yang sudah selesai
                shutil.rmtree(temp_extract)
                os.remove(zip_path)
                print(f"✅ Sukses memindahkan {zf} ke: posters/{kat_folder}/{slug_name}/")

            except Exception as e:
                print(f"❌ Gagal memproses {zf}: {e}")
                if os.path.exists(temp_extract):
                    shutil.rmtree(temp_extract)

def build_manifest():
    """
    Memindai seluruh folder posters secara mendalam,
    mengupdate poster.md jadi non-petik baku, dan menerbitkan manifest.json
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
            
            # Normalisasi kategori ke non-petik baku (Doa, Bidah, Dzikir, dll.)
            kategori_baku = get_canonical_kategori(raw_kategori)
            kategori_set.add(kategori_baku)

            # Temukan semua gambar slide (1.jpg, 2.jpg, dst.)
            images = [f for f in files if re.match(r"^\d+\.(jpg|jpeg|png|webp)$", f, re.IGNORECASE)]
            images.sort(key=lambda x: int(re.match(r"^(\d+)", x).group(1)))

            has_pdf = "brosur.pdf" if "brosur.pdf" in files else None

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

    print(f"✅ Sukses membuat manifest.json!")
    print(f"Total: {len(posters_list)} poster, {len(sorted_kategori)} kategori bersih.")

if __name__ == "__main__":
    extract_all_zips()
    build_manifest()
