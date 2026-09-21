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
    "Rabi'ul Awal (3)",
    "Rabi'ul Akhir (4)",
    "Jumadil Awal (5)",
    "Jumadil Akhir (6)",
    "Rajab (7)",
    "Sya'ban (8)",
    "Ramadhan (9)",
    "Syawwal (10)",
    "Dzulqa'dah (11)",
    "Dzulhijjah (12)"
]

# Mapping untuk normalisasi key bulan Hijriah agar tidak terduplikasi
HIJRIAH_MAP = {m.lower(): m for m in HIJRIAH_ORDER}

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
        print("Tidak ada file ZIP ditemukan di _uploads. Selesai.")
        scan_and_repair()
        return

    for zip_filename in zip_files:
        zip_file_path = os.path.join(zip_dir, zip_filename)
        print(f"Memproses ZIP: {zip_file_path}")

        os.makedirs(temp_dir, exist_ok=True)
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        target_folder = None

        md_path = os.path.join(temp_dir, 'poster.md')
        if os.path.exists(md_path):
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                yaml_match = re.search(r'---(.*?)---', content, re.DOTALL)
                if yaml_match:
                    try:
                        data = yaml.safe_load(yaml_match.group(1))
                        kategori = data.get('kategori', 'Unknown')
                        judul = data.get('judul', 'Unknown')

                        slug_base = re.sub(r'[^a-z0-9]+', '-', judul.lower()).strip('-')
                        if not slug_base: 
                            slug_base = 'poster'

                        kategori_path = os.path.join('posters', kategori.lower())
                        next_num = get_next_sequence(kategori_path)
                        num_str = get_padded_number(next_num)
                        final_slug = f"{slug_base}-{num_str}"
                        
                        target_folder = os.path.join('posters', kategori.lower(), final_slug)
                        print(f"Target folder ditemukan: {target_folder}")

                    except Exception as e:
                        print(f"Gagal parsing YAML di poster.md: {e}")
                
        if not target_folder:
            fallback_name = os.path.splitext(zip_filename)[0]
            target_folder = os.path.join('posters', 'unknown', fallback_name)
            print(f"Menggunakan fallback folder: {target_folder}")

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

    # Set default emoji 🌙 untuk bulan Hijriah
    for month in HIJRIAH_ORDER:
        if month not in existing_emoji_map:
            existing_emoji_map[month] = "🌙"

    manifest_data = {
        "kategori_list": [],
        "kategori_emoji": existing_emoji_map,
        "total_poster": 0,
        "posters": []
    }
    
    # Map untuk menyimpan nama tampilan kategori unik
    kategori_map = {}

    base_poster_path = "posters"
    if not os.path.exists(base_poster_path):
        print("Folder posters belum ada.")
        return

    for kategori in os.listdir(base_poster_path):
        kategori_path = os.path.join(base_poster_path, kategori)
        if os.path.isdir(kategori_path):

            for poster_folder in os.listdir(kategori_path):
                poster_path = os.path.join(kategori_path, poster_folder)
                if os.path.isdir(poster_path):
                    md_file_path = os.path.join(poster_path, 'poster.md')
                    if os.path.exists(md_file_path):
                        try:
                            with open(md_file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                yaml_match = re.search(r'---(.*?)---', content, re.DOTALL)
                                if yaml_match:
                                    data = yaml.safe_load(yaml_match.group(1))
                                    yaml_kategori = data.get('kategori', kategori)
                                    yaml_slug = data.get('judul', poster_folder)
                                    slug = re.sub(r'[^a-z0-9]+', '-', yaml_slug.lower()).strip('-')
                                    
                                    # Self-Healing untuk folder unknown
                                    if kategori.lower() == 'unknown' and yaml_kategori.lower() != 'unknown':
                                        kategori_baru_path = os.path.join('posters', yaml_kategori.lower())
                                        next_num = get_next_sequence(kategori_baru_path) 
                                        num_str = get_padded_number(next_num)
                                        final_slug = f"{slug}-{num_str}"
                                        
                                        target_folder = os.path.join('posters', yaml_kategori.lower(), final_slug)
                                        print(f"🛠️ Self-Healing: Memindahkan {poster_path} -> {target_folder}")
                                        
                                        if os.path.exists(target_folder):
                                            shutil.rmtree(target_folder)
                                            
                                        shutil.move(poster_path, target_folder)
                                        if not os.listdir(kategori_path):
                                            os.rmdir(kategori_path)
                                            
                                        poster_path = target_folder

                                    # Masukkan data kategori ke kategori_map dengan proteksi duplikasi
                                    kat_lower = yaml_kategori.lower()
                                    if kat_lower in HIJRIAH_MAP:
                                        display_kat = HIJRIAH_MAP[kat_lower]
                                    else:
                                        display_kat = yaml_kategori.title()
                                    
                                    # Normalisasi isi kategori di data agar konsisten
                                    data['kategori'] = display_kat
                                    kategori_map[kat_lower] = display_kat

                                    real_folder_name = os.path.basename(poster_path)
                                    real_kategori = os.path.basename(os.path.dirname(poster_path))
                                    data['path'] = f"{real_kategori.lower()}/{real_folder_name}"
                                    
                                    new_emoji = data.get('kategori_emoji')
                                    if new_emoji and new_emoji != '📂':
                                        manifest_data['kategori_emoji'][display_kat] = new_emoji
                                    
                                    manifest_data['posters'].append(data)
                                    manifest_data['total_poster'] += 1

                        except Exception as e:
                            print(f"Gagal membaca {md_file_path}: {e}")

    # === LOGIKA DEDUPLIKASI DAN PENGURUTAN KATEGORI ===
    # 1. Ambil Kategori Bulan Hijriah yang memang ada di postingan
    hijriah_terpakai = [m for m in HIJRIAH_ORDER if m.lower() in kategori_map]
    
    # 2. Ambil Kategori Non-Hijriah (Unik) dan Urutkan secara alfabetis
    non_hijriah = sorted(list(set(
        v for k, v in kategori_map.items() if k not in HIJRIAH_MAP
    )))

    # Gabungkan tanpa ada elemen ganda
    manifest_data['kategori_list'] = hijriah_terpakai + non_hijriah

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    
    print("Selesai! Manifest diperbarui tanpa duplikasi kategori.")
    print(f"Total Poster: {manifest_data['total_poster']}")

if __name__ == "__main__":
    main()
