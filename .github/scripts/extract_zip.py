import os
import shutil
import zipfile
import yaml
import re
import sys

def main():
    zip_dir = '_uploads'
    temp_dir = '_temp_extract'

    # Validasi: Apakah folder _uploads sudah ada?
    if not os.path.exists(zip_dir):
        print("❌ ERROR: Folder '_uploads' tidak ditemukan. Pastikan Anda sudah membuat folder _uploads di root repositori!")
        sys.exit(1)

    # Cari file .zip di folder _uploads
    zip_files = [f for f in os.listdir(zip_dir) if f.endswith('.zip')]
    
    if not zip_files:
        print("📭 Tidak ada file ZIP ditemukan di _uploads. Selesai.")
        return

    zip_file_path = os.path.join(zip_dir, zip_files[0])
    print(f"📦 Memproses ZIP: {zip_file_path}")

    # Buat folder temporary untuk ekstrak
    os.makedirs(temp_dir, exist_ok=True)

    # 1. Ektrak ZIP ke folder temporary
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    target_folder = None

    # 2. Baca Metadata dari poster.md
    md_path = os.path.join(temp_dir, 'poster.md')
    if os.path.exists(md_path):
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Ambil bagian YAML di antara garis "---"
            yaml_match = re.search(r'---(.*?)---', content, re.DOTALL)
            if yaml_match:
                try:
                    data = yaml.safe_load(yaml_match.group(1))
                    kategori = data.get('kategori', 'Unknown')
                    judul = data.get('judul', 'Unknown')

                    # Ubah judul menjadi slug (contoh: Jangan Merasa Aman -> jangan-merasa-aman)
                    slug = re.sub(r'[^a-z0-9]+', '-', judul.lower()).strip('-')
                    if not slug: 
                        slug = 'poster-001'
                    
                    target_folder = os.path.join('posters', kategori.lower(), f"{slug}-001")
                    print(f"✅ Target folder ditemukan: {target_folder}")

                except Exception as e:
                    print(f"⚠️ Gagal parsing YAML di poster.md: {e}")
            
    # Jika gagal membaca MD atau tidak ada MD, fallback ke nama folder ZIP
    if not target_folder:
        fallback_name = os.path.splitext(zip_files[0])[0]
        target_folder = os.path.join('posters', 'unknown', fallback_name)
        print(f"⚠️ Menggunakan fallback folder: {target_folder}")

    # 3. Pindahkan file ke folder target yang sebenarnya
    os.makedirs(target_folder, exist_ok=True)
    
    # Pindahkan semua isi temporary ke target
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            src_path = os.path.join(root, file)
            dst_path = os.path.join(target_folder, file)
            shutil.move(src_path, dst_path)

    # 4. Buat .gitkeep agar GitHub mendeteksi foldernya
    gitkeep_path = os.path.join(target_folder, '.gitkeep')
    with open(gitkeep_path, 'w') as f:
        f.write('')

    # 5. Bersihkan file sementara
    shutil.rmtree(temp_dir)
    os.remove(zip_file_path)
    print("🎉 Berhasil! ZIP diproses dan file dipindahkan ke folder target.")

if __name__ == "__main__":
    main()
