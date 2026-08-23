import os
import shutil
import zipfile
import yaml
import re
import sys
import json

# Fungsi untuk penomoran dinamis (001 sampai 999, lalu 1000, 1001 dst)
def get_padded_number(num):
    return f"{num:0{max(3, len(str(num)))}d}"

def get_next_sequence(kategori_path):
    """Mencari nomor urut tertinggi di dalam folder kategori (GLOBAL per kategori)"""
    if not os.path.exists(kategori_path):
        return 1
    
    max_num = 0
    for folder in os.listdir(kategori_path):
        if os.path.isdir(os.path.join(kategori_path, folder)):
            # Ambil angka terakhir dari folder manapun di dalam kategori tersebut
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

    # === PERUBAHAN UTAMA DI SINI ===
    # Ambil daftar semua file .zip di dalam folder
    zip_files = [f for f in os.listdir(zip_dir) if f.endswith('.zip')]
    
    if not zip_files:
        print("Tidak ada file ZIP ditemukan di _uploads. Selesai.")
        scan_and_repair() # Tetap repair jika tidak ada ZIP
        return

    # Loop untuk memproses SEMUA file ZIP sampai habis
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

                        # === LOGIKA PENOMORAN DINAMIS ===
                        kategori_path = os.path.join('posters', kategori.lower())
                        next_num = get_next_sequence(kategori_path)
                        num_str = get_padded_number(next_num)
                        final_slug = f"{slug_base}-{num_str}"
                        
                        target_folder = os.path.join('posters', kategori.lower(), final_slug)
                        print(f"Target folder ditemukan (Auto-Increment Global): {target_folder}")

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

    # === SETELAH SEMUA ZIP DIPROSES, BARU PANGGIL SCAN & REPAIR ===
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

    for kategori in os.listdir(base_poster_path):
        kategori_path = os.path.join(base_poster_path, kategori)
        if os.path.isdir(kategori_path):
            
            kategori_key = kategori.lower()
            if kategori_key not in kategori_map:
                kategori_map[kategori_key] = kategori

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
                                    
                                    # === SELF-HEALING UNTUK FOLDER SALAH ===
                                    if kategori.lower() == 'unknown' and yaml_kategori.lower() != 'unknown':
                                        # Dapatkan nomor urut global terbaru untuk kategori baru
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
                                        
                                    elif kategori.lower() != yaml_kategori.lower():
                                         print(f"⚠️ Warning: Folder '{kategori}' tidak cocok dengan YAML '{yaml_kategori}' di {poster_folder}")

                                    # === BACA DATA UNTUK MANIFEST ===
                                    # Mengambil nama folder yang sebenarnya setelah pindah
                                    real_folder_name = os.path.basename(poster_path)
                                    real_kategori = os.path.basename(os.path.dirname(poster_path))
                                    data['path'] = f"{real_kategori.lower()}/{real_folder_name}"
                                    
                                    current_emoji = data.get('kategori_emoji', '📂')
                                    manifest_data['kategori_emoji'][yaml_kategori.lower()] = current_emoji
                                    
                                    manifest_data['posters'].append(data)
                                    manifest_data['total_poster'] += 1

                        except Exception as e:
                            print(f"Gagal membaca {md_file_path}: {e}")

    manifest_data['kategori_list'] = [kategori_map[k] for k in sorted(kategori_map.keys())]

    manifest_path = "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    
    print("Selesai! 'manifest.json' berhasil diperbarui.")
    print(f"Total Poster: {manifest_data['total_poster']}, Kategori: {manifest_data['kategori_list']}")

if __name__ == "__main__":
    main()

