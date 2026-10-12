# ==============================================================================
# SCRIPT OTOMATISASI EKSTRAKSI ZIP & PEMBUAT MANIFEST DAKWAH SUNNAH
# SINKRONISASI FOLDER _uploads, AUTO-SEQUENCING NOMOR URUT FOLDER, & FIX MULTILINE
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
    "doa": "🤲", "bidah": "🚫", "dzikir": "🙌", "tauhid": "☝️",
    "kitab": "📚", "sholat": "🕌", "adab": "✨", "akidah": "🛡️",
    "muamalah": "🤝", "hadits shahih & hasan": "✅", "sunnah": "👤",
    "tafsir": "📖", "syirik": "⚠️", "rumah tangga": "🏠",
    "reminder": "📌", "hadits dhaif & maudhu": "❌", "fikih": "🕋",
    "muharram (1)": "🌙", "safar (2)": "🌙", "rabiul awwal (3)": "🌙",
    "rabiul akhir (4)": "🌙", "jumadil awwal (5)": "🌙", "jumadil akhir (6)": "🌙",
    "rajab (7)": "🌙", "syaban (8)": "🌙", "ramadhan (9)": "🌙",
    "syawwal (10)": "🌙", "dzulqadah (11)": "🌙", "dzulhijjah (12)": "🌙",
    "puasa": "🍽️", "manhaj salaf": "🔥", "firqah-firqah": "‼️"
}

def clean_non_petik(text):
    if not text: return ""
    return text.replace("'", "").replace("’", "").replace("‘", "").strip()

def get_canonical_kategori(kat_str):
    if not kat_str: return "Umum"
    clean_lower = clean_non_petik(kat_str).lower()
    if clean_lower in HIJRIAH_NORMALIZE_MAP: return HIJRIAH_NORMALIZE_MAP[clean_lower]
    if clean_lower in DISPLAY_KATEGORI_MAP: return DISPLAY_KATEGORI_MAP[clean_lower]
    words = clean_lower.split()
    return " ".join([w.capitalize() for w in words]) if words else "Umum"

def parse_frontmatter(md_content):
    meta = {}
    content = md_content
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", md_content, re.DOTALL)
    if match:
        yaml_text = match.group(1)
        content = match.group(2).strip()
        current_key = None
        
        # Smart Multiline Parser (Solusi pelengkap untuk YAML)
        for line in yaml_text.splitlines():
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#"): continue
            
            if ":" in line and not stripped_line.startswith("*") and not stripped_line.startswith("@"):
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip("'").strip('"')
                meta[key] = val
                current_key = key
            else:
                if current_key:
                    add_val = stripped_line.strip("'").strip('"')
                    meta[current_key] += " " + add_val
    return meta, content

def extract_all_zips():
    repo_root = os.getcwd()
    posters_root = os.path.join(repo_root, "posters")
    os.makedirs(posters_root, exist_ok=True)

    possible_upload_dirs = [
        os.path.join(repo_root, "_uploads"),
        os.path.join(repo_root, "uploads")
    ]

    for uploads_dir in possible_upload_dirs:
        if not os.path.exists(uploads_dir): continue

        zip_files = [f for f in os.listdir(uploads_dir) if f.lower().endswith(".zip")]
        for zf in zip_files:
            zip_path = os.path.join(uploads_dir, zf)
            slug_name = os.path.splitext(zf)[0]
            # Hapus akhiran -001 bawaan dari Admin
            base_slug = re.sub(r'-\d{3}$', '', slug_name)
            temp_extract = os.path.join(repo_root, "_temp_extract")

            try:
                if os.path.exists(temp_extract): shutil.rmtree(temp_extract)
                os.makedirs(temp_extract, exist_ok=True)

                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(temp_extract)

                kat_folder = "umum"
                for r, d, f in os.walk(temp_extract):
                    if "poster.md" in f:
                        with open(os.path.join(r, "poster.md"), "r", encoding="utf-8") as md_f:
                            m, _ = parse_frontmatter(md_f.read())
                            kat_raw = m.get("kategori", "Umum")
                            kat_baku = get_canonical_kategori(kat_raw)
                            kat_folder = clean_non_petik(kat_baku).lower().replace(" ", "-")
                        break

                # Agar tidak terjadi timpa file saat ekstrak, kita simpan sbg folder temporary
                target_dir = os.path.join(posters_root, kat_folder, base_slug)
                counter = 1
                while os.path.exists(target_dir):
                    target_dir = os.path.join(posters_root, kat_folder, f"{base_slug}-temp{counter}")
                    counter += 1

                os.makedirs(target_dir, exist_ok=True)

                for r, d, f in os.walk(temp_extract):
                    for file_name in f:
                        src_file = os.path.join(r, file_name)
                        dst_file = os.path.join(target_dir, file_name)
                        shutil.copy2(src_file, dst_file)

                shutil.rmtree(temp_extract)
                os.remove(zip_path)
                print(f"✅ Sukses Ekstrak ZIP -> {target_dir}")

            except Exception as e:
                print(f"❌ Gagal memproses {zf}: {e}")
                if os.path.exists(temp_extract): shutil.rmtree(temp_extract)

