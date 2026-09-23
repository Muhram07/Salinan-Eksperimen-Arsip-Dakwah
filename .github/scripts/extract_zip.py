import os
import shutil
import zipfile
import yaml
import re
import sys
import json

# === DAFTAR URUTAN RESMI 12 BULAN HIJRIAH ===
HIJRIAH_ORDER = [
    "Muharram (1)",
    "Safar (2)",
    "Rabi'ul Awwal (3)",
    "Rabi'ul Akhir (4)",
    "Jumadil Awwal (5)",
    "Jumadil Akhir (6)",
    "Rajab (7)",
    "Sya'ban (8)",
    "Ramadhan (9)",
    "Syawwal (10)",
    "Dzulqa'dah (11)",
    "Dzulhijjah (12)"
]

HIJRIAH_NORMALIZE_MAP = {}
for m in HIJRIAH_ORDER:
    num_match = re.search(r'\((\d+)\)', m)
    num = num_match.group(1) if num_match else ""
    base_name = re.sub(r'\s*\(\d+\)', '', m).strip().lower()
    
    HIJRIAH_NORMALIZE_MAP[m.lower()] = m
    HIJRIAH_NORMALIZE_MAP[base_name] = m
    HIJRIAH_NORMALIZE_MAP[f"{base_name}-{num}"] = m
    HIJRIAH_NORMALIZE_MAP[f"{base_name} {num}"] = m
    
    base_single_w = base_name.replace('awwal', 'awal').replace('syawwal', 'syawal')
    HIJRIAH_NORMALIZE_MAP[base_single_w] = m
    HIJRIAH_NORMALIZE_MAP[f"{base_single_w}-{num}"] = m
    HIJRIAH_NORMALIZE_MAP[f"{base_single_w} {num}"] = m

KATEGORI_REPLACE_MAP = {
    "aqidah": "Akidah",
    "akidah": "Akidah",
    "bidah": "Bid'ah",
    "bid'ah": "Bid'ah",
    "bid’ah": "Bid'ah",
    "fiqih": "Fikih",
    "fikih": "Fikih",
    "shalat": "Sholat",
    "sholat": "Sholat",
    "hadits": "Hadits",
    "dzikir": "Dzikir",
    "zikir": "Dzikir",
}

def get_canonical_kategori(kat_str):
    if not kat_str:
        return "Umum"
    clean_str = kat_str.strip().lower().replace("’", "'").replace("‘", "'")
    if clean_str in HIJRIAH_NORMALIZE_MAP:
        return HIJRIAH_NORMALIZE_MAP[clean_str]
    if clean_str in KATEGORI_REPLACE_MAP:
        return KATEGORI_REPLACE_MAP[clean_str]
    return kat_str.strip().title()

def get_folder_slug(kat_str):
    canonical = get_canonical_kategori(kat_str)
    slug = canonical.lower().replace("’", "").replace("'", "")
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'[^a-z0-9\-\(\)]+', '', slug)
    return slug

def get_padded_number(num):
    return f"{num:0{max(3, len(str(num)))}d}"

def get_next_sequence(kategori_path):
    if not os.path.exists(kategori_path):
        return 1
    max_num = 0
    for folder in os.listdir(kategori_path):
        if os.path.isdir(os.path.join(kategori_path, folder)):
            parts = folder.split('-')
            if len(parts) > 1 and parts[-1].isdigit():
                try:
                    num = int(parts[-1])
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass
    return max_num + 1

