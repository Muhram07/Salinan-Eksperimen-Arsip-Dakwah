import os
import shutil
import zipfile
import yaml
import re
import sys
import json

def main():
    zip_dir = '_uploads'
    temp_dir = '_temp_extract'

    # Validasi folder _uploads
    if not os.path.exists(zip_dir):
        print("ERROR: Folder '_uploads' tidak ditemukan.")
        sys.exit(1)

    zip_files = [f for f in os.listdir(zip_dir) if f.endswith('.zip')]
    
    if not zip_files:
        print("Tidak ada file ZIP ditemukan di _uploads. Selesai.")
        # Tetap lanjut ke scanning untuk self-healing jika ada ZIP
        scan_and_repair()
        return

    zip_file_path = os.path.join(zip_dir, zip_files[0])
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

                    slug = re.sub(r'[^a-z0-9]+', '-', judul.lower()).strip('-')
                    if not slug: 
                        slug = 'poster-001'
                    
                    # Gunakan lowercase untuk konsistensi folder
                    target_folder = os.path.join('posters', kategori.lower(), f"{slug}-001")
                    print(f"Target folder ditemukan: {target_folder}")

                except Exception as e:
                    print(f"Gagal parsing YAML di poster.md: {e}")
            
    if not target_folder:
        fallback_name = os.path.splitext(zip_files[0])[0]
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

    # Panggil fungsi scan & repair
    scan_and_repair()


def scan_and_repair():
    """Memindai semua folder untuk perbaikan otomatis (Self-Healing) dan update manifest"""
    print("Memindai & memperbaiki struktur folder posters...")
    
    manifest_data = {
        "kategori_list": [],
        "kategori_emoji": {},
        "total_poster": 0,
        "posters": []
    }
    
    kategori_map = {} 

    base_poster_path = "posters"
    if not os.path.exists(base_poster_path):
        print("Folder posters belum ada.")
        return

    # Loop semua folder di dalam posters
    for kategori in os.listdir(base_poster_path):
        kategori_path = os.path.join(base_poster_path, kategori)
        if os.path.isdir(kategori_path):
            
            # Normalisasi key (abaikan besar/kecil)
            kategori_key = kategori.lower()
            if kategori_key not in kategori_map:
                kategori_map[kategori_key] = kategori

            # Loop semua folder poster
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
                                    
                                    # === LOGIKA SELF-HEALING ===
                                    # Jika folder saat ini 'unknown', tapi YAML menyebut kategori lain
                                    if kategori.lower() == 'unknown' and yaml_kategori.lower() != 'unknown':
                                        target_folder = os.path.join('posters', yaml_kategori.lower(), f"{slug}-001")
                                        print(f"🛠️ Self-Healing: Memindahkan {poster_path} -> {target_folder}")
                                        
                                        # Hapus dulu folder target jika sudah ada agar tidak error
                                        if os.path.exists(target_folder):
                                            shutil.rmtree(target_folder)
                                            
                                        # Pindahkan folder
                                        shutil.move(poster_path, target_folder)
                                        # Hapus folder unknown jika sudah kosong
                                        if not os.listdir(kategori_path):
                                            os.rmdir(kategori_path)
                                            
                                        # Update path ke target yang baru
                                        poster_path = target_folder
                                        
                                    elif kategori.lower() != yaml_kategori.lower():
                                         # Jika ada ketidakcocokan nama folder tapi bukan unknown, beri warning saja
                                         print(f"⚠️ Warning: Folder '{kategori}' tidak cocok dengan YAML '{yaml_kategori}' di {poster_folder}")

                                    # === BACA DATA SETELAH SELF-HEALING ===
                                    # Ambil data dari YAML lagi (sudah terlanjur diambil di data)
                                    data['path'] = f"{yaml_kategori.lower()}/{slug}-001"
                                    
                                    current_emoji = data.get('kategori_emoji', '📂')
                                    manifest_data['kategori_emoji'][yaml_kategori.lower()] = current_emoji
                                    
                                    manifest_data['posters'].append(data)
                                    manifest_data['total_poster'] += 1

                        except Exception as e:
                            print(f"Gagal membaca {md_file_path}: {e}")

    # Build daftar kategori dari hasil mapping nama asli
    manifest_data['kategori_list'] = [kategori_map[k] for k in sorted(kategori_map.keys())]

    manifest_path = "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    
    print("Selesai! 'manifest.json' berhasil diperbarui.")
    print(f"Total Poster: {manifest_data['total_poster']}, Kategori: {manifest_data['kategori_list']}")

if __name__ == "__main__":
    main()
