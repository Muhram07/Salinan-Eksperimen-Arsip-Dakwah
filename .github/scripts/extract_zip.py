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
        print("❌ ERROR: Folder '_uploads' tidak ditemukan.")
        sys.exit(1)

    zip_files = [f for f in os.listdir(zip_dir) if f.endswith('.zip')]
    
    if not zip_files:
        print("📭 Tidak ada file ZIP ditemukan di _uploads. Selesai.")
        return

    zip_file_path = os.path.join(zip_dir, zip_files[0])
    print(f"📦 Memproses ZIP: {zip_file_path}")

    os.makedirs(temp_dir, exist_ok=True)

    # 1. Ektrak ZIP
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    target_folder = None
    slug_name = ""

    # 2. Baca Metadata dari poster.md
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
                    
                    slug_name = slug
                    target_folder = os.path.join('posters', kategori.lower(), f"{slug}-001")
                    print(f"✅ Target folder ditemukan: {target_folder}")

                except Exception as e:
                    print(f"⚠️ Gagal parsing YAML di poster.md: {e}")
            
    if not target_folder:
        fallback_name = os.path.splitext(zip_files[0])[0]
        target_folder = os.path.join('posters', 'unknown', fallback_name)
        slug_name = fallback_name
        print(f"⚠️ Menggunakan fallback folder: {target_folder}")

    # 3. Pindahkan file ke folder target yang sebenarnya
    os.makedirs(target_folder, exist_ok=True)
    
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            src_path = os.path.join(root, file)
            dst_path = os.path.join(target_folder, file)
            shutil.move(src_path, dst_path)

    # Hapus folder temp
    shutil.rmtree(temp_dir)
    os.remove(zip_file_path)
    print("✅ ZIP berhasil diekstrak dan dipindahkan.")

    # ============= BAGIAN BARU: SCAN & BUAT MANIFEST =============
    print("📊 Memindai seluruh folder posters untuk memperbarui indeks...")
    
    manifest_data = {
        "kategori_list": [],
        "total_poster": 0,
        "posters": []
    }
    kategori_set = set()

    # Scan semua folder poster
    base_poster_path = "posters"
    if os.path.exists(base_poster_path):
        for kategori in os.listdir(base_poster_path):
            kategori_path = os.path.join(base_poster_path, kategori)
            if os.path.isdir(kategori_path):
                kategori_set.add(kategori)
                
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
                                        # Tambahkan path folder untuk akses gambar
                                        rel_path = f"{kategori}/{poster_folder}"
                                        data['path'] = rel_path
                                        manifest_data['posters'].append(data)
                                        manifest_data['total_poster'] += 1
                            except Exception as e:
                                print(f"Gagal membaca {md_file_path}: {e}")

    manifest_data['kategori_list'] = sorted(list(kategori_set))

    # Tulis manifest.json ke root repositori
    manifest_path = "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    
    print("🎉 Selesai! 'manifest.json' berhasil diperbarui di root repository.")
    print(f"📊 Total Poster: {manifest_data['total_poster']}, Kategori: {manifest_data['kategori_list']}")

if __name__ == "__main__":
    main()￼Enter