def main():
    zip_dir = '_uploads'
    temp_dir = '_temp_extract'

    if not os.path.exists(zip_dir):
        print("ERROR: Folder '_uploads' tidak ditemukan.")
        sys.exit(1)

    zip_files = [f for f in os.listdir(zip_dir) if f.endswith('.zip')]
    if not zip_files:
        print("Tidak ada file ZIP ditemukan di _uploads. Melanjutkan ke pemindaian & perbaikan folder...")
        scan_and_repair()
        return

    for zip_filename in zip_files:
        zip_file_path = os.path.join(zip_dir, zip_filename)
        print(f"Memproses ZIP: {zip_file_path}")

        os.makedirs(temp_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        except Exception as e:
            print(f"Gagal mengekstrak {zip_filename}: {e}")
            continue

        target_folder = None
        md_path = os.path.join(temp_dir, 'poster.md')
        if os.path.exists(md_path):
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                yaml_match = re.search(r'---(.*?)---', content, re.DOTALL)
                if yaml_match:
                    try:
                        data = yaml.safe_load(yaml_match.group(1))
                        raw_kategori = data.get('kategori', 'Unknown')
                        judul = data.get('judul', 'Unknown')

                        canonical_kategori = get_canonical_kategori(raw_kategori)
                        kat_folder_slug = get_folder_slug(canonical_kategori)

                        slug_base = re.sub(r'[^a-z0-9]+', '-', judul.lower()).strip('-')
                        if not slug_base: 
                            slug_base = 'poster'

                        kategori_path = os.path.join('posters', kat_folder_slug)
                        next_num = get_next_sequence(kategori_path)
                        num_str = get_padded_number(next_num)
                        final_slug = f"{slug_base}-{num_str}"
                        
                        target_folder = os.path.join('posters', kat_folder_slug, final_slug)
                    except Exception as e:
                        print(f"Gagal parsing YAML di poster.md: {e}")
                
        if not target_folder:
            fallback_name = os.path.splitext(zip_filename)[0]
            target_folder = os.path.join('posters', 'unknown', fallback_name)

        os.makedirs(target_folder, exist_ok=True)
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                src_path = os.path.join(root, file)
                dst_path = os.path.join(target_folder, file)
                shutil.move(src_path, dst_path)

        shutil.rmtree(temp_dir)
        os.remove(zip_file_path)
        print("ZIP berhasil diekstrak dan dipindahkan.")

    scan_and_repair()

def scan_and_repair():
    print("Memindai & memperbaiki struktur folder posters...")
    manifest_path = "manifest.json"
    existing_emoji_map = {}

    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                old_manifest = json.load(f)
                existing_emoji_map = old_manifest.get('kategori_emoji', {})
        except Exception as e:
            print(f"Gagal membaca manifest.json lama: {e}")

    for month in HIJRIAH_ORDER:
        if month not in existing_emoji_map:
            existing_emoji_map[month] = "🌙"

    manifest_data = {
        "kategori_list": [],
        "kategori_emoji": existing_emoji_map,
        "total_poster": 0,
        "posters": []
    }
    
    kategori_terpakai_set = set()
    base_poster_path = "posters"
    
    if not os.path.exists(base_poster_path):
        print("Folder posters belum ada.")
        return

    for kat_folder in os.listdir(base_poster_path):
        kat_folder_path = os.path.join(base_poster_path, kat_folder)
        if os.path.isdir(kat_folder_path):
            canonical_kat = get_canonical_kategori(kat_folder)
            target_kat_folder = get_folder_slug(canonical_kat)
            target_kat_path = os.path.join(base_poster_path, target_kat_folder)

            if kat_folder != target_kat_folder:
                os.makedirs(target_kat_path, exist_ok=True)
                for sub_item in os.listdir(kat_folder_path):
                    src_sub = os.path.join(kat_folder_path, sub_item)
                    dst_sub = os.path.join(target_kat_path, sub_item)
                    if not os.path.exists(dst_sub):
                        shutil.move(src_sub, dst_sub)
                    else:
                        if os.path.isdir(src_sub):
                            for f_in in os.listdir(src_sub):
                                shutil.move(os.path.join(src_sub, f_in), os.path.join(dst_sub, f_in))
                            shutil.rmtree(src_sub)
                shutil.rmtree(kat_folder_path)

    for kat_folder in os.listdir(base_poster_path):
        kat_folder_path = os.path.join(base_poster_path, kat_folder)
        if os.path.isdir(kat_folder_path):
            for poster_folder in os.listdir(kat_folder_path):
                poster_path = os.path.join(kat_folder_path, poster_folder)
                if os.path.isdir(poster_path):
                    md_file_path = os.path.join(poster_path, 'poster.md')
                    if os.path.exists(md_file_path):
                        try:
                            with open(md_file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                yaml_match = re.search(r'---(.*?)---', content, re.DOTALL)
                                if yaml_match:
                                    data = yaml.safe_load(yaml_match.group(1))
                                    raw_kategori = data.get('kategori', kat_folder)
                                    display_kat = get_canonical_kategori(raw_kategori)
                                    
                                    data['kategori'] = display_kat
                                    kategori_terpakai_set.add(display_kat)

                                    real_folder_name = os.path.basename(poster_path)
                                    real_kategori_folder = os.path.basename(os.path.dirname(poster_path))
                                    data['path'] = f"{real_kategori_folder}/{real_folder_name}"
                                    
                                    new_emoji = data.get('kategori_emoji')
                                    if new_emoji and new_emoji != '📂':
                                        manifest_data['kategori_emoji'][display_kat] = new_emoji
                                    
                                    manifest_data['posters'].append(data)
                                    manifest_data['total_poster'] += 1
                        except Exception as e:
                            print(f"Gagal membaca {md_file_path}: {e}")

    hijriah_terpakai = [m for m in HIJRIAH_ORDER if m in kategori_terpakai_set]
    non_hijriah = sorted(list(kategori_terpakai_set - set(HIJRIAH_ORDER)))

    manifest_data['kategori_list'] = hijriah_terpakai + non_hijriah

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Selesai! Total Poster Aktif: {manifest_data['total_poster']}")

if __name__ == "__main__":
    main()