def fix_folder_sequences(posters_root):
    """
    Fungsi cerdas untuk merapikan nomor urut folder (001, 002, 003).
    Mendeteksi folder ganda/berantakan & memberinya nomor baru yg benar.
    Yg sudah benar dibiarkan.
    """
    if not os.path.exists(posters_root): return

    for kat_folder in os.listdir(posters_root):
        kat_path = os.path.join(posters_root, kat_folder)
        if not os.path.isdir(kat_path): continue

        subfolders = [f for f in os.listdir(kat_path) if os.path.isdir(os.path.join(kat_path, f))]

        seen_seqs = set()
        duplicates_or_invalid = []

        # Tahap 1: Cek folder mana yang nomor urutnya valid & tidak duplikat
        for folder in subfolders:
            match = re.search(r'-(\d{3})$', folder)
            if match:
                seq = int(match.group(1))
                if seq in seen_seqs:
                    duplicates_or_invalid.append(folder)
                else:
                    seen_seqs.add(seq)
            else:
                # Folder tidak ada nomor urut (contoh bawaan temp saat ekstrak)
                duplicates_or_invalid.append(folder)

        if not duplicates_or_invalid:
            continue

        # Tahap 2: Ganti nama (Rename) yg berantakan dengan urutan selanjutnya
        current_max = max(seen_seqs) if seen_seqs else 0

        for folder in duplicates_or_invalid:
            current_max += 1
            new_seq_str = f"{current_max:03d}"
            
            # Buang nomor usang atau akhiran "-temp" 
            base_name = re.sub(r'-\d{3}$', '', folder)
            base_name = re.sub(r'-temp\d+$', '', base_name)
            
            new_folder_name = f"{base_name}-{new_seq_str}"
            old_path = os.path.join(kat_path, folder)
            new_path = os.path.join(kat_path, new_folder_name)
            
            # Cek jika entah kenapa nama path sudah ada, maka loncat 1 angka lagi
            while os.path.exists(new_path):
                current_max += 1
                new_seq_str = f"{current_max:03d}"
                new_folder_name = f"{base_name}-{new_seq_str}"
                new_path = os.path.join(kat_path, new_folder_name)

            os.rename(old_path, new_path)
            print(f"🔄 Auto-Urutkan: {kat_folder}/{folder} -> {new_folder_name}")

def build_manifest():
    repo_root = os.getcwd()
    posters_dir = os.path.join(repo_root, "posters")
    manifest_path = os.path.join(repo_root, "manifest.json")

    if not os.path.exists(posters_dir): return

    posters_list = []
    kategori_set = set()

    for root, dirs, files in os.walk(posters_dir):
        if "poster.md" in files:
            md_path = os.path.join(root, "poster.md")
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    meta, content = parse_frontmatter(f.read())
            except Exception:
                continue

            rel_path = os.path.relpath(root, posters_dir).replace("\\", "/")
            raw_kategori = meta.get("kategori", "Umum")
            kategori_baku = get_canonical_kategori(raw_kategori)
            kategori_set.add(kategori_baku)

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
        if match: return (0, int(match.group(1)), k)
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

    print(f"✅ Manifest dibuat! Total: {len(posters_list)} poster.")

if __name__ == "__main__":
    extract_all_zips()
    # Fitur Cerdas: Urutkan folder-folder lama/baru yg acak-acakan sebelum dibuat manifest
    repo_path = os.getcwd()
    fix_folder_sequences(os.path.join(repo_path, "posters"))
    build_manifest()
